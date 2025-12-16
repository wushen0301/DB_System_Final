from database import login
from typing import Optional, Dict, Any
import sqlite3

from nicegui import ui, Client
from navigate import navigate_to
from state import STATE, handle_login
import staff

#登入頁面
@ui.page('/login') 
def login_page():
    # 頁面載入時檢查全域狀態
    if STATE['is_login']:
        #target_page = '/manager' if STATE['is_manager'] else '/work'
        #navigate_to(target_page)
        navigate_to('/staff')
        return

    ui.add_head_html('<title>員工登入</title>')
    
    with ui.header().classes('items-center justify-between'):
        ui.label('員工登入').classes('text-lg')
        ui.button('回首頁', on_click=lambda: navigate_to('/'), icon='home').props('flat color=white')
        
    with ui.card().classes('absolute-center w-80'):
        ui.label('請輸入帳號密碼').classes('text-2xl font-bold mb-4')
        
        account_ref = ui.input('帳號').props().classes('w-full')
        password_ref = ui.input('密碼', password=True) \
            .props('type=password toggle-password') \
            .classes('w-full')
        
        # 連接到 handle_login
        ui.button('登入', 
                  on_click=lambda: handle_login(account_ref.value, password_ref.value)
                 ).classes('w-full mt-4 bg-primary')