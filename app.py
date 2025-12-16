from nicegui import ui

#各頁面、db管理、跳轉函式的import
#確保各頁面都被導入
import login, staff, manage_meal, manager, manage_order, state, order, update_password
import database
from navigate import navigate_to

ui.run.title = '點餐系統' #NiceGUI 啟動時的視窗標題(網頁名稱)

#主頁面(只有兩個大按鈕)
@ui.page('/')
def index_page():
    ui.add_head_html('<title>點餐系統首頁</title>')
    
    #使用ui.column並搭配absolute-center將內容垂直水平居中
    with ui.column().classes('absolute-center items-center gap-8'):
        ui.label('歡迎使用點餐系統').classes('text-4xl font-bold text-primary')
        
        with ui.row().classes('gap-12'):
            #員工使用按鈕，跳轉到 /login
            ui.button('員工使用', 
                      on_click=lambda: navigate_to('/login'),   #嘗試改成呼叫輔助函式的方法
                      icon='badge').props('size=xl color=red-7 shadow=5').classes('w-60 h-40 text-xl')
            
            #客人點餐系統按鈕，跳轉到 /order
            ui.button('客人點餐系統', 
                      on_click=lambda: navigate_to('/order'),   #嘗試改成呼叫輔助函式的方法
                      icon='restaurant_menu').props('size=xl color=green-7 shadow=5').classes('w-60 h-40 text-xl')

#應用程式啟動
if __name__ in {"__main__", "__mp_main__"}:
    #確保資料庫已經建立(初始化)
    database.initialize_database()
    #啟動NiceGUI應用程式，設為深色主題
    ui.run(title=ui.run.title, dark=True)