from nicegui import ui

from navigate import navigate_to
from state import STATE, handle_logout
from database import get_all_orders, get_order_details, update_order_status
from typing import Dict, Optional, Any, List

#全域表格物件，用於後續刷新
order_table = None

#訂單明細與狀態更新對話框
def detail_and_status_dialog(order_data: Dict):
    oid = order_data['OID']
    
    #獲取訂單明細
    details = get_order_details(oid)
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
        
        ui.label(f'訂單明細與處理 - OID: {oid}').classes('text-2xl font-bold')
        ui.label(f"取餐方式: {order_data['ServingMethod']}").classes('text-lg')
        ui.separator()

        #訂單明細清單
        with ui.column().classes('w-full max-h-64 overflow-y-auto mb-4'):
            if not details:
                ui.label("無明細數據").classes('text-warning')
            else:
                #明細表格header
                with ui.row().classes('w-full justify-between font-bold text-base bg-primary p-2 rounded'):
                    ui.label("餐點名稱").classes('w-4/12')
                    ui.label("數量").classes('w-3/12 text-center')
                    ui.label("小計").classes('w-3/12 text-right')
                
                #明細項目
                for item in details:
                    with ui.row().classes('w-full justify-between items-center py-1 border-b border-gray-200'):
                        ui.label(f"{item['MealName']}").classes('w-4/12')
                        ui.label(f"{item['Quantity']}").classes('w-3/12 text-center')
                        ui.label(f"NT$ {item['Total']:.0f}").classes('w-3/12 text-right font-bold')
        
        #總金額顯示
        ui.label(f"總金額: NT$ {order_data['TotalAmount']:.0f}").classes('text-xl font-bold text-right w-full mt-2')
        ui.separator()
        
        #狀態更新並刷新介面
        def set_status(new_status: str):
            if update_order_status(oid, new_status):
                ui.notify(f"訂單 OID:{oid} 狀態更新為 {new_status} 成功！", color='positive')
                #關閉對話框並刷新order_table
                dialog.close() 
                refresh_order_table()
            else:
                ui.notify('狀態更新失敗。', color='negative')

        with ui.row().classes('justify-start w-full mt-4 gap-4'):
            #完成訂單按鈕
            ui.button('完成訂單', 
                      on_click=lambda: set_status('Completed'), 
                      color='positive').props('icon=done_all')
                      
            ui.button('關閉', on_click=dialog.close).props('flat color=grey')

    dialog.open()

#重新載入訂單資料並更新表格
def refresh_order_table():
    global order_table
    order_data = get_all_orders()
    if order_table:
        #直接更新表格的rows資料
        order_table.rows = order_data
        order_table.update()
        ui.notify('訂單列表已刷新', position='bottom-right', timeout=1000)


#訂單管理頁面
@ui.page('/manage_order')
def manage_order_page():
    global order_table
    
    #防止直接輸入網址跳過登入
    if not STATE['is_login']:
        navigate_to('/login')
        return

    ui.add_head_html('<title>訂單管理</title>')

    with ui.header().classes('items-center justify-between bg-primary'):
        ui.label(f'訂單管理 ({STATE["account"]})').classes('text-lg')
        ui.button('回選擇頁', on_click=lambda: navigate_to('/staff'), icon='arrow_back').props('flat color=white')
        ui.button('登出', on_click=lambda: handle_logout(), icon='logout').props('flat color=white')

    with ui.column().classes('p-4 w-full items-start'):
        
        ui.label('待處理訂單列表').classes('text-3xl font-bold mb-4')
        
        #定義表格Headers
        order_columns: List[Dict[str, Any]] = [
            {'name': 'oid', 'label': '訂單號', 'field': 'OID', 'required': True, 'align': 'left', 'style': 'width: 80px'},
            {'name': 'time', 'label': '時間', 'field': 'Time', 'required': True, 'align': 'left', 'style': 'width: 150px'},
            {'name': 'total', 'label': '總金額(NT$)', 'field': 'TotalAmount', 'required': True, 'align': 'right'},
            {'name': 'method', 'label': '取餐方式', 'field': 'ServingMethod', 'required': True, 'align': 'center'},
            {'name': 'status', 'label': '狀態', 'field': 'Status', 'required': True, 'align': 'center'},
            {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center', 'style': 'width: 100px'}
        ]

        #建立訂單表格
        initial_order_data = get_all_orders()
        
        order_table = ui.table(columns=order_columns, rows=initial_order_data, row_key='OID').classes('w-full')
        
        #定義表格操作按鈕(用 row-template)
        
        #自定義狀態顯示(雖然只會有 Preparing)
        order_table.add_slot('body-cell-Status', r'''
            <q-td :props="props">
                <q-badge color="warning" label="準備中" />
            </q-td>
        ''')
        
        #操作按鈕(查看訂單詳情)
        order_table.add_slot('body-cell-actions', r"""
            <q-td :props="props">
                <q-btn flat icon="visibility" color="primary" label="查看/處理" @click="$parent.$emit('show_details', props.row)" />
            </q-td>
        """)
        
        #當表格中的按鈕被點擊時，觸發show_details事件，並呼叫detail_and_status_dialog
        order_table.on('show_details', lambda e: detail_and_status_dialog(e.args))
        
        #額外的刷新按鈕
        ui.button('手動刷新訂單', on_click=refresh_order_table, icon='refresh').classes('mt-4')