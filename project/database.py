import os
import sys
import sqlite3
import shutil
from datetime import datetime


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_NAME = "purchase.db"
DB_PATH = os.path.join(_app_dir(), DB_NAME)


def _bundled_db_path():
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = os.path.join(base, DB_NAME)
        if os.path.exists(p):
            return p
    return None


def ensure_db():
    created = False
    if not os.path.exists(DB_PATH):
        bundled = _bundled_db_path()
        if bundled and os.path.exists(bundled):
            shutil.copyfile(bundled, DB_PATH)
        created = True
    conn = sqlite3.connect(DB_PATH)
    try:
        if created:
            _init_schema(conn)
        _migrate_schema(conn)
    finally:
        conn.close()


def _init_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS counter (
            yymm TEXT NOT NULL,
            category TEXT NOT NULL,
            seq INTEGER NOT NULL,
            PRIMARY KEY (yymm, category)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS detail_counter (
            yymm TEXT NOT NULL,
            category TEXT NOT NULL,
            seq INTEGER NOT NULL,
            PRIMARY KEY (yymm, category)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS units (
            name TEXT PRIMARY KEY
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchasers (
            name TEXT PRIMARY KEY
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchase_status (
            name TEXT PRIMARY KEY
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            number TEXT PRIMARY KEY,
            yymm TEXT,
            category TEXT,
            unit TEXT,
            date TEXT,
            task_name TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT,
            detail_no TEXT,
            item_name TEXT,
            purchase_item TEXT,
            spec_model TEXT,
            purchase_cycle TEXT,
            stock_count TEXT,
            purchase_qty TEXT,
            unit TEXT,
            unit_price TEXT,
            budget_wan TEXT,
            purchase_method TEXT,
            purchase_channel TEXT,
            plan_time TEXT,
            demand_unit TEXT,
            plan_release TEXT,
            progress_req TEXT,
            supplier TEXT,
            inquiry_price TEXT,
            tax_rate TEXT,
            actual_status TEXT,
            purchase_body TEXT,
            add_adjust TEXT,
            remark TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS detail_layout (
            col_index INTEGER PRIMARY KEY,
            width INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS main_layout (
            col_index INTEGER PRIMARY KEY,
            width INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS print_config (
            module TEXT PRIMARY KEY,
            config_json TEXT
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS release_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_order_number TEXT,
            purchaser TEXT,
            release_date TEXT,
            status TEXT,
            record_count INTEGER,
            UNIQUE(source_order_number, purchaser)
        )
        """
    )
    conn.commit()

    # Ensure operation_logs table exists
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            operator TEXT,
            op_time TEXT
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_candidates INTEGER,
            inserted INTEGER,
            skipped INTEGER,
            failed INTEGER,
            details TEXT
        )
        """
    )
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_months (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(1) FROM units")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO units(name) VALUES(?)", [("生产部",), ("采购部",), ("仓储部",)])
        conn.commit()
    
    cur.execute("SELECT COUNT(1) FROM purchase_status")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO purchase_status(name) VALUES(?)", [("未发放",), ("已发放",), ("采购中",), ("已完成",)])
        conn.commit()

    cur.execute("SELECT COUNT(1) FROM plan_months")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO plan_months(name) VALUES(?)", [("2601",), ("2602",), ("2603",)])
        conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            plan_release TEXT,
            weight INTEGER,
            is_active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_candidates INTEGER,
            inserted INTEGER,
            skipped INTEGER,
            failed INTEGER,
            details TEXT
        )
        """
    )
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_month TEXT,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            plan_qty REAL,
            plan_budget REAL,
            department TEXT,
            remarks TEXT
        )
        """
    )
    conn.commit()

    # Operation logs for audit
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            operator TEXT,
            op_time TEXT
        )
        """
    )
    conn.commit()


def _migrate_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_month TEXT,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            plan_qty REAL,
            plan_budget REAL,
            department TEXT,
            remarks TEXT
        )
        """
    )
    conn.commit()
    # Layout tables for Plan Release and Versions
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_release_layout (
            col_index INTEGER PRIMARY KEY,
            width INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_versions (
            layout_name TEXT PRIMARY KEY,
            version TEXT
        )
        """
    )
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            plan_release TEXT,
            weight INTEGER,
            is_active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    # Check if is_active exists
    cur.execute("PRAGMA table_info(recommendations)")
    cols = [r[1] for r in cur.fetchall()]
    if "is_active" not in cols:
        cur.execute("ALTER TABLE recommendations ADD COLUMN is_active INTEGER DEFAULT 1")
    if "purchase_method" not in cols:
        cur.execute("ALTER TABLE recommendations ADD COLUMN purchase_method TEXT")
    if "purchase_channel" not in cols:
        cur.execute("ALTER TABLE recommendations ADD COLUMN purchase_channel TEXT")
    conn.commit()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS units (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchasers (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    cur.execute("SELECT COUNT(1) FROM units")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO units(name) VALUES(?)", [("生产部",), ("采购部",), ("仓储部",)])
        conn.commit()
    cur.execute("PRAGMA table_info(orders)")
    cols = [r[1] for r in cur.fetchall()]
    if "task_name" not in cols:
        cur.execute("ALTER TABLE orders ADD COLUMN task_name TEXT")
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS detail_layout (
            col_index INTEGER PRIMARY KEY,
            width INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS main_layout (
            col_index INTEGER PRIMARY KEY,
            width INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    
    # Add purchase_status table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS purchase_status (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    cur.execute("SELECT COUNT(1) FROM purchase_status")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO purchase_status(name) VALUES(?)", [("未发放",), ("已发放",), ("采购中",), ("已完成",)])
        conn.commit()

    # Add print_config table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS print_config (
            module TEXT PRIMARY KEY,
            config_json TEXT
        )
        """
    )
    conn.commit()

    # Add release_orders table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS release_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_order_number TEXT,
            purchaser TEXT,
            release_date TEXT,
            status TEXT,
            record_count INTEGER,
            UNIQUE(source_order_number, purchaser)
        )
        """
    )
    conn.commit()

    # Add plan_months table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_months (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    cur.execute("SELECT COUNT(1) FROM plan_months")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.executemany("INSERT INTO plan_months(name) VALUES(?)", [("2601",), ("2602",), ("2603",)])
        conn.commit()


def init_db():
    ensure_db()


def _connect():
    ensure_db()
    return sqlite3.connect(DB_PATH)


def _get_and_inc(cur: sqlite3.Cursor, table: str, yymm: str, category: str) -> int:
    cur.execute(
        f"SELECT seq FROM {table} WHERE yymm=? AND category=?",
        (yymm, category),
    )
    row = cur.fetchone()
    if row is None:
        seq = 1
        cur.execute(
            f"INSERT INTO {table}(yymm, category, seq) VALUES(?, ?, ?)",
            (yymm, category, seq),
        )
    else:
        seq = int(row[0]) + 1
        cur.execute(
            f"UPDATE {table} SET seq=? WHERE yymm=? AND category=?",
            (seq, yymm, category),
        )
    return seq


def next_main_number(yymm: str, category_code: str) -> str:
    conn = _connect()
    try:
        cur = conn.cursor()
        # 使用 (yymm, category_code) 联合主键作为计数器的 key
        # 这样不同类别的单据会分别计数
        
        seq = _get_and_inc(cur, "counter", yymm, category_code)
        conn.commit()
        return f"CG-{yymm}{category_code}{seq:04d}"
    finally:
        conn.close()


def next_detail_number(yymm: str, category_code: str) -> str:
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Instead of using a separate counter table, query the current max sequence from order_details
        # The detail_no format is expected to be like "2601MP-1", "2601MP-2", etc.
        # We need to parse the suffix integer.
        
        prefix = f"{yymm}{category_code}-"
        cur.execute(
            "SELECT detail_no FROM order_details WHERE detail_no LIKE ?",
            (prefix + "%",),
        )
        max_seq = 0
        for (dn,) in cur.fetchall():
            try:
                if not dn: continue
                # Split by '-' and take the last part
                # Format: 2601MP-1 -> parts ["2601MP", "1"]
                # Handle cases where prefix might appear multiple times or other formats?
                # Assuming standard format.
                # The prefix logic in recalc_detail_counter uses split("-")[-1]
                
                # If dn doesn't start with prefix, ignore? Query uses LIKE prefix% so it should be safe.
                
                part = str(dn).split("-")[-1]
                n = int(part)
                if n > max_seq:
                    max_seq = n
            except Exception:
                pass
        
        seq = max_seq + 1
        
        # We don't need to update detail_counter table anymore if we strictly follow "max existing + 1"
        # But for consistency or if detail_counter is used elsewhere?
        # The requirement says: "start from current valid records... if deleted... still +1"
        # Wait: "如果删除了新记录再重新添加，还是35" -> If max was 34, new is 35. If I delete 35, max is 34. Next new is 35 again.
        # This means we should NOT persist a counter that remembers 35 was used.
        # We should ALWAYS calculate Max(Existing) + 1.
        
        # So we ignore detail_counter table logic here and just return calculated seq.
        
        return f"{yymm}{category_code}-{seq}"
    finally:
        conn.close()


def save_order(number: str, yymm: str, category_code: str, unit: str, date_str: str, task_name: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO orders(number, yymm, category, unit, date, task_name) VALUES(?,?,?,?,?,?)",
            (number, yymm, category_code, unit, date_str, task_name),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_order_details(order_number: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count, purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel, plan_time, demand_unit, plan_release, progress_req, supplier, inquiry_price, tax_rate, actual_status, purchase_body, add_adjust, remark FROM order_details WHERE order_number=?",
            (order_number,),
        )
        rows = cur.fetchall()
        
        # Sort DESC by Detail No (Large to Small) for Purchase Plan Entry
        def sort_key(r):
            dn = r[0]
            try:
                # 2601MP-10 -> 10
                return int(dn.split("-")[-1])
            except:
                return -1
        
        rows.sort(key=sort_key, reverse=True)
        return rows
    finally:
        conn.close()


def count_details(order_number: str) -> int:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM order_details WHERE order_number=?", (order_number,))
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def validate_detail_sequence(order_number: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT detail_no FROM order_details WHERE order_number=? ORDER BY id",
            (order_number,),
        )
        detail_nos = [r[0] for r in cur.fetchall() if r and r[0]]
        seen = {}
        nums = []
        for dn in detail_nos:
            try:
                part = str(dn).split("-")[-1]
                n = int(part)
                nums.append(n)
                seen[n] = seen.get(n, 0) + 1
            except Exception:
                pass
        issues = []
        dups = [n for n, c in seen.items() if c > 1]
        if dups:
            issues.append(f"重复序号: {','.join(map(str, sorted(dups)))}")
        if nums:
            mx = max(nums)
            missing = [str(i) for i in range(1, mx + 1) if i not in seen]
            if missing:
                issues.append(f"缺失序号: {','.join(missing)}")
        ok = len(issues) == 0
        return ok, "; ".join(issues) if issues else "序号连续且无重复"
    finally:
        conn.close()


def reset_test_data():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM order_details")
        cur.execute("DELETE FROM orders")
        cur.execute("DELETE FROM counter")
        cur.execute("DELETE FROM detail_counter")
        cur.execute("DELETE FROM release_orders")
        conn.commit()
    finally:
        conn.close()


def recalc_detail_counter(yymm: str, category_code: str):
    prefix = f"{yymm}{category_code}-"
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT detail_no FROM order_details WHERE detail_no LIKE ?",
            (prefix + "%",),
        )
        max_seq = 0
        for (dn,) in cur.fetchall():
            try:
                part = str(dn).split("-")[-1]
                n = int(part)
                if n > max_seq:
                    max_seq = n
            except Exception:
                pass
        # ensure a row exists in detail_counter
        cur.execute(
            "SELECT seq FROM detail_counter WHERE yymm=? AND category=?",
            (yymm, category_code),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO detail_counter(yymm, category, seq) VALUES(?,?,?)",
                (yymm, category_code, max_seq),
            )
        else:
            cur.execute(
                "UPDATE detail_counter SET seq=? WHERE yymm=? AND category=?",
                (max_seq, yymm, category_code),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_orders(number_filter=None, task_filter=None, unit_filter=None, month_filter=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = "SELECT yymm, category, unit, date, task_name, number FROM orders WHERE 1=1"
        params = []
        if number_filter:
            sql += " AND number LIKE ?"
            params.append(f"%{number_filter}%")
        if task_filter:
            sql += " AND task_name LIKE ?"
            params.append(f"%{task_filter}%")
        if unit_filter:
            sql += " AND unit LIKE ?"
            params.append(f"%{unit_filter}%")
        if month_filter:
            sql += " AND yymm LIKE ?"
            params.append(f"%{month_filter}%")
            
        sql += " ORDER BY orders.rowid DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_order_by_number(number: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT yymm, category, unit, date, task_name FROM orders WHERE number=?",
            (number,),
        )
        return cur.fetchone()
    finally:
        conn.close()


def update_order_date(number: str, date_str: str) -> bool:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET date=? WHERE number=?", (date_str, number))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def save_operation_log(order_number: str, field: str, old_value: str, new_value: str, operator: str, op_time: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO operation_logs(order_number, field, old_value, new_value, operator, op_time) VALUES(?,?,?,?,?,?)",
            (order_number, field, old_value or "", new_value or "", operator or "", op_time),
        )
        conn.commit()
    finally:
        conn.close()


def get_order_processing_status(order_number: str) -> str:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM release_orders WHERE source_order_number=?",
            (order_number,)
        )
        rows = [r[0] for r in cur.fetchall()]
        if not rows:
            return "未发放"
        for s in rows:
            if s in ("未发放", "待发放"):
                return "未发放"
        return "已发放"
    finally:
        conn.close()


def save_order_details_transaction(order_number: str, rows_data_list: list):
    conn = _connect()
    try:
        cur = conn.cursor()
        # First delete existing details for this order to prevent duplicates and handle deletions
        cur.execute("DELETE FROM order_details WHERE order_number=?", (order_number,))
        
        # Then insert all current rows
        for detail_no, row_data in rows_data_list:
            cur.execute(
                """
                INSERT INTO order_details(
                    order_number, detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count, purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel, plan_time, demand_unit, plan_release, progress_req, supplier, inquiry_price, tax_rate, actual_status, purchase_body, add_adjust, remark
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                [order_number, detail_no] + row_data,
            )
        conn.commit()
        
        # Sync with release_orders
        _sync_release_orders(cur, order_number)
        conn.commit()
    finally:
        conn.close()

def _sync_release_orders(cur: sqlite3.Cursor, order_number: str):
    # 1. Find all purchasers in current details
    cur.execute(
        "SELECT plan_release, COUNT(1) FROM order_details WHERE order_number=? AND plan_release IS NOT NULL AND plan_release != '' GROUP BY plan_release",
        (order_number,)
    )
    groups = cur.fetchall()
    
    current_purchasers = set()
    today = today_str()
    
    for purchaser, count in groups:
        current_purchasers.add(purchaser)
        # Check if exists
        cur.execute(
            "SELECT id FROM release_orders WHERE source_order_number=? AND purchaser=?",
            (order_number, purchaser)
        )
        row = cur.fetchone()
        if row:
            # Update count
            cur.execute(
                "UPDATE release_orders SET record_count=? WHERE id=?",
                (count, row[0])
            )
        else:
            # Insert new
            cur.execute(
                "INSERT INTO release_orders(source_order_number, purchaser, release_date, status, record_count) VALUES(?,?,?,?,?)",
                (order_number, purchaser, today, "待发放", count)
            )
            
    # 2. Remove entries for purchasers that no longer exist in details
    # If current_purchasers is empty, delete all for this order
    if not current_purchasers:
        cur.execute("DELETE FROM release_orders WHERE source_order_number=?", (order_number,))
    else:
        placeholders = ",".join(["?"] * len(current_purchasers))
        cur.execute(
            f"DELETE FROM release_orders WHERE source_order_number=? AND purchaser NOT IN ({placeholders})",
            [order_number] + list(current_purchasers)
        )


def save_detail_row(order_number: str, detail_no: str, row_data: list):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO order_details(
                order_number, detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count, purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel, plan_time, demand_unit, plan_release, progress_req, supplier, inquiry_price, tax_rate, actual_status, purchase_body, add_adjust, remark
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            [order_number, detail_no] + row_data,
        )
        conn.commit()
    finally:
        conn.close()


def category_code_from_display(text: str) -> str:
    if "MPJ" in text:
        return "MPJ"
    if "MPB_WX" in text:
        return "MPB_WX"
    if "MPB" in text:
        return "MPB"
    return "MP"


def today_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def category_display_from_code(code: str) -> str:
    if code == "MPJ":
        return "机加件"
    if code == "MPB_WX":
        return "外销模块"
    if code == "MPB":
        return "半成品"
    return "民品"


def fetch_units():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM units ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def add_unit(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO units(name) VALUES(?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        conn.close()


def rename_unit(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM units WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE units SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_detail_column_widths():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT col_index, width FROM detail_layout ORDER BY col_index")
        return {int(c): int(w) for c, w in cur.fetchall()}
    finally:
        conn.close()


def set_detail_column_width(col_index: int, width: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE detail_layout SET width=? WHERE col_index=?", (int(width), int(col_index)))
        if cur.rowcount == 0:
            cur.execute("INSERT INTO detail_layout(col_index, width) VALUES(?,?)", (int(col_index), int(width)))
        conn.commit()
    finally:
        conn.close()


def get_main_column_widths():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT col_index, width FROM main_layout ORDER BY col_index")
        return {int(c): int(w) for c, w in cur.fetchall()}
    finally:
        conn.close()


def set_main_column_width(col_index: int, width: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE main_layout SET width=? WHERE col_index=?", (int(width), int(col_index)))
        if cur.rowcount == 0:
            cur.execute("INSERT INTO main_layout(col_index, width) VALUES(?,?)", (int(col_index), int(width)))
        conn.commit()
    finally:
        conn.close()


def get_plan_release_column_widths():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT col_index, width FROM plan_release_layout ORDER BY col_index")
        return {int(c): int(w) for c, w in cur.fetchall()}
    finally:
        conn.close()


def set_plan_release_column_width(col_index: int, width: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE plan_release_layout SET width=? WHERE col_index=?", (int(width), int(col_index)))
        if cur.rowcount == 0:
            cur.execute("INSERT INTO plan_release_layout(col_index, width) VALUES(?,?)", (int(col_index), int(width)))
        conn.commit()
    finally:
        conn.close()


def set_layout_version(layout_name: str, version: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE layout_versions SET version=? WHERE layout_name=?", (version, layout_name))
        if cur.rowcount == 0:
            cur.execute("INSERT INTO layout_versions(layout_name, version) VALUES(?,?)", (layout_name, version))
        conn.commit()
    finally:
        conn.close()


def get_layout_version(layout_name: str) -> str:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT version FROM layout_versions WHERE layout_name=?", (layout_name,))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""
    finally:
        conn.close()


def fetch_purchasers():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM purchasers ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def add_purchaser(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO purchasers(name) VALUES(?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        conn.close()


def rename_purchaser(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM purchasers WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE purchasers SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def fetch_purchase_statuses():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM purchase_status ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

def add_purchase_status(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO purchase_status(name) VALUES(?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        conn.close()

def rename_purchase_status(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM purchase_status WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE purchase_status SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def fetch_plan_months():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM plan_months ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

def add_plan_month(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO plan_months(name) VALUES(?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        conn.close()

def rename_plan_month(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM plan_months WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE plan_months SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def fetch_release_orders(number_filter=None, purchaser_filter=None, task_filter=None, month_filter=None, unit_filter=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Join release_orders with orders to get task_name, yymm, unit
        sql = """
            SELECT 
                r.release_date, 
                r.source_order_number, 
                r.purchaser, 
                o.task_name, 
                o.unit, 
                o.yymm, 
                r.record_count, 
                r.status
            FROM release_orders r
            LEFT JOIN orders o ON r.source_order_number = o.number
            WHERE 1=1
        """
        params = []
        if number_filter:
            sql += " AND r.source_order_number LIKE ?"
            params.append(f"%{number_filter}%")
        if purchaser_filter:
            sql += " AND r.purchaser LIKE ?"
            params.append(f"%{purchaser_filter}%")
        if task_filter:
            sql += " AND o.task_name LIKE ?"
            params.append(f"%{task_filter}%")
        if month_filter:
            sql += " AND o.yymm LIKE ?"
            params.append(f"%{month_filter}%")
        if unit_filter:
            sql += " AND o.unit LIKE ?"
            params.append(f"%{unit_filter}%")
            
        sql += " ORDER BY r.id ASC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_release_details(order_number: str, purchaser: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                detail_no, purchase_item, spec_model, purchase_qty, 
                unit, unit_price, budget_wan, purchase_method, purchase_channel, 
                plan_release, progress_req, inquiry_price, tax_rate, remark
            FROM order_details 
            WHERE order_number=? AND plan_release=?
        """,
            (order_number, purchaser),
        )
        rows = cur.fetchall()
        
        # Sort ASC by Detail No (Small to Large) for Plan Release
        def sort_key(r):
            dn = r[0]
            try:
                # 2601MP-10 -> 10
                return int(dn.split("-")[-1])
            except:
                return 999999
        
        rows.sort(key=sort_key)
        return rows
    finally:
        conn.close()

def update_release_status(order_number: str, purchaser: str, new_status: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE release_orders SET status=? WHERE source_order_number=? AND purchaser=?",
            (new_status, order_number, purchaser)
        )
        conn.commit()
    finally:
        conn.close()


def get_print_config(module: str) -> dict:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT config_json FROM print_config WHERE module=?", (module,))
        row = cur.fetchone()
        if row and row[0]:
            import json
            try:
                return json.loads(row[0])
            except:
                pass
        return {}
    finally:
        conn.close()


def save_print_config(module: str, config: dict):
    import json
    json_str = json.dumps(config)
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO print_config(module, config_json) VALUES(?, ?)", (module, json_str))
        conn.commit()
    finally:
        conn.close()


def get_workbench_stats(yymm_filter: str):
    """
    Returns (total_plans, pending_plans, processed_plans, civil_count, machined_count, semi_count,
             total_amount, civil_amount, machined_amount, semi_amount)
    
    1. Total Plans: count of orders where yymm = filter
    2. Pending Plans: count of orders that have at least one unreleased record (status='未发放')
    3. Processed Plans: Total - Pending
    4. Category Counts: Breakdown of Total Plans
    5. Amounts: Sum of budget_wan * 10000
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # 1. Total Plans and Category Breakdown
        sql1 = """
            SELECT 
                COUNT(1),
                SUM(CASE WHEN category NOT IN ('MPJ', 'MPB') THEN 1 ELSE 0 END),
                SUM(CASE WHEN category = 'MPJ' THEN 1 ELSE 0 END),
                SUM(CASE WHEN category = 'MPB' THEN 1 ELSE 0 END)
            FROM orders
        """
        params1 = []
        if yymm_filter:
            sql1 += " WHERE yymm = ?"
            params1.append(yymm_filter)
            
        cur.execute(sql1, params1)
        row = cur.fetchone()
        total_plans = row[0] if row and row[0] else 0
        civil_count = row[1] if row and row[1] else 0
        machined_count = row[2] if row and row[2] else 0
        semi_count = row[3] if row and row[3] else 0
        
        # 2. Pending Plans (Orders with unreleased tasks)
        # We count DISTINCT source_order_number from release_orders where status='未发放'
        # AND join orders to filter by yymm
        sql2 = """
            SELECT COUNT(DISTINCT r.source_order_number) 
            FROM release_orders r
            JOIN orders o ON r.source_order_number = o.number
            WHERE r.status IN ('未发放','待发放')
        """
        params2 = []
        if yymm_filter:
            sql2 += " AND o.yymm = ?"
            params2.append(yymm_filter)
            
        cur.execute(sql2, params2)
        pending_plans = cur.fetchone()[0]
        
        # 3. Processed Plans
        processed_plans = total_plans - pending_plans
        if processed_plans < 0:
            processed_plans = 0 # Should not happen if logic is correct
            
        # 4. Amounts (Inquiry Price Sum)
        # Join orders and order_details
        # inquiry_price is text like "1,200.00"
        sql_amt = """
            SELECT 
                SUM(CAST(REPLACE(IFNULL(d.inquiry_price, '0'), ',', '') AS REAL)),
                SUM(CASE WHEN o.category NOT IN ('MPJ', 'MPB') THEN CAST(REPLACE(IFNULL(d.inquiry_price, '0'), ',', '') AS REAL) ELSE 0 END),
                SUM(CASE WHEN o.category = 'MPJ' THEN CAST(REPLACE(IFNULL(d.inquiry_price, '0'), ',', '') AS REAL) ELSE 0 END),
                SUM(CASE WHEN o.category = 'MPB' THEN CAST(REPLACE(IFNULL(d.inquiry_price, '0'), ',', '') AS REAL) ELSE 0 END)
            FROM order_details d
            JOIN orders o ON d.order_number = o.number
        """
        params_amt = []
        if yymm_filter:
            sql_amt += " WHERE o.yymm = ?"
            params_amt.append(yymm_filter)
            
        cur.execute(sql_amt, params_amt)
        row_amt = cur.fetchone()
        
        total_amount = row_amt[0] if row_amt and row_amt[0] else 0.0
        civil_amount = row_amt[1] if row_amt and row_amt[1] else 0.0
        machined_amount = row_amt[2] if row_amt and row_amt[2] else 0.0
        semi_amount = row_amt[3] if row_amt and row_amt[3] else 0.0
        
        return (total_plans, pending_plans, processed_plans, civil_count, machined_count, semi_count,
                total_amount, civil_amount, machined_amount, semi_amount)
    finally:
        conn.close()


def fetch_recommendations():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, item_name, plan_release, weight, is_active, purchase_method, purchase_channel FROM recommendations ORDER BY id")
        return cur.fetchall()
    finally:
        conn.close()


def save_recommendations_transaction(rows_data_list: list):
    """
    rows_data_list: list of (item_name, plan_release, weight, is_active, purchase_method, purchase_channel)
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM recommendations")
        cur.executemany(
            "INSERT INTO recommendations(item_name, plan_release, weight, is_active, purchase_method, purchase_channel) VALUES(?,?,?,?,?,?)",
            rows_data_list
        )
        conn.commit()
    finally:
        conn.close()


def fetch_existing_recommendation_item_names() -> set:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT item_name FROM recommendations")
        return {r[0] for r in cur.fetchall() if r and r[0]}
    finally:
        conn.close()


def get_released_items_for_recommendation() -> list:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT d.purchase_item, d.plan_release, d.purchase_method, d.purchase_channel
            FROM release_orders r
            JOIN order_details d ON d.order_number = r.source_order_number AND d.plan_release = r.purchaser
            WHERE r.status = '已发放'
            """
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            item = str(r[0] or "").strip()
            plan_release = str(r[1] or "").strip()
            p_method = str(r[2] or "").strip()
            p_channel = str(r[3] or "").strip()
            if item:
                result.append((item, plan_release, p_method, p_channel))
        return result
    finally:
        conn.close()


def insert_recommendations_batch(items: list, timeout: float = 5.0, max_retries: int = 3) -> dict:
    import time
    inserted = 0
    skipped = 0
    failed = 0
    failures = []
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    try:
        cur = conn.cursor()
        existing = fetch_existing_recommendation_item_names()
        to_insert = []
        for item_name, plan_release, p_method, p_channel in items:
            if item_name in existing:
                skipped += 1
                continue
            to_insert.append((item_name, plan_release, 100, 1, p_method, p_channel))
        if not to_insert:
            return {"inserted": 0, "skipped": skipped, "failed": 0, "failures": []}
        tries = 0
        while True:
            try:
                cur.executemany(
                    "INSERT INTO recommendations(item_name, plan_release, weight, is_active, purchase_method, purchase_channel) VALUES(?,?,?,?,?,?)",
                    to_insert,
                )
                conn.commit()
                inserted += len(to_insert)
                break
            except sqlite3.OperationalError as e:
                tries += 1
                if tries > max_retries:
                    failed += len(to_insert)
                    failures.append(str(e))
                    break
                time.sleep(min(0.5 * tries, 2.0))
        return {"inserted": inserted, "skipped": skipped, "failed": failed, "failures": failures}
    finally:
        conn.close()


def save_sync_log(start_time: str, end_time: str, total: int, inserted: int, skipped: int, failed: int, details: str):
    def ensure_sync_logs_table(cur: sqlite3.Cursor):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                total_candidates INTEGER,
                inserted INTEGER,
                skipped INTEGER,
                failed INTEGER,
                details TEXT
            )
            """
        )
    conn = _connect()
    try:
        cur = conn.cursor()
        ensure_sync_logs_table(cur)
        cur.execute(
            "INSERT INTO sync_logs(start_time, end_time, total_candidates, inserted, skipped, failed, details) VALUES(?,?,?,?,?,?,?)",
            (start_time, end_time, total, inserted, skipped, failed, details),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_sync_logs(limit: int = 50):
    def ensure_sync_logs_table(cur: sqlite3.Cursor):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                total_candidates INTEGER,
                inserted INTEGER,
                skipped INTEGER,
                failed INTEGER,
                details TEXT
            )
            """
        )
    conn = _connect()
    try:
        cur = conn.cursor()
        ensure_sync_logs_table(cur)
        cur.execute(
            "SELECT id, start_time, end_time, total_candidates, inserted, skipped, failed, details FROM sync_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def user_has_permission(permission: str) -> bool:
    return True


def get_order_inquiry_total(order_number: str) -> float:
    """
    Calculate total amount from inquiry_price column for a given order.
    Non-numeric or empty values are treated as 0.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT inquiry_price FROM order_details WHERE order_number=?", (order_number,))
        rows = cur.fetchall()
        
        total = 0.0
        for (price_str,) in rows:
            if not price_str:
                continue
            try:
                # Handle potential thousand separators or currency symbols if any (though usually clean)
                # Assuming simple float or int string
                val = float(str(price_str).replace(",", "").strip())
                total += val
            except (ValueError, TypeError):
                pass
        return total
    finally:
        conn.close()


def find_recommendation(text: str) -> tuple:
    if not text:
        return None
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT item_name, plan_release, weight, purchase_method, purchase_channel FROM recommendations WHERE is_active=1")
        rows = cur.fetchall()
        
        matches = []
        for item_name, plan_release, weight, p_method, p_channel in rows:
            if item_name and item_name in text:
                matches.append((item_name, plan_release, weight, p_method, p_channel))
        
        # Sort by weight (desc), then by length of item_name (desc) (longer match is more specific)
        if matches:
            matches.sort(key=lambda x: (x[2], len(x[0])), reverse=True)
            return (matches[0][1], matches[0][3], matches[0][4])
        return None
    finally:
        conn.close()


def save_monthly_plan(id: int, plan_month: str, item_name: str, spec_model: str, unit: str, plan_qty: float, plan_budget: float, department: str, remarks: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        if id:
            cur.execute(
                "UPDATE monthly_plans SET plan_month=?, item_name=?, spec_model=?, unit=?, plan_qty=?, plan_budget=?, department=?, remarks=? WHERE id=?",
                (plan_month, item_name, spec_model, unit, plan_qty, plan_budget, department, remarks, id)
            )
        else:
            cur.execute(
                "INSERT INTO monthly_plans(plan_month, item_name, spec_model, unit, plan_qty, plan_budget, department, remarks) VALUES(?,?,?,?,?,?,?,?)",
                (plan_month, item_name, spec_model, unit, plan_qty, plan_budget, department, remarks)
            )
        conn.commit()
    finally:
        conn.close()


def delete_monthly_plan(id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM monthly_plans WHERE id=?", (id,))
        conn.commit()
    finally:
        conn.close()


def import_monthly_plans(rows_data: list):
    """
    rows_data: list of tuples (plan_month, item_name, spec_model, unit, plan_qty, plan_budget, department, remarks)
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO monthly_plans(plan_month, item_name, spec_model, unit, plan_qty, plan_budget, department, remarks) VALUES(?,?,?,?,?,?,?,?)",
            rows_data
        )
        conn.commit()
    finally:
        conn.close()


def fetch_monthly_plans_with_stats(plan_month: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Join logic:
        # 1. Subquery executed amounts from order_details + orders (filtered by yymm)
        # 2. Left join monthly_plans with subquery on item_name AND spec_model
        # NOTE: Using TRIM() to ignore whitespace differences
        sql = """
            SELECT
                mp.id, mp.item_name, mp.spec_model, mp.unit, mp.plan_qty, mp.plan_budget, mp.department, mp.remarks,
                COALESCE(sub.exec_qty, 0),
                COALESCE(sub.exec_amt, 0)
            FROM monthly_plans mp
            LEFT JOIN (
                SELECT
                    TRIM(od.purchase_item) as item_name,
                    TRIM(od.spec_model) as spec_model,
                    SUM(CAST(REPLACE(IFNULL(od.purchase_qty, '0'), ',', '') AS REAL)) as exec_qty,
                    SUM(CAST(REPLACE(IFNULL(od.inquiry_price, '0'), ',', '') AS REAL)) as exec_amt
                FROM order_details od
                JOIN orders o ON od.order_number = o.number
                WHERE o.yymm = ?
                GROUP BY TRIM(od.purchase_item), TRIM(od.spec_model)
            ) sub ON TRIM(mp.item_name) = sub.item_name AND TRIM(mp.spec_model) = sub.spec_model
            WHERE mp.plan_month = ?
            ORDER BY mp.id
        """
        cur.execute(sql, (plan_month, plan_month))
        return cur.fetchall()
    finally:
        conn.close()


def update_order_info(old_number: str, new_task: str, new_unit: str, new_category_code: str, new_yymm: str) -> dict:
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # 1. Fetch current info to compare
        cur.execute("SELECT yymm, category FROM orders WHERE number=?", (old_number,))
        row = cur.fetchone()
        if not row:
            return {"success": False, "msg": f"未找到单号 {old_number}"}
            
        old_yymm, old_cat = row
        
        # 2. Check if regeneration is needed
        if new_category_code == old_cat and new_yymm == old_yymm:
            # Simple update
            cur.execute(
                "UPDATE orders SET task_name=?, unit=? WHERE number=?",
                (new_task, new_unit, old_number)
            )
            conn.commit()
            return {"success": True, "mode": "simple", "new_number": old_number, "msg": "更新成功"}
            
        # 3. Regeneration needed
        # Calculate new main number
        # Note: We must call _get_and_inc inside this transaction context ideally, 
        # but _get_and_inc commits its own transaction if we use next_main_number.
        # So we should duplicate the logic here or reuse _get_and_inc with the current cursor?
        # _get_and_inc takes a cursor and DOES NOT commit. next_main_number DOES commit.
        # We should use _get_and_inc directly.
        
        seq = _get_and_inc(cur, "counter", new_yymm, new_category_code)
        new_number = f"CG-{new_yymm}{new_category_code}{seq:04d}"
        
        # Prepare prefixes
        old_prefix = f"{old_yymm}{old_cat}-"
        new_prefix = f"{new_yymm}{new_category_code}-"
        
        # Update orders table (primary key update)
        # SQLite supports updating PK if cascades are enabled, but here we do it manually or via deferred FKs.
        # Let's turn off foreign keys temporarily or just do it carefully? 
        # SQLite usually cascades updates if defined. Let's check schema... NO foreign keys defined in CREATE TABLE.
        # So we must update all manually.
        
        # 3.1 Update orders
        cur.execute(
            "UPDATE orders SET number=?, yymm=?, category=?, task_name=?, unit=? WHERE number=?",
            (new_number, new_yymm, new_category_code, new_task, new_unit, old_number)
        )
        
        # 3.2 Update release_orders
        cur.execute(
            "UPDATE release_orders SET source_order_number=? WHERE source_order_number=?",
            (new_number, old_number)
        )
        
        # 3.3 Update order_details FK
        cur.execute(
            "UPDATE order_details SET order_number=? WHERE order_number=?",
            (new_number, old_number)
        )
        
        # 3.4 Update detail_no in order_details
        # We need to fetch all details, update them in python, and push back? 
        # Or use SQLite string functions. 
        # detail_no format: 2601MP-1. We want to replace 2601MP- with 2602MPJ-
        # SQLite replace: REPLACE(string, pattern, replacement)
        # But we only want to replace the prefix.
        
        # Fetch affected detail_nos
        cur.execute("SELECT id, detail_no FROM order_details WHERE order_number=?", (new_number,))
        details = cur.fetchall()
        
        for did, dno in details:
            if dno.startswith(old_prefix):
                # Replace prefix
                suffix = dno[len(old_prefix):]
                new_dno = new_prefix + suffix
                cur.execute("UPDATE order_details SET detail_no=? WHERE id=?", (new_dno, did))
        
        # 3.5 Recalc detail counter for the NEW category/month?
        # The logic in recalc_detail_counter finds max(detail_no) for that prefix.
        # We should update the detail_counter for the NEW category.
        # And we might want to update the detail_counter for the OLD category? 
        # Actually, detail_counter is just a cache of max seq.
        # Let's just run recalc for both.
        
        # But wait, we are inside a transaction. We can't call functions that open new connections.
        # We should replicate recalc logic or call it after commit.
        # Let's do it after commit.
        
        conn.commit()
        
        # Post-commit: recalc counters
        try:
            recalc_detail_counter(new_yymm, new_category_code)
            recalc_detail_counter(old_yymm, old_cat)
        except:
            pass
            
        return {
            "success": True, 
            "mode": "regenerate", 
            "new_number": new_number, 
            "msg": f"单号已变更为: {new_number}\n相关明细已自动重命名"
        }
        
    except Exception as e:
        conn.rollback()
        return {"success": False, "msg": str(e)}
    finally:
        conn.close()



def fetch_monthly_details_for_export(yymm: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                o.number, o.task_name, o.category, o.unit, o.date,
                od.detail_no, od.item_name, od.purchase_item, od.spec_model, 
                od.unit, od.purchase_qty, od.budget_wan, od.purchase_method, od.purchase_channel,
                od.plan_release, od.inquiry_price, od.supplier, od.remark, od.plan_time
            FROM order_details od
            JOIN orders o ON od.order_number = o.number
            WHERE o.yymm = ?
        """
        cur.execute(sql, (yymm,))
        rows = cur.fetchall()
        
        # Sort in Python
        # Logic: 
        # 1. Category Order: MPB (Semi) -> MP (Civil) -> MPJ (Machined)
        # 2. Detail No: Alphanumeric sort (extract number from suffix)
        
        def sort_key(row):
            # row[2] is category
            cat = row[2]
            cat_order = 99
            if cat == "MPB": cat_order = 1
            elif cat == "MP": cat_order = 2
            elif cat == "MPJ": cat_order = 3
            
            # row[5] is detail_no, e.g., "2601MPB-1"
            # Extract number after last '-'
            detail_no = row[5]
            try:
                seq = int(detail_no.split("-")[-1])
            except:
                seq = 999999
            
            return (cat_order, seq)
            
        rows.sort(key=sort_key)
        return rows
    finally:
        conn.close()
