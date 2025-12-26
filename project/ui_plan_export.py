from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QFileDialog, QAbstractItemView
)
from PySide6.QtCore import Qt
import database
from export import OrderExporter
from print import OrderPrinter

class PlanExportWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_months()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("计划月份:"))
        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(100)
        toolbar.addWidget(self.combo_month)
        
        btn_load = QPushButton("加载数据")
        btn_load.clicked.connect(self.load_data)
        toolbar.addWidget(btn_load)
        
        btn_export = QPushButton("导出Excel")
        btn_export.clicked.connect(self.export_excel)
        toolbar.addWidget(btn_export)
        
        btn_print = QPushButton("打印")
        btn_print.clicked.connect(self.print_table)
        toolbar.addWidget(btn_print)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Search Area (moved to top, just below month toolbar)
        search = QHBoxLayout()
        search.addWidget(QLabel("序号:"))
        from PySide6.QtWidgets import QLineEdit
        self.filter_seq = QLineEdit()
        self.filter_seq.setPlaceholderText("如 2601MPB-1 或 1-5")
        self.filter_seq.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_seq)

        search.addWidget(QLabel("采购标的:"))
        self.filter_item = QLineEdit()
        self.filter_item.setPlaceholderText("关键词")
        self.filter_item.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_item)

        search.addWidget(QLabel("主单编号:"))
        self.filter_order = QLineEdit()
        self.filter_order.setPlaceholderText("精确或模糊")
        self.filter_order.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_order)

        search.addWidget(QLabel("需求单位:"))
        self.combo_unit = QComboBox()
        self.combo_unit.setEditable(False)
        self.combo_unit.currentIndexChanged.connect(self.apply_filters)
        search.addWidget(self.combo_unit)

        self.btn_unit_multi = QPushButton("多选...")
        self.btn_unit_multi.clicked.connect(self._open_unit_multi_dialog)
        search.addWidget(self.btn_unit_multi)

        btn_clear = QPushButton("清空筛选")
        btn_clear.clicked.connect(self._clear_filters)
        search.addWidget(btn_clear)
        search.addStretch()
        layout.addLayout(search)

        self._unit_multi_selected = set()

        # Table
        # Columns for export preview (updated per requirements)
        self.columns = [
            "序号", "主单编号", "需求单位", "采购标的", "规格型号",
            "单位", "采购数量", "预算(万)",
            "采购方式", "采购渠道", "计划发放", "询价金额", "备注"
        ]
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read only
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Adjust some widths
        self.table.setColumnWidth(0, 110) # 序号
        self.table.setColumnWidth(1, 150) # 主单编号
        self.table.setColumnWidth(2, 120) # 需求单位
        self.table.setColumnWidth(3, 160) # 采购标的
        self.table.setColumnWidth(4, 160) # 规格型号
        
        layout.addWidget(self.table)
        
        self.current_rows_data = [] # Store raw data for export

    def load_months(self):
        self.combo_month.clear()
        months = database.fetch_plan_months()
        self.combo_month.addItems(months)
        if months:
            self.combo_month.setCurrentIndex(0)

    def load_data(self):
        month = self.combo_month.currentText()
        if not month:
            return
            
        # database.fetch_monthly_details_for_export returns:
        # 0:o.number, 1:o.task_name, 2:o.category, 3:o.unit, 4:o.date,
        # 5:od.detail_no, 6:od.item_name, 7:od.purchase_item, 8:od.spec_model, 
        # 9:od.unit, 10:od.purchase_qty, 11:od.budget_wan, 12:od.purchase_method, 13:od.purchase_channel,
        # 14:od.plan_release, 15:od.inquiry_price, 16:od.supplier, 17:od.remark, 18:od.plan_time
        
        raw_data = database.fetch_monthly_details_for_export(month)
        self.current_rows_data = raw_data
        
        # Load units for filter
        units = database.fetch_units()
        self.combo_unit.blockSignals(True)
        self.combo_unit.clear()
        self.combo_unit.addItem("全部")
        for u in units:
            self.combo_unit.addItem(u)
        self.combo_unit.blockSignals(False)

        # Apply filters to refresh table
        self.apply_filters()
        QMessageBox.information(self, "完成", f"已加载 {len(raw_data)} 条数据")

    def _prepare_export_data(self):
        # Header Info for printing/export
        # Since this is a monthly summary, we don't have a single order number.
        # We can set title to "月度采购计划汇总"
        month = self.combo_month.currentText()
        header_info = {
            "number": "汇总",
            "task_name": "月度汇总",
            "unit": "多部门",
            "yymm": month,
            "purchaser": "所有"
        }
        
        rows = []
        for r in range(self.table.rowCount()):
            row_data = []
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                row_data.append(it.text() if it else "")
            rows.append(row_data)
            
        return header_info, rows

    def export_excel(self):
        if self.table.rowCount() == 0:
            return
            
        month = self.combo_month.currentText()
        default_name = f"采购计划明细_{month}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", default_name, "Excel Files (*.xlsx)")
        
        if not file_path:
            return
            
        header_info, rows = self._prepare_export_data()
        
        try:
            exporter = OrderExporter(header_info, self.columns, rows, title=f"{month} 采购计划明细")
            exporter.export(file_path)
            QMessageBox.information(self, "成功", f"导出成功:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def print_table(self):
        if self.table.rowCount() == 0:
            return
            
        header_info, rows = self._prepare_export_data()
        
        # Remove "主单编号" from printing columns per requirement
        print_columns = [c for c in self.columns if c != "主单编号"]
        # Determine index of removed column to drop from row data
        try:
            drop_idx = self.columns.index("主单编号")
        except ValueError:
            drop_idx = None
        print_rows = []
        for r in rows:
            if drop_idx is None:
                print_rows.append(r)
            else:
                print_rows.append([r[i] for i in range(len(r)) if i != drop_idx])
        
        # Inject Group Headers for Printing
        # Replicates logic from export.py to ensure consistency
        processed_rows = []
        inserted_semi_header = False
        inserted_civil_header = False
        inserted_mach_header = False
        
        # Colors matching export.py
        COLOR_SEMI = "#F0F0F0"
        COLOR_CIVIL = "#DCE6F1"
        
        for row_data in print_rows:
            # detail_no is index 0
            detail_no = str(row_data[0]) if len(row_data) > 0 else ""
            
            is_semi = "MPB" in detail_no
            is_civil = "MP-" in detail_no or (detail_no.endswith("MP") if "MP" in detail_no else False) or ("MP" in detail_no and "MPB" not in detail_no and "MPJ" not in detail_no)
            is_mach = "MPJ" in detail_no
            
            if is_semi and not inserted_semi_header:
                processed_rows.append({"is_header": True, "text": "半成品MPB", "color": COLOR_SEMI})
                inserted_semi_header = True
                
            if is_civil and not inserted_civil_header:
                processed_rows.append({"is_header": True, "text": "民品MP", "color": COLOR_CIVIL})
                inserted_civil_header = True
            
            if is_mach and not inserted_mach_header:
                processed_rows.append({"is_header": True, "text": "机加件MPJ", "color": COLOR_CIVIL})
                inserted_mach_header = True
            
            processed_rows.append(row_data)
            
        rows = processed_rows
        
        month = self.combo_month.currentText()
        
        # Convert "2601" to "2026年1月份"
        title_month = month
        if len(month) == 4 and month.isdigit():
            yy = month[:2]
            mm = month[2:]
            title_month = f"20{yy}年{int(mm)}月份"
            
        printer = OrderPrinter(header_info, print_columns, rows)
        # Customize title
        printer.title = f"{title_month}民品采购计划表"
        printer.show_preview()

    def apply_filters(self):
        # Filter current_rows_data and render table
        seq_text = self.filter_seq.text().strip() if hasattr(self, 'filter_seq') else ""
        item_kw = self.filter_item.text().strip() if hasattr(self, 'filter_item') else ""
        order_kw = self.filter_order.text().strip() if hasattr(self, 'filter_order') else ""
        unit_sel = self.combo_unit.currentText() if hasattr(self, 'combo_unit') and self.combo_unit.count()>0 else "全部"
        unit_set = self._unit_multi_selected if hasattr(self, '_unit_multi_selected') else set()

        def match_seq(detail_no: str) -> bool:
            if not seq_text:
                return True
            import re
            m = re.match(r"^(\d+)\s*-\s*(\d+)$", seq_text)
            if m:
                try:
                    lo = int(m.group(1)); hi = int(m.group(2))
                    suf_m = re.search(r"-(\d+)$", detail_no or "")
                    if not suf_m:
                        return False
                    n = int(suf_m.group(1))
                    return lo <= n <= hi
                except:
                    return False
            return seq_text in (detail_no or "")

        def match_item(purchase_item: str) -> bool:
            if not item_kw:
                return True
            return item_kw in (purchase_item or "")

        def match_order(order_number: str) -> bool:
            if not order_kw:
                return True
            return order_kw in (order_number or "")

        def match_unit(unit_val: str) -> bool:
            if unit_set:
                return unit_val in unit_set
            if unit_sel and unit_sel != "全部":
                return unit_val == unit_sel
            return True

        rows = []
        for row in self.current_rows_data:
            detail_no = str(row[5] or "")
            purchase_item = str(row[7] or "")
            order_number = str(row[0] or "")
            unit_val = str(row[3] or "")
            if match_seq(detail_no) and match_item(purchase_item) and match_order(order_number) and match_unit(unit_val):
                rows.append(row)

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # Map to new columns:
            # 0 序号(detail_no), 1 主单编号(o.number), 2 需求单位(o.unit), 3 采购标的(purchase_item), 4 规格型号(spec_model)
            # 5 单位, 6 采购数量, 7 预算(万), 8 采购方式, 9 采购渠道, 10 计划发放, 11 询价金额, 12 备注
            self.table.setItem(r, 0, QTableWidgetItem(str(row[5] or "")))
            self.table.setItem(r, 1, QTableWidgetItem(str(row[0] or "")))
            self.table.setItem(r, 2, QTableWidgetItem(str(row[3] or "")))
            self.table.setItem(r, 3, QTableWidgetItem(str(row[7] or "")))
            self.table.setItem(r, 4, QTableWidgetItem(str(row[8] or "")))
            self.table.setItem(r, 5, QTableWidgetItem(str(row[9] or "")))
            self.table.setItem(r, 6, QTableWidgetItem(str(row[10] or "")))
            self.table.setItem(r, 7, QTableWidgetItem(str(row[11] or "")))
            self.table.setItem(r, 8, QTableWidgetItem(str(row[12] or "")))
            self.table.setItem(r, 9, QTableWidgetItem(str(row[13] or "")))
            self.table.setItem(r, 10, QTableWidgetItem(str(row[14] or "")))
            self.table.setItem(r, 11, QTableWidgetItem(str(row[15] or "")))
            self.table.setItem(r, 12, QTableWidgetItem(str(row[17] or "")))

    def _open_unit_multi_dialog(self):
        # Simple multi-select dialog for units
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("选择需求单位")
        v = QVBoxLayout(dlg)
        lst = QListWidget()
        lst.setSelectionMode(QAbstractItemView.NoSelection)
        import database
        units = database.fetch_units()
        for u in units:
            it = QListWidgetItem(u)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if u in self._unit_multi_selected else Qt.Unchecked)
            lst.addItem(it)
        v.addWidget(lst)
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        v.addWidget(box)
        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        if dlg.exec():
            sel = set()
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == Qt.Checked:
                    sel.add(it.text())
            self._unit_multi_selected = sel
            # Reflect a hint in combo text
            if sel:
                self.combo_unit.setCurrentIndex(0)  # 全部
                self.combo_unit.setEditable(True)
                self.combo_unit.lineEdit().setText(f"多选({len(sel)})")
                self.combo_unit.setEditable(False)
            else:
                # reset display
                self.combo_unit.setEditable(True)
                self.combo_unit.lineEdit().setText("")
                self.combo_unit.setEditable(False)
            self.apply_filters()

    def _clear_filters(self):
        self.filter_seq.setText("")
        self.filter_item.setText("")
        self.filter_order.setText("")
        self._unit_multi_selected = set()
        if self.combo_unit.count()>0:
            self.combo_unit.setCurrentIndex(0)
        self.apply_filters()
