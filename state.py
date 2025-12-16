from nicegui import ui, Client
from navigate import navigate_to
from database import login
from typing import Optional, Dict, Any
import sqlite3

#登入狀態(直接使用全域變數，先不理會資安部分)
STATE: Dict[str, Any] = {
    'is_login': False,
    'is_manager': False,
    'account': None
}
#處理登入
async def handle_login(account: str, password: str):
    global STATE
    user_data = login(account, password)
    if isinstance(user_data, tuple):
        #驗證成功
        #user_data(SID, account, class)
        STATE['is_login'] = True
        STATE['account'] = user_data[1]
        STATE['is_manager'] = (user_data[2] == 'Manager')
        
        ui.notify(f"登入成功! 歡迎, {STATE['account']}", color='positive')

        #根據Class做頁面跳轉
        #target_page = '/manager' if STATE['is_manager'] else '/work'
        #navigate_to(target_page)
        navigate_to('/staff')
    else:
        #登入失敗
        ui.notify('登入失敗，帳號或密碼錯誤。', color='negative')

#處理登出
async def handle_logout():
    global STATE
    STATE['is_login'] = False
    STATE['is_manager'] = False
    STATE['account'] = None

    ui.notify('已登出。', color='info')
    navigate_to('/login')