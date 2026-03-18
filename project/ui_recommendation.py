from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QMessageBox, QFileDialog, QAbstractItemView, QFrame, QComboBox, QProgressDialog,
    QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
import database
import pandas as pd
import os

class DataLoader(QThread):
    data_loaded = Signal(list, int, list)

    def __init__(self, filter_text, limit, offset):
        super().__init__()
        self.filter_text = filter_text
        self.limit = limit
        self.offset = offset

    def run(self):
        try:
            rows, total = database.fetch_recommendations(self.filter_text, self.limit, self.offset)
            purchasers = database.fetch_purchasers()
            self.data_loaded.emit(rows, total, purchasers)
        except Exception as e:
            print(f"Data loading failed: {e}")
            self.data_loaded.emit([], 0, [])

class RecommendationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.page_size = 50
        self.current_page = 1
        self.total_count = 0
        self.loading = False
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("自动推荐信息维护")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Search Area
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("采购标的:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入采购标的关键字搜索...")
        self.search_input.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        self.btn_search = QPushButton("搜索")
        self.btn_search.clicked.connect(self.on_search)
        search_layout.addWidget(self.btn_search)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.btn_add = QPushButton("添加行")
        self.btn_add.setObjectName("btnAdd")
        self.btn_add.clicked.connect(self.add_row)
        
        self.btn_del = QPushButton("删除行")
        self.btn_del.setObjectName("btnDel")
        self.btn_del.clicked.connect(self.del_row)
        
        self.btn_import = QPushButton("导入Excel")
        self.btn_import.setObjectName("btnImport")
        self.btn_import.clicked.connect(self.import_excel)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setObjectName("btnRefresh")
        self.btn_refresh.setToolTip("刷新列表数据")
        self.btn_refresh.clicked.connect(self.load_data)

        self.btn_sync = QPushButton("同步推荐信息")
        self.btn_sync.setObjectName("btnSync")
        self.btn_sync.setToolTip("从已发放记录增量同步到推荐库")
        self.btn_sync.clicked.connect(self.sync_recommendations)
        
        self.btn_save = QPushButton("保存")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_data)
        
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_del)
        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_refresh)
        if database.user_has_permission("sync_recommendations"):
            toolbar.addWidget(self.btn_sync)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_save)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["序号", "采购标的", "计划发放", "采购方式", "采购途径", "权重", "是否生效"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Sequence column width
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Pagination
        page_layout = QHBoxLayout()
        self.lbl_page_info = QLabel("共 0 条，第 1/1 页")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        
        page_layout.addStretch()
        page_layout.addWidget(self.lbl_page_info)
        page_layout.addWidget(self.btn_prev)
        page_layout.addWidget(self.btn_next)
        layout.addLayout(page_layout)
        
        self.setStyleSheet("""
            QPushButton { padding: 6px 12px; border-radius: 4px; }
            QPushButton#primary { background-color: #2F80ED; color: white; font-weight: bold; }
            QPushButton#btnAdd { background-color: #10B981; color: white; }
            QPushButton#btnDel { background-color: #EF4444; color: white; }
            QPushButton#btnImport { background-color: #F59E0B; color: white; }
            QPushButton#btnRefresh { background-color: #8B5CF6; color: white; }
            QPushButton#btnSync { background-color: #6366F1; color: white; }
            QTableWidget { background-color: white; border: 1px solid #E5E7EB; }
            QHeaderView::section { background-color: #F3F4F6; padding: 6px; border: none; font-weight: bold; }
        """)

    def on_search(self):
        self.current_page = 1
        self.load_data()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        max_page = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.load_data()

    def load_data(self):
        if self.loading:
            return
        self.loading = True
        self.table.setEnabled(False)
        self.btn_search.setEnabled(False)
        self.lbl_page_info.setText("加载中...")
        
        filter_text = self.search_input.text().strip() if hasattr(self, 'search_input') else None
        offset = (self.current_page - 1) * self.page_size
        
        self.loader = DataLoader(filter_text, self.page_size, offset)
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.loader.finished.connect(lambda: self.cleanup_loader())
        self.loader.start()

    def cleanup_loader(self):
        self.loading = False
        self.table.setEnabled(True)
        self.btn_search.setEnabled(True)
        self.loader.deleteLater()
        self.loader = None

    def on_data_loaded(self, rows, total_count, purchasers):
        self.total_count = total_count
        max_page = (total_count + self.page_size - 1) // self.page_size
        if max_page < 1: max_page = 1
        self.lbl_page_info.setText(f"共 {total_count} 条，第 {self.current_page}/{max_page} 页")
        
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < max_page)

        self.table.setRowCount(0)
        start_seq = (self.current_page - 1) * self.page_size + 1
        
        for i, row in enumerate(rows):
            # row: id, item_name, plan_release, weight, is_active
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # 序号
            item_seq = QTableWidgetItem(str(start_seq + i))
            item_seq.setData(Qt.UserRole, row[0]) # Store ID
            self.table.setItem(r, 0, item_seq)
            self.table.item(r, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) # Read-only
            
            self.table.setItem(r, 1, QTableWidgetItem(str(row[1] if row[1] else "")))
            
            # 计划发放 - Dropdown
            plan_release_val = str(row[2] if row[2] else "")
            combo_release = QComboBox()
            combo_release.addItems(purchasers)
            combo_release.setCurrentText(plan_release_val)
            if plan_release_val and plan_release_val not in purchasers:
                combo_release.addItem(plan_release_val)
                combo_release.setCurrentText(plan_release_val)
            self.table.setCellWidget(r, 2, combo_release)

            # 采购方式 - Dropdown
            p_method_val = str(row[5] if len(row) > 5 and row[5] else "")
            combo_method = QComboBox()
            combo_method.addItems(["", "询比采购", "公开招标", "集中采购", "框架协议"])
            combo_method.setEditable(True)
            combo_method.setCurrentText(p_method_val)
            # Use a lambda that captures 'r' by value is tricky in a loop because 'r' changes?
            # Actually, enumerate produces a new 'r' each iteration, but closures bind to variable.
            # Safe way: use default arg.
            combo_method.currentTextChanged.connect(lambda text, r=r: self.on_method_changed(r, text))
            self.table.setCellWidget(r, 3, combo_method)

            # 采购途径 - Text
            p_channel_val = str(row[6] if len(row) > 6 and row[6] else "")
            self.table.setItem(r, 4, QTableWidgetItem(p_channel_val))

            self.table.setItem(r, 5, QTableWidgetItem(str(row[3] if row[3] else "")))
            
            # is_active
            is_active_val = int(row[4]) if len(row) > 4 and row[4] is not None else 1
            combo = QComboBox()
            combo.addItems(["是", "否"])
            combo.setCurrentText("是" if is_active_val == 1 else "否")
            self.table.setCellWidget(r, 6, combo)

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        # 序号
        start_seq = (self.current_page - 1) * self.page_size + 1
        item_seq = QTableWidgetItem(str(start_seq + r))
        item_seq.setData(Qt.UserRole, None) # No ID for new row
        self.table.setItem(r, 0, item_seq)
        self.table.item(r, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        
        # 计划发放 - Dropdown
        purchasers = database.fetch_purchasers()
        combo_release = QComboBox()
        combo_release.addItems(purchasers)
        self.table.setCellWidget(r, 2, combo_release)

        # 采购方式 - Dropdown
        combo_method = QComboBox()
        combo_method.addItems(["", "询比采购", "公开招标", "集中采购", "框架协议"])
        combo_method.setEditable(True)
        combo_method.currentTextChanged.connect(lambda text, cb=combo_method, row=r: self.on_method_changed(row, text))
        self.table.setCellWidget(r, 3, combo_method)

        # 采购途径 - Text (Default empty)
        self.table.setItem(r, 4, QTableWidgetItem(""))

        # is_active default "是"
        combo = QComboBox()
        combo.addItems(["是", "否"])
        combo.setCurrentText("是")
        self.table.setCellWidget(r, 6, combo)

    def del_row(self):
        ranges = self.table.selectedRanges()
        if not ranges:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return
            
        if QMessageBox.question(self, "确认", "确定要删除选中行吗？此操作将直接删除数据库记录。") != QMessageBox.Yes:
            return
        
        rows_to_del = set()
        for rng in ranges:
            for r in range(rng.topRow(), rng.bottomRow() + 1):
                rows_to_del.add(r)
                
        for r in sorted(rows_to_del, reverse=True):
            # Check ID
            item = self.table.item(r, 0)
            rid = item.data(Qt.UserRole) if item else None
            
            try:
                if rid:
                    database.delete_recommendation(rid)
                self.table.removeRow(r)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
                return
            
        # Re-number sequences
        start_seq = (self.current_page - 1) * self.page_size + 1
        for r in range(self.table.rowCount()):
            # Preserve ID? No, the items shifted, but we need to ensure the ID is still attached to the row.
            # QTableWidget shifts items automatically when removing rows.
            # But we are creating NEW QTableWidgetItem for column 0 in this loop:
            # self.table.setItem(r, 0, QTableWidgetItem(str(r + 1))) -> THIS IS BUGGY!
            # It overwrites the item and loses the UserRole ID!
            
            # FIX: Get existing item, update text, keep data.
            old_item = self.table.item(r, 0)
            if old_item:
                old_item.setText(str(start_seq + r))
            else:
                # Should not happen usually, but if so:
                new_item = QTableWidgetItem(str(start_seq + r))
                self.table.setItem(r, 0, new_item)

    def on_method_changed(self, row, text):
        target = ""
        if text == "询比采购":
            target = "线下采购"
        elif text in ["公开招标", "集中采购"]:
            target = "采购平台"
        elif text == "框架协议":
            target = "能建商城"
            
        if target:
            self.table.setItem(row, 4, QTableWidgetItem(target))

    def save_data(self):
        rows_data = []
        for r in range(self.table.rowCount()):
            # Get ID
            item_seq = self.table.item(r, 0)
            rid = item_seq.data(Qt.UserRole) if item_seq else None
            
            item_name = self.table.item(r, 1).text().strip() if self.table.item(r, 1) else ""
            
            # Get plan_release from combo
            combo_release = self.table.cellWidget(r, 2)
            plan_release = combo_release.currentText().strip() if combo_release else ""
            
            # Get purchase_method
            combo_method = self.table.cellWidget(r, 3)
            p_method = combo_method.currentText().strip() if combo_method else ""
            
            # Get purchase_channel
            p_channel = self.table.item(r, 4).text().strip() if self.table.item(r, 4) else ""
            
            weight_str = self.table.item(r, 5).text().strip() if self.table.item(r, 5) else "0"
            
            # Get is_active from combo
            combo = self.table.cellWidget(r, 6)
            is_active = 1 if combo and combo.currentText() == "是" else 0
            
            if not item_name and not plan_release:
                continue
                
            try:
                weight = int(weight_str)
            except ValueError:
                weight = 0
                
            rows_data.append((rid, item_name, plan_release, weight, is_active, p_method, p_channel))
            
        try:
            database.save_recommendations_upsert(rows_data)
            QMessageBox.information(self, "成功", "数据已保存")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def sync_recommendations(self):
        if QMessageBox.question(self, "确认", "将从已发放记录增量同步到推荐库，确认继续？") != QMessageBox.Yes:
            return
        dlg = QProgressDialog("正在同步...", "取消", 0, 100, self)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        self._sync_progress = dlg
        class Worker(QThread):
            progress = Signal(int, int)
            finished_stats = Signal(dict)
            failed_items = Signal(list)
            def run(self_inner):
                items = database.get_released_items_for_recommendation()
                total = len(items)
                batch = 200
                inserted = 0
                skipped = 0
                failed = 0
                failures = []
                for i in range(0, total, batch):
                    if self_inner.isInterruptionRequested():
                        break
                    part = items[i:i+batch]
                    r = database.insert_recommendations_batch(part)
                    inserted += r.get("inserted", 0)
                    skipped += r.get("skipped", 0)
                    failed += r.get("failed", 0)
                    if r.get("failures"):
                        failures.extend(r.get("failures"))
                    self_inner.progress.emit(min(i+batch, total), total)
                from datetime import datetime
                start_time = ""
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    details = "\n".join(failures)
                    database.save_sync_log(start_time, end_time, total, inserted, skipped, failed, details)
                except Exception:
                    pass
                self_inner.finished_stats.emit({
                    "total": total,
                    "inserted": inserted,
                    "skipped": skipped,
                    "failed": failed,
                    "failures": failures
                })
                self_inner.failed_items.emit(items if failures else [])
        self._sync_worker = Worker()
        def on_progress(done, total):
            if total == 0:
                self._sync_progress.setValue(100)
            else:
                val = int(done * 100 / total)
                self._sync_progress.setValue(val)
        def on_finished(stats):
            self._sync_progress.reset()
            self.load_data()  # Refresh list after sync
            msg = f"总计: {stats['total']}\n新增: {stats['inserted']}\n跳过: {stats['skipped']}\n失败: {stats['failed']}"
            box = QMessageBox(self)
            box.setWindowTitle("同步完成")
            box.setText(msg)
            btn_detail = box.addButton("查看详情", QMessageBox.ActionRole)
            btn_retry = box.addButton("重试失败项", QMessageBox.ActionRole)
            box.addButton("关闭", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() == btn_detail:
                logs = database.fetch_sync_logs(1)
                if logs:
                    det = logs[0][-1] or ""
                    QMessageBox.information(self, "详情", det if det else "无失败记录")
            elif box.clickedButton() == btn_retry and stats.get("failures"):
                self.sync_recommendations()
        self._sync_worker.progress.connect(on_progress)
        self._sync_worker.finished_stats.connect(on_finished)
        self._sync_worker.finished.connect(self._sync_worker.deleteLater)
        self._sync_worker.finished.connect(lambda: setattr(self, "_sync_worker", None))
        self._sync_progress.canceled.connect(self._sync_worker.requestInterruption)
        self._sync_worker.start()

    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
            
        try:
            df = pd.read_excel(file_path)
            # Expect columns: "采购标的", "计划发放", "权重"
            # Optional: "采购方式", "采购途径"
            # Map standard names
            column_map = {
                "采购标的": "item_name",
                "计划发放": "plan_release",
                "权重": "weight",
                "采购方式": "purchase_method",
                "采购途径": "purchase_channel"
            }
            
            # Simple validation
            found_cols = [c for c in column_map.keys() if c in df.columns]
            if not found_cols:
                QMessageBox.warning(self, "提示", f"Excel需包含以下列名之一: {', '.join(column_map.keys())}")
                return

            # Append to table
            start_row = self.table.rowCount()
            purchasers = database.fetch_purchasers()
            
            for i, (_, row) in enumerate(df.iterrows()):
                r = start_row + i
                self.table.insertRow(r)
                
                # 序号
                start_seq = (self.current_page - 1) * self.page_size + 1
                item_seq = QTableWidgetItem(str(start_seq + r))
                item_seq.setData(Qt.UserRole, None)
                self.table.setItem(r, 0, item_seq)
                self.table.item(r, 0).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                
                item_name = str(row.get("采购标的", ""))
                if item_name == "nan": item_name = ""
                
                plan_release = str(row.get("计划发放", ""))
                if plan_release == "nan": plan_release = ""
                
                weight = str(row.get("权重", ""))
                if weight == "nan": weight = "0"
                
                p_method = str(row.get("采购方式", ""))
                if p_method == "nan": p_method = ""
                
                p_channel = str(row.get("采购途径", ""))
                if p_channel == "nan": p_channel = ""
                
                self.table.setItem(r, 1, QTableWidgetItem(item_name))
                
                # 计划发放 - Dropdown
                combo_release = QComboBox()
                combo_release.addItems(purchasers)
                combo_release.setCurrentText(plan_release)
                if plan_release and plan_release not in purchasers:
                    combo_release.addItem(plan_release)
                    combo_release.setCurrentText(plan_release)
                self.table.setCellWidget(r, 2, combo_release)
                
                # 采购方式 - Dropdown
                combo_method = QComboBox()
                combo_method.addItems(["", "询比采购", "公开招标", "集中采购", "框架协议"])
                combo_method.setEditable(True)
                combo_method.setCurrentText(p_method)
                combo_method.currentTextChanged.connect(lambda text, r=r: self.on_method_changed(r, text))
                self.table.setCellWidget(r, 3, combo_method)
                
                # 采购途径
                self.table.setItem(r, 4, QTableWidgetItem(p_channel))
                
                self.table.setItem(r, 5, QTableWidgetItem(weight))
                
                # is_active default "是"
                combo = QComboBox()
                combo.addItems(["是", "否"])
                combo.setCurrentText("是")
                self.table.setCellWidget(r, 6, combo)
                
            QMessageBox.information(self, "成功", "导入完成，请检查并保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
