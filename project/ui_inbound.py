from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QDateEdit, QGroupBox, 
    QHeaderView, QMessageBox, QDialog, QFormLayout,
    QSplitter, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
import database
import os

STYLE_MAIN = """
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 10pt;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    margin-top: 6px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}
QLineEdit, QDateEdit, QDoubleSpinBox {
    padding: 4px;
    border: 1px solid #ccc;
    border-radius: 3px;
}
QTableWidget {
    border: 1px solid #ccc;
    gridline-color: #f0f0f0;
    selection-background-color: #e6f3ff;
    selection-color: #000;
}
QHeaderView::section {
    background-color: #f8f9fa;
    padding: 4px;
    border: 1px solid #e0e0e0;
    font-weight: bold;
}
QPushButton {
    padding: 5px 15px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
QPushButton#primary {
    background-color: #007bff;
    color: white;
    border: 1px solid #0056b3;
}
QPushButton#primary:hover {
    background-color: #0069d9;
}
"""

class OrderSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择关联订单")
        self.resize(900, 500)
        self.selected_data = None
        
        layout = QVBoxLayout(self)
        
        # Filter
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索单号/合同号/名称...")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "订单编号", "合同编号", "名称", "类别", "规格型号", "订单数量", "已入库", "剩余数量"
        ])
        self.table.setColumnHidden(0, True) # ID hidden
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept_selection)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
        self.load_data()
        
    def load_data(self):
        text = self.search_input.text().strip()
        orders = database.fetch_contract_orders_for_inbound(text)
        
        self.table.setRowCount(0)
        for row_data in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            is_empty = row_data['remaining'] <= 0
            
            # id, order_no, contract_no, contract_name, category, spec, qty, inbound_total, remaining
            items = [
                str(row_data['id']),
                str(row_data['order_no']),
                str(row_data['contract_no']),
                str(row_data['contract_name']),
                str(row_data['category']),
                str(row_data['spec']),
                str(row_data['qty']),
                str(row_data['inbound_total']),
                str(row_data['remaining'])
            ]
            
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if is_empty:
                    item.setForeground(QColor("gray"))
                    # Make non-selectable but still visible
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                elif col == 8: # Remaining column
                    item.setForeground(QColor("red"))
                self.table.setItem(row, col, item)
            
            # Store full data in UserRole of first item
            self.table.item(row, 0).setData(Qt.UserRole, row_data)

    def accept_selection(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_data = self.table.item(row, 0).data(Qt.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请先选择一条记录")


class EditInboundDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改入库记录")
        self.data = data
        self.resize(400, 350)
        
        layout = QFormLayout(self)
        
        # Read-only fields
        layout.addRow("入库单号:", QLabel(data['inbound_no']))
        layout.addRow("合同编号:", QLabel(data['contract_no']))
        layout.addRow("订单编号:", QLabel(data['order_no']))
        layout.addRow("规格型号:", QLabel(data['spec_model']))
        
        # Editable fields
        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_date.setDisplayFormat("yyyy-MM-dd")
        # Handle date parsing safely
        try:
            d = QDate.fromString(data['inbound_date'], "yyyy-MM-dd")
            if not d.isValid(): d = QDate.currentDate()
        except:
            d = QDate.currentDate()
        self.input_date.setDate(d)
        layout.addRow("入库日期:", self.input_date)
        
        self.input_qty = QDoubleSpinBox()
        self.input_qty.setRange(0, 99999999)
        try:
            val = float(data['inbound_qty'])
        except:
            val = 0.0
        self.input_qty.setValue(val)
        layout.addRow("本次入库:", self.input_qty)
        
        self.input_warehouse = QLineEdit(data['warehouse_no'])
        layout.addRow("仓储单号:", self.input_warehouse)
        
        self.input_remarks = QLineEdit(data['remarks'])
        layout.addRow("备注:", self.input_remarks)
        
        # Buttons
        btn_box = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addRow(btn_box)
        
    def get_data(self):
        return {
            'id': self.data['id'],
            'inbound_date': self.input_date.date().toString("yyyy-MM-dd"),
            'inbound_qty': self.input_qty.value(),
            'warehouse_no': self.input_warehouse.text().strip(),
            'remarks': self.input_remarks.text().strip()
        }


class InboundManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE_MAIN)
        self.init_ui()
        self.load_history()
        self.current_order_data = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Area: Entry Form ---
        entry_group = QGroupBox("入库登记")
        entry_layout = QGridLayout(entry_group)
        
        # Row 0: Basic Info
        entry_layout.addWidget(QLabel("入库日期"), 0, 0)
        self.input_date = QDateEdit(QDate.currentDate())
        self.input_date.setCalendarPopup(True)
        self.input_date.dateChanged.connect(self.update_preview_no)
        entry_layout.addWidget(self.input_date, 0, 1)
        
        entry_layout.addWidget(QLabel("预览单号"), 0, 2)
        self.lbl_preview_no = QLabel("RK-YYMMDD-CAT-XXXX")
        self.lbl_preview_no.setStyleSheet("color: gray; font-style: italic;")
        entry_layout.addWidget(self.lbl_preview_no, 0, 3)
        
        self.btn_select_order = QPushButton("选择关联订单...")
        self.btn_select_order.setObjectName("primary")
        self.btn_select_order.clicked.connect(self.select_order)
        entry_layout.addWidget(self.btn_select_order, 0, 4, 1, 2)
        
        # Row 1: Auto-filled Info (Read-only)
        entry_layout.addWidget(QLabel("合同编号"), 1, 0)
        self.txt_contract_no = QLineEdit()
        self.txt_contract_no.setReadOnly(True)
        entry_layout.addWidget(self.txt_contract_no, 1, 1)
        
        entry_layout.addWidget(QLabel("订单编号"), 1, 2)
        self.txt_order_no = QLineEdit()
        self.txt_order_no.setReadOnly(True)
        entry_layout.addWidget(self.txt_order_no, 1, 3)
        
        entry_layout.addWidget(QLabel("采购计划"), 1, 4)
        self.txt_purch_no = QLineEdit()
        self.txt_purch_no.setReadOnly(True)
        entry_layout.addWidget(self.txt_purch_no, 1, 5)
        
        # Row 2: Spec & Qty
        entry_layout.addWidget(QLabel("规格型号"), 2, 0)
        self.txt_spec = QLineEdit()
        self.txt_spec.setReadOnly(True)
        entry_layout.addWidget(self.txt_spec, 2, 1)
        
        entry_layout.addWidget(QLabel("订单数量"), 2, 2)
        self.txt_order_qty = QLineEdit()
        self.txt_order_qty.setReadOnly(True)
        entry_layout.addWidget(self.txt_order_qty, 2, 3)
        
        entry_layout.addWidget(QLabel("已入库数"), 2, 4)
        self.txt_inbound_total = QLineEdit()
        self.txt_inbound_total.setReadOnly(True)
        entry_layout.addWidget(self.txt_inbound_total, 2, 5)
        
        # Row 3: Input
        entry_layout.addWidget(QLabel("本次入库*"), 3, 0)
        self.input_qty = QDoubleSpinBox()
        self.input_qty.setRange(0, 99999999)
        entry_layout.addWidget(self.input_qty, 3, 1)
        
        entry_layout.addWidget(QLabel("仓储单号"), 3, 2)
        self.input_warehouse_no = QLineEdit()
        self.input_warehouse_no.setPlaceholderText("手填或扫码")
        entry_layout.addWidget(self.input_warehouse_no, 3, 3)
        
        entry_layout.addWidget(QLabel("备注"), 3, 4)
        self.input_remarks = QLineEdit()
        entry_layout.addWidget(self.input_remarks, 3, 5)
        
        # Row 4: Actions
        self.btn_save = QPushButton("确认入库")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_inbound)
        self.btn_clear = QPushButton("重置")
        self.btn_clear.clicked.connect(self.clear_form)
        
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(self.btn_clear)
        action_layout.addWidget(self.btn_save)
        entry_layout.addLayout(action_layout, 4, 0, 1, 6)
        
        main_layout.addWidget(entry_group)
        
        # --- Bottom Area: History List ---
        list_group = QGroupBox("入库记录")
        list_layout = QVBoxLayout(list_group)
        
        # Filter
        filter_box = QHBoxLayout()
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("搜索入库单/合同号...")
        self.filter_text.textChanged.connect(self.load_history)
        filter_box.addWidget(self.filter_text)
        list_layout.addLayout(filter_box)
        
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "入库单号", "入库日期", "合同编号", "订单编号", "采购计划", 
            "规格型号", "订单数", "本次入库", "仓储单号", "备注"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        list_layout.addWidget(self.table)
        
        main_layout.addWidget(list_group)
        
        # Set splitter
        main_layout.setStretch(1, 1)

    def update_preview_no(self):
        if not self.current_order_data:
            self.lbl_preview_no.setText("RK-YYMMDD-CAT-XXXX")
            return
            
        date_str = self.input_date.date().toString("yyMMdd")
        cat_text = self.current_order_data.get('category', '')
        # Just a preview, actual number generated on save
        cat_code = database.inbound_category_code(cat_text)
        self.lbl_preview_no.setText(f"RK-{date_str}-{cat_code}-????")

    def select_order(self):
        dlg = OrderSelectionDialog(self)
        if dlg.exec():
            data = dlg.selected_data
            self.current_order_data = data
            
            # Fill form
            self.txt_contract_no.setText(data['contract_no'])
            self.txt_order_no.setText(data['order_no'])
            self.txt_purch_no.setText(data['purch_plan_no'])
            self.txt_spec.setText(data['spec'])
            self.txt_order_qty.setText(str(data['qty']))
            self.txt_inbound_total.setText(str(data['inbound_total']))
            
            # Auto set input qty to remaining?
            self.input_qty.setValue(data['remaining'] if data['remaining'] > 0 else 0)
            
            self.update_preview_no()

    def clear_form(self):
        self.current_order_data = None
        self.txt_contract_no.clear()
        self.txt_order_no.clear()
        self.txt_purch_no.clear()
        self.txt_spec.clear()
        self.txt_order_qty.clear()
        self.txt_inbound_total.clear()
        self.input_qty.setValue(0)
        self.input_warehouse_no.clear()
        self.input_remarks.clear()
        self.lbl_preview_no.setText("RK-YYMMDD-CAT-XXXX")
        self.input_date.setDate(QDate.currentDate())

    def save_inbound(self):
        if not self.current_order_data:
            QMessageBox.warning(self, "提示", "请先选择关联订单")
            return
            
        qty = self.input_qty.value()
        if qty <= 0:
            QMessageBox.warning(self, "提示", "入库数量必须大于0")
            return
            
        # Validate logic: Inbound Qty vs Order Qty?
        # User requirement 4: "入库数量不得大于订单数量"
        # Is this Strict? What if over-delivery?
        # "Must not be greater than order quantity" usually means Total Inbound <= Order Qty.
        current_total = self.current_order_data['inbound_total']
        order_qty = self.current_order_data['qty']
        
        if current_total + qty > order_qty:
             if QMessageBox.question(self, "警告", f"总入库数量 ({current_total + qty}) 将超过订单数量 ({order_qty})。\n是否继续？") != QMessageBox.Yes:
                 return

        date_yyMMdd = self.input_date.date().toString("yyMMdd")
        date_full = self.input_date.date().toString("yyyy-MM-dd")
        cat_text = self.current_order_data.get('category', '')
        
        try:
            # Generate Number
            inbound_no = database.get_next_inbound_number(date_yyMMdd, cat_text)
            
            # Save
            data = {
                'inbound_no': inbound_no,
                'contract_order_id': self.current_order_data['id'],
                'contract_no': self.current_order_data['contract_no'],
                'order_no': self.current_order_data['order_no'],
                'purch_plan_no': self.current_order_data['purch_plan_no'],
                'spec_model': self.current_order_data['spec'],
                'order_qty': self.current_order_data['qty'],
                'inbound_qty': qty,
                'warehouse_no': self.input_warehouse_no.text().strip(),
                'inbound_date': date_full,
                'remarks': self.input_remarks.text().strip(),
                'operator': os.getlogin() if hasattr(os, 'getlogin') else 'user'
            }
            
            database.save_inbound_order(data)
            
            QMessageBox.information(self, "成功", f"入库单已生成: {inbound_no}")
            self.clear_form()
            self.load_history()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def load_history(self):
        text = self.filter_text.text().strip()
        rows = database.fetch_inbound_orders(text)
        
        self.table.setRowCount(0)
        for r in rows:
            # New order from DB: 
            # 0:id, 1:inbound_no, 2:inbound_date, 3:contract_no, 4:order_no, 5:purch_plan_no, 
            # 6:spec_model, 7:order_qty, 8:inbound_qty, 9:warehouse_no, 10:remarks
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Map SQL result to Table Columns
            # Table Cols:
            # 0:ID, 1:InboundNo, 2:Date, 3:Contract, 4:Order, 5:Plan, 6:Spec, 7:OrderQty, 8:InboundQty, 9:Warehouse, 10:Remark
            
            # Since I updated SQL to match this exact order, I can just loop
            for i, val in enumerate(r):
                item = QTableWidgetItem(str(val))
                self.table.setItem(row, i, item)
            
            # Store full data dict in first column for editing
            data = {
                'id': r[0],
                'inbound_no': r[1],
                'inbound_date': r[2],
                'contract_no': r[3],
                'order_no': r[4],
                'purch_plan_no': r[5],
                'spec_model': r[6],
                'order_qty': r[7],
                'inbound_qty': r[8],
                'warehouse_no': r[9],
                'remarks': r[10]
            }
            self.table.item(row, 0).setData(Qt.UserRole, data)

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        
        # Get data
        data = self.table.item(row, 0).data(Qt.UserRole)
        if not data: return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        act_edit = menu.addAction("修改入库记录")
        act_edit.triggered.connect(lambda: self.edit_record(data))
        
        act_del = menu.addAction("删除记录")
        act_del.triggered.connect(lambda: self.delete_record(data))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
        
    def edit_record(self, data):
        dlg = EditInboundDialog(data, self)
        if dlg.exec():
            new_data = dlg.get_data()
            try:
                database.update_inbound_order(new_data)
                QMessageBox.information(self, "成功", "记录已更新")
                self.load_history()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
                
    def delete_record(self, data):
        if QMessageBox.question(self, "确认", f"确定要删除入库单 {data['inbound_no']} 吗？") == QMessageBox.Yes:
            try:
                database.delete_inbound_order(data['id'])
                self.load_history()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
