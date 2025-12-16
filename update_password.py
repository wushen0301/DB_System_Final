from nicegui import ui

from navigate import navigate_to
from state import STATE, handle_logout # 導入狀態和登出
from database import update_password

@ui.page('/update_password')
def update_password_page():
    #檢查登入狀態
    if not STATE['is_login']:
        navigate_to('/login')
        return

    current_account = STATE['account']

    ui.add_head_html('<title>修改密碼</title>')
    
    #頂部導航
    with ui.header().classes('items-center justify-between'):
        ui.label(f'修改密碼 ({current_account})').classes('text-lg')
        ui.button('回選擇頁', on_click=lambda: navigate_to('/staff'), icon='arrow_back').props('flat color=white')
        ui.button('登出', on_click=lambda: handle_logout(), icon='logout').props('flat color=white')

    #主要修改密碼表單
    with ui.card().classes('absolute-center w-96'):
        ui.label('請輸入新密碼').classes('text-2xl font-bold mb-4')
        
        new_password_ref = ui.input('新密碼', password=True).props('type=password toggle-password').classes('w-full')
        confirm_password_ref = ui.input('確認新密碼', password=True).props('type=password toggle-password').classes('w-full')
        
        def save_new_password():
            new_password = new_password_ref.value
            confirm_password = confirm_password_ref.value
            
            if not new_password or not confirm_password:
                ui.notify('新密碼和確認密碼不能為空。', color='warning')
                return
            
            if new_password != confirm_password:
                ui.notify('兩次密碼輸入不一致。', color='negative')
                return
            
            is_update = update_password(current_account, new_password)        
            if(is_update):
                ui.notify(f'成功修改密碼。', color='positive')
            else:
                ui.notify('發生錯誤，請稍後重試。', color='warning')

        ui.button('確認修改', on_click=save_new_password).classes('w-full mt-4 bg-primary')