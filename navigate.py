from nicegui import ui, app, Client
from typing import Callable, Any

#處理頁面跳轉的輔助函式
def navigate_to(route: str):
    try:
        #嘗試使用NiceGUI推薦的方式
        ui.open(route) 
    except AttributeError:
        #如果ui.open失敗，使用Client物件的open方法
        #注意:這裡需要確保Client在當前context中
        if ui.context.client is not None:
             ui.context.client.open(route)
        else:
             #最終 fallback 方式，通常會成功
             app.open(route)