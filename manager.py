from nicegui import ui
import asyncio

from navigate import navigate_to
from state import STATE, handle_logout
from database import get_all_staff, insert_staff, update_password, delete_staff 
from typing import Dict, Optional, Any, List

#global表格物件
staff_table = None

#刷新員工資料
def refresh_staff_table():
    global staff_table
    staff_data = get_all_staff()
    if staff_table:
        staff_table.rows = staff_data
        staff_table.update()
        
#新增或編輯員工的對話框
def staff_dialog(staff_data: Optional[Dict[str, Any]] = None):
    is_editing = staff_data is not None
    data = staff_data or {}
    
    original_account = data.get('Account', '')
    original_class = data.get('Class', 'Staff')
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        dialog.props('persistent') 
        ui.label('編輯員工' if is_editing else '新增員工').classes('text-2xl font-bold')
        
        account_input = ui.input('帳號', value=original_account).classes('w-full')
        account_input.props('readonly') if is_editing else None
        class_select = ui.select(['Manager', 'Staff'], 
                                 label='職位', 
                                 value=original_class).classes('w-full')
        if is_editing:
            class_select.props('readonly')
            
        #密碼輸入：編輯時可選，新增時必填
        password_label = '密碼*' if not is_editing else '修改密碼 (留空則不修改)'
        password_input = ui.input(password_label, password=True).props('type=password toggle-password').classes('w-full')
        
        if is_editing:
            ui.label("編輯模式下，帳號和職位不可修改，只能更新密碼。").classes('text-sm text-warning')
            
        async def save_staff():
            account = account_input.value.strip()
            password = password_input.value.strip()
            staff_class = class_select.value #只有新增時使用
            
            if not account:
                ui.notify('帳號不能為空。', color='warning')
                return

            if is_editing:
                #編輯模式(只能修改密碼)
                if password:
                    success = update_password(account, password)
                    if success:
                        ui.notify(f'更新員工 "{account}" 密碼成功。', color='positive')
                    else:
                        ui.notify('密碼更新失敗，請檢查資料庫。', color='negative')
                        return
                else:
                    ui.notify('未輸入新密碼，未進行任何修改。', color='info')
                    dialog.close()
                    return

            else:
                #新增模式
                if not password:
                    ui.notify('新增員工必須輸入密碼。', color='warning')
                    return
                
                insert_id = insert_staff(account, password, staff_class)
                success = insert_id is not None
                
                if success:
                    ui.notify(f'新增員工帳號 "{account}" 成功。', color='positive')
                else:
                    ui.notify('新增員工帳號失敗，可能帳號已存在。', color='negative')
                    return

            #操作成功後延遲並刷新/關閉
            await asyncio.sleep(0.5) 
            refresh_staff_table() 
            dialog.close()

        with ui.row().classes('justify-end w-full mt-4 gap-4'):
            ui.button('取消', on_click=dialog.close).props('flat')
            ui.button('儲存', on_click=save_staff).classes('bg-primary')
    
    dialog.open()

#刪除員工確認的對話框
def delete_staff_confirmation(staff_data: Dict):
    account_to_delete = staff_data['Account']

    async def confirm_delete():
        if account_to_delete == STATE['account']:
             ui.notify(f"錯誤：您不能刪除自己的帳號。", color='negative')
             dialog.close()
             return

        if delete_staff(account_to_delete):
            ui.notify(f"成功刪除員工帳號: {account_to_delete}", color='positive')
            await asyncio.sleep(0.5)
            refresh_staff_table() 
            dialog.close()
        else:
            ui.notify('刪除失敗，請檢查資料庫連線。', color='negative')

    with ui.dialog() as dialog, ui.card():
        ui.label(f"確定要刪除員工帳號嗎？").classes('text-lg')
        ui.label(f"帳號: {account_to_delete}").classes('text-xl font-bold text-negative')
        ui.label("此操作無法復原。").classes('text-sm text-warning')

        with ui.row().classes('justify-end w-full mt-4 gap-4'):
            ui.button('取消', on_click=dialog.close).props('flat')
            ui.button('確認刪除', on_click=confirm_delete).classes('bg-negative')
            
    dialog.open()

#管理員主頁面
@ui.page('/manager')
def manager_management_page():
    global staff_table
    
    #檢查登入狀態和權限
    if not STATE['is_login'] or not STATE['is_manager']:
        navigate_to('/login')
        return

    ui.add_head_html('<title>管理員工</title>')

    with ui.header().classes('items-center justify-between'):
        ui.label(f'員工管理 ({STATE["account"]})').classes('text-lg')
        ui.button('回選擇頁', on_click=lambda: navigate_to('/staff'), icon='arrow_back').props('flat color=white')
        ui.button('登出', on_click=lambda: handle_logout(), icon='logout').props('flat color=white')

    with ui.column().classes('p-4 w-full items-start'):
        
        ui.button('新增員工', icon='person_add', on_click=lambda: staff_dialog()).classes('mb-4 bg-positive')
        
        #定義表格header
        staff_columns: List[Dict[str, Any]] = [
            {'name': 'sid', 'label': 'ID', 'field': 'SID', 'required': True, 'align': 'left'},
            {'name': 'account', 'label': '帳號', 'field': 'Account', 'required': True, 'align': 'left'},
            {'name': 'class', 'label': '職位', 'field': 'Class', 'required': True, 'align': 'center'},
            {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center', 'style': 'width: 120px'}
        ]

        #建立員工表格
        initial_staff_data = get_all_staff()
        staff_table = ui.table(columns=staff_columns, rows=initial_staff_data).classes('w-full')
        
        #定義表格操作按鈕(使用row-template)
        staff_table.add_slot('body-cell-actions', r"""
            <q-td :props="props">
                <q-btn flat icon="edit" color="primary" @click="$parent.$emit('edit', props.row)" />
                <q-btn flat icon="delete" color="negative" @click="$parent.$emit('delete', props.row)" />
            </q-td>
        """)
        
        #處理編輯/刪除
        staff_table.on('edit', lambda e: staff_dialog(e.args))
        staff_table.on('delete', lambda e: delete_staff_confirmation(e.args))