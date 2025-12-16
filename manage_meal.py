from nicegui import ui
import asyncio

from navigate import navigate_to
from state import STATE, handle_logout
from database import get_all_meals, insert_meal, update_meal, delete_meal
from typing import Dict, Optional, Any, List

#global表格物件
meal_table = None

#刷新餐點資料
def refresh_meal_table():
    global meal_table
    meal_data = get_all_meals()
    if meal_table:
        meal_table.rows = meal_data
        meal_table.update()

#新增或編輯餐點的對話框
def meal_dialog(meal_data: Optional[Dict[str, Any]] = None):
    is_editing = meal_data is not None
    data = meal_data or {}
    
    original_mid = data.get('MID')
    original_name = data.get('Name', '')
    original_price = data.get('Price', 0.0)
    original_picname = data.get('PicName', '')
    original_is_available = data.get('IsAvailable', True) 

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        dialog.props('persistent') 
        ui.label('編輯餐點' if is_editing else '新增餐點').classes('text-2xl font-bold')
        
        name_input = ui.input('餐點名稱*', value=original_name).classes('w-full')
        price_input = ui.number('價格*', value=original_price, min=1, precision=2).classes('w-full')
        picname_input = ui.input('圖片名稱 (Picname)', value=original_picname).classes('w-full')
        is_available_input = ui.select([True, False], 
                                 label='是否開放點餐', 
                                 value=original_is_available).classes('w-full')
        
        async def save_meal():
            name = name_input.value.strip()
            price = price_input.value
            picname = picname_input.value.strip()
            is_available = is_available_input.value #獲取True/False
            
            if not name or price is None or price <= 0:
                ui.notify('餐點名稱和有效價格為必填項。', color='warning')
                return
            
            success = False
            
            if is_editing:
                #編輯模式
                success = update_meal(original_mid, name, price, picname, is_available)
                action = '更新'
            else:
                #新增模式
                insert_id = insert_meal(name, price, picname, is_available)
                success = insert_id is not None
                action = '新增'

            if success:
                ui.notify(f'{action}餐點 "{name}" 成功。', color='positive')
                await asyncio.sleep(0.5) 
                refresh_meal_table() 
                dialog.close()
            else:
                ui.notify(f'{action}餐點失敗，請檢查名稱是否重複或資料庫連線。', color='negative')

        with ui.row().classes('justify-end w-full mt-4 gap-4'):
            ui.button('取消', on_click=dialog.close).props('flat')
            ui.button('儲存', on_click=save_meal).classes('bg-primary')
    
    dialog.open()

#刪除餐點確認的對話框
def delete_meal_confirmation(meal_data: Dict):
    
    async def confirm_delete():
        if delete_meal(meal_data['MID']):
            ui.notify(f"成功刪除餐點: {meal_data['Name']}", color='positive')
            await asyncio.sleep(0.5)
            refresh_meal_table()
            dialog.close()
        else:
            ui.notify('刪除失敗，請檢查資料庫連線。', color='negative')

    with ui.dialog() as dialog, ui.card():
        ui.label(f"確定要刪除餐點嗎？").classes('text-lg')
        ui.label(f"餐點名稱: {meal_data['Name']}").classes('text-xl font-bold text-negative')
        ui.label("此操作無法復原。").classes('text-sm text-warning')

        with ui.row().classes('justify-end w-full mt-4 gap-4'):
            ui.button('取消', on_click=dialog.close).props('flat')
            ui.button('確認刪除', on_click=confirm_delete).classes('bg-negative')
            
    dialog.open()

#價格格式
def format_price(val: int):
    if val is None:
        return 'NT$ 0'
    return f'NT$ {val: int}'
        
#可不可販售的格式
def format_is_available(val: bool):
    return '可販售' if val else '停售'

#餐點管理主頁面
@ui.page('/manage_meal')
def manage_meal_page():
    global meal_table
    
    #檢查登入狀態
    if not STATE['is_login']:
        navigate_to('/login')
        return

    ui.add_head_html('<title>餐點管理</title>')

    with ui.header().classes('items-center justify-between'):
        ui.label(f'餐點管理 ({STATE["account"]})').classes('text-lg')
        ui.button('回選擇頁', on_click=lambda: navigate_to('/staff'), icon='arrow_back').props('flat color=white')
        ui.button('登出', on_click=lambda: handle_logout(), icon='logout').props('flat color=white')

    with ui.column().classes('p-4 w-full items-start'):
        
        #頂部新增餐點按鈕
        ui.button('新增餐點', icon='add', on_click=lambda: meal_dialog()).classes('mb-4 bg-positive')

        #定義表格header
        meal_columns: List[Dict[str, Any]] = [
            {'name': 'mid', 'label': 'ID', 'field': 'MID', 'required': True, 'align': 'left'},
            {'name': 'name', 'label': '名稱', 'field': 'Name', 'required': True, 'align': 'left', 'style': 'width: 25%'},
            {'name': 'price', 'label': '價格', 'field': 'Price', 'required': True, 'align': 'left'},
            {'name': 'picname', 'label': '圖片名', 'field': 'PicName', 'required': False, 'align': 'left'},
            {'name': 'is_available', 'label': '上架狀態', 'field': 'IsAvailable', 'required': True, 'align': 'center'},
            {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center', 'style': 'width: 120px'}
        ]

        #建立餐點表格
        initial_meal_data = get_all_meals()
        meal_table = ui.table(columns=meal_columns, rows=initial_meal_data, row_key='MID').classes('w-full')
        
        #定義表格操作按鈕
        meal_table.add_slot('body-cell-actions', r"""
            <q-td :props="props">
                <q-btn flat icon="edit" color="primary" @click="$parent.$emit('edit', props.row)" />
                <q-btn flat icon="delete" color="negative" @click="$parent.$emit('delete', props.row)" />
            </q-td>
        """)
        
        #處理編輯/刪除
        meal_table.on('edit', lambda e: meal_dialog(e.args))
        meal_table.on('delete', lambda e: delete_meal_confirmation(e.args))