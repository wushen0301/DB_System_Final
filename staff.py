from nicegui import ui
from navigate import navigate_to
from state import STATE, handle_logout 

@ui.page('/staff')
def staff_selection_page():
    #防止直接輸入網址跳過登入。
    if not STATE['is_login']:
        navigate_to('/login')
        return

    ui.add_head_html('<title>員工操作選擇</title>')

    # 頂部導航
    with ui.header().classes('items-center justify-between'):
        ui.label(f'員工操作選擇 ({STATE["account"]})').classes('text-lg')
        ui.button('登出', on_click=lambda: handle_logout(), icon='logout').props('flat color=white')

    #主要內容區塊：兩個大按鈕 (負責導向到管理頁面)
    with ui.column().classes('absolute-center items-center gap-8'):
        ui.label('請選擇要進行的操作').classes('text-4xl font-bold text-primary')
        
        with ui.row().classes('gap-12'):
            ui.button('管理餐點', 
                      on_click=lambda: navigate_to('/manage_meal'),
                      icon='restaurant_menu').props('size=xl color=green-7 shadow=5').classes('w-60 h-40 text-xl')
            ui.button('管理員工', 
                      on_click=lambda: check_manager_access(),
                      icon='people').props('size=xl color=red-7 shadow=5').classes('w-60 h-40 text-xl')
        with ui.row().classes('gap-12'):
            ui.button('處理訂單', 
                      on_click=lambda: navigate_to('/manage_order'),
                      icon='receipt').props('size=xl color=indigo-7 shadow=5').classes('w-60 h-40 text-xl')
        ui.button('修改密碼',
                  on_click=lambda: navigate_to('/update_password'),
                  icon='lock_reset').props('size=md color=blue-7 shadow=5').classes('w-60 text-lg')

#權限檢查
def check_manager_access():
    if STATE['is_manager']:
        navigate_to('/manager')
    else:
        ui.notify('權限不足！只有管理員可以管理員工。', color='negative', icon='lock')