from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QGridLayout,
    QLabel,
    QHeaderView,
    QMessageBox,
    QComboBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
import pandas as pd


HEADERS = [
    "序号",
    "采购标的",
    "规格型号",
    "采购数量",
    "单位",
    "单价(元)",
    "总价（元）",
    "采购方式",
    "采购途径",
    "计划发放",
    "进度要求",
    "询价(报价)",
    "税率",
    "采购周期",
    "备注",
]
ALLOWED_METHODS = ["", "询比采购", "公开招标", "集中采购", "框架协议"]
ALLOWED_CHANNELS = ["", "能建商城", "采购平台", "线下采购"]


class DetailWidget(QWidget):
    def __init__(self, yymm: str, category_code: str, main_number: str, next_detail_no_fn, header_info: dict | None = None):
        super().__init__()
        self._loading = False
        self.yymm = yymm
        self.category_code = category_code
        self.main_number = main_number
        self.next_detail_no_fn = next_detail_no_fn
        splitter = QSplitter(Qt.Vertical)
        root = QVBoxLayout(self)
        root.addWidget(splitter)
        # 顶部区域：信息条 + 右侧操作按钮
        top_container = QFrame()
        top_container.setFrameShape(QFrame.NoFrame)
        top_h = QHBoxLayout(top_container)
        top_h.setContentsMargins(8, 6, 8, 6)
        top_h.setSpacing(8)
        top = QFrame()
        top.setObjectName("detailHeader")
        top.setFrameShape(QFrame.StyledPanel)
        top_layout = QGridLayout(top)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setHorizontalSpacing(6)
        top_layout.setVerticalSpacing(6)
        self.h_number = QLabel(); self.h_number.setObjectName("headerValue")
        self.h_task = QLabel(); self.h_task.setObjectName("headerValue")
        self.h_unit = QLabel(); self.h_unit.setObjectName("headerValue")
        self.h_category = QLabel(); self.h_category.setObjectName("headerValue")
        self.h_date = QLabel(); self.h_date.setObjectName("headerValue")
        self.h_yymm = QLabel(); self.h_yymm.setObjectName("headerValue")

        LABEL_WIDTH = 90

        def pair(title: str, value_lbl: QLabel):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)
            lab = QLabel(f"{title}：")
            lab.setObjectName("headerLabel")
            lab.setFixedWidth(LABEL_WIDTH)
            h.addWidget(lab)
            h.addWidget(value_lbl, 1)
            return w

        top_layout.addWidget(pair("主单编号", self.h_number), 0, 0)
        top_layout.addWidget(pair("采购任务名称", self.h_task), 0, 1)
        top_layout.addWidget(pair("计划月份", self.h_yymm), 0, 2)
        top_layout.addWidget(pair("需求单位", self.h_unit), 1, 0)
        top_layout.addWidget(pair("标的类别", self.h_category), 1, 1)
        top_layout.addWidget(pair("日期", self.h_date), 1, 2)
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 1)
        top_layout.setColumnStretch(2, 1)
        # 右侧大按钮区
        actions_wrap = QFrame()
        actions_h = QHBoxLayout(actions_wrap)
        actions_h.setContentsMargins(0, 0, 0, 0)
        actions_h.setSpacing(8)
        self.save_btn = QPushButton("保存")
        self.import_btn = QPushButton("数据\n导入")
        self.release_btn = QPushButton("发放")
        self.back_btn = QPushButton("返回")
        for b in [self.save_btn, self.import_btn, self.release_btn, self.back_btn]:
            b.setFixedSize(64, 64)
        self.save_btn.setObjectName("actSave")
        self.import_btn.setObjectName("actImport")
        self.release_btn.setObjectName("actRelease")
        self.back_btn.setObjectName("actBack")
        actions_h.addWidget(self.import_btn)
        actions_h.addWidget(self.save_btn)
        actions_h.addWidget(self.release_btn)
        actions_h.addWidget(self.back_btn)
        actions_h.addStretch(1)
        top_h.addWidget(top, 1)
        top_h.addWidget(actions_wrap, 0)
        splitter.addWidget(top_container)
        self.table = QTableWidget(0, len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Configure Table for Auto-Wrap and Auto-Row-Height
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        header.sectionResized.connect(self.on_header_resized)
        from PySide6.QtCore import QTimer
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(300)
        self._pending_resize = None
        self.apply_saved_widths()
        
        # Top Actions (Add/Del Row) moved here
        self.add_btn = QPushButton("添加行")
        self.del_btn = QPushButton("删除行")
        self.add_btn.setObjectName("btnAdd")
        self.del_btn.setObjectName("btnDel")
        
        btns = QHBoxLayout()
        btns.addWidget(self.add_btn)
        btns.addWidget(self.del_btn)
        btns.addStretch(1)
        
        # Add buttons layout before table
        # splitter.addWidget(self.table) # Remove duplicate add
        
        # Wrap table and buttons in a widget for the splitter
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addLayout(btns)
        table_layout.addWidget(self.table)
        
        splitter.addWidget(table_container)
        
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.del_row)
        self.save_btn.clicked.connect(self.save_rows)
        self.import_btn.clicked.connect(self.import_excel)
        self.release_btn.clicked.connect(self.do_plan_release)
        self.table.itemChanged.connect(self.on_item_changed)
        if header_info:
            self.set_header_info(header_info)
        self.load_rows()
        self.setStyleSheet(
            """
            QFrame#detailHeader { background: #F4F6F8; border: 1px solid #DFE3E8; border-radius: 8px; }
            QLabel#headerLabel { color: #6B7280; }
            QLabel#headerValue { color: #111827; font-weight: 600; }
            QPushButton { padding: 8px 16px; border-radius: 6px; font-weight: 600; }
            QPushButton#actSave { background: #0EA5E9; color: #fff; border-radius: 12px; }
            QPushButton#actImport { background: #F59E0B; color: #fff; border-radius: 12px; }
            QPushButton#actRelease { background: #6366F1; color: #fff; border-radius: 12px; }
            QPushButton#actBack { background: #EF4444; color: #fff; border-radius: 12px; }
            QPushButton#btnAdd { background: #10B981; color: #fff; }
            QPushButton#btnDel { background: #EF4444; color: #fff; }
            QTableWidget { background: #FFFFFF; }
            QHeaderView::section { background: #ECECEC; padding: 6px; }
            """
        )

    def _ensure_total_item(self, r: int):
        it = self.table.item(r, 6)
        if it is None:
            it = QTableWidgetItem("")
            it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(r, 6, it)
        return it

    def _update_total_cell(self, r: int):
        from calc import calc_total
        up = self._display_value(r, 5).strip()
        qty = self._display_value(r, 3).strip()
        val, ok = calc_total(up, qty)
        it = self._ensure_total_item(r)
        it.setText(val)
        if ok:
            it.setBackground(Qt.yellow)
            it.setToolTip("已自动计算")
        else:
            it.setBackground(Qt.white)
            it.setToolTip("请输入有效数字")

    def apply_saved_widths(self):
        import database
        widths = database.get_detail_column_widths()
        for col, w in widths.items():
            if 0 <= col < self.table.columnCount() and int(w) > 20:
                self.table.setColumnWidth(col, int(w))

    def on_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        self._pending_resize = (int(logicalIndex), int(newSize))
        self._resize_timer.timeout.connect(self._flush_resize)
        self._resize_timer.start()

    def _flush_resize(self):
        if not self._pending_resize:
            return
        col, w = self._pending_resize
        self._pending_resize = None
        import database
        database.set_detail_column_width(col, w)
        database.set_layout_version("detail", "v1")

    def set_header_info(self, info: dict):
        self.h_number.setText(str(info.get("number", "")))
        self.h_task.setText(str(info.get("task_name", "")))
        self.h_unit.setText(str(info.get("unit", "")))
        self.h_category.setText(str(info.get("category", "")))
        self.h_date.setText(str(info.get("date", "")))
        self.h_yymm.setText(str(info.get("yymm", "")))

    def add_row(self):
        # Insert at the top (row 0)
        r = 0 
        self.table.insertRow(r)
        
        # IMPORTANT: When adding a new row, we must pass the current yymm and category_code
        # to generate the correct sequence number prefix (e.g., 2601MPJ-1).
        # However, `next_detail_no_fn` relies on `database.next_detail_number` which queries DB.
        # If we add multiple rows in UI without saving, they won't be in DB yet.
        # So `next_detail_number` will return the SAME number for all new rows until saved.
        # This is a known issue with "stateless" auto-increment in UI.
        # To fix this, we need to count how many "unsaved" rows are already in the table that match the prefix.
        
        # But for now, let's just generate it. The user might need to save to get unique IDs if we rely strictly on DB.
        # OR we can try to be smart:
        # Get base seq from DB
        # Add count of existing rows in table that have the same prefix and look like new rows?
        # A simpler approach for the User Experience:
        # Just call the function. If it returns duplicate, we might need to handle it.
        # Wait, `next_detail_no_fn` is `database.next_detail_number`.
        
        # Let's try to parse the max sequence currently VISIBLE in the table as well, 
        # because the user might have added rows but not saved them.
        
        db_seq_str = self.next_detail_no_fn(self.yymm, self.category_code)
        # db_seq_str format: "2601MPJ-5"
        
        # Check current table for max sequence
        max_table_seq = 0
        prefix = f"{self.yymm}{self.category_code}-"
        
        for i in range(self.table.rowCount()):
            # skip the row we just inserted (it's empty or 0)
            if i == r: continue
            
            item = self.table.item(i, 0)
            if item:
                txt = item.text()
                if txt.startswith(prefix):
                    try:
                        n = int(txt.split("-")[-1])
                        if n > max_table_seq:
                            max_table_seq = n
                    except:
                        pass
        
        # Parse DB seq
        try:
            db_n = int(db_seq_str.split("-")[-1])
        except:
            db_n = 0
            
        final_n = max(db_n, max_table_seq + 1)
        final_seq = f"{prefix}{final_n}"
        
        self.table.setItem(r, 0, QTableWidgetItem(final_seq))
        
        # Purchase Method (Column 7)
        method_combo = QComboBox()
        method_combo.addItems(ALLOWED_METHODS)
        method_combo.setEditable(True)
        # Connect signal using lambda to capture row/combo
        # Note: Row index can change, so we might need a safer way or update logic
        # But for insertRow(0), the new row is always 0 at creation time.
        # However, signals need to reference the widget itself to find its current row.
        method_combo.currentTextChanged.connect(lambda text, cb=method_combo: self.on_method_changed(cb, text))
        self.table.setCellWidget(r, 7, method_combo)
        
        # Progress Req (Column 10) - Default to yymm + "15"
        progress_val = f"{self.yymm}15"
        self.table.setItem(r, 10, QTableWidgetItem(progress_val))
        self._ensure_total_item(r)

        import database
        purchasers = database.fetch_purchasers()
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(["未分配"] + purchasers)
        self.table.setCellWidget(r, 9, combo)

    def on_method_changed(self, combo, text):
        # Find the row for this combo
        # indexAt logic is risky if widget is not visible, but cellWidget works
        row = -1
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 7) == combo:
                row = r
                break
        if row == -1:
            return
            
        # Logic:
        # 询比采购 -> 线下采购
        # 公开招标 -> 采购平台
        # 集中采购 -> 采购平台
        # 框架协议 -> 能建商城
        target = ""
        if text == "询比采购":
            target = "线下采购"
        elif text in ["公开招标", "集中采购"]:
            target = "采购平台"
        elif text == "框架协议":
            target = "能建商城"
            
        if target:
            self.table.setItem(row, 8, QTableWidgetItem(target))

    def del_row(self):
        # Delete selected rows
        ranges = self.table.selectedRanges()
        if not ranges:
            QMessageBox.information(self, "提示", "请先选择要删除的行")
            return
        
        # Sort ranges descending by row index to avoid shifting issues
        rows_to_del = set()
        for rng in ranges:
            for r in range(rng.topRow(), rng.bottomRow() + 1):
                rows_to_del.add(r)
        
        for r in sorted(rows_to_del, reverse=True):
            self.table.removeRow(r)

    def _display_value(self, r: int, c: int):
        w = self.table.cellWidget(r, c)
        if isinstance(w, QComboBox):
            txt = w.currentText()
            if c == 9 and txt == "未分配":
                return ""
            return txt
        it = self.table.item(r, c)
        return it.text() if it else ""

    def _save_data(self):
        import database

        if not self.main_number:
            return False
        
        # 1. Cleanup empty rows from UI first
        for r in range(self.table.rowCount() - 1, -1, -1):
            pi = self._display_value(r, 1).strip()
            sm = self._display_value(r, 2).strip()
            if not pi and not sm:
                self.table.removeRow(r)
        
        # 2. Collect all valid rows data
        # IMPORTANT: Iterate in REVERSE (bottom-up) to preserve chronological order in DB IDs.
        # The UI shows Newest First (Top). So the Bottom row is the Oldest.
        # We want Oldest to be inserted first (ID 1), Newest last (ID N).
        rows_to_save = []
        for r in range(self.table.rowCount() - 1, -1, -1):
            seq_item = self.table.item(r, 0)
            seq = seq_item.text() if seq_item else ""
            purchase_item = self._display_value(r, 1)
            spec_model = self._display_value(r, 2)
            purchase_qty = self._display_value(r, 3)
            unit = self._display_value(r, 4)
            unit_price = self._display_value(r, 5)
            budget_wan = self._display_value(r, 6)
            purchase_method = self._display_value(r, 7)
            purchase_channel = self._display_value(r, 8)
            plan_release = self._display_value(r, 9)
            progress_req = self._display_value(r, 10)
            inquiry_price = self._display_value(r, 11)
            tax_rate = self._display_value(r, 12)
            purchase_cycle = self._display_value(r, 13)
            remark = self._display_value(r, 14)
            
            data = [
                "",  # item_name
                purchase_item,
                spec_model,
                purchase_cycle,
                "",  # stock_count
                purchase_qty,
                unit,
                unit_price,
                budget_wan,
                purchase_method,
                purchase_channel,
                "",  # plan_time
                "",  # demand_unit
                plan_release,
                progress_req,
                "",  # supplier
                inquiry_price,
                tax_rate,
                "",  # actual_status
                "",  # purchase_body
                "",  # add_adjust
                remark,
            ]
            rows_to_save.append((seq, data))

        # 3. Save to DB in one transaction (Delete old + Insert new)
        database.save_order_details_transaction(self.main_number, rows_to_save)
        
        import database as _db
        _db.recalc_detail_counter(self.yymm, self.category_code)
        return True

    def save_rows(self):
        if self._save_data():
            QMessageBox.information(self, "保存", "明细已保存")

    def do_plan_release(self):
        # Block if any '未分配' or empty
        for r in range(self.table.rowCount()):
            txt = self._display_value(r, 9).strip()
            if not txt or txt == "未分配":
                QMessageBox.warning(self, "提示", "尚有未分配记录，不能发放")
                return
        if self._save_data():
            # Mark release status '已发放' for all purchasers in current rows
            purchasers = set()
            for r in range(self.table.rowCount()):
                p = self._display_value(r, 9).strip()
                if p:
                    purchasers.add(p)
            if purchasers:
                import database
                for p in purchasers:
                    database.update_release_status(self.main_number, p, "已发放")
            QMessageBox.information(self, "发放", "已更新到计划发放模块并标记为已发放")

    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            self._import_from_dataframe(df)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def _import_from_dataframe(self, df: pd.DataFrame):
        self._loading = True
        required_cols = [
            "采购标的",
            "规格型号",
            "采购数量",
            "单位",
            "单价(元)",
            "采购方式",
            "采购途径",
            "计划发放",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            try:
                from export import write_detail_import_template
                path = "docs/detail_import_template.xlsx"
                write_detail_import_template(path, purchasers_hint=True)
                QMessageBox.warning(self, "提示", f"Excel需包含列: {', '.join(missing)}\n已生成模板: {path}")
            except Exception:
                QMessageBox.warning(self, "提示", f"Excel需包含列: {', '.join(missing)}")
            return

        import database
        purchasers = database.fetch_purchasers()
        prefix = f"{self.yymm}{self.category_code}-"

        max_table_seq = 0
        for i in range(self.table.rowCount()):
            it = self.table.item(i, 0)
            if it:
                txt = it.text()
                if txt.startswith(prefix):
                    try:
                        n = int(txt.split("-")[-1])
                        if n > max_table_seq:
                            max_table_seq = n
                    except:
                        pass

        db_seq_str = self.next_detail_no_fn(self.yymm, self.category_code)
        try:
            db_n = int(db_seq_str.split("-")[-1])
            start_seq = max(db_n, max_table_seq + 1)
        except:
            start_seq = 1

        from calc import calc_total, _parse_non_negative
        MAX_REMARK_LEN = 500
        errors = []
        success = 0
        truncated_remarks = 0

        for i in range(len(df) - 1, -1, -1):
            row = df.iloc[i]

            item_name = str(row.get("采购标的", "")).strip()
            spec_model = str(row.get("规格型号", "")).strip()
            qty_text = str(row.get("采购数量", "")).strip()
            unit_text = str(row.get("单位", "")).strip()
            price_text = str(row.get("单价(元)", "")).strip()
            method_text = str(row.get("采购方式", "")).strip()
            channel_text = str(row.get("采购途径", "")).strip()
            plan_release = str(row.get("计划发放", "")).strip()
            remark_text_raw = row.get("备注", "")
            try:
                remark_text = str(remark_text_raw)
                remark_text = remark_text.strip()
            except Exception:
                remark_text = ""

            if item_name == "nan": item_name = ""
            if spec_model == "nan": spec_model = ""
            if qty_text == "nan": qty_text = ""
            if unit_text == "nan": unit_text = ""
            if price_text == "nan": price_text = ""
            if method_text == "nan": method_text = ""
            if channel_text == "nan": channel_text = ""
            if plan_release == "nan" or plan_release == "未分配": plan_release = ""
            if remark_text == "nan": remark_text = ""

            if len(remark_text) > MAX_REMARK_LEN:
                remark_text = remark_text[:MAX_REMARK_LEN]
                truncated_remarks += 1

            qty_val = _parse_non_negative(qty_text)
            price_val = _parse_non_negative(price_text)
            if qty_val is None:
                errors.append(f"第{i+1}行 采购数量非法: {qty_text}")
                continue
            if price_val is None:
                errors.append(f"第{i+1}行 单价非法: {price_text}")
                continue
            if method_text not in ALLOWED_METHODS:
                errors.append(f"第{i+1}行 采购方式不在允许列表: {method_text}")
                continue
            if channel_text not in ALLOWED_CHANNELS:
                errors.append(f"第{i+1}行 采购途径不在标准选项: {channel_text}")
                continue
            if plan_release and plan_release not in purchasers:
                errors.append(f"第{i+1}行 计划发放人员不存在: {plan_release}")
                continue

            r = 0
            self.table.insertRow(r)
            current_seq_num = start_seq + i
            seq = f"{prefix}{current_seq_num}"
            self.table.setItem(r, 0, QTableWidgetItem(seq))
            self.table.setItem(r, 1, QTableWidgetItem(item_name))
            self.table.setItem(r, 2, QTableWidgetItem(spec_model))
            self.table.setItem(r, 3, QTableWidgetItem(str(qty_text)))
            self.table.setItem(r, 4, QTableWidgetItem(unit_text))
            self.table.setItem(r, 5, QTableWidgetItem(str(price_text)))

            method_combo = QComboBox()
            method_combo.addItems(ALLOWED_METHODS)
            method_combo.setEditable(True)
            method_combo.setCurrentText(method_text)
            method_combo.currentTextChanged.connect(lambda text, cb=method_combo: self.on_method_changed(cb, text))
            self.table.setCellWidget(r, 7, method_combo)

            self.table.setItem(r, 8, QTableWidgetItem(channel_text))

            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(["未分配"] + purchasers)
            combo.setCurrentText(plan_release if plan_release else "未分配")
            self.table.setCellWidget(r, 9, combo)

            progress_val = f"{self.yymm}15"
            self.table.setItem(r, 10, QTableWidgetItem(progress_val))

            self.table.setItem(r, 14, QTableWidgetItem(remark_text))

            # Apply auto recommendation if Excel left empty
            try:
                import database
                rec = database.find_recommendation(item_name)
            except Exception:
                rec = None
            if rec:
                pr_rel, pr_method, pr_channel = rec
                if not plan_release and pr_rel:
                    if pr_rel not in purchasers:
                        combo.addItem(pr_rel)
                    combo.setCurrentText(pr_rel)
                if not method_text and pr_method:
                    method_combo.setCurrentText(pr_method)
                if not channel_text and pr_channel:
                    self.table.setItem(r, 8, QTableWidgetItem(pr_channel))

            self._ensure_total_item(r)
            self._update_total_cell(r)
            success += 1

        self._loading = False
        if errors:
            msg = "\n".join(errors[:10])
            extra = f"\n备注有 {truncated_remarks} 条被截断至500字符" if truncated_remarks > 0 else ""
            QMessageBox.warning(self, "部分成功", f"成功 {success} 条，失败 {len(errors)} 条。{extra}\n前10条错误:\n{msg}")
        else:
            extra = f"，其中备注有 {truncated_remarks} 条被截断至500字符" if truncated_remarks > 0 else ""
            QMessageBox.information(self, "成功", f"成功导入 {success} 条数据{extra}")

    def on_item_changed(self, item):
        if getattr(self, "_loading", False):
            return
        
        # Column 1 is "Item Name" (采购标的)
        if item.column() == 1:
            text = item.text().strip()
            if not text:
                return
                
            import database
            rec = database.find_recommendation(text)
            if rec:
                # rec: (plan_release, purchase_method, purchase_channel)
                
                # Update Plan Release (Column 9)
                r = item.row()
                combo = self.table.cellWidget(r, 9)
                if isinstance(combo, QComboBox):
                    # Only update if empty? User requirement implies "automatically fill". 
                    # Assuming overwrite or fill if found.
                    if rec[0]:
                        combo.setCurrentText(rec[0])
                
                # Update Purchase Method (Column 7)
                combo_method = self.table.cellWidget(r, 7)
                if isinstance(combo_method, QComboBox):
                    if rec[1]:
                        combo_method.setCurrentText(rec[1])
                        
                # Update Purchase Channel (Column 8)
                if rec[2]:
                    self.table.setItem(r, 8, QTableWidgetItem(rec[2]))
        if item.column() in (3, 5):
            self._update_total_cell(item.row())

    def load_rows(self):
        self._loading = True
        import database
        self.table.setRowCount(0)
        rows = database.fetch_order_details(self.main_number)
        purchasers = database.fetch_purchasers()
        
        # Sort rows in reverse order by id (detail_no is not guaranteed sequential if deleted)
        # Or simply insert at 0 in the loop to reverse order
        # fetch_order_details returns ordered by id ASC
        
        for row in rows:
            # Insert at 0 to reverse order (newest at top if rows are chronological)
            # Actually, fetch_order_details returns [id ASC]. 
            # If we want "newest added" at top, and "newest added" means higher ID...
            # Then iterating ASC and inserting at 0 will put highest ID at top (reverse order).
            r = 0
            self.table.insertRow(r)
            # row: (detail_no, item_name, purchase_item, spec_model, purchase_cycle, stock_count,
            #       purchase_qty, unit, unit_price, budget_wan, purchase_method, purchase_channel,
            #       plan_time, demand_unit, plan_release, progress_req, supplier, inquiry_price,
            #       tax_rate, actual_status, purchase_body, add_adjust, remark)
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            mapping = [
                (1, row[2]),  # 采购标的
                (2, row[3]),  # 规格型号
                (3, row[6]),  # 采购数量
                (4, row[7]),  # 单位
                (5, row[8]),  # 单价(元)
                (6, row[9]),  # 采购预算(万元)
                # (7, row[10]), # 采购方式 (Handled by combo)
                (8, row[11]), # 采购途径
                # (9, row[14]), # 计划发放 (handled separately)
                (10, row[15]),# 进度要求
                (11, row[17]),# 询价(报价)
                (12, row[18]),# 税率
                (13, row[4]), # 采购周期
                (14, row[22]),# 备注
            ]
            for c, val in mapping:
                self.table.setItem(r, c, QTableWidgetItem(str(val if val is not None else "")))
            
            # Purchase Method (Column 7)
            method_val = str(row[10]) if row[10] else ""
            method_combo = QComboBox()
            method_combo.addItems(ALLOWED_METHODS)
            method_combo.setEditable(True)
            method_combo.setCurrentText(method_val)
            method_combo.currentTextChanged.connect(lambda text, cb=method_combo: self.on_method_changed(cb, text))
            self.table.setCellWidget(r, 7, method_combo)

            # Plan Release (Column 9)
            plan_release_val = str(row[14]) if row[14] else ""
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(["未分配"] + purchasers)
            combo.setCurrentText(plan_release_val if plan_release_val else "未分配")
            self.table.setCellWidget(r, 9, combo)
            self._update_total_cell(r)
        self._loading = False
