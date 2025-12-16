import sqlite3
import os
from typing import List, Dict, Optional, Any

#建立資料庫，檔案名稱和路徑
DB='ordering_system.db'

#建立並return資料庫連線物件
def get_db_connection():
    try:
        conn = sqlite3.connect(DB)
        return conn
    
    except sqlite3.Error as e:
        print(f"資料庫連線錯誤: {e}")
        return None

#建立所有需要的資料表
def create_tables(conn):
    cursor = conn.cursor()

    #餐點: Meal(MID, Name, Price, PicName, IsAvailable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Meal (
        MID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL UNIQUE,
        Price INTEGER NOT NULL,
        PicName TEXT,
        IsAvailable INTEGER NOT NULL DEFAULT 1  --1為販售中，0為停售
    );
    """)

    #員工: Staff(SID, Account, Password, Class)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staff (
        SID INTEGER PRIMARY KEY AUTOINCREMENT,
        Account TEXT NOT NULL UNIQUE,
        Password TEXT NOT NULL,
        Class TEXT NOT NULL CHECK(Class IN ('Manager', 'Staff'))
    );
    """)

    #訂單: Order(OID, Time, TotalAmount, Status, ServingMethod)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS 'Order' (
        OID INTEGER PRIMARY KEY AUTOINCREMENT,
        Time TEXT NOT NULL,
        TotalAmount INTEGER NOT NULL,
        Status TEXT NOT NULL CHECK(Status IN ('Preparing', 'Completed')),
        ServingMethod TEXT NOT NULL CHECK(ServingMethod IN ('DineIn', 'TakeOut'))
    );
    """)
    
    #訂單明細: OrderDetail(ODID, Order_ID, Meal_ID, Quantity, PriceAtOrder, Total)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS OrderDetail (
        ODID INTEGER PRIMARY KEY AUTOINCREMENT,
        Order_ID INTEGER NOT NULL,
        Meal_ID INTEGER NOT NULL,
        Quantity INTEGER NOT NULL,
        PriceAtOrder INTEGER NOT NULL,
        Total INTEGER NOT NULL,
        FOREIGN KEY (Order_ID) REFERENCES "Order" (OID) ON DELETE CASCADE,
        FOREIGN KEY (Meal_ID) REFERENCES Meal (MID)
    );
    """)

    conn.commit()
    print("所有資料表已成功建立或已存在。")

#核心初始化函式
def initialize_database():
    """
    初始化資料庫：連線、建表、插入預設資料。
    """
    conn = get_db_connection()
    if conn:
        create_tables(conn)         # 使用連線物件建表
        #insert_default_data(conn)   # 使用連線物件插入資料
        conn.close()
        print(f"資料庫初始化完成，檔案名: {DB}")
    else:
        print("無法建立資料庫連線，初始化失敗。")

#員工登入驗證
def login(account: str, password: str) -> Optional[tuple]:
    """
    透過帳號和密碼驗證員工，成功則回傳員工資料 (SID, Account, Class)。
    如果失敗或發生錯誤，返回 None。
    """
    conn = get_db_connection()
    if conn is None:
        return None
        
    try:
        query = "SELECT SID, Account, Class FROM Staff WHERE Account = ? AND Password = ?"
        cursor = conn.execute(query, (account, password))

        #獲取單一結果，因為是Unique
        staff_data = cursor.fetchone()
        
        if staff_data:
            return staff_data
        
        return None
    
    except sqlite3.Error as e:
        print(f"查詢 Staff 資料時發生錯誤: {e}")
        return None
    
    finally:
        conn.close()

#新增員工用
def insert_staff(account: str, password: str, staff_class: str):
    conn = get_db_connection()
    if conn is None:
        return 

    try:
        #檢查帳號是否已存在，避免重複插入導致錯誤
        check_query = "SELECT COUNT(*) FROM Staff WHERE Account = ?"
        cursor = conn.execute(check_query, (account,))
        if cursor.fetchone()[0] > 0:
            print(f"員工帳號 '{account}' 已存在，跳過新增。")
            return
            
        #插入資料
        insert_query = """
        INSERT INTO Staff (Account, Password, Class) 
        VALUES (?, ?, ?)
        """
        conn.execute(insert_query, (account, password, staff_class))
        conn.commit()
        print(f"成功新增帳號：{account}")
        return True

    except sqlite3.Error as e:
        print(f"新增員工資料時發生錯誤: {e}")
        return

    finally:
        if conn:
            conn.close()

#修改員工密碼用
def update_password(account: str, new_password: str) -> bool:
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        query = """
        UPDATE Staff SET Password = ?
        WHERE Account = ?
        """
        cursor = conn.execute(query, (new_password, account))
        conn.commit()
        
        #檢查是否有行被更新(Row count > 0)
        return cursor.rowcount > 0 
        
    except sqlite3.Error as e:
        print(f"更新員工 {account} 密碼時發生錯誤: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

#刪除員工用
def delete_staff(account: str) -> bool:
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        query = "DELETE FROM Staff WHERE Account = ?"
        cursor = conn.execute(query, (account,))
        conn.commit()
        
        #檢查是否有行被刪除
        return cursor.rowcount > 0 
        
    except sqlite3.Error as e:
        print(f"刪除員工帳號 {account} 時發生錯誤: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

#查詢所有員工的清單並回傳
def get_all_staff() -> List[Dict]:
    conn = get_db_connection()
    if conn is None: return []
    #設置row_factory確保返回字典格式，方便NiceGUI表格使用
    conn.row_factory = sqlite3.Row 
    try:
        #查詢不包括密碼
        query = "SELECT SID, Account, Class FROM Staff ORDER BY SID ASC"
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    except sqlite3.Error as e:
        print(f"查詢所有員工時發生錯誤: {e}")
        return []
    
    finally: 
        if conn: 
            conn.close()

#新增餐點用
def insert_meal(name: str, price: int, picname: str, is_available: bool) -> Optional[int]:
    conn = get_db_connection()
    if conn is None: 
        return None
    
    #將Python bool轉換為SQL的0或1
    sql_is_available = 1 if is_available else 0
    
    try:
        #檢查餐點名稱是否重複
        check_query = "SELECT COUNT(*) FROM Meal WHERE Name = ?"
        if conn.execute(check_query, (name,)).fetchone()[0] > 0:
            print(f"餐點名稱 '{name}' 已存在，新增失敗。")
            return None

        #插入新的餐點
        query = "INSERT INTO Meal (Name, Price, Picname, IsAvailable) VALUES (?, ?, ?, ?)"
        cursor = conn.execute(query, (name, price, picname, sql_is_available))
        conn.commit()
        return cursor.lastrowid
        
    except sqlite3.Error as e:
        print(f"新增餐點 {name} 時發生錯誤: {e}")
        return None
        
    finally:
        if conn: 
            conn.close()

#修改餐點用
def update_meal(mid: int, name: str, price: int, picname: str, is_available: bool) -> bool:
    conn = get_db_connection()
    if conn is None: 
        return False
    
    #將Python bool轉換為SQL的0或1
    sql_is_available = 1 if is_available else 0
    
    try:
        query = """
        UPDATE Meal SET Name = ?, Price = ?, Picname = ?, IsAvailable = ?
        WHERE MID = ?
        """
        cursor = conn.execute(query, (name, price, picname, sql_is_available, mid))
        conn.commit()

        #檢查是否有行被更新(Row count > 0)
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        print(f"更新餐點 ID {mid} 時發生錯誤: {e}")
        return False
        
    finally:
        if conn: 
            conn.close()

#刪除餐點用
def delete_meal(mid: int) -> bool:
    conn = get_db_connection()
    if conn is None: 
        return False
    
    try:
        query = "DELETE FROM Meal WHERE MID = ?"
        cursor = conn.execute(query, (mid,))
        conn.commit()

        #檢查是否有行被刪除
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        print(f"刪除餐點 ID {mid} 時發生錯誤: {e}")
        return False
        
    finally:
        if conn: 
            conn.close()

#查詢所有餐點的清單並回傳
def get_all_meals() -> List[Dict]:
    conn = get_db_connection()
    if conn is None: return []
    #設置row_factory確保返回字典格式，方便NiceGUI表格使用
    conn.row_factory = sqlite3.Row 
    
    try:
        #查詢所有欄位
        query = "SELECT MID, Name, Price, PicName, IsAvailable FROM Meal ORDER BY MID ASC"
        cursor = conn.execute(query)
        meal_list = [dict(row) for row in cursor.fetchall()]
        for meal in meal_list:
            #將0/1轉換為True/False
            meal['IsAvailable'] = bool(meal['IsAvailable'])
        return meal_list
        
    except sqlite3.Error as e:
        print(f"查詢所有餐點時發生錯誤: {e}")
        return []
        
    finally:
        if conn: conn.close()

#建立訂單
def create_order(total_amount: int, serving_method: str, status: str = 'Preparing') -> Optional[int]:
    conn = get_db_connection()
    if conn is None: return None
    
    #確保金額為整數
    total_amount_int = int(round(total_amount)) 
    
    try:
        query = """
        INSERT INTO "Order" (Time, TotalAmount, Status, ServingMethod) 
        VALUES (DATETIME('now', 'localtime'), ?, ?, ?)
        """
        cursor = conn.execute(query, (total_amount_int, status, serving_method))
        conn.commit()
        return cursor.lastrowid
        
    except sqlite3.Error as e:
        print(f"建立訂單時發生錯誤: {e}")
        return None
        
    finally:
        if conn: 
            conn.close()

#新增訂單明細，成功時回傳True，失敗False
def insert_order_detail(oid: int, mid: int, quantity: int, price_at_order: int, total: int) -> bool:
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        query = """
        INSERT INTO OrderDetail (Order_ID, Meal_ID, Quantity, PriceAtOrder, Total) 
        VALUES (?, ?, ?, ?, ?)
        """
        conn.execute(query, (oid, mid, quantity, price_at_order, total))
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"新增訂單明細 OID:{oid}, MID:{mid} 時發生錯誤: {e}")
        return False
        
    finally:
        if conn: 
            conn.close()

#執行完整交易
def submit_full_order(items: List[Dict[str, Any]], serving_method: str) -> Optional[int]:
    #計算總金額
    total_amount = sum(item['total'] for item in items)
    if total_amount <= 0:
        print("訂單總金額為零或負數，取消提交。")
        return None
        
    #建立Order的紀錄
    oid = create_order(total_amount, serving_method)
    if oid is None:
        return None 

    #建立OrderDetail的記錄
    details_success = True
    for item in items:
        #(oid, mid, quantity, price_at_order, total)，參數對應要看一下
        if not insert_order_detail(
            oid,                #Order_ID
            item['mid'],        #Meal_ID
            item['quantity'],   #Quantity
            item['price'],      #PriceAtOrder
            item['total']       #Total
        ):
            details_success = False
            
    if not details_success:
        print(f"WARNING: OID {oid} 明細部分寫入失敗。")
        
    return oid

#查詢所有訂單(Order)
def get_all_orders() -> List[Dict]:
    conn = get_db_connection()
    if conn is None: return []
    
    conn.row_factory = sqlite3.Row 
    
    try:
        #查詢Order所有欄位
        query = """
        SELECT OID, Time, TotalAmount, Status, ServingMethod 
        FROM "Order" 
        WHERE Status = 'Preparing'  --只顯示準備中的訂單
        ORDER BY Time ASC           --依時間從舊到新排序
        """
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
        
    except sqlite3.Error as e:
        print(f"查詢所有訂單時發生錯誤: {e}")
        return []
        
    finally:
        if conn: 
            conn.close()

#用OID查詢訂單詳細(OrderDetail)
def get_order_details(oid: int) -> List[Dict]:
    conn = get_db_connection()
    if conn is None: return []
    
    conn.row_factory = sqlite3.Row
    
    try:
        query = """
        SELECT 
            OD.Quantity, OD.Total, OD.PriceAtOrder, 
            M.Name AS MealName
        FROM OrderDetail OD
        JOIN Meal M ON OD.Meal_ID = M.MID
        WHERE OD.Order_ID = ?
        """
        cursor = conn.execute(query, (oid,))
        return [dict(row) for row in cursor.fetchall()]
        
    except sqlite3.Error as e:
        print(f"查詢訂單明細 OID:{oid} 時發生錯誤: {e}")
        return []
        
    finally:
        if conn: 
            conn.close()

#更新指定OID的訂單狀態
def update_order_status(oid: int, new_status: str) -> bool:
    conn = get_db_connection()
    if conn is None: return False
    
    #檢查狀態是否有效
    if new_status not in ['Preparing', 'Completed']:
        print(f"無效的訂單狀態: {new_status}")
        return False
        
    try:
        query = "UPDATE \"Order\" SET Status = ? WHERE OID = ?"
        cursor = conn.execute(query, (new_status, oid))
        conn.commit()
        return cursor.rowcount > 0
        
    except sqlite3.Error as e:
        print(f"更新訂單 OID:{oid} 狀態時發生錯誤: {e}")
        return False
        
    finally:
        if conn: conn.close()

#插入預設的管理員帳號用
def demo_manager():
    insert_staff('demo_manager', 'password', 'Manager')
    insert_staff('demo_staff1', '123', 'Staff')

#插入預設的餐點用
def demo_meals():  
    insert_meal('番茄肉醬義大利麵', 180.0, 'spaghetti.jpg', True)
    insert_meal('冰紅茶', 45.0, 'iced_tea.png', True)
    insert_meal('提拉米蘇', 95.0, 'tiramisu.jpg', True)
    insert_meal('玉米濃湯', 40.0, 'corn_soup.png', False)