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

    # --- NEW TABLE: plan_search_items ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_search_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_no TEXT UNIQUE,
            main_order_no TEXT,
            demand_unit TEXT,
            item_name TEXT,
            spec_model TEXT,
            qty REAL,
            unit TEXT,
            plan_date TEXT,
            plan_release TEXT
        )
        """
    )
    conn.commit()

    # Check if plan_release exists in plan_search_items
    cur.execute("PRAGMA table_info(plan_search_items)")
    cols = [r[1] for r in cur.fetchall()]
    if "plan_release" not in cols:
        cur.execute("ALTER TABLE plan_search_items ADD COLUMN plan_release TEXT")
    conn.commit()

    # --- NEW TABLE: historical_quotes ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            quantity REAL,
            audit_price REAL,
            supplier TEXT,
            quote_date TEXT,
            source_file TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'pending'
        )
        """
    )
    conn.commit()

    # --- NEW TABLES: Standard Items & Mappings (Phase 2) ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS standard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            spec TEXT,
            unit TEXT,
            avg_price REAL,
            min_price REAL,
            max_price REAL,
            latest_price REAL,
            data_count INTEGER DEFAULT 0,
            updated_at TEXT,
            UNIQUE(name, spec)
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS item_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT,
            raw_spec TEXT,
            standard_item_id INTEGER,
            confidence REAL,
            source TEXT,
            created_at TEXT,
            UNIQUE(raw_name, raw_spec),
            FOREIGN KEY(standard_item_id) REFERENCES standard_items(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    # --- Settlement Management Tables ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_no TEXT UNIQUE,
            supplier TEXT,
            status TEXT DEFAULT '待对账',
            total_amount REAL,
            created_at TEXT,
            remarks TEXT
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliation_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_id INTEGER,
            invoice_item_id INTEGER,
            inbound_order_id INTEGER,
            quantity REAL,
            amount_excl_tax REAL,
            amount_incl_tax REAL,
            FOREIGN KEY(reconciliation_id) REFERENCES reconciliations(id) ON DELETE CASCADE,
            FOREIGN KEY(invoice_item_id) REFERENCES invoice_items(id),
            FOREIGN KEY(inbound_order_id) REFERENCES inbound_orders(id)
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
    _remove_inbound_no_unique_constraint(conn)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quote_audit_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT,
            status TEXT DEFAULT '未审核',
            remark TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quote_audit_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            detail_no TEXT,
            order_number TEXT,
            demand_unit TEXT,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            qty REAL,
            budget REAL,
            purchase_method TEXT,
            purchase_channel TEXT,
            plan_release TEXT,
            inquiry_price REAL,
            audit_price REAL,
            remark TEXT,
            FOREIGN KEY(record_id) REFERENCES quote_audit_records(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    # Ensure core tables exist (idempotent)
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
            remark TEXT,
            audit_price TEXT
        )
        """
    )
    # Check if audit_price exists in order_details
    cur.execute("PRAGMA table_info(order_details)")
    cols = [r[1] for r in cur.fetchall()]
    if "audit_price" not in cols:
        cur.execute("ALTER TABLE order_details ADD COLUMN audit_price TEXT")
    conn.commit()

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
    if "approval_doc" not in cols:
        cur.execute("ALTER TABLE orders ADD COLUMN approval_doc TEXT")
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

    # --- Monthly Plans Table ---
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

    # --- Inbound Management Tables ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inbound_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inbound_no TEXT UNIQUE NOT NULL,
            contract_order_id INTEGER,
            contract_no TEXT,
            order_no TEXT,
            purch_plan_no TEXT,
            spec_model TEXT,
            order_qty REAL,
            inbound_qty REAL,
            warehouse_no TEXT,
            inbound_date TEXT,
            operator TEXT,
            create_time TEXT,
            remarks TEXT,
            invoice_id INTEGER
        )
    """
    )
    # Check for invoice_id (migration)
    cur.execute("PRAGMA table_info(inbound_orders)")
    cols = [r[1] for r in cur.fetchall()]
    if "invoice_id" not in cols:
        cur.execute("ALTER TABLE inbound_orders ADD COLUMN invoice_id INTEGER")
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inbound_counter (
            date_str TEXT NOT NULL,
            category TEXT NOT NULL,
            seq INTEGER NOT NULL,
            PRIMARY KEY (date_str, category)
        )
    """
    )
    conn.commit()

    # --- Invoice Management Tables ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT,
            invoice_code TEXT,
            invoice_number TEXT,
            date TEXT,
            seller_name TEXT,
            seller_tax_id TEXT,
            buyer_name TEXT,
            buyer_tax_id TEXT,
            amount_excluding_tax REAL,
            tax_amount REAL,
            total_amount REAL,
            status TEXT DEFAULT '新增',
            material_inbound_no TEXT,
            file_path TEXT,
            created_at TEXT,
            remarks TEXT,
            invoice_type TEXT,
            UNIQUE(invoice_code, invoice_number)
        )
    """
    )
    # Check for invoice_type column
    cur.execute("PRAGMA table_info(invoices)")
    cols = [r[1] for r in cur.fetchall()]
    if "invoice_type" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN invoice_type TEXT")
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            quantity REAL,
            unit_price REAL,
            amount REAL,
            tax_rate REAL,
            tax_amount REAL,
            inbound_id INTEGER,
            inbound_no TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )
    """
    )
    # Check for inbound_id/inbound_no columns
    cur.execute("PRAGMA table_info(invoice_items)")
    cols = [r[1] for r in cur.fetchall()]
    if "inbound_id" not in cols:
        cur.execute("ALTER TABLE invoice_items ADD COLUMN inbound_id INTEGER")
    if "inbound_no" not in cols:
        cur.execute("ALTER TABLE invoice_items ADD COLUMN inbound_no TEXT")
    conn.commit()

    # --- Contract Management Tables ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contract_categories (
            name TEXT PRIMARY KEY
        )
        """
    )
    conn.commit()
    cur.execute("SELECT COUNT(1) FROM contract_categories")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO contract_categories(name) VALUES(?)", [("模块",), ("脚线",), ("其它",)])
        conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contract_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            upload_time TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_number TEXT UNIQUE,
            name TEXT,
            category TEXT,
            supplier TEXT,
            sign_date TEXT,
            end_date TEXT,
            amount REAL,
            status TEXT,
            attachment TEXT,
            remarks TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    
    # Check contracts columns
    cur.execute("PRAGMA table_info(contracts)")
    cols = [r[1] for r in cur.fetchall()]
    if "attachment" not in cols:
        cur.execute("ALTER TABLE contracts ADD COLUMN attachment TEXT")
    if "created_at" not in cols:
        cur.execute("ALTER TABLE contracts ADD COLUMN created_at TEXT")
    conn.commit()
    
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contract_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            spec_model TEXT,
            unit TEXT,
            quantity REAL,
            unit_price REAL,
            total_price REAL,
            executed_qty REAL,
            remarks TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS contract_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            spec_id INTEGER,
            order_date TEXT,
            order_no TEXT,
            quantity REAL,
            unit_price REAL,
            total_price REAL,
            sales_order TEXT,
            prod_order TEXT,
            purch_plan_no TEXT,
            status TEXT DEFAULT '新增',
            remarks TEXT,
            FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
            FOREIGN KEY(spec_id) REFERENCES contract_specs(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    
    # Check contract_orders columns
    cur.execute("PRAGMA table_info(contract_orders)")
    cols = [r[1] for r in cur.fetchall()]
    if "sales_order" not in cols:
        cur.execute("ALTER TABLE contract_orders ADD COLUMN sales_order TEXT")
    if "prod_order" not in cols:
        cur.execute("ALTER TABLE contract_orders ADD COLUMN prod_order TEXT")
    if "purch_plan_no" not in cols:
        cur.execute("ALTER TABLE contract_orders ADD COLUMN purch_plan_no TEXT")
    if "status" not in cols:
        cur.execute("ALTER TABLE contract_orders ADD COLUMN status TEXT DEFAULT '新增'")
    conn.commit()
    
    # --- NEW TABLE MIGRATION: plan_search_items ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan_search_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_no TEXT UNIQUE,
            main_order_no TEXT,
            demand_unit TEXT,
            item_name TEXT,
            spec_model TEXT,
            qty REAL,
            unit TEXT,
            plan_date TEXT,
            plan_release TEXT
        )
        """
    )
    conn.commit()

    # Check if plan_release exists in plan_search_items
    cur.execute("PRAGMA table_info(plan_search_items)")
    cols = [r[1] for r in cur.fetchall()]
    if "plan_release" not in cols:
        cur.execute("ALTER TABLE plan_search_items ADD COLUMN plan_release TEXT")
    conn.commit()

    # --- NEW TABLE MIGRATION: historical_quotes ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            item_name TEXT,
            spec_model TEXT,
            unit TEXT,
            quantity REAL,
            audit_price REAL,
            supplier TEXT,
            quote_date TEXT,
            source_file TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'pending'
        )
        """
    )
    # Check if status exists in historical_quotes
    cur.execute("PRAGMA table_info(historical_quotes)")
    cols = [r[1] for r in cur.fetchall()]
    if "status" not in cols:
        cur.execute("ALTER TABLE historical_quotes ADD COLUMN status TEXT DEFAULT 'pending'")
    conn.commit()

    # --- NEW TABLES MIGRATION: Standard Items & Mappings (Phase 2) ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS standard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            spec TEXT,
            unit TEXT,
            avg_price REAL,
            min_price REAL,
            max_price REAL,
            latest_price REAL,
            data_count INTEGER DEFAULT 0,
            updated_at TEXT,
            UNIQUE(name, spec)
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS item_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT,
            raw_spec TEXT,
            standard_item_id INTEGER,
            confidence REAL,
            source TEXT,
            created_at TEXT,
            UNIQUE(raw_name, raw_spec),
            FOREIGN KEY(standard_item_id) REFERENCES standard_items(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()



# --- NEW TABLES MIGRATION: Settlement Management ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_no TEXT UNIQUE,
            supplier TEXT,
            status TEXT DEFAULT '待对账',
            total_amount REAL,
            created_at TEXT,
            remarks TEXT
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reconciliation_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_id INTEGER,
            invoice_item_id INTEGER,
            inbound_order_id INTEGER,
            quantity REAL,
            amount_excl_tax REAL,
            amount_incl_tax REAL,
            FOREIGN KEY(reconciliation_id) REFERENCES reconciliations(id) ON DELETE CASCADE,
            FOREIGN KEY(invoice_item_id) REFERENCES invoice_items(id),
            FOREIGN KEY(inbound_order_id) REFERENCES inbound_orders(id)
        )
        """
    )
    conn.commit()

    # --- NEW TABLES MIGRATION: Table Column Config ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS table_column_configs (
            table_key TEXT,
            column_index INTEGER,
            width INTEGER,
            PRIMARY KEY (table_key, column_index)
        )
        """
    )
    conn.commit()

    # --- NEW TABLES MIGRATION: AI Config ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_config (
            config_key TEXT PRIMARY KEY,
            provider TEXT,
            base_url TEXT,
            api_key TEXT,
            model_name TEXT,
            system_prompt TEXT
        )
        """
    )
    conn.commit()

    # --- NEW TABLES MIGRATION: Knowledge Base ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filepath TEXT,
            doc_type TEXT,
            upload_time TEXT,
            chunk_count INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            chunk_index INTEGER,
            content TEXT,
            FOREIGN KEY(doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    
    # Try to enable FTS5 if available
    try:
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(content, doc_id UNINDEXED)")
        conn.commit()
    except Exception as e:
        # Fallback if FTS5 is not enabled in SQLite build (though usually it is)
        print(f"Warning: FTS5 not supported: {e}")

def init_db():
    ensure_db()


def _connect():
    ensure_db()
    return sqlite3.connect(DB_PATH)


def _get_and_inc(cur: sqlite3.Cursor, table: str, key_val: str, category: str, key_col: str = "yymm") -> int:
    cur.execute(
        f"SELECT seq FROM {table} WHERE {key_col}=? AND category=?",
        (key_val, category),
    )
    row = cur.fetchone()
    if row is None:
        seq = 1
        cur.execute(
            f"INSERT INTO {table}({key_col}, category, seq) VALUES(?, ?, ?)",
            (key_val, category, seq),
        )
    else:
        seq = int(row[0]) + 1
        cur.execute(
            f"UPDATE {table} SET seq=? WHERE {key_col}=? AND category=?",
            (seq, key_val, category),
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
            "SELECT detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count, purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel, plan_time, demand_unit, plan_release, progress_req, supplier, inquiry_price, tax_rate, actual_status, purchase_body, add_adjust, remark, id FROM order_details WHERE order_number=?",
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
        sql = "SELECT yymm, category, unit, date, task_name, number, approval_doc FROM orders WHERE 1=1"
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

def sync_plan_search_items_from_orders():
    """
    Sync data from order_details and orders to plan_search_items.
    Only adds/updates based on sequence_no (detail_no).
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Select from order_details + orders
        # Mapping:
        # sequence_no <= detail_no
        # main_order_no <= order_number
        # demand_unit <= orders.unit
        # item_name <= purchase_item
        # spec_model <= spec_model
        # qty <= purchase_qty
        # unit <= unit
        # plan_date <= orders.date
        
        sql_src = """
            SELECT 
                od.detail_no, 
                od.order_number, 
                o.unit as demand_unit, 
                od.purchase_item, 
                od.spec_model, 
                od.purchase_qty, 
                od.unit as unit, 
                o.date as plan_date,
                od.plan_release
            FROM order_details od
            JOIN orders o ON od.order_number = o.number
            WHERE od.detail_no IS NOT NULL AND od.detail_no != ''
        """
        
        cur.execute(sql_src)
        rows = cur.fetchall()
        
        count = 0
        for row in rows:
            # row: detail_no, order_number, demand_unit, purchase_item, spec_model, purchase_qty, unit, plan_date, plan_release
            seq = row[0]
            
            # Check if exists
            cur.execute("SELECT id FROM plan_search_items WHERE sequence_no=?", (seq,))
            existing = cur.fetchone()
            
            if existing:
                # Update
                cur.execute(
                    """
                    UPDATE plan_search_items SET 
                        main_order_no=?, demand_unit=?, item_name=?, spec_model=?, 
                        qty=?, unit=?, plan_date=?, plan_release=?
                    WHERE sequence_no=?
                    """,
                    (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], seq)
                )
            else:
                # Insert
                cur.execute(
                    """
                    INSERT INTO plan_search_items(
                        sequence_no, main_order_no, demand_unit, item_name, spec_model, 
                        qty, unit, plan_date, plan_release
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (seq, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                )
            count += 1
            
        conn.commit()
        return count
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


def update_approval_doc(number: str, doc_info: str) -> bool:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET approval_doc=? WHERE number=?", (doc_info, number))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_approval_doc(number: str) -> str:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT approval_doc FROM orders WHERE number=?", (number,))
        row = cur.fetchone()
        return row[0] if row else ""
    finally:
        conn.close()



def save_operation_log(order_number: str, field: str, old_value: str, new_value: str, operator: str, op_time: str):
    conn = _connect()
    try:
        cur = conn.cursor()
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


def delete_unit(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM units WHERE name=?", (name,))
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

def fetch_all_released_plans(month_filter=None, purchaser_filter=None):
    """
    Fetch all released plan details across all orders.
    Returns: list of dicts with combined order and detail info.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                o.number, o.task_name, o.yymm,
                d.id, d.detail_no, d.purchase_item, d.spec_model, d.purchase_qty, d.unit, 
                d.plan_release, d.actual_status
            FROM orders o
            JOIN order_details d ON o.number = d.order_number
            WHERE d.plan_release IS NOT NULL 
              AND d.plan_release != '' 
              AND d.plan_release != '未分配'
        """
        params = []
        
        if month_filter and month_filter != "全部":
            sql += " AND o.yymm = ?"
            params.append(month_filter)
            
        if purchaser_filter and purchaser_filter != "全部":
            sql += " AND d.plan_release = ?"
            params.append(purchaser_filter)
            
        sql += " ORDER BY o.yymm DESC, o.number DESC, d.id ASC"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "order_number": r[0],
                "task_name": r[1],
                "yymm": r[2],
                "detail_id": r[3],
                "detail_no": r[4],
                "item_name": r[5],
                "spec": r[6],
                "qty": r[7],
                "unit": r[8],
                "purchaser": r[9],
                "status": r[10] if r[10] else "未启动"
            })
        return results
    finally:
        conn.close()

def update_detail_status_batch(detail_ids: list, new_status: str):
    """
    Batch update the actual_status of specific order details.
    """
    if not detail_ids:
        return
    conn = _connect()
    try:
        cur = conn.cursor()
        placeholders = ",".join(["?"] * len(detail_ids))
        sql = f"UPDATE order_details SET actual_status = ? WHERE id IN ({placeholders})"
        params = [new_status] + detail_ids
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def get_progress_stats(month_filter=None, purchaser_filter=None):
    """
    Get aggregated stats for the dashboard.
    Returns: total_count, completed_count, status_distribution (dict), purchaser_stats (dict)
    """
    plans = fetch_all_released_plans(month_filter, purchaser_filter)
    
    total = len(plans)
    completed = 0
    status_dist = {}
    purchaser_stats = {}
    
    for p in plans:
        st = p["status"]
        purchaser = p["purchaser"]
        
        if st == "已完成":
            completed += 1
            
        status_dist[st] = status_dist.get(st, 0) + 1
        
        if purchaser not in purchaser_stats:
            purchaser_stats[purchaser] = {"total": 0, "completed": 0}
            
        purchaser_stats[purchaser]["total"] += 1
        if st == "已完成":
            purchaser_stats[purchaser]["completed"] += 1
            
    return total, completed, status_dist, purchaser_stats


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


def delete_purchaser(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM purchasers WHERE name=?", (name,))
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


def delete_purchase_status(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM purchase_status WHERE name=?", (name,))
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

def delete_plan_month(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM plan_months WHERE name=?", (name,))
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
            
        sql += " ORDER BY r.release_date DESC, r.id DESC"
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


# --- Inbound Management Functions ---

def inbound_category_code(text: str) -> str:
    if not text: return "GEN"
    if "半成品" in text: return "MPB"
    if "机加" in text: return "MPJ"
    if "模块" in text: return "MOD"
    if "脚线" in text: return "LIN"
    return "OTH"

def get_next_inbound_number(date_str_yymmdd: str, category_text: str) -> str:
    # date_str_yymmdd: e.g., "260101"
    # category_text: e.g., "模块" -> "MOD"
    cat_code = inbound_category_code(category_text)
    
    conn = _connect()
    try:
        cur = conn.cursor()
        seq = _get_and_inc(cur, "inbound_counter", date_str_yymmdd, cat_code, key_col="date_str")
        conn.commit()
        # RK-YYMMDD-CAT-XXXX
        return f"RK-{date_str_yymmdd}-{cat_code}-{seq:04d}"
    finally:
        conn.close()

def _update_contract_order_status(cur, contract_order_id):
    if not contract_order_id:
        return
        
    # Get order quantity
    cur.execute("SELECT quantity FROM contract_orders WHERE id=?", (contract_order_id,))
    row = cur.fetchone()
    if not row:
        return
    order_qty = row[0] or 0
    
    # Get total inbound quantity
    cur.execute("SELECT SUM(inbound_qty) FROM inbound_orders WHERE contract_order_id=?", (contract_order_id,))
    r = cur.fetchone()
    inbound_sum = r[0] if r and r[0] else 0
    
    new_status = '新增'
    if inbound_sum >= order_qty:
        new_status = '已入库'
    elif inbound_sum > 0:
        new_status = '部分入库'
        
    cur.execute("UPDATE contract_orders SET status=? WHERE id=?", (new_status, contract_order_id))


def save_inbound_order(data: dict):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO inbound_orders(
                inbound_no, contract_order_id, contract_no, order_no, purch_plan_no, 
                spec_model, order_qty, inbound_qty, warehouse_no, inbound_date, 
                operator, create_time, remarks
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data['inbound_no'], data['contract_order_id'], data['contract_no'], 
                data['order_no'], data['purch_plan_no'], data['spec_model'], 
                data['order_qty'], data['inbound_qty'], data['warehouse_no'], 
                data['inbound_date'], data.get('operator', ''), 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('remarks', '')
            )
        )
        
        _update_contract_order_status(cur, data.get('contract_order_id'))
            
        conn.commit()
        return True
    finally:
        conn.close()

def fetch_inbound_orders(filter_text=None, date_range=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                id, inbound_no, inbound_date, contract_no, order_no, purch_plan_no, 
                spec_model, order_qty, inbound_qty, warehouse_no, remarks
            FROM inbound_orders
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (inbound_no LIKE ? OR contract_no LIKE ? OR order_no LIKE ? OR warehouse_no LIKE ?)"
            params.extend([f"%{filter_text}%"] * 4)
            
        if date_range:
            start, end = date_range
            sql += " AND inbound_date BETWEEN ? AND ?"
            params.extend([start, end])
            
        sql += " ORDER BY inbound_date DESC, id DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def update_inbound_order(data: dict):
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Get contract_order_id first
        cur.execute("SELECT contract_order_id FROM inbound_orders WHERE id=?", (data['id'],))
        row = cur.fetchone()
        contract_order_id = row[0] if row else None
        
        cur.execute(
            """
            UPDATE inbound_orders SET 
                inbound_date=?, inbound_qty=?, warehouse_no=?, remarks=?
            WHERE id=?
            """,
            (
                data['inbound_date'], data['inbound_qty'], 
                data['warehouse_no'], data['remarks'], data['id']
            )
        )
        
        if contract_order_id:
            _update_contract_order_status(cur, contract_order_id)
            
        conn.commit()
        return True
    finally:
        conn.close()


def delete_inbound_order(inbound_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Get contract_order_id first
        cur.execute("SELECT contract_order_id FROM inbound_orders WHERE id=?", (inbound_id,))
        row = cur.fetchone()
        contract_order_id = row[0] if row else None
        
        cur.execute("DELETE FROM inbound_orders WHERE id=?", (inbound_id,))
        
        if contract_order_id:
            _update_contract_order_status(cur, contract_order_id)
            
        conn.commit()
        return True
    finally:
        conn.close()

def fetch_contract_orders_grouped(filter_text=None):
    """
    Fetch contract orders grouped by Order No for Main Order Selection.
    Returns list of dicts: order_no, contract_no, contract_name, purch_plan_no, total_qty, pending_qty
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # 1. Get all contract orders grouped by order_no
        # Join with contracts
        sql = """
            SELECT 
                co.order_no, 
                MAX(c.contract_number), 
                MAX(c.name), 
                MAX(co.purch_plan_no),
                SUM(co.quantity),
                MAX(co.order_date)
            FROM contract_orders co
            JOIN contracts c ON co.contract_id = c.id
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (co.order_no LIKE ? OR c.contract_number LIKE ? OR c.name LIKE ?)"
            params.extend([f"%{filter_text}%"] * 3)
            
        sql += " GROUP BY co.order_no ORDER BY co.order_date DESC"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        # 2. Calculate inbound totals per order_no
        # We need to query inbound_orders grouped by order_no
        cur.execute("SELECT order_no, SUM(inbound_qty) FROM inbound_orders GROUP BY order_no")
        inbound_map = {r[0]: r[1] for r in cur.fetchall()}
        
        results = []
        for r in rows:
            # order_no, contract_no, c_name, purch_no, total_qty, date
            ono, cno, cname, pno, qty, date = r
            qty = qty or 0
            inbound = inbound_map.get(ono, 0)
            pending = qty - inbound
            
            # Only show if there is pending quantity? Or show all?
            # User might want to add more even if "completed" (e.g. extras)?
            # But usually we show pending.
            
            results.append({
                'order_no': ono,
                'contract_no': cno,
                'contract_name': cname,
                'purch_plan_no': pno,
                'total_qty': qty,
                'pending_qty': pending,
                'date': date
            })
            
        return results
    finally:
        conn.close()

def fetch_specs_by_order_no(order_no):
    """
    Fetch all specifications for a given order number.
    Returns list of dicts with spec details and individual pending quantities.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        sql = """
            SELECT 
                co.id, co.contract_id, co.spec_id, cs.spec_model, cs.unit, 
                co.quantity, co.unit_price, co.total_price
            FROM contract_orders co
            LEFT JOIN contract_specs cs ON co.spec_id = cs.id
            WHERE co.order_no = ?
        """
        cur.execute(sql, (order_no,))
        rows = cur.fetchall()
        
        # Get inbound qty per contract_order_id
        cur.execute("SELECT contract_order_id, SUM(inbound_qty) FROM inbound_orders WHERE order_no=? GROUP BY contract_order_id", (order_no,))
        inbound_map = {r[0]: r[1] for r in cur.fetchall()}
        
        results = []
        for r in rows:
            # id, cid, sid, model, unit, qty, price, total
            oid, cid, sid, model, unit, qty, price, total = r
            qty = qty or 0
            inbound = inbound_map.get(oid, 0)
            pending = qty - inbound
            
            results.append({
                'contract_order_id': oid,
                'contract_id': cid,
                'spec_id': sid,
                'spec_model': model,
                'unit': unit,
                'order_qty': qty,
                'unit_price': price,
                'total_price': total,
                'inbound_total': inbound,
                'pending_qty': pending
            })
            
        return results
    finally:
        conn.close()

def check_warehouse_no_unique(warehouse_no):
    """
    Check if warehouse_no already exists. Returns True if UNIQUE (not found), False if EXISTS.
    """
    if not warehouse_no: return True
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM inbound_orders WHERE warehouse_no=?", (warehouse_no,))
        return cur.fetchone() is None
    finally:
        conn.close()

def fetch_inbound_orders_extended(filter_text=None):
    """
    Fetch inbound orders with price info.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        # Join with contract_orders to get price
        sql = """
            SELECT 
                io.id, io.inbound_no, io.inbound_date, io.contract_no, io.order_no, io.purch_plan_no, 
                io.spec_model, io.order_qty, io.inbound_qty, io.warehouse_no, io.remarks,
                co.unit_price, io.operator
            FROM inbound_orders io
            LEFT JOIN contract_orders co ON io.contract_order_id = co.id
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (io.inbound_no LIKE ? OR io.contract_no LIKE ? OR io.order_no LIKE ? OR io.warehouse_no LIKE ?)"
            params.extend([f"%{filter_text}%"] * 4)
            
        sql += " ORDER BY io.inbound_date DESC, io.id DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def upsert_inbound_order_batch(records: list):
    """
    records: list of dicts with fields matching inbound_orders.
    Uses inbound_no as the key.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        success_count = 0
        update_count = 0
        errors = []
        
        # 1. Generate a single inbound_no for this batch if there are any "是" records
        has_new = any(str(r.get('is_new', '')).strip() == '是' for r in records)
        new_inbound_no = None
        if has_new:
            date_yyMMdd = datetime.now().strftime("%y%m%d")
            new_inbound_no = get_next_inbound_number(date_yyMMdd, "导入")
        
        for i, rec in enumerate(records):
            is_new = str(rec.get('is_new', '')).strip()
            inbound_no = str(rec.get('inbound_no') or '').strip()
            
            if is_new not in ('是', '否'):
                errors.append(f"第 {i+2} 行: '是否新增'必须填写'是'或'否'")
                continue
                
            if is_new == '是':
                if inbound_no:
                    errors.append(f"第 {i+2} 行: '是否新增'为'是'时，'入库单号'必须留空")
                    continue
                
                # Assign the newly generated single inbound_no
                inbound_no = new_inbound_no
                
                order_no = str(rec.get('order_no') or '').strip()
                spec_model = str(rec.get('spec_model') or '').strip()
                
                cur.execute(
                    """
                    SELECT co.id, co.contract_id, c.contract_number 
                    FROM contract_orders co
                    JOIN contracts c ON co.contract_id = c.id
                    JOIN contract_specs cs ON co.spec_id = cs.id
                    WHERE co.order_no=? AND cs.spec_model=?
                    """,
                    (order_no, spec_model)
                )
                link = cur.fetchone()
                
                if not link:
                    errors.append(f"第 {i+2} 行: 无法匹配订单编号 '{order_no}' 和规格型号 '{spec_model}'")
                    continue
                
                contract_order_id = link[0]
                contract_no = link[2]
                
                cur.execute(
                    """
                    INSERT INTO inbound_orders(
                        inbound_no, contract_order_id, contract_no, order_no, 
                        spec_model, inbound_qty, warehouse_no, inbound_date, 
                        operator, create_time, remarks
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        inbound_no, contract_order_id, contract_no, order_no,
                        spec_model, rec.get('inbound_qty'), rec.get('warehouse_no'),
                        rec.get('inbound_date'), rec.get('operator'),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rec.get('remarks')
                    )
                )
                success_count += 1
                _update_contract_order_status(cur, contract_order_id)
                
            else: # is_new == '否'
                if not inbound_no:
                    errors.append(f"第 {i+2} 行: '是否新增'为'否'时，'入库单号'不能为空")
                    continue
                
                # Check if exists
                cur.execute("SELECT id, contract_order_id FROM inbound_orders WHERE inbound_no=?", (inbound_no,))
                row = cur.fetchone()
                
                if not row:
                    errors.append(f"第 {i+2} 行: 更新失败，系统中不存在入库单号 '{inbound_no}'")
                    continue
                    
                # Update
                cur.execute(
                    """
                    UPDATE inbound_orders SET 
                        inbound_date=?, inbound_qty=?, warehouse_no=?, remarks=?, operator=?
                    WHERE id=?
                    """,
                    (
                        rec.get('inbound_date'), rec.get('inbound_qty'), 
                        rec.get('warehouse_no'), rec.get('remarks'), 
                        rec.get('operator'), row[0]
                    )
                )
                update_count += 1
                _update_contract_order_status(cur, row[1])
        
        conn.commit()
        return success_count, update_count, errors
    finally:
        conn.close()

def fetch_contract_orders_for_inbound(filter_text=None):
    # Returns list of pending orders suitable for inbound
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # 1. Get all contract orders
        # Join with contracts to get contract_no and category
        sql = """
            SELECT 
                co.id, co.order_no, c.contract_number, c.name, c.category,
                cs.spec_model, co.quantity, co.purch_plan_no, co.order_date
            FROM contract_orders co
            JOIN contracts c ON co.contract_id = c.id
            LEFT JOIN contract_specs cs ON co.spec_id = cs.id
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (co.order_no LIKE ? OR c.contract_number LIKE ? OR c.name LIKE ?)"
            params.extend([f"%{filter_text}%"] * 3)
            
        sql += " ORDER BY co.order_date DESC"
        cur.execute(sql, params)
        orders = cur.fetchall()
        
        # 2. Get already inbound qty per contract_order_id
        cur.execute("SELECT contract_order_id, SUM(inbound_qty) FROM inbound_orders GROUP BY contract_order_id")
        inbound_map = {r[0]: r[1] for r in cur.fetchall()}
        
        results = []
        for r in orders:
            # co.id, order_no, contract_no, c_name, category, spec, qty, purch_no, date
            oid, ono, cno, cname, cat, spec, qty, pno, date = r
            qty = qty or 0
            inbound = inbound_map.get(oid, 0)
            remaining = qty - inbound
            
            results.append({
                'id': oid,
                'order_no': ono,
                'contract_no': cno,
                'contract_name': cname,
                'category': cat,
                'spec': spec,
                'qty': qty,
                'inbound_total': inbound,
                'remaining': remaining,
                'purch_plan_no': pno,
                'date': date
            })
            
        return results
    finally:
        conn.close()


# --- Contract & Supplier Management Functions ---

def fetch_suppliers():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

def add_supplier(name: str) -> bool:
    name = name.strip()
    if not name: return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers(name) VALUES(?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def rename_supplier(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM suppliers WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE suppliers SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_supplier(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE name=?", (name,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def fetch_contract_categories():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM contract_categories ORDER BY name")
        return [r[0] for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

def add_contract_category(name: str) -> bool:
    name = name.strip()
    if not name: return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO contract_categories(name) VALUES(?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def rename_contract_category(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name or old_name == new_name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM contract_categories WHERE name=?", (new_name,))
        if cur.fetchone():
            return False
        cur.execute("UPDATE contract_categories SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_contract_category(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM contract_categories WHERE name=?", (name,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def fetch_contracts(filter_text=None, category=None, supplier=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Including executed_amount subquery
        sql = """
            SELECT 
                c.id, c.contract_number, c.name, c.category, c.supplier, 
                c.sign_date, c.end_date, c.amount, c.status, c.attachment,
                (SELECT SUM(total_price) FROM contract_orders WHERE contract_id = c.id) as executed_amount
            FROM contracts c
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (c.contract_number LIKE ? OR c.name LIKE ?)"
            params.extend([f"%{filter_text}%"] * 2)
        if category and category != "全部":
            sql += " AND c.category = ?"
            params.append(category)
        if supplier and supplier != "全部":
            sql += " AND c.supplier = ?"
            params.append(supplier)
            
        sql += " ORDER BY c.created_at DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def save_contract(data):
    conn = _connect()
    try:
        cur = conn.cursor()
        if 'id' in data and data['id']:
            # Update
            sql = """
                UPDATE contracts SET 
                    contract_number=?, name=?, category=?, supplier=?, 
                    sign_date=?, end_date=?, amount=?, status=?, attachment=?, remarks=?
                WHERE id=?
            """
            cur.execute(sql, (
                data['contract_number'], data['name'], data['category'], data['supplier'],
                data['sign_date'], data['end_date'], data['amount'], data['status'], 
                data['attachment'], data['remarks'], data['id']
            ))
        else:
            # Insert
            sql = """
                INSERT INTO contracts (
                    contract_number, name, category, supplier, 
                    sign_date, end_date, amount, status, attachment, remarks, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """
            cur.execute(sql, (
                data['contract_number'], data['name'], data['category'], data['supplier'],
                data['sign_date'], data['end_date'], data['amount'], "执行中", 
                data['attachment'], data['remarks'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        raise Exception("合同编号已存在")
    finally:
        conn.close()

def get_contract_by_id(contract_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Return structure matches what edit_contract expects:
        # 0:id, 1:no, 2:name, 3:cat, 4:sup, 5:sign, 6:end, 7:amt, 8:rem, 9:status, 10:doc
        sql = """
            SELECT 
                id, contract_number, name, category, supplier, 
                sign_date, end_date, amount, remarks, status, attachment
            FROM contracts WHERE id=?
        """
        cur.execute(sql, (contract_id,))
        return cur.fetchone()
    finally:
        conn.close()

def save_contract_attachment(contract_id, file_name, file_path):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contract_attachments(contract_id, file_name, file_path, upload_time) VALUES(?,?,?,?)",
            (contract_id, file_name, file_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    finally:
        conn.close()

def delete_contract(contract_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Manually cascade delete
        cur.execute("DELETE FROM contract_orders WHERE contract_id=?", (contract_id,))
        cur.execute("DELETE FROM contract_specs WHERE contract_id=?", (contract_id,))
        cur.execute("DELETE FROM contract_attachments WHERE contract_id=?", (contract_id,))
        cur.execute("DELETE FROM contracts WHERE id=?", (contract_id,))
        conn.commit()
    finally:
        conn.close()

def fetch_contract_specs(contract_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, spec_model, unit, quantity, unit_price, total_price, executed_qty FROM contract_specs WHERE contract_id=?", (contract_id,))
        return cur.fetchall()
    finally:
        conn.close()

def save_contract_spec(data):
    conn = _connect()
    try:
        cur = conn.cursor()
        if 'id' in data and data['id']:
            cur.execute(
                "UPDATE contract_specs SET spec_model=?, unit=?, quantity=?, unit_price=?, total_price=? WHERE id=?",
                (data['spec_model'], data['unit'], data['quantity'], data['unit_price'], data['total_price'], data['id'])
            )
        else:
            cur.execute(
                "INSERT INTO contract_specs(contract_id, spec_model, unit, quantity, unit_price, total_price, executed_qty) VALUES(?,?,?,?,?,?,0)",
                (data['contract_id'], data['spec_model'], data['unit'], data['quantity'], data['unit_price'], data['total_price'])
            )
        conn.commit()
    finally:
        conn.close()

def save_contract_specs_transaction(contract_id, specs_data):
    # specs_data: list of (id, model, unit, qty, price, total)
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Fetch existing IDs
        cur.execute("SELECT id FROM contract_specs WHERE contract_id=?", (contract_id,))
        existing_ids = {r[0] for r in cur.fetchall()}
        
        incoming_ids = set()
        
        for sp in specs_data:
            sid, model, unit, qty, price, total = sp
            if sid:
                incoming_ids.add(sid)
                cur.execute(
                    "UPDATE contract_specs SET spec_model=?, unit=?, quantity=?, unit_price=?, total_price=? WHERE id=?",
                    (model, unit, qty, price, total, sid)
                )
            else:
                cur.execute(
                    "INSERT INTO contract_specs(contract_id, spec_model, unit, quantity, unit_price, total_price, executed_qty) VALUES(?,?,?,?,?,?,0)",
                    (contract_id, model, unit, qty, price, total)
                )
        
        # Delete removed specs
        to_delete = existing_ids - incoming_ids
        for did in to_delete:
            # Check if used in orders
            cur.execute("SELECT COUNT(1) FROM contract_orders WHERE spec_id=?", (did,))
            if cur.fetchone()[0] > 0:
                raise Exception(f"规格(ID:{did})已被订单引用，无法删除。请先删除相关订单。")
            cur.execute("DELETE FROM contract_specs WHERE id=?", (did,))
            
        conn.commit()
    finally:
        conn.close()

def delete_contract_spec(spec_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM contract_specs WHERE id=?", (spec_id,))
        conn.commit()
    finally:
        conn.close()

def fetch_contract_orders(contract_id, filter_no=None, date_from=None, date_to=None, filter_spec=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Explicit column selection to ensure order
        # 0:id, 1:date, 2:no, 3:model, 4:qty, 5:price, 6:total, 7:sales, 8:prod, 9:purch, 10:status, 11:remark, 12:spec_id
        sql = """
            SELECT 
                co.id, co.order_date, co.order_no, cs.spec_model, 
                co.quantity, co.unit_price, co.total_price, 
                co.sales_order, co.prod_order, co.purch_plan_no, 
                co.status, co.remarks, co.spec_id
            FROM contract_orders co
            LEFT JOIN contract_specs cs ON co.spec_id = cs.id
            WHERE co.contract_id=?
        """
        params = [contract_id]
        
        if filter_no:
            sql += " AND co.order_no LIKE ?"
            params.append(f"%{filter_no}%")
        
        if date_from:
            sql += " AND co.order_date >= ?"
            params.append(date_from)
            
        if date_to:
            sql += " AND co.order_date <= ?"
            params.append(date_to)
            
        if filter_spec:
            sql += " AND cs.spec_model LIKE ?"
            params.append(f"%{filter_spec}%")
            
        sql += " ORDER BY co.order_date DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_contract_orders_by_no_exact(contract_id, order_no):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                co.id, co.order_date, co.order_no, cs.spec_model, 
                co.quantity, co.unit_price, co.total_price, 
                co.sales_order, co.prod_order, co.purch_plan_no, 
                co.status, co.remarks, co.spec_id
            FROM contract_orders co
            LEFT JOIN contract_specs cs ON co.spec_id = cs.id
            WHERE co.contract_id=? AND co.order_no=?
        """
        cur.execute(sql, (contract_id, order_no))
        return cur.fetchall()
    finally:
        conn.close()

def save_contract_order(data):
    conn = _connect()
    try:
        cur = conn.cursor()
        if 'id' in data and data['id']:
            cur.execute(
                """
                UPDATE contract_orders SET 
                    spec_id=?, order_date=?, order_no=?, quantity=?, unit_price=?, 
                    total_price=?, sales_order=?, prod_order=?, purch_plan_no=?, status=?, remarks=?
                WHERE id=?
                """,
                (
                    data['spec_id'], data['order_date'], data['order_no'], data['quantity'], 
                    data['unit_price'], data['total_price'], data['sales_order'], 
                    data['prod_order'], data['purch_plan_no'], data.get('status', '新增'), data['remarks'], data['id']
                )
            )
        else:
            cur.execute(
                """
                INSERT INTO contract_orders(
                    contract_id, spec_id, order_date, order_no, quantity, unit_price, 
                    total_price, sales_order, prod_order, purch_plan_no, status, remarks
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    data['contract_id'], data['spec_id'], data['order_date'], data['order_no'],
                    data['quantity'], data['unit_price'], data['total_price'], 
                    data['sales_order'], data['prod_order'], data['purch_plan_no'], data.get('status', '新增'), data['remarks']
                )
            )
            
        # Update executed qty in specs
        cur.execute("SELECT SUM(quantity) FROM contract_orders WHERE spec_id=?", (data['spec_id'],))
        total_qty = cur.fetchone()[0] or 0
        cur.execute("UPDATE contract_specs SET executed_qty=? WHERE id=?", (total_qty, data['spec_id']))
        
        conn.commit()
    finally:
        conn.close()

def delete_contract_order(order_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Get spec_id before delete to update count
        cur.execute("SELECT spec_id FROM contract_orders WHERE id=?", (order_id,))
        row = cur.fetchone()
        if not row: return
        spec_id = row[0]
        
        cur.execute("DELETE FROM contract_orders WHERE id=?", (order_id,))
        
        # Update executed qty
        cur.execute("SELECT SUM(quantity) FROM contract_orders WHERE spec_id=?", (spec_id,))
        total_qty = cur.fetchone()[0] or 0
        cur.execute("UPDATE contract_specs SET executed_qty=? WHERE id=?", (total_qty, spec_id))
        
        conn.commit()
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


def fetch_recommendations(filter_text=None, limit=None, offset=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = "SELECT id, item_name, plan_release, weight, is_active, purchase_method, purchase_channel FROM recommendations WHERE 1=1"
        params = []
        if filter_text:
            sql += " AND item_name LIKE ?"
            params.append(f"%{filter_text}%")
        
        # Get total count for pagination
        count_sql = "SELECT COUNT(*) FROM recommendations WHERE 1=1"
        count_params = []
        if filter_text:
            count_sql += " AND item_name LIKE ?"
            count_params.append(f"%{filter_text}%")
        cur.execute(count_sql, count_params)
        total_count = cur.fetchone()[0]

        sql += " ORDER BY id"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset if offset else 0)
            
        cur.execute(sql, params)
        return cur.fetchall(), total_count
    finally:
        conn.close()


def save_recommendations_upsert(rows_data_list: list):
    """
    rows_data_list: list of (id, item_name, plan_release, weight, is_active, purchase_method, purchase_channel)
    If id is None, INSERT. If id exists, UPDATE.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        for row in rows_data_list:
            rid, item_name, plan_release, weight, is_active, p_method, p_channel = row
            if rid:
                # Update
                cur.execute(
                    """
                    UPDATE recommendations SET 
                        item_name=?, plan_release=?, weight=?, is_active=?, purchase_method=?, purchase_channel=?
                    WHERE id=?
                    """,
                    (item_name, plan_release, weight, is_active, p_method, p_channel, rid)
                )
            else:
                # Insert
                cur.execute(
                    """
                    INSERT INTO recommendations(item_name, plan_release, weight, is_active, purchase_method, purchase_channel)
                    VALUES(?,?,?,?,?,?)
                    """,
                    (item_name, plan_release, weight, is_active, p_method, p_channel)
                )
        conn.commit()
    finally:
        conn.close()


def delete_recommendation(rid: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM recommendations WHERE id=?", (rid,))
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


def search_orders_fuzzy(keyword):
    """
    Search orders by keyword matching number, task_name, or unit.
    Returns list of (order_no, task_name, unit, create_date, category)
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        keyword = f"%{keyword}%"
        sql = """
            SELECT number, task_name, unit, date, category
            FROM orders
            WHERE number LIKE ? OR task_name LIKE ? OR unit LIKE ?
            ORDER BY date DESC
            LIMIT 50
        """
        
        cur.execute(sql, (keyword, keyword, keyword))
        results = cur.fetchall()
        return results
    finally:
        conn.close()

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
                od.plan_release, od.inquiry_price, od.supplier, od.remark, od.plan_time, od.audit_price
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

# --- Plan Search (Retrieval) Functions ---

def fetch_plan_search_items(filter_seq=None, filter_item=None, filter_order=None, filter_unit=None, 
                           page=1, page_size=20, sort_by=None, sort_desc=False):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                sequence_no, main_order_no, demand_unit, item_name, spec_model, 
                qty, unit, plan_date, plan_release
            FROM plan_search_items
            WHERE 1=1
        """
        params = []
        
        if filter_seq:
            sql += " AND sequence_no = ?"
            params.append(filter_seq)
            
        if filter_item:
            sql += " AND item_name LIKE ?"
            params.append(f"%{filter_item}%")
            
        if filter_order:
            sql += " AND main_order_no = ?"
            params.append(filter_order)
            
        if filter_unit and filter_unit != "全部":
            sql += " AND demand_unit = ?"
            params.append(filter_unit)
            
        # Count total
        count_sql = f"SELECT COUNT(1) FROM ({sql})"
        cur.execute(count_sql, params)
        total_count = cur.fetchone()[0]
        
        # Sorting
        if sort_by:
            # Map UI column names to DB fields if necessary, or use field names directly
            # Assuming sort_by is one of the field names
            direction = "DESC" if sort_desc else "ASC"
            sql += f" ORDER BY {sort_by} {direction}"
        else:
            # Default sort by id/sequence?
            # User said "Default load all... Support sort". 
            # Let's default to sequence_no ASC or ID ASC?
            # Usually users want to see recently added or just sorted by sequence.
            # Let's try to sort by sequence_no naturally if possible, or just string sort.
            sql += " ORDER BY id DESC"
            
        # Pagination
        offset = (page - 1) * page_size
        sql += " LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        return rows, total_count
    finally:
        conn.close()

def import_plan_search_items(data_list):
    """
    data_list: list of dicts with keys matching table columns
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        inserted = 0
        updated = 0
        
        for item in data_list:
            seq = item.get('sequence_no')
            if not seq:
                continue
                
            # Check if exists
            cur.execute("SELECT id FROM plan_search_items WHERE sequence_no=?", (seq,))
            row = cur.fetchone()
            
            if row:
                # Update
                cur.execute(
                    """
                    UPDATE plan_search_items SET 
                        main_order_no=?, demand_unit=?, item_name=?, spec_model=?, 
                        qty=?, unit=?, plan_date=?, plan_release=?
                    WHERE sequence_no=?
                    """,
                    (
                        item.get('main_order_no'), item.get('demand_unit'), item.get('item_name'), 
                        item.get('spec_model'), item.get('qty'), item.get('unit'), 
                        item.get('plan_date'), item.get('plan_release'), seq
                    )
                )
                updated += 1
            else:
                # Insert
                cur.execute(
                    """
                    INSERT INTO plan_search_items(
                        sequence_no, main_order_no, demand_unit, item_name, spec_model, 
                        qty, unit, plan_date, plan_release
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        seq, item.get('main_order_no'), item.get('demand_unit'), 
                        item.get('item_name'), item.get('spec_model'), item.get('qty'), 
                        item.get('unit'), item.get('plan_date'), item.get('plan_release')
                    )
                )
                inserted += 1
                
        conn.commit()
        return inserted, updated
    finally:
        conn.close()

def update_order_detail_prices(order_number: str, detail_no: str, inquiry_price: str, audit_price: str) -> bool:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE order_details SET inquiry_price=?, audit_price=? WHERE order_number=? AND detail_no=?",
            (inquiry_price, audit_price, order_number, detail_no)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def get_all_plan_search_items_for_export(filter_seq=None, filter_item=None, filter_order=None, filter_unit=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                sequence_no, main_order_no, demand_unit, item_name, spec_model, 
                qty, unit, plan_date, plan_release
            FROM plan_search_items
            WHERE 1=1
        """
        params = []
        
        if filter_seq:
            sql += " AND sequence_no = ?"
            params.append(filter_seq)
            
        if filter_item:
            sql += " AND item_name LIKE ?"
            params.append(f"%{filter_item}%")
            
        if filter_order:
            sql += " AND main_order_no = ?"
            params.append(filter_order)
            
        if filter_unit and filter_unit != "全部":
            sql += " AND demand_unit = ?"
            params.append(filter_unit)
            
        sql += " ORDER BY sequence_no"
        
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

# --- Invoice Management Functions ---

def save_invoice(data: dict, items: list) -> int:
    """
    data: dict of invoice header fields
    items: list of dicts for invoice items
    Returns invoice_id
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Check if exists
        cur.execute(
            "SELECT id FROM invoices WHERE invoice_code=? AND invoice_number=?",
            (data.get('invoice_code'), data.get('invoice_number'))
        )
        row = cur.fetchone()
        
        if row:
            # Update
            invoice_id = row[0]
            cur.execute(
                """
                UPDATE invoices SET 
                    date=?, seller_name=?, seller_tax_id=?, buyer_name=?, buyer_tax_id=?,
                    amount_excluding_tax=?, tax_amount=?, total_amount=?, 
                    remarks=?, invoice_type=?, file_path=?
                WHERE id=?
                """,
                (
                    data.get('date'), data.get('seller_name'), data.get('seller_tax_id'),
                    data.get('buyer_name'), data.get('buyer_tax_id'),
                    data.get('amount_excluding_tax'), data.get('tax_amount'), data.get('total_amount'),
                    data.get('remarks'), data.get('invoice_type'), data.get('file_path'),
                    invoice_id
                )
            )
            # Delete old items
            cur.execute("DELETE FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        else:
            # Insert Invoice
            cur.execute(
                """
                INSERT INTO invoices(
                    uuid, invoice_code, invoice_number, date, 
                    seller_name, seller_tax_id, buyer_name, buyer_tax_id,
                    amount_excluding_tax, tax_amount, total_amount, 
                    status, material_inbound_no, file_path, created_at, remarks, invoice_type
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    data.get('uuid'), data.get('invoice_code'), data.get('invoice_number'), data.get('date'),
                    data.get('seller_name'), data.get('seller_tax_id'), data.get('buyer_name'), data.get('buyer_tax_id'),
                    data.get('amount_excluding_tax'), data.get('tax_amount'), data.get('total_amount'),
                    '新增', data.get('material_inbound_no'), data.get('file_path'), 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('remarks'), data.get('invoice_type')
                )
            )
            invoice_id = cur.lastrowid
        
        # Insert Items
        for item in items:
            cur.execute(
                """
                INSERT INTO invoice_items(
                    invoice_id, item_name, spec_model, unit, 
                    quantity, unit_price, amount, tax_rate, tax_amount
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    invoice_id, item.get('item_name'), item.get('spec_model'), item.get('unit'),
                    item.get('quantity'), item.get('unit_price'), item.get('amount'), 
                    item.get('tax_rate'), item.get('tax_amount')
                )
            )
            
        conn.commit()
        return invoice_id
    finally:
        conn.close()

def fetch_invoices(filter_text=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                id, invoice_code, invoice_number, date, seller_name, 
                total_amount, status, material_inbound_no, created_at, invoice_type
            FROM invoices
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (invoice_number LIKE ? OR seller_name LIKE ? OR material_inbound_no LIKE ?)"
            params.extend([f"%{filter_text}%"] * 3)
            
        sql += " ORDER BY date DESC, id DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_invoice_items(invoice_id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, item_name, spec_model, unit, quantity, unit_price, amount, tax_rate, tax_amount, inbound_id, inbound_no
            FROM invoice_items
            WHERE invoice_id=?
            """,
            (invoice_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()

def link_invoice_item_to_inbound(item_id: int, inbound_id: int, inbound_no: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE invoice_items SET inbound_id=?, inbound_no=? WHERE id=?",
            (inbound_id, inbound_no, item_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def fetch_inbound_orders_for_linking(filter_text=None):
    """
    Fetch inbound orders for linking selection.
    Includes a flag or check if it's already linked to ANY invoice item.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Check which inbound_ids are already used in invoice_items
        cur.execute("SELECT DISTINCT inbound_id FROM invoice_items WHERE inbound_id IS NOT NULL")
        rows = cur.fetchall()
        used_ids = set()
        for r in rows:
            val = r[0]
            if isinstance(val, int):
                used_ids.add(val)
            elif isinstance(val, str):
                for p in val.split(','):
                    if p.strip():
                        try:
                            used_ids.add(int(p.strip()))
                        except:
                            pass
        
        sql = """
            SELECT 
                id, inbound_no, inbound_date, contract_no, order_no, 
                spec_model, inbound_qty, warehouse_no
            FROM inbound_orders
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (inbound_no LIKE ? OR contract_no LIKE ? OR order_no LIKE ? OR warehouse_no LIKE ?)"
            params.extend([f"%{filter_text}%"] * 4)
            
        sql += " ORDER BY inbound_date DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            # id, no, date, contract, order, spec, qty, wh
            is_linked = r[0] in used_ids
            results.append(r + (is_linked,))
            
        return results
    finally:
        conn.close()

def delete_invoice(invoice_id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        # Unlink inbound orders first
        cur.execute("UPDATE inbound_orders SET invoice_id=NULL WHERE invoice_id=?", (invoice_id,))
        
        # Delete items (cascade should handle, but manual is safer if cascade not enabled)
        cur.execute("DELETE FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        cur.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        conn.commit()
    finally:
        conn.close()

def fetch_unlinked_inbound_orders(filter_text=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                id, inbound_no, inbound_date, contract_no, order_no, 
                spec_model, inbound_qty, warehouse_no
            FROM inbound_orders
            WHERE invoice_id IS NULL
        """
        params = []
        if filter_text:
            sql += " AND (inbound_no LIKE ? OR contract_no LIKE ? OR order_no LIKE ?)"
            params.extend([f"%{filter_text}%"] * 3)
            
        sql += " ORDER BY inbound_date DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_linked_inbound_orders(invoice_id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                id, inbound_no, inbound_date, contract_no, order_no, 
                spec_model, inbound_qty, warehouse_no
            FROM inbound_orders
            WHERE invoice_id=?
            ORDER BY inbound_date DESC
            """,
            (invoice_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()

def link_inbound_to_invoice(invoice_id: int, inbound_ids: list):
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # 1. Update inbound orders
        # Reset any that were linked to this invoice but not in the new list (if full sync)
        # But here we probably just add.
        # User requirement: "关联入库记录，状态显示'待入账'"
        # Assuming additive or reset? Usually reset/sync.
        
        # Strategy: 
        # 1. Unlink all current for this invoice
        # 2. Link new ones
        
        cur.execute("UPDATE inbound_orders SET invoice_id=NULL WHERE invoice_id=?", (invoice_id,))
        
        if inbound_ids:
            placeholders = ",".join(["?"] * len(inbound_ids))
            cur.execute(f"UPDATE inbound_orders SET invoice_id=? WHERE id IN ({placeholders})", [invoice_id] + inbound_ids)
        
        # 2. Update Invoice Status
        # If has linked items -> '待入账' (if not already '已入账')
        # If no linked items -> '新增'
        
        # Check current status
        cur.execute("SELECT status, material_inbound_no FROM invoices WHERE id=?", (invoice_id,))
        row = cur.fetchone()
        current_status = row[0]
        mat_no = row[1]
        
        new_status = current_status
        if inbound_ids:
            if current_status == '新增':
                new_status = '待入账'
        else:
            if current_status == '待入账':
                new_status = '新增'
        
        # If mat_no is present, it should be '已入账' regardless?
        if mat_no:
            new_status = '已入账'
            
        cur.execute("UPDATE invoices SET status=? WHERE id=?", (new_status, invoice_id))
        conn.commit()
    finally:
        conn.close()

def fetch_contract_statistics(filter_year=None, filter_supplier=None, filter_category=None):
    """
    Fetch aggregated statistics for contracts.
    Returns a list of dictionaries with keys:
    - contract_id, contract_number, contract_name, supplier, category, sign_date
    - total_amount (contracts.amount)
    - executed_amount (sum of contract_orders.total_price)
    - order_count (count of contract_orders)
    - invoiced_amount (sum of invoice_items.amount linked to this contract)
    - settled_amount (sum of invoice_items.amount where invoice status is '已入账')
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Base query for contracts
        sql = """
            SELECT 
                c.id, c.contract_number, c.name, c.supplier, c.category, c.sign_date, c.amount
            FROM contracts c
            WHERE 1=1
        """
        params = []
        
        if filter_year:
            sql += " AND c.sign_date LIKE ?"
            params.append(f"{filter_year}%")
            
        if filter_supplier and filter_supplier != "全部":
            sql += " AND c.supplier = ?"
            params.append(filter_supplier)
            
        if filter_category and filter_category != "全部":
            sql += " AND c.category = ?"
            params.append(filter_category)
            
        sql += " ORDER BY c.sign_date DESC"
        
        cur.execute(sql, params)
        contracts = cur.fetchall()
        
        results = []
        
        for c in contracts:
            c_id, c_no, c_name, c_sup, c_cat, c_date, c_amt = c
            c_amt = c_amt or 0.0
            
            # 1. Executed Amount & Order Count
            cur.execute(
                "SELECT SUM(total_price), COUNT(id) FROM contract_orders WHERE contract_id=?", 
                (c_id,)
            )
            exec_row = cur.fetchone()
            exec_amt = exec_row[0] if exec_row and exec_row[0] else 0.0
            order_cnt = exec_row[1] if exec_row and exec_row[1] else 0
            
            # 2. Invoiced Amount & Settled Amount
            # Logic: Contract -> Contract Orders -> Inbound Orders -> Invoice Items -> Invoices
            # We need to sum invoice_items.amount (or amount+tax? usually just amount or total_amount depending on req)
            # Let's assume "amount" (excluding tax) or "total_amount" (including tax)? 
            # Contract amount is usually total. Invoice total_amount is likely what matches.
            # Let's use total_amount (amount + tax) from invoice_items.
            # But invoice_items table has: amount, tax_amount. So total = amount + tax_amount.
            # Or we can query invoice_items.amount + invoice_items.tax_amount
            
            # Find all contract_order_ids for this contract
            cur.execute("SELECT id FROM contract_orders WHERE contract_id=?", (c_id,))
            co_ids = [str(r[0]) for r in cur.fetchall()]
            
            invoiced_amt = 0.0
            settled_amt = 0.0
            
            if co_ids:
                placeholders = ",".join(["?"] * len(co_ids))
                # Find inbound orders linked to these contract orders
                cur.execute(
                    f"SELECT id FROM inbound_orders WHERE contract_order_id IN ({placeholders})",
                    co_ids
                )
                inbound_ids = [str(r[0]) for r in cur.fetchall()]
                
                if inbound_ids:
                    target_ids = set(inbound_ids)
                    
                    # Get all invoice items with inbound_id
                    # Note: We fetch all to filter in Python because inbound_id can be comma-separated string
                    cur.execute("SELECT inbound_id, amount, tax_amount, invoice_id FROM invoice_items WHERE inbound_id IS NOT NULL")
                    all_items = cur.fetchall()
                    
                    relevant_inv_ids = set()
                    item_amts = [] # (amt, invoice_id)
                    
                    for r in all_items:
                        val = r[0]
                        current_ids = set()
                        if isinstance(val, int):
                            current_ids.add(str(val))
                        elif isinstance(val, str):
                            current_ids.update([x.strip() for x in val.split(',') if x.strip()])
                            
                        if not current_ids.isdisjoint(target_ids):
                            amt = (r[1] or 0) + (r[2] or 0)
                            item_amts.append((amt, r[3]))
                            relevant_inv_ids.add(r[3])
                            
                    if relevant_inv_ids:
                        p_holders = ",".join(["?"] * len(relevant_inv_ids))
                        cur.execute(f"SELECT id, status FROM invoices WHERE id IN ({p_holders})", list(relevant_inv_ids))
                        status_map = {row[0]: row[1] for row in cur.fetchall()}
                        
                        for amt, inv_id in item_amts:
                            invoiced_amt += amt
                            if status_map.get(inv_id) == '已入账':
                                settled_amt += amt
            
            results.append({
                'contract_id': c_id,
                'contract_number': c_no,
                'contract_name': c_name,
                'supplier': c_sup,
                'category': c_cat,
                'sign_date': c_date,
                'total_amount': c_amt,
                'executed_amount': exec_amt,
                'order_count': order_cnt,
                'invoiced_amount': invoiced_amt,
                'settled_amount': settled_amt
            })
            
        return results
    finally:
        conn.close()

def update_invoice_material_no(invoice_id: int, mat_no: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        status = '已入账' if mat_no else '待入账'
        # Fallback to '新增' if no linked items? 
        # Check linked items
        cur.execute("SELECT COUNT(1) FROM inbound_orders WHERE invoice_id=?", (invoice_id,))
        count = cur.fetchone()[0]
        if not mat_no and count == 0:
            status = '新增'
            
        cur.execute("UPDATE invoices SET material_inbound_no=?, status=? WHERE id=?", (mat_no, status, invoice_id))
        conn.commit()
    finally:
        conn.close()

def fetch_reconciliations(filter_text=None, status_filter=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT id, reconciliation_no, supplier, status, total_amount, created_at, remarks
            FROM reconciliations
            WHERE 1=1
        """
        params = []
        if filter_text:
            sql += " AND (reconciliation_no LIKE ? OR supplier LIKE ?)"
            params.extend([f"%{filter_text}%"] * 2)
        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)
        
        sql += " ORDER BY created_at DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def save_reconciliation(data: dict):
    conn = _connect()
    try:
        cur = conn.cursor()
        if 'id' in data and data['id']:
            cur.execute(
                """
                UPDATE reconciliations SET 
                    supplier=?, status=?, total_amount=?, remarks=?
                WHERE id=?
                """,
                (data['supplier'], data['status'], data['total_amount'], data['remarks'], data['id'])
            )
            rec_id = data['id']
        else:
            cur.execute(
                """
                INSERT INTO reconciliations(reconciliation_no, supplier, status, total_amount, created_at, remarks)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    data['reconciliation_no'], data['supplier'], data.get('status', '待对账'),
                    data['total_amount'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('remarks')
                )
            )
            rec_id = cur.lastrowid
        conn.commit()
        return rec_id
    finally:
        conn.close()

def delete_reconciliation(rec_id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM reconciliations WHERE id=?", (rec_id,))
        conn.commit()
    finally:
        conn.close()

def get_next_reconciliation_number():
    conn = _connect()
    try:
        cur = conn.cursor()
        # Format: DZ-YYMMDD-0001
        prefix = f"DZ-{datetime.now().strftime('%y%m%d')}-"
        cur.execute("SELECT reconciliation_no FROM reconciliations WHERE reconciliation_no LIKE ? ORDER BY reconciliation_no DESC LIMIT 1", (prefix + "%",))
        row = cur.fetchone()
        if row:
            try:
                seq = int(row[0].split("-")[-1])
                return f"{prefix}{seq+1:04d}"
            except:
                pass
        return f"{prefix}0001"
    finally:
        conn.close()

def fetch_unreconciled_invoices(supplier_filter=None):
    """
    Fetch invoices that are NOT in any reconciliation.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                i.id, i.invoice_number, i.seller_name, i.total_amount, i.date, i.status
            FROM invoices i
            WHERE i.status != '已完成' 
            AND NOT EXISTS (
                SELECT 1 FROM reconciliation_details rd 
                JOIN invoice_items ii ON rd.invoice_item_id = ii.id
                WHERE ii.invoice_id = i.id
            )
        """
        params = []
        if supplier_filter:
            sql += " AND i.seller_name LIKE ?"
            params.append(f"%{supplier_filter}%")
            
        sql += " ORDER BY i.date DESC"
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_invoice_items_with_inbound_split(invoice_ids: list):
    """
    Fetch invoice items for given invoice IDs, splitting them by inbound orders.
    """
    if not invoice_ids: return []
    conn = _connect()
    try:
        cur = conn.cursor()
        placeholders = ",".join(["?"] * len(invoice_ids))
        cur.execute(f"""
            SELECT 
                ii.id, ii.invoice_id, ii.item_name, ii.spec_model, ii.unit, 
                ii.quantity, ii.unit_price, ii.amount, ii.tax_rate, ii.inbound_id
            FROM invoice_items ii
            WHERE ii.invoice_id IN ({placeholders})
        """, invoice_ids)
        items = cur.fetchall()
        
        results = []
        for item in items:
            ii_id, inv_id, name, spec, unit, qty, price, amt, tax_rate, inbound_ids_str = item
            
            inbound_id_list = []
            if inbound_ids_str:
                if isinstance(inbound_ids_str, int):
                    inbound_id_list = [inbound_ids_str]
                else:
                    inbound_id_list = [int(x) for x in str(inbound_ids_str).split(',') if x.strip().isdigit()]
            
            if not inbound_id_list:
                results.append({
                    'invoice_item_id': ii_id,
                    'inbound_order_id': None,
                    'warehouse_no': '',
                    'quantity': qty,
                    'amount': amt,
                    'unit_price': price,
                    'tax_rate': tax_rate,
                    'item_name': name,
                    'spec_model': spec,
                    'unit': unit
                })
            else:
                p_holders = ",".join(["?"] * len(inbound_id_list))
                cur.execute(f"SELECT id, warehouse_no, inbound_qty FROM inbound_orders WHERE id IN ({p_holders})", inbound_id_list)
                inbounds = cur.fetchall()
                
                total_inbound_qty = sum([r[2] or 0 for r in inbounds])
                if total_inbound_qty == 0: total_inbound_qty = 1
                
                for ib in inbounds:
                    ib_id, ib_no, ib_qty = ib
                    ib_qty = ib_qty or 0
                    ratio = ib_qty / total_inbound_qty
                    
                    split_qty = qty * ratio
                    split_amt = amt * ratio
                    
                    results.append({
                        'invoice_item_id': ii_id,
                        'inbound_order_id': ib_id,
                        'warehouse_no': ib_no,
                        'quantity': split_qty,
                        'amount': split_amt,
                        'unit_price': price,
                        'tax_rate': tax_rate,
                        'item_name': name,
                        'spec_model': spec,
                        'unit': unit
                    })
        return results
    finally:
        conn.close()

def create_reconciliation_details_batch(rec_id: int, items_data: list):
    conn = _connect()
    try:
        cur = conn.cursor()
        for item in items_data:
            amt = item['amount']
            tax_rate = item.get('tax_rate', 0) or 0
            if tax_rate > 1: tax_rate = tax_rate / 100.0
            
            amt_incl = amt * (1 + tax_rate)
            
            cur.execute(
                """
                INSERT INTO reconciliation_details(
                    reconciliation_id, invoice_item_id, inbound_order_id, 
                    quantity, amount_excl_tax, amount_incl_tax
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    rec_id, item['invoice_item_id'], item['inbound_order_id'],
                    item['quantity'], amt, amt_incl
                )
            )
        conn.commit()
    finally:
        conn.close()

def fetch_reconciliation_details(rec_id: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                rd.id, 
                i.invoice_number, 
                io.warehouse_no, 
                ii.unit, 
                rd.quantity, 
                ii.unit_price, 
                rd.amount_excl_tax, 
                rd.amount_incl_tax, 
                ii.spec_model,
                ii.item_name
            FROM reconciliation_details rd
            LEFT JOIN invoice_items ii ON rd.invoice_item_id = ii.id
            LEFT JOIN invoices i ON ii.invoice_id = i.id
            LEFT JOIN inbound_orders io ON rd.inbound_order_id = io.id
            WHERE rd.reconciliation_id = ?
        """
        cur.execute(sql, (rec_id,))
        return cur.fetchall()
    finally:
        conn.close()

def get_table_column_widths(table_key: str):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT column_index, width FROM table_column_configs WHERE table_key=?", (table_key,))
        return {int(c): int(w) for c, w in cur.fetchall()}
    finally:
        conn.close()

def save_table_column_width(table_key: str, col_index: int, width: int):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO table_column_configs(table_key, column_index, width) VALUES(?,?,?)",
            (table_key, col_index, width)
        )
        conn.commit()
    finally:
        conn.close()

def _remove_inbound_no_unique_constraint(conn: sqlite3.Connection):
    cur = conn.cursor()
    try:
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inbound_orders'")
        row = cur.fetchone()
        if not row: return
        
        sql = row[0]
        if "inbound_no TEXT UNIQUE" in sql:
            # print("Migrating inbound_orders to remove UNIQUE constraint...")
            cur.execute("ALTER TABLE inbound_orders RENAME TO inbound_orders_old")
            new_sql = sql.replace("inbound_no TEXT UNIQUE", "inbound_no TEXT")
            cur.execute(new_sql)
            cur.execute("INSERT INTO inbound_orders SELECT * FROM inbound_orders_old")
            cur.execute("DROP TABLE inbound_orders_old")
            conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        pass

def get_ai_config(config_key='default'):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT provider, base_url, api_key, model_name, system_prompt FROM ai_config WHERE config_key=?", (config_key,))
        row = cur.fetchone()
        if row:
            return {
                "provider": row[0],
                "base_url": row[1],
                "api_key": row[2],
                "model_name": row[3],
                "system_prompt": row[4]
            }
        return None
    finally:
        conn.close()

def save_ai_config(config_key, provider, base_url, api_key, model_name, system_prompt):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ai_config (config_key, provider, base_url, api_key, model_name, system_prompt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(config_key) DO UPDATE SET
                provider=excluded.provider,
                base_url=excluded.base_url,
                api_key=excluded.api_key,
                model_name=excluded.model_name,
                system_prompt=excluded.system_prompt
            """,
            (config_key, provider, base_url, api_key, model_name, system_prompt)
        )
        conn.commit()
    finally:
        conn.close()

def create_quote_audit_record(name, created_at=None, status='未审核', remark=''):
    if not created_at:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO quote_audit_records (name, created_at, status, remark) VALUES (?, ?, ?, ?)",
            (name, created_at, status, remark)
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"Error creating quote audit record: {e}")
        return None
    finally:
        conn.close()

def get_quote_audit_records():
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at, status, remark FROM quote_audit_records ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        conn.close()

def delete_quote_audit_record(record_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM quote_audit_records WHERE id = ?", (record_id,))
        cur.execute("DELETE FROM quote_audit_details WHERE record_id = ?", (record_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting quote audit record: {e}")
        return False
    finally:
        conn.close()

def add_quote_audit_details(record_id, details):
    conn = _connect()
    try:
        cur = conn.cursor()
        for d in details:
            cur.execute(
                """
                INSERT INTO quote_audit_details (
                    record_id, detail_no, order_number, demand_unit, item_name, spec_model, 
                    unit, qty, budget, purchase_method, purchase_channel, plan_release, 
                    inquiry_price, audit_price, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id, d.get('detail_no', ''), d.get('order_number', ''), d.get('demand_unit', ''),
                    d.get('item_name', ''), d.get('spec_model', ''), d.get('unit', ''),
                    d.get('qty', 0), d.get('budget', 0), d.get('purchase_method', ''),
                    d.get('purchase_channel', ''), d.get('plan_release', ''),
                    d.get('inquiry_price', 0), d.get('audit_price', 0), d.get('remark', '')
                )
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding quote audit details: {e}")
        return False
    finally:
        conn.close()

def get_quote_audit_details(record_id):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, detail_no, order_number, demand_unit, item_name, spec_model, 
                   unit, qty, budget, purchase_method, purchase_channel, plan_release, 
                   inquiry_price, audit_price, remark 
            FROM quote_audit_details 
            WHERE record_id = ?
            ORDER BY id ASC
            """,
            (record_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()

def update_quote_audit_status(record_id, status):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE quote_audit_records SET status = ? WHERE id = ?", (status, record_id))
        conn.commit()
        return True
    finally:
        conn.close()

def update_quote_audit_detail_price(detail_id, audit_price):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE quote_audit_details SET audit_price = ? WHERE id = ?", (audit_price, detail_id))
        conn.commit()
        return True
    finally:
        conn.close()
