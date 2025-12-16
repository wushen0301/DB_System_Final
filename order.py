from nicegui import ui, app # 確保 app 模組被導入
import asyncio

from navigate import navigate_to
from database import get_all_meals, submit_full_order
from typing import Dict, List, Any, Optional

#購物車(global)
CART: Dict[int, Dict[str, Any]] = {}

#定義圖片資料夾路徑
PICTURE_FOLDER = 'picture' 
#註冊文件路徑
app.add_static_files('/pictures', PICTURE_FOLDER) 

#用於在對話框中刷新主頁面狀態提示的標籤
cart_summary_label: Optional[ui.label] = None

#計算購物車總金額
def calculate_total() -> int:
    return sum(item['total'] for item in CART.values())

#更新購物車總結標籤
def update_summary_label(summary_label: ui.label):
    total = calculate_total()
    count = sum(item['quantity'] for item in CART.values())
    summary_label.set_text(f"🛒 購物車總計: NT$ {total:.0f} (共 {count} 份餐點)")

#在確認的對話框中修改餐點數量
def update_cart_item(mid: int, new_quantity: int, dialog: ui.dialog):
    global cart_summary_label
    
    #數量為0則刪除
    if new_quantity <= 0 and mid in CART:
        del CART[mid]
        ui.notify('餐點已移除', color='negative', timeout=1000)
    elif new_quantity > 0 and mid in CART:
        item = CART[mid]
        item['quantity'] = new_quantity
        item['total'] = item['price'] * new_quantity
        ui.notify(f"已更新 {item['name']} 數量為 {new_quantity}", color='info', timeout=1000)
        
    #重新打開確認對話框，更新內容
    dialog.close()
    if cart_summary_label:
        update_summary_label(cart_summary_label) #更新頁面底部的總結
        
    #延遲後重新開啟對話框
    ui.timer(0.1, lambda: confirm_order_dialog(), once=True)

#從主點餐頁面把餐點加入購物車
def add_to_cart_from_menu(meal: Dict[str, Any], quantity_select: ui.select, summary_label: ui.label):
    quantity = int(quantity_select.value)
    if quantity <= 0:
        ui.notify('請選擇數量。', color='warning')
        return

    mid = meal['MID']
    price = int(round(meal['Price']))
    
    if mid not in CART:
        CART[mid] = {
            'mid': mid,
            'name': meal['Name'],
            'price': price, 
            'picname': meal['PicName'],
            'quantity': 0,
            'total': 0 
        }
    
    #更新數量和總價格 (修改字典內部元素，不需要 global)
    CART[mid]['quantity'] += quantity
    CART[mid]['total'] = CART[mid]['quantity'] * price
    
    ui.notify(f"已加入 {quantity} 份 {meal['Name']}", color='positive', icon='add_shopping_cart')
    update_summary_label(summary_label)
    
    #重設下拉式選單為0
    quantity_select.set_value(0)


#確認點餐清單對話框
def confirm_order_dialog():
    if not CART:
        ui.notify('購物車是空的，請先點餐。', color='warning')
        return

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
        ui.label('確認您的訂單清單').classes('text-2xl font-bold mb-4')
        
        #訂單明細
        with ui.column().classes('w-full border p-3 rounded-lg bg-primary max-h-80 overflow-y-auto'):
            
            for mid, item in list(CART.items()): 
                with ui.row().classes('w-full items-center justify-between py-2 border-b last:border-b-0'):
                    
                    #名稱
                    ui.label(f"{item['name']}").classes('w-1/3 text-lg font-semibold')
                    quantity_select = ui.select(list(range(0, 100)), 
                                                 value=item['quantity'], 
                                                 label='數量',
                                                 on_change=lambda e, m=mid: update_cart_item(m, int(e.value), dialog)).classes('w-20')
                    
                    #顯示小計
                    ui.label(f"NT$ {item['total']:.0f}").classes('text-lg font-bold w-1/4 text-right')

        #底部總結與操作按鈕
        total_amount = calculate_total()
        ui.label(f"總計: NT$ {total_amount:.0f}").classes('text-2xl font-extrabold text-red-600 mt-4 w-full text-right')
        
        #取餐方式選擇
        serving_method_select = ui.select(['DineIn', 'TakeOut'], 
                                             value='DineIn', 
                                             label='取餐方式').classes('w-32 mt-4')

        with ui.row().classes('w-full justify-between mt-4'):
            #繼續點餐按鈕
            ui.button('繼續點餐', on_click=dialog.close).props('flat')
            
            #送出訂單按鈕
            ui.button('送出訂單', icon='send', color='primary', 
                      on_click=lambda: place_order(dialog, serving_method_select.value)).classes('bg-positive')
    
    dialog.open()


#送出訂單處理
#處理結帳跟提交訂單
def place_order(dialog: ui.dialog, serving_method: str):
    global CART, cart_summary_label
    
    if not CART:
        ui.notify('購物車是空的，無法結帳。', color='negative')
        return

    #items列表
    items_to_submit = list(CART.values())
    
    #提交訂單到資料庫
    oid = submit_full_order(items_to_submit, serving_method)
    
    if oid:
        ui.notify(f'訂單提交成功！訂單號: {oid}', color='positive', timeout=5000)
        
        #清空購物車
        CART = {}
        dialog.close()
        
        #更新主頁面總結標籤
        if cart_summary_label:
            update_summary_label(cart_summary_label) 
            
        #顯示成功頁面
        success_dialog = ui.dialog()
        with success_dialog, ui.card():
            ui.label(f"您的訂單 (編號: {oid}) 已送出。").classes('text-2xl text-positive')
            ui.label("感謝您的點餐！").classes('text-lg')
            #點擊後重新載入，清空所有狀態
            ui.button('繼續點餐', on_click=lambda: ui.open('/order', new_tab=False)).classes('mt-4')
        success_dialog.open()

    else:
        ui.notify('訂單提交失敗，請重試。', color='negative')

#點餐主頁面
@ui.page('/order')
def customer_order_page():
    global cart_summary_label 
    
    ui.add_head_html('<title>點餐</title>')
    
    #頂部導航
    with ui.header().classes('items-center justify-between'):
        ui.label('歡迎點餐').classes('text-2xl font-bold')
        ui.button('回首頁', on_click=lambda: navigate_to('/'), icon='home').props('flat color=white')

    #菜單列表
    with ui.column().classes('w-full p-4 items-center'):
        ui.label('今日菜單').classes('text-4xl font-bold mb-6 text-primary')
        menu_container = ui.row().classes('w-full max-w-7xl gap-6 justify-center')
        
        meals = get_all_meals()
        available_meals = [m for m in meals if m.get('IsAvailable', 0)] 
        
        with menu_container:
            if not available_meals:
                ui.label("目前沒有可供點選的餐點。").classes('text-2xl text-warning')
            
            for meal in available_meals:
                with ui.card().classes('w-80 h-auto shadow-xl'):
                    
                    #圖片顯示
                    picname = meal.get('PicName')
                    img_src = f'/pictures/{picname}' if picname else 'https://picsum.photos/300/200'
                    ui.image(img_src).classes('rounded-t-lg h-40 w-full object-cover')
                    
                    with ui.card_section():
                        ui.label(meal['Name']).classes('text-xl font-bold')
                        ui.label(f"NT$ {int(round(meal['Price'])):.0f}").classes('text-lg text-primary')
                        
                        #數量選擇(預設0, 最高10)
                        quantity_select = ui.select(list(range(0, 11)), 
                                                     value=0, 
                                                     label='數量').classes('w-24 mt-3')
                        
                        #加入購物車按鈕
                        ui.button('加入購物車', icon='add_shopping_cart', color='positive',
                                  on_click=lambda m=meal, q=quantity_select: add_to_cart_from_menu(m, q, cart_summary_label))
                        
    #頁面最下方的確認點餐清單/總結
    with ui.footer().classes('bg-grey-200 p-4 shadow-xl border-t border-gray-400'):
        with ui.row().classes('w-full justify-between items-center max-w-7xl mx-auto'):
            
            #購物車總結標籤
            cart_summary_label = ui.label("購物車總計: NT$ 0 (共 0 份餐點)").classes('text-xl font-bold')
            
            #確認點餐按鈕
            ui.button('確認點餐清單', icon='list_alt', color='primary', 
                      on_click=confirm_order_dialog)
            
    #首次載入時更新總結
    if cart_summary_label:
        update_summary_label(cart_summary_label)