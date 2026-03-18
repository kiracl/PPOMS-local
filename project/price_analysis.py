import sqlite3
import pandas as pd
import database
from datetime import datetime
import difflib
import uuid
import xlrd # For .xls support in packaged app

def import_historical_quotes(file_path: str):
    """
    Import historical quotes from Excel file.
    Expected columns: 采购标的, 规格型号, 单位, 数量, 审核价, 供应商, 报价日期
    Returns: (success_count, error_msg)
    """
    try:
        df = pd.read_excel(file_path)
        
        # Normalize columns
        df.columns = [str(c).strip() for c in df.columns]
        
        required = ["采购标的", "审核价"] # Minimal requirement
        missing = [c for c in required if c not in df.columns]
        if missing:
            return 0, f"缺少必要列: {', '.join(missing)}"
            
        # Optional columns mapping
        col_map = {
            "采购标的": "item_name",
            "规格型号": "spec_model",
            "单位": "unit",
            "数量": "quantity",
            "审核价": "audit_price",
            "供应商": "supplier",
            "报价日期": "quote_date"
        }
        
        batch_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())[:8]
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = database._connect()
        cur = conn.cursor()
        
        count = 0
        for _, row in df.iterrows():
            item_name = str(row.get("采购标的", "")).strip()
            if not item_name or item_name.lower() == "nan":
                continue
                
            audit_price_raw = row.get("审核价", 0)
            try:
                audit_price = float(str(audit_price_raw).replace(",", "").strip())
            except:
                audit_price = 0.0
                
            if audit_price <= 0:
                continue
                
            spec_model = str(row.get("规格型号", "")).strip()
            if spec_model.lower() == "nan": spec_model = ""
            
            unit = str(row.get("单位", "")).strip()
            if unit.lower() == "nan": unit = ""
            
            qty_raw = row.get("数量", 0)
            try:
                quantity = float(str(qty_raw).replace(",", "").strip())
            except:
                quantity = 0.0
                
            supplier = str(row.get("供应商", "")).strip()
            if supplier.lower() == "nan": supplier = ""
            
            quote_date = str(row.get("报价日期", "")).strip()
            if quote_date.lower() == "nan": quote_date = ""
            # Try to format date if it's datetime object
            if hasattr(row.get("报价日期"), "strftime"):
                quote_date = row.get("报价日期").strftime("%Y-%m-%d")
            
            cur.execute(
                """
                INSERT INTO historical_quotes(
                    batch_id, item_name, spec_model, unit, quantity, 
                    audit_price, supplier, quote_date, source_file, created_at, status
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    batch_id, item_name, spec_model, unit, quantity,
                    audit_price, supplier, quote_date, file_path, created_at, "pending"
                )
            )
            count += 1
            
        conn.commit()
        conn.close()
        return count, ""
        
    except Exception as e:
        return 0, str(e)

def run_analysis_task(progress_callback=None):
    """
    Background task to process pending historical quotes.
    1. Fetch pending quotes.
    2. Normalize and map to standard items.
    3. Update standard item statistics.
    """
    conn = database._connect()
    try:
        cur = conn.cursor()
        # Fetch pending
        cur.execute("SELECT id, item_name, spec_model, unit, audit_price, quote_date FROM historical_quotes WHERE status='pending'")
        pending_rows = cur.fetchall()
        
        total = len(pending_rows)
        if total == 0:
            return "没有待处理的数据"

        processed = 0
        # Cache standard items for fuzzy matching to avoid repeated queries
        cur.execute("SELECT id, name, spec FROM standard_items")
        cached_standards = cur.fetchall() # List of (id, name, spec)
        
        for row in pending_rows:
            qid, qname, qspec, qunit, qprice, qdate = row
            if qprice is None: qprice = 0.0
            
            # 1. Normalize
            raw_name = (qname or "").strip()
            raw_spec = (qspec or "").strip()
            
            # 2. Check Mapping
            cur.execute("SELECT standard_item_id FROM item_mappings WHERE raw_name=? AND raw_spec=?", (raw_name, raw_spec))
            map_row = cur.fetchone()
            
            std_id = None
            is_new_standard = False
            
            if map_row:
                std_id = map_row[0]
            else:
                # 3. Find Candidate Standard Item (Fuzzy Match)
                best_match_id = None
                best_score = 0.0
                
                target_name = raw_name
                target_spec = raw_spec
                
                for cid, cname, cspec in cached_standards:
                    # Score based on name similarity + spec similarity
                    # Name is more important.
                    s1 = difflib.SequenceMatcher(None, target_name, cname).ratio()
                    if s1 < 0.6: continue # Optimization
                    
                    s2 = difflib.SequenceMatcher(None, target_spec, cspec).ratio()
                    
                    # Weighted score: Name 70%, Spec 30%
                    score = s1 * 0.7 + s2 * 0.3
                    
                    if score > best_score:
                        best_score = score
                        best_match_id = cid
                
                # Threshold
                if best_score > 0.85:
                    std_id = best_match_id
                    # Create Mapping
                    cur.execute(
                        "INSERT INTO item_mappings(raw_name, raw_spec, standard_item_id, confidence, source, created_at) VALUES(?,?,?,?,?,?)",
                        (raw_name, raw_spec, std_id, best_score, "auto_fuzzy", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                else:
                    # Create New Standard Item
                    try:
                        cur.execute(
                            "INSERT INTO standard_items(name, spec, unit, avg_price, min_price, max_price, latest_price, data_count, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (raw_name, raw_spec, qunit, qprice, qprice, qprice, qprice, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        std_id = cur.lastrowid
                        is_new_standard = True
                        
                        # Update cache
                        cached_standards.append((std_id, raw_name, raw_spec))
                        
                        # Create Mapping (Self)
                        cur.execute(
                            "INSERT INTO item_mappings(raw_name, raw_spec, standard_item_id, confidence, source, created_at) VALUES(?,?,?,?,?,?)",
                            (raw_name, raw_spec, std_id, 1.0, "auto_new", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                    except sqlite3.IntegrityError:
                        # Should match existing if unique constraint fails
                        cur.execute("SELECT id FROM standard_items WHERE name=? AND spec=?", (raw_name, raw_spec))
                        existing = cur.fetchone()
                        if existing:
                            std_id = existing[0]
                            # Create Mapping
                            cur.execute(
                                "INSERT INTO item_mappings(raw_name, raw_spec, standard_item_id, confidence, source, created_at) VALUES(?,?,?,?,?,?)",
                                (raw_name, raw_spec, std_id, 1.0, "auto_fallback", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            )

            # 4. Update Stats (If mapped to existing)
            if std_id and not is_new_standard:
                # Recalculate stats for this standard item
                cur.execute("SELECT avg_price, min_price, max_price, data_count FROM standard_items WHERE id=?", (std_id,))
                curr = cur.fetchone()
                if curr:
                    old_avg, old_min, old_max, old_count = curr
                    old_count = old_count or 0
                    old_avg = old_avg or 0.0
                    
                    new_count = old_count + 1
                    new_avg = (old_avg * old_count + qprice) / new_count
                    
                    # Handle None/0 mins
                    if old_min is None or old_min == 0:
                        new_min = qprice
                    else:
                        new_min = min(old_min, qprice) if qprice > 0 else old_min
                        
                    new_max = max(old_max or 0, qprice)
                    
                    cur.execute(
                        "UPDATE standard_items SET avg_price=?, min_price=?, max_price=?, latest_price=?, data_count=?, updated_at=? WHERE id=?",
                        (new_avg, new_min, new_max, qprice, new_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), std_id)
                    )
            
            # 5. Mark processed
            cur.execute("UPDATE historical_quotes SET status='processed' WHERE id=?", (qid,))
            
            processed += 1
            if progress_callback:
                progress_callback(processed, total)
                
        conn.commit()
        return f"分析完成，处理了 {processed} 条数据"
    finally:
        conn.close()

def get_recommendation(item_name: str, spec_model: str, threshold: float = 0.4):
    """
    Get price recommendation based on standard library (Phase 2) or raw history (Fallback).
    """
    if not item_name:
        return None
        
    conn = database._connect()
    try:
        cur = conn.cursor()
        
        raw_name = item_name.strip()
        raw_spec = (spec_model or "").strip()
        
        # 1. Try Mapping (Exact Match on Raw Input)
        cur.execute(
            """
            SELECT s.avg_price, s.latest_price, s.name, s.spec, s.updated_at
            FROM item_mappings m
            JOIN standard_items s ON m.standard_item_id = s.id
            WHERE m.raw_name = ? AND m.raw_spec = ?
            """,
            (raw_name, raw_spec)
        )
        row = cur.fetchone()
        
        if row:
            avg_p, latest_p, s_name, s_spec, date = row
            price = latest_p if latest_p is not None else avg_p
            return {
                "price": price or 0.0,
                "avg_price": avg_p or 0.0,
                "source": f"标准库: {s_name} {s_spec}",
                "match_type": "精确映射",
                "confidence": 1.0
            }
            
        # 2. Try Direct Match on Standard Items (Name + Spec)
        cur.execute(
            "SELECT avg_price, latest_price, updated_at FROM standard_items WHERE name=? AND spec=?",
            (raw_name, raw_spec)
        )
        row = cur.fetchone()
        if row:
            avg_p, latest_p, date = row
            price = latest_p if latest_p is not None else avg_p
            return {
                "price": price or 0.0,
                "avg_price": avg_p or 0.0,
                "source": f"标准库: {raw_name} {raw_spec}",
                "match_type": "标准精确",
                "confidence": 1.0
            }

        # 3. Fuzzy Match on Standard Items
        cur.execute("SELECT name, spec, avg_price, latest_price FROM standard_items")
        candidates = cur.fetchall()
        
        best_match = None
        best_score = 0.0
        
        target = f"{raw_name} {raw_spec}"
        
        for cname, cspec, cavg, clatest in candidates:
            cand = f"{cname} {cspec}"
            score = difflib.SequenceMatcher(None, target, cand).ratio()
            if score > best_score:
                best_score = score
                best_match = (clatest or cavg, cname, cspec)
        
        if best_match and best_score >= threshold:
            price, mname, mspec = best_match
            return {
                "price": price or 0.0,
                "avg_price": price or 0.0,
                "source": f"标准推荐: {mname} {mspec} ({int(best_score*100)}%)",
                "match_type": "模糊",
                "confidence": best_score
            }
            
        # 4. Fallback to Raw History (if analysis hasn't run yet)
        cur.execute(
            """
            SELECT audit_price, quote_date, supplier 
            FROM historical_quotes 
            WHERE item_name = ? AND spec_model = ? AND audit_price IS NOT NULL
            ORDER BY quote_date DESC, id DESC
            LIMIT 5
            """, 
            (raw_name, raw_spec)
        )
        rows = cur.fetchall()
        if rows:
            latest_price = rows[0][0] or 0.0
            avg_price = sum((r[0] or 0.0) for r in rows) / len(rows)
            return {
                "price": latest_price,
                "avg_price": avg_price,
                "source": f"历史记录 (精确匹配, 最近: {rows[0][1]})",
                "match_type": "精确",
                "confidence": 1.0
            }
            
        # Simple fuzzy on raw history as last resort
        cur.execute(
            """
            SELECT item_name, spec_model, audit_price, quote_date 
            FROM historical_quotes 
            WHERE item_name LIKE ? AND audit_price IS NOT NULL
            ORDER BY quote_date DESC
            LIMIT 50
            """,
            (f"%{raw_name}%",)
        )
        candidates_raw = cur.fetchall()
        best_match_raw = None
        best_ratio_raw = 0.0
        
        for cand in candidates_raw:
            c_name, c_spec, c_price, c_date = cand
            cand_str = f"{c_name} {c_spec}".strip()
            ratio = difflib.SequenceMatcher(None, target, cand_str).ratio()
            if ratio > best_ratio_raw:
                best_ratio_raw = ratio
                best_match_raw = (c_price or 0.0, c_date, c_name, c_spec)
                
        if best_match_raw and best_ratio_raw >= threshold:
             return {
                "price": best_match_raw[0],
                "avg_price": best_match_raw[0],
                "source": f"历史推荐: {best_match_raw[2]} {best_match_raw[3]} ({int(best_ratio_raw*100)}%)",
                "match_type": "模糊",
                "confidence": best_ratio_raw
            }
            
        return None
        
    finally:
        conn.close()

def get_stats():
    conn = database._connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM historical_quotes")
        total_raw = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(1) FROM historical_quotes WHERE status='pending'")
        pending = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(1) FROM standard_items")
        standards = cur.fetchone()[0]
        
        return {
            "total_records": total_raw, 
            "pending_records": pending,
            "standard_items": standards,
            "unique_items": standards # Approx
        }
    finally:
        conn.close()

def clear_history():
    conn = database._connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM historical_quotes")
        cur.execute("DELETE FROM standard_items")
        cur.execute("DELETE FROM item_mappings")
        conn.commit()
    finally:
        conn.close()

# --- Phase 3: Admin Features ---

def fetch_standard_items(filter_text=None, page=1, page_size=20):
    conn = database._connect()
    try:
        cur = conn.cursor()
        sql = "SELECT id, name, spec, unit, avg_price, latest_price, data_count, updated_at FROM standard_items WHERE 1=1"
        params = []
        if filter_text:
            sql += " AND (name LIKE ? OR spec LIKE ?)"
            params.extend([f"%{filter_text}%"] * 2)
        
        sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page-1)*page_size])
        
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def fetch_all_standard_items(filter_text=None):
    conn = database._connect()
    try:
        cur = conn.cursor()
        sql = "SELECT id, name, spec, unit, avg_price, latest_price, data_count, updated_at FROM standard_items WHERE 1=1"
        params = []
        if filter_text:
            sql += " AND (name LIKE ? OR spec LIKE ?)"
            params.extend([f"%{filter_text}%"] * 2)
        
        sql += " ORDER BY updated_at DESC"
        
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def update_standard_item(id, name, spec, unit, latest_price):
    conn = database._connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE standard_items SET name=?, spec=?, unit=?, latest_price=?, updated_at=? WHERE id=?",
            (name, spec, unit, latest_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def delete_standard_item(id):
    conn = database._connect()
    try:
        cur = conn.cursor()
        
        # Reset history status for all related mappings before deletion
        cur.execute("SELECT raw_name, raw_spec FROM item_mappings WHERE standard_item_id=?", (id,))
        mappings = cur.fetchall()
        for rname, rspec in mappings:
            cur.execute(
                "UPDATE historical_quotes SET status='pending' WHERE item_name=? AND spec_model=?", 
                (rname, rspec)
            )
            
        cur.execute("DELETE FROM item_mappings WHERE standard_item_id=?", (id,))
        cur.execute("DELETE FROM standard_items WHERE id=?", (id,))
        conn.commit()
        return True
    finally:
        conn.close()

def fetch_mappings_by_standard_id(standard_id):
    conn = database._connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, raw_name, raw_spec, confidence, source, created_at FROM item_mappings WHERE standard_item_id=?",
            (standard_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()

def delete_mapping(mapping_id):
    conn = database._connect()
    try:
        cur = conn.cursor()
        # Get raw_name, raw_spec before delete to reset history status
        cur.execute("SELECT raw_name, raw_spec FROM item_mappings WHERE id=?", (mapping_id,))
        row = cur.fetchone()
        if row:
            rname, rspec = row
            # Reset historical quotes to pending so they can be re-analyzed
            cur.execute(
                "UPDATE historical_quotes SET status='pending' WHERE item_name=? AND spec_model=?", 
                (rname, rspec)
            )
            
        cur.execute("DELETE FROM item_mappings WHERE id=?", (mapping_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def export_standard_items_to_excel(file_path, filter_text=None):
    data = fetch_all_standard_items(filter_text)
    if not data:
        return 0, "没有数据可导出"
        
    # data: id, name, spec, unit, avg_price, latest_price, data_count, updated_at
    df = pd.DataFrame(data, columns=["ID", "品名", "规格", "单位", "平均价", "最新参考价", "样本数", "更新时间"])
    
    try:
        df.to_excel(file_path, index=False)
        return len(data), ""
    except Exception as e:
        return 0, str(e)

def learn_from_plan_items(items):
    """
    Learn from manual inputs in the plan.
    items: list of dict {name, spec, unit, price}
    """
    if not items:
        return 0, "没有数据"
        
    conn = database._connect()
    try:
        cur = conn.cursor()
        count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_id = f"LEARN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Cache existing standards to minimize queries
        cur.execute("SELECT id, name, spec FROM standard_items")
        # create a dict for faster lookup: (name, spec) -> id
        std_map = {(r[1], r[2]): r[0] for r in cur.fetchall()}
        
        for item in items:
            name = item.get('name', '').strip()
            spec = item.get('spec', '').strip()
            unit = item.get('unit', '').strip()
            price = item.get('price', 0.0)
            
            if not name or price <= 0:
                continue
                
            # 1. Insert into historical_quotes as a record
            cur.execute(
                """
                INSERT INTO historical_quotes(
                    batch_id, item_name, spec_model, unit, quantity, 
                    audit_price, supplier, quote_date, source_file, created_at, status
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    batch_id, name, spec, unit, 1, 
                    price, "人工录入", timestamp, "反向学习", timestamp, "processed"
                )
            )
            
            # 2. Update or Create Standard Item
            key = (name, spec)
            std_id = std_map.get(key)
            
            if std_id:
                # Update existing
                cur.execute("SELECT avg_price, min_price, max_price, data_count FROM standard_items WHERE id=?", (std_id,))
                curr = cur.fetchone()
                if curr:
                    old_avg, old_min, old_max, old_count = curr
                    old_count = old_count or 0
                    old_avg = old_avg or 0.0
                    
                    new_count = old_count + 1
                    new_avg = (old_avg * old_count + price) / new_count
                    new_min = min(old_min, price) if old_min and old_min > 0 else price
                    new_max = max(old_max or 0, price)
                    
                    cur.execute(
                        "UPDATE standard_items SET avg_price=?, min_price=?, max_price=?, latest_price=?, data_count=?, updated_at=? WHERE id=?",
                        (new_avg, new_min, new_max, price, new_count, timestamp, std_id)
                    )
            else:
                # Create new
                cur.execute(
                    "INSERT INTO standard_items(name, spec, unit, avg_price, min_price, max_price, latest_price, data_count, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (name, spec, unit, price, price, price, price, 1, timestamp)
                )
                std_id = cur.lastrowid
                std_map[key] = std_id
                
                # Auto mapping
                cur.execute(
                    "INSERT INTO item_mappings(raw_name, raw_spec, standard_item_id, confidence, source, created_at) VALUES(?,?,?,?,?,?)",
                    (name, spec, std_id, 1.0, "manual_learn", timestamp)
                )
            
            count += 1
            
        conn.commit()
        return count, ""
    except Exception as e:
        return 0, str(e)
    finally:
        conn.close()
