
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QComboBox, 
    QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QTabWidget, QStackedWidget, QGroupBox, QDateEdit, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QDate
from PySide6.QtGui import QColor, QBrush
import database
from datetime import datetime
import openpyxl

class SettlementModule(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Page 0: Home (Tabs)
        self.home_page = QWidget()
        self.home_layout = QVBoxLayout(self.home_page)
        self.tabs = QTabWidget()
        self.reconciliation_tab = ReconciliationManager(self)
        self.settlement_tab = SettlementManager(self)
        
        self.tabs.addTab(self.reconciliation_tab, "对账管理")
        self.tabs.addTab(self.settlement_tab, "结算办理")
        self.home_layout.addWidget(self.tabs)
        
        self.stack.addWidget(self.home_page)
        
        # Page 1: Reconciliation Editor (Detail View)
        self.editor_page = ReconciliationEditor(self)
        self.stack.addWidget(self.editor_page)
        
        # Connect signals
        self.reconciliation_tab.open_editor.connect(self.open_reconciliation_editor)
        self.settlement_tab.open_viewer.connect(self.open_settlement_viewer)
        self.editor_page.back_signal.connect(self.go_back)
        
    def open_reconciliation_editor(self, rec_id=None):
        self.editor_page.load_data(rec_id, mode="edit")
        self.stack.setCurrentWidget(self.editor_page)
        
    def open_settlement_viewer(self, rec_id):
        self.editor_page.load_data(rec_id, mode="view")
        self.stack.setCurrentWidget(self.editor_page)
        
    def go_back(self):
        self.stack.setCurrentWidget(self.home_page)
        self.reconciliation_tab.refresh_data()
        self.settlement_tab.refresh_data()


class ReconciliationManager(QWidget):
    open_editor = Signal(object) # rec_id or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Top Bar
        top_layout = QHBoxLayout()
        self.btn_new = QPushButton("新建对账单")
        self.btn_new.clicked.connect(lambda: self.open_editor.emit(None))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索对账单号/供应商...")
        self.search_input.textChanged.connect(self.refresh_data)
        
        top_layout.addWidget(self.btn_new)
        top_layout.addWidget(self.search_input)
        top_layout.addStretch()
        
        self.layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "对账单号", "供应商", "总金额", "状态", "创建时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_double_click)
        
        self.layout.addWidget(self.table)
        
        self.refresh_data()
        
    def refresh_data(self):
        filter_text = self.search_input.text().strip()
        data = database.fetch_reconciliations(filter_text)
        
        self.table.setRowCount(0)
        for row in data:
            rid, rno, sup, status, amt, ctime, rem = row
            r_idx = self.table.rowCount()
            self.table.insertRow(r_idx)
            
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(r_idx, 1, QTableWidgetItem(rno))
            self.table.setItem(r_idx, 2, QTableWidgetItem(sup))
            self.table.setItem(r_idx, 3, QTableWidgetItem(f"{amt:.2f}" if amt else "0.00"))
            self.table.setItem(r_idx, 4, QTableWidgetItem(status))
            self.table.setItem(r_idx, 5, QTableWidgetItem(ctime))
            
            # Delete Button
            if status == '待对账':
                btn_del = QPushButton("删除")
                btn_del.clicked.connect(lambda _, x=rid: self.delete_record(x))
                self.table.setCellWidget(r_idx, 6, btn_del)
            else:
                self.table.setItem(r_idx, 6, QTableWidgetItem("-"))
                
    def on_double_click(self, index):
        rid = int(self.table.item(index.row(), 0).text())
        self.open_editor.emit(rid)
        
    def delete_record(self, rid):
        if QMessageBox.question(self, "确认", "确定要删除此对账单吗？") == QMessageBox.Yes:
            database.delete_reconciliation(rid)
            self.refresh_data()

class SettlementManager(QWidget):
    open_viewer = Signal(object) # rec_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Top Bar
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索已对账单据...")
        self.search_input.textChanged.connect(self.refresh_data)
        
        top_layout.addWidget(self.search_input)
        top_layout.addStretch()
        
        self.layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "对账单号", "供应商", "总金额", "状态", "创建时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_double_click)
        
        self.layout.addWidget(self.table)
        
        self.refresh_data()
        
    def refresh_data(self):
        filter_text = self.search_input.text().strip()
        # Fetch only '已对账' or '结算中' or '已结算'
        # For simplicity, let's fetch all and filter in python or add param
        # Adding param to database function is better.
        # But for now I'll fetch '已对账' specifically as the starting point for settlement.
        # User said: "list records marked as Reconciliation Completed"
        data = database.fetch_reconciliations(filter_text, status_filter="已对账")
        # Also include '已结算'? Maybe later.
        
        self.table.setRowCount(0)
        for row in data:
            rid, rno, sup, status, amt, ctime, rem = row
            r_idx = self.table.rowCount()
            self.table.insertRow(r_idx)
            
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(r_idx, 1, QTableWidgetItem(rno))
            self.table.setItem(r_idx, 2, QTableWidgetItem(sup))
            self.table.setItem(r_idx, 3, QTableWidgetItem(f"{amt:.2f}" if amt else "0.00"))
            self.table.setItem(r_idx, 4, QTableWidgetItem(status))
            self.table.setItem(r_idx, 5, QTableWidgetItem(ctime))
            
    def on_double_click(self, index):
        rid = int(self.table.item(index.row(), 0).text())
        self.open_viewer.emit(rid)


class ReconciliationEditor(QWidget):
    back_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_id = None
        self.mode = "edit" # edit or view
        
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.btn_back = QPushButton("返回")
        self.btn_back.clicked.connect(self.back_signal.emit)
        self.title_label = QLabel("对账单详情")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        header_layout.addWidget(self.btn_back)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Action Buttons
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_complete = QPushButton("完成对账")
        self.btn_complete.clicked.connect(self.complete_reconciliation)
        self.btn_export = QPushButton("导出明细")
        self.btn_export.clicked.connect(self.export_details)
        
        header_layout.addWidget(self.btn_save)
        header_layout.addWidget(self.btn_complete)
        header_layout.addWidget(self.btn_export)
        
        self.layout.addLayout(header_layout)
        
        # Form
        form_group = QGroupBox("基本信息")
        form_layout = QHBoxLayout(form_group)
        
        self.input_no = QLineEdit()
        self.input_no.setReadOnly(True)
        self.input_supplier = QComboBox()
        self.input_supplier.setEditable(True)
        # Populate suppliers
        self.input_supplier.addItems(database.fetch_suppliers())
        
        self.input_status = QLineEdit()
        self.input_status.setReadOnly(True)
        self.input_total = QLineEdit()
        self.input_total.setReadOnly(True)
        
        form_layout.addWidget(QLabel("单号:"))
        form_layout.addWidget(self.input_no)
        form_layout.addWidget(QLabel("供应商:"))
        form_layout.addWidget(self.input_supplier)
        form_layout.addWidget(QLabel("状态:"))
        form_layout.addWidget(self.input_status)
        form_layout.addWidget(QLabel("总金额:"))
        form_layout.addWidget(self.input_total)
        
        self.layout.addWidget(form_group)
        
        # Details
        detail_group = QGroupBox("对账明细")
        detail_layout = QVBoxLayout(detail_group)
        
        # Toolbar
        tool_layout = QHBoxLayout()
        self.btn_add_invoices = QPushButton("添加发票")
        self.btn_add_invoices.clicked.connect(self.add_invoices)
        tool_layout.addWidget(self.btn_add_invoices)
        tool_layout.addStretch()
        
        detail_layout.addLayout(tool_layout)
        
        self.table = QTableWidget()
        # Columns: ID, InvoiceNo, WhNo, Unit, Qty, Price, Amount(Excl), Amount(Incl), Spec, ItemName
        columns = ["ID", "发票编号", "仓库单号", "单位", "数量", "单价", "金额(不含税)", "含税总价", "规格型号", "物品名称"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Enable column resizing
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Load saved widths
        widths = database.get_table_column_widths("settlement_reconciliation_details")
        if widths:
            for col, width in widths.items():
                self.table.setColumnWidth(col, width)
        else:
            # Default widths
            self.table.setColumnWidth(0, 50) # ID
            self.table.setColumnWidth(1, 120) # Invoice
            self.table.setColumnWidth(2, 120) # Warehouse
            self.table.setColumnWidth(9, 200) # Item Name
        
        # Connect resize signal
        self.table.horizontalHeader().sectionResized.connect(self.save_column_width)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        detail_layout.addWidget(self.table)
        self.layout.addWidget(detail_group)
    
    def save_column_width(self, logicalIndex, oldSize, newSize):
        database.save_table_column_width("settlement_reconciliation_details", logicalIndex, newSize)
        
    def load_data(self, rec_id, mode="edit"):
        self.current_id = rec_id
        self.mode = mode
        
        # Reset UI
        self.table.setRowCount(0)
        self.input_supplier.setCurrentIndex(-1)
        self.input_total.setText("0.00")
        
        if mode == "view":
            self.btn_save.setVisible(False)
            self.btn_complete.setVisible(False)
            self.btn_add_invoices.setVisible(False)
            self.input_supplier.setEnabled(False)
            self.title_label.setText("结算单详情")
        else:
            self.btn_save.setVisible(True)
            self.btn_complete.setVisible(True)
            self.btn_add_invoices.setVisible(True)
            self.input_supplier.setEnabled(True)
            self.title_label.setText("编辑对账单")
            
        if rec_id:
            # Fetch Header
            recs = database.fetch_reconciliations() # Ideally get by ID
            rec = next((r for r in recs if r[0] == rec_id), None)
            if rec:
                self.input_no.setText(rec[1])
                self.input_supplier.setCurrentText(rec[2])
                self.input_status.setText(rec[3])
                self.input_total.setText(str(rec[4]))
                
                if rec[3] == '已对账' and mode == 'edit':
                    # If completed, disable editing
                    self.btn_save.setVisible(False)
                    self.btn_complete.setVisible(False)
                    self.btn_add_invoices.setVisible(False)
                    self.input_supplier.setEnabled(False)
                
            # Fetch Details
            details = database.fetch_reconciliation_details(rec_id)
            for row in details:
                # id, inv_no, wh_no, unit, qty, price, amt_ex, amt_in, spec, name
                r_idx = self.table.rowCount()
                self.table.insertRow(r_idx)
                for i, val in enumerate(row):
                    self.table.setItem(r_idx, i, QTableWidgetItem(str(val) if val is not None else ""))
        else:
            # New
            self.input_no.setText(database.get_next_reconciliation_number())
            self.input_status.setText("待对账")
            self.input_supplier.setCurrentText("")
            
    def add_invoices(self):
        supplier = self.input_supplier.currentText().strip()
        if not supplier:
            QMessageBox.warning(self, "提示", "请先选择供应商")
            return
            
        # Dialog to select invoices
        dlg = InvoiceSelectionDialog(supplier, self)
        if dlg.exec():
            selected_ids = dlg.get_selected_ids()
            if selected_ids:
                # Process logic: 
                # 1. Fetch items with split
                items = database.fetch_invoice_items_with_inbound_split(selected_ids)
                
                # 2. Add to table (preview)
                for item in items:
                    r_idx = self.table.rowCount()
                    self.table.insertRow(r_idx)
                    # Columns: ID, InvoiceNo, WhNo, Unit, Qty, Price, Amount(Excl), Amount(Incl), Spec, ItemName
                    # item has: invoice_item_id, inbound_order_id, warehouse_no, quantity, amount, unit_price, tax_rate, item_name, spec_model, unit
                    
                    # Calculate Incl Tax
                    amt = item['amount']
                    tax = item.get('tax_rate', 0) or 0
                    if tax > 1: tax = tax / 100.0
                    amt_incl = amt * (1 + tax)
                    
                    # Need Invoice No. We can fetch it or pass it. 
                    # fetch_invoice_items_with_inbound_split doesn't return invoice no.
                    # Let's fix that or fetch separately. 
                    # Actually, for preview, we might need it.
                    # Let's rely on saving first? No, user wants to see before saving usually.
                    # But wait, create_reconciliation_details_batch needs a rec_id.
                    # So we must save the header first.
                    
                    # Let's just prompt to save first?
                    pass
                
                # Save immediately for simplicity?
                # User flow: Select Invoices -> System creates Reconciliation Details in DB -> Refresh Table
                
                # Save Header if new
                if not self.current_id:
                    self.save_header()
                    
                if self.current_id:
                    database.create_reconciliation_details_batch(self.current_id, items)
                    self.load_data(self.current_id, self.mode) # Refresh
                    
    def save_header(self):
        data = {
            'id': self.current_id,
            'reconciliation_no': self.input_no.text(),
            'supplier': self.input_supplier.currentText(),
            'status': self.input_status.text(),
            'total_amount': float(self.input_total.text() or 0),
            'remarks': ''
        }
        self.current_id = database.save_reconciliation(data)
        
    def save_data(self):
        # Recalculate total amount from DB details?
        if self.current_id:
            # Sum up details
            details = database.fetch_reconciliation_details(self.current_id)
            total = sum([r[7] for r in details]) # 7 is amount_incl_tax
            self.input_total.setText(f"{total:.2f}")
            self.save_header()
            QMessageBox.information(self, "成功", "保存成功")
            
    def complete_reconciliation(self):
        if not self.current_id: return
        
        self.save_data() # Ensure saved
        
        if QMessageBox.question(self, "确认", "确定要完成对账吗？完成后将进入结算流程。") == QMessageBox.Yes:
            # Update status
            data = {
                'id': self.current_id,
                'reconciliation_no': self.input_no.text(),
                'supplier': self.input_supplier.currentText(),
                'status': '已对账',
                'total_amount': float(self.input_total.text() or 0),
                'remarks': ''
            }
            database.save_reconciliation(data)
            self.load_data(self.current_id, "edit") # Refresh UI state
            QMessageBox.information(self, "成功", "已标记为已对账")
            
    def export_details(self):
        if self.table.rowCount() == 0:
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", f"对账明细_{self.input_no.text()}.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
            
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # Headers
        headers = []
        for c in range(self.table.columnCount()):
            headers.append(self.table.horizontalHeaderItem(c).text())
        ws.append(headers)
        
        # Data
        for r in range(self.table.rowCount()):
            row_data = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                row_data.append(item.text() if item else "")
            ws.append(row_data)
            
        wb.save(path)
        QMessageBox.information(self, "成功", f"导出成功: {path}")

class InvoiceSelectionDialog(QDialog):
    def __init__(self, supplier, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"选择发票 - {supplier}")
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "发票号", "供应商", "金额", "日期", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        
        layout.addWidget(self.table)
        
        # Load data
        data = database.fetch_unreconciled_invoices(supplier)
        self.table.setRowCount(0)
        for row in data:
            r_idx = self.table.rowCount()
            self.table.insertRow(r_idx)
            for i, val in enumerate(row):
                self.table.setItem(r_idx, i, QTableWidgetItem(str(val)))
                
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected_ids(self):
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())
            
        ids = []
        for r in rows:
            ids.append(int(self.table.item(r, 0).text()))
        return ids
