import argparse
import sys
import sqlite3
import database
from datetime import datetime

ALLOWED_METHODS = ["", "询比采购", "公开招标", "集中采购", "框架协议"]
ALLOWED_CHANNELS = ["", "能建商城", "采购平台", "线下采购"]
STATUS_OPTIONS = [
    "未启动", "询价中", "定点审批中", "合同流转中", 
    "已下单待收货", "部分到货", "已完成"
]

def get_db_connection():
    return sqlite3.connect(database.DB_PATH)

def cmd_create_order(args):
    """创建主单 (Master Order)"""
    yymm = args.month
    category = args.category
    unit = args.unit
    task_name = args.name
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Generate Order Number
    # Note: database.next_main_number logic is slightly complex to replicate perfectly if we don't use the function.
    # But we can import it.
    # We need to access the internal function or add a wrapper. 
    # Let's check if database.py exposes next_main_number. 
    # Yes, it does: def next_main_number(yymm: str, category_code: str) -> str:
    
    # Wait, next_main_number was in the file I read?
    # I saw next_detail_number. I missed next_main_number in the grep but I saw it in the read output at line 1143!
    # Yes: def next_main_number(yymm: str, category_code: str) -> str:
    
    try:
        order_no = database.next_main_number(yymm, category)
    except AttributeError:
        # Fallback if I misread the file and it's not exported, but it seemed to be top-level.
        print("Error: database.next_main_number not found.")
        return

    # 2. Save Order
    database.save_order(order_no, yymm, category, unit, date_str, task_name)
    print(f"SUCCESS: Order created. Number: {order_no}")

def cmd_add_item(args):
    """添加明细 (Detail Item)"""
    order_no = args.order
    item_name = args.name
    spec = args.spec
    qty = args.qty
    unit = args.unit
    
    # Optional args
    price = args.price if args.price else ""
    remark = args.remark if args.remark else ""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Validate Order and get YYMM/Category
        cursor.execute("SELECT yymm, category FROM orders WHERE number=?", (order_no,))
        row = cursor.fetchone()
        if not row:
            print(f"Error: Order {order_no} not found.")
            return
        
        yymm, category = row
        
        # 2. Generate Detail Sequence Number
        # Use database.next_detail_number(yymm, category)
        detail_no = database.next_detail_number(yymm, category)
        
        # 3. Auto-Recommendation Logic
        purchase_method = ""
        purchase_channel = ""
        plan_release = ""
        
        # Try database recommendation
        rec = database.find_recommendation(item_name)
        if rec:
            # rec: (plan_release, purchase_method, purchase_channel)
            plan_release = rec[0] if rec[0] else ""
            purchase_method = rec[1] if rec[1] else ""
            purchase_channel = rec[2] if rec[2] else ""
            
        # 4. Linkage Logic (Method -> Channel)
        # If method is set (by recommendation), try to infer channel if channel is empty
        if purchase_method:
            if purchase_method == "询比采购":
                if not purchase_channel: purchase_channel = "线下采购"
            elif purchase_method in ["公开招标", "集中采购"]:
                if not purchase_channel: purchase_channel = "采购平台"
            elif purchase_method == "框架协议":
                if not purchase_channel: purchase_channel = "能建商城"
        
        # 5. Defaults
        progress_req = f"{yymm}15" # Default progress requirement
        status = "" # Default status
        
        # 6. Insert into DB
        # We need to construct the insert statement matching table schema
        # Schema:
        # id, order_number, detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count,
        # purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel, plan_time,
        # demand_unit, plan_release, progress_req, supplier, inquiry_price, tax_rate, actual_status,
        # purchase_body, add_adjust, remark
        
        # Note: 'item_name' in DB seems to be mapped to row[0] which is empty string in ui_detail.py save logic?
        # In ui_detail.py:
        # data = ["", purchase_item, spec_model, ...]
        # Wait, let's check save logic in ui_detail.py again.
        # Line 410: "", # item_name
        # Line 411: purchase_item (This is the actual "Name" column in UI, "采购标的")
        # Line 412: spec_model
        
        # So DB 'item_name' column is UNUSED/Empty? And 'purchase_item' is the real name?
        # Let's check database.py fetch_order_details:
        # SELECT detail_no, item_name, purchase_item ...
        # ui_detail.py load_rows mapping:
        # (1, row[2]), # 采购标的 -> matches purchase_item
        # So yes, 'purchase_item' is the "Name". 'item_name' is ignored or legacy.
        
        sql = """
            INSERT INTO order_details (
                order_number, detail_no, item_name, purchase_item, spec_model, 
                purchase_qty, unit, unit_price, purchase_method, purchase_channel, 
                plan_release, progress_req, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(sql, (
            order_no, detail_no, "", item_name, spec,
            qty, unit, price, purchase_method, purchase_channel,
            plan_release, progress_req, remark
        ))
        
        conn.commit()
        print(f"SUCCESS: Item added. Sequence: {detail_no}")
        print(f"  Details: Name={item_name}, Method={purchase_method}, Channel={purchase_channel}, Purchaser={plan_release}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def cmd_update_progress(args):
    """更新明细进度状态 (Update Detail Progress Status)"""
    detail_nos = args.details
    status = args.status
    
    if not detail_nos:
        print("Error: No detail numbers provided.")
        return
        
    if status not in STATUS_OPTIONS:
        print(f"Error: Invalid status '{status}'. Allowed options: {', '.join(STATUS_OPTIONS)}")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First, find the IDs for these detail numbers
        placeholders = ",".join(["?"] * len(detail_nos))
        sql_find = f"SELECT id, detail_no FROM order_details WHERE detail_no IN ({placeholders})"
        cursor.execute(sql_find, detail_nos)
        rows = cursor.fetchall()
        
        found_ids = [r[0] for r in rows]
        found_nos = [r[1] for r in rows]
        
        missing = set(detail_nos) - set(found_nos)
        if missing:
            print(f"Warning: The following detail numbers were not found: {', '.join(missing)}")
            
        if not found_ids:
            print("Error: No valid detail numbers found to update.")
            return
            
        # Update using the batch function from database
        database.update_detail_status_batch(found_ids, status)
        print(f"SUCCESS: Updated {len(found_ids)} items to status '{status}'.")
        print(f"  Updated items: {', '.join(found_nos)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Purchase Plan CLI 2.0")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Command: order
    parser_order = subparsers.add_parser("order", help="Manage Orders")
    order_subparsers = parser_order.add_subparsers(dest="subcommand", help="Order Actions")
    
    # Subcommand: order create
    cmd_create = order_subparsers.add_parser("create", help="Create a new Master Order")
    cmd_create.add_argument("--month", required=True, help="Plan Month (e.g., 2601)")
    cmd_create.add_argument("--category", required=True, help="Category Code (e.g., MPJ)")
    cmd_create.add_argument("--unit", required=True, help="Demand Unit")
    cmd_create.add_argument("--name", required=True, help="Task Name")
    
    # Subcommand: order add-item
    cmd_add = order_subparsers.add_parser("add-item", help="Add a detail item to an order")
    cmd_add.add_argument("--order", required=True, help="Order Number (e.g., CG-2601MPJ0001)")
    cmd_add.add_argument("--name", required=True, help="Purchase Subject (Name)")
    cmd_add.add_argument("--spec", required=True, help="Specification/Model")
    cmd_add.add_argument("--qty", required=True, help="Quantity")
    cmd_add.add_argument("--unit", required=True, help="Unit")
    cmd_add.add_argument("--price", help="Unit Price")
    cmd_add.add_argument("--remark", help="Remark")
    
    # Subcommand: order update-status
    cmd_update = order_subparsers.add_parser("update-status", help="Update progress status for detail items")
    cmd_update.add_argument("--status", required=True, help=f"Target status. Allowed: {', '.join(STATUS_OPTIONS)}")
    cmd_update.add_argument("--details", nargs='+', required=True, help="One or more Detail Numbers (e.g., 2603MPJ-1 2603MPJ-2)")
    
    args = parser.parse_args()
    
    if args.command == "order":
        if args.subcommand == "create":
            cmd_create_order(args)
        elif args.subcommand == "add-item":
            cmd_add_item(args)
        elif args.subcommand == "update-status":
            cmd_update_progress(args)
        else:
            parser_order.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
