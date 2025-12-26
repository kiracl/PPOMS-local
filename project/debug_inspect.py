import sqlite3
import binascii
import os

DB_PATH = "purchase.db"

def get_hex(s):
    if s is None: return "None"
    return binascii.hexlify(str(s).encode('utf-8')).decode('utf-8')

def inspect():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("--- Monthly Plans (2601) ---")
    cur.execute("SELECT id, item_name, spec_model FROM monthly_plans WHERE plan_month='2601'")
    plans = cur.fetchall()
    for row in plans:
        print(f"ID: {row[0]}")
        print(f"  Item: '{row[1]}' (Hex: {get_hex(row[1])})")
        print(f"  Spec: '{row[2]}' (Hex: {get_hex(row[2])})")

    print("\n--- Order Details (YYMM=2601) ---")
    cur.execute("""
        SELECT d.id, d.item_name, d.purchase_item, d.spec_model, o.yymm 
        FROM order_details d
        JOIN orders o ON d.order_number = o.number
        WHERE o.yymm='2601'
    """)
    details = cur.fetchall()
    for row in details:
        print(f"ID: {row[0]}")
        print(f"  ItemName: '{row[1]}' (Hex: {get_hex(row[1])})")
        print(f"  PurchItem: '{row[2]}' (Hex: {get_hex(row[2])})")
        print(f"  Spec: '{row[3]}' (Hex: {get_hex(row[3])})")

    conn.close()

if __name__ == "__main__":
    inspect()
