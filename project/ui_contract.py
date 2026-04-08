import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QComboBox, QDateEdit, QGroupBox, 
    QHeaderView, QMessageBox, QFileDialog, QScrollArea, QDialog, QFormLayout,
    QSplitter, QFrame, QDoubleSpinBox, QTextEdit, QGridLayout, QMenu, QStackedWidget,
    QTabWidget
)
from PySide6.QtCore import Qt, QDate, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QColor, QIcon, QAction, QDesktopServices
import database
import os
import shutil
import sys
from datetime import datetime
from ui_contract_report import ContractReportWidget

COLUMN_CONFIG_FILE = "column_config.json"

def load_column_config():
    if os.path.exists(COLUMN_CONFIG_FILE):
        try:
            with open(COLUMN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_column_config(config):
    try:
        with open(COLUMN_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save column config: {e}")

# Style constants (matching existing UI)
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
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
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
QHeaderView::section:hover {
    background-color: #e9ecef;
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

class ContractListWidget(QWidget):
    open_contract_signal = Signal(int, str, str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE_MAIN)
        self.init_ui()
        self.load_data()
        self.current_contract_id = None
        self.restore_column_widths()

    def restore_column_widths(self):
        config = load_column_config()
        
        # Contract Table
        if "contract_list" in config:
            widths = config["contract_list"]
            for col, width in widths.items():
                if width > 0:
                    self.table_contract.setColumnWidth(int(col), width)
        
        # Specs Table
        if "specs_list" in config:
            widths = config["specs_list"]
            for col, width in widths.items():
                if width > 0:
                    self.table_specs.setColumnWidth(int(col), width)

    def save_table_widths(self, table_name, table_widget):
        config = load_column_config()
        widths = {}
        for i in range(table_widget.columnCount()):
            widths[str(i)] = table_widget.columnWidth(i)
        config[table_name] = widths
        save_column_config(config)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Area: Entry & Filter ---
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 1. Entry Form (Left/Top)
        entry_group = QGroupBox("合同录入")
        entry_layout = QGridLayout(entry_group)
        
        self.input_contract_no = QLineEdit()
        self.input_contract_no.setPlaceholderText("唯一标识")
        self.input_name = QLineEdit()
        self.input_category = QComboBox()
        self.input_category.addItems(["模块", "脚线", "其它"]) # TODO: Load from config
        self.input_category.setEditable(True)
        self.input_supplier = QComboBox() 
        self.input_supplier.addItems(database.fetch_suppliers())
        self.input_supplier.setEditable(True)
        
        self.input_sign_date = QDateEdit(QDate.currentDate())
        self.input_sign_date.setCalendarPopup(True)
        self.input_end_date = QDateEdit(QDate.currentDate().addYears(1))
        self.input_end_date.setCalendarPopup(True)
        
        self.input_amount = QDoubleSpinBox()
        self.input_amount.setRange(0, 999999999)
        self.input_amount.setPrefix("¥")
        
        self.input_remarks = QLineEdit()
        
        self.btn_upload = QPushButton("上传附件")
        self.btn_upload.clicked.connect(self.upload_file)
        self.lbl_file = QLabel("未选择文件")
        self.file_path = None
        
        self.btn_save = QPushButton("保存合同")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_contract)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self.clear_form)
        
        # Row 0
        entry_layout.addWidget(QLabel("合同编号*"), 0, 0)
        entry_layout.addWidget(self.input_contract_no, 0, 1)
        entry_layout.addWidget(QLabel("合同名称*"), 0, 2)
        entry_layout.addWidget(self.input_name, 0, 3)
        
        # Row 1
        entry_layout.addWidget(QLabel("类别"), 1, 0)
        entry_layout.addWidget(self.input_category, 1, 1)
        entry_layout.addWidget(QLabel("供应商"), 1, 2)
        entry_layout.addWidget(self.input_supplier, 1, 3)
        
        # Row 2
        entry_layout.addWidget(QLabel("签订日期"), 2, 0)
        entry_layout.addWidget(self.input_sign_date, 2, 1)
        entry_layout.addWidget(QLabel("截止日期"), 2, 2)
        entry_layout.addWidget(self.input_end_date, 2, 3)
        
        # Row 3
        entry_layout.addWidget(QLabel("合同金额"), 3, 0)
        entry_layout.addWidget(self.input_amount, 3, 1)
        entry_layout.addWidget(QLabel("备注"), 3, 2)
        entry_layout.addWidget(self.input_remarks, 3, 3)
        
        # Row 4
        entry_layout.addWidget(self.btn_upload, 4, 0)
        entry_layout.addWidget(self.lbl_file, 4, 1, 1, 2)
        entry_layout.addWidget(self.btn_clear, 4, 2)
        entry_layout.addWidget(self.btn_save, 4, 3)
        
        top_splitter.addWidget(entry_group)
        
        # 2. Filter Area (Right/Top)
        filter_group = QGroupBox("高级筛选")
        filter_layout = QFormLayout(filter_group)
        
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("合同号/名称模糊搜索")
        self.filter_text.textChanged.connect(self.load_data)
        
        self.filter_cat = QComboBox()
        self.filter_cat.currentTextChanged.connect(self.load_data)
        
        self.filter_sup = QComboBox()
        self.filter_sup.addItem("全部")
        self.filter_sup.addItems(database.fetch_suppliers())
        self.filter_sup.currentTextChanged.connect(self.load_data)
        
        filter_layout.addRow("关键词:", self.filter_text)
        filter_layout.addRow("类别:", self.filter_cat)
        filter_layout.addRow("供应商:", self.filter_sup)
        
        top_splitter.addWidget(filter_group)
        
        main_layout.addWidget(top_splitter)
        
        # --- Bottom Area: Data Grid ---
        # Using Splitter for Master-Detail (Contract List - Specs)
        bottom_splitter = QSplitter(Qt.Vertical)
        
        # Contract List
        self.table_contract = QTableWidget()
        self.table_contract.setColumnCount(11)
        self.table_contract.setHorizontalHeaderLabels(["ID", "合同编号", "名称", "类别", "供应商", "签订日期", "截止日期", "金额", "已执行金额", "状态", "附件合同"])
        self.table_contract.setColumnHidden(0, True)
        self.table_contract.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_contract.horizontalHeader().setStretchLastSection(True)
        self.table_contract.horizontalHeader().sectionResized.connect(lambda *args: self.save_table_widths("contract_list", self.table_contract))
        self.table_contract.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_contract.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_contract.itemClicked.connect(self.on_contract_selected)
        self.table_contract.itemDoubleClicked.connect(self.open_order_window)
        self.table_contract.cellClicked.connect(self.on_cell_clicked)
        
        self.table_contract.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_contract.customContextMenuRequested.connect(self.on_context_menu)
        
        bottom_splitter.addWidget(self.table_contract)
        
        # Specs List (Detail)
        specs_group = QGroupBox("规格明细 (选中合同后编辑)")
        specs_layout = QVBoxLayout(specs_group)
        
        specs_toolbar = QHBoxLayout()
        self.btn_add_spec = QPushButton("添加规格")
        self.btn_add_spec.clicked.connect(self.add_spec_row)
        self.btn_save_specs = QPushButton("保存明细")
        self.btn_save_specs.clicked.connect(self.save_specs)
        self.btn_del_spec = QPushButton("删除选中")
        self.btn_del_spec.clicked.connect(self.delete_spec_row)
        
        specs_toolbar.addWidget(self.btn_add_spec)
        specs_toolbar.addWidget(self.btn_del_spec)
        specs_toolbar.addStretch()
        specs_toolbar.addWidget(self.btn_save_specs)
        
        specs_layout.addLayout(specs_toolbar)
        
        self.table_specs = QTableWidget()
        self.table_specs.setColumnCount(8) # ID, Model, Unit, Qty, Price, Total, Executed, Remaining
        self.table_specs.setHorizontalHeaderLabels(["ID", "规格型号", "单位", "数量", "含税单价", "含税总价", "已执行", "剩余"])
        self.table_specs.setColumnHidden(0, True)
        self.table_specs.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_specs.horizontalHeader().setStretchLastSection(True)
        self.table_specs.horizontalHeader().sectionResized.connect(lambda *args: self.save_table_widths("specs_list", self.table_specs))
        # Enable editing for some columns
        self.table_specs.itemChanged.connect(self.on_spec_changed)
        
        specs_layout.addWidget(self.table_specs)
        
        specs_widget = QWidget()
        specs_widget.setLayout(specs_layout)
        bottom_splitter.addWidget(specs_widget)
        
        main_layout.addWidget(bottom_splitter)
        
        # Set splitter sizes
        bottom_splitter.setSizes([300, 200])
        
        self.refresh_categories()

    def refresh_categories(self):
        cats = database.fetch_contract_categories()
        
        # Update input_category
        current_input = self.input_category.currentText()
        self.input_category.clear()
        self.input_category.addItems(cats)
        self.input_category.setCurrentText(current_input)
        
        # Update filter_cat
        current_filter = self.filter_cat.currentText()
        self.filter_cat.clear()
        self.filter_cat.addItem("全部")
        self.filter_cat.addItems(cats)
        if current_filter:
            self.filter_cat.setCurrentText(current_filter)

    def refresh_suppliers(self):
        suppliers = database.fetch_suppliers()
        
        # Update input_supplier
        current_input = self.input_supplier.currentText()
        self.input_supplier.clear()
        self.input_supplier.addItems(suppliers)
        self.input_supplier.setCurrentText(current_input)
        
        # Update filter_sup
        current_filter = self.filter_sup.currentText()
        self.filter_sup.clear()
        self.filter_sup.addItem("全部")
        self.filter_sup.addItems(suppliers)
        if current_filter:
            self.filter_sup.setCurrentText(current_filter)

    def upload_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择PDF文件", "", "PDF Files (*.pdf)")
        if fname:
            # Check size
            size = os.path.getsize(fname)
            if size > 10 * 1024 * 1024:
                QMessageBox.warning(self, "错误", "文件大小超过10MB")
                return
            self.file_path = fname
            self.lbl_file.setText(os.path.basename(fname))

    def clear_form(self):
        self.input_contract_no.clear()
        self.input_name.clear()
        self.input_amount.setValue(0)
        self.input_remarks.clear()
        self.file_path = None
        self.lbl_file.setText("未选择文件")
        self.current_contract_id = None
        self.current_editing_id = None
        self.btn_save.setText("保存合同")

    def save_contract(self):
        no = self.input_contract_no.text().strip()
        name = self.input_name.text().strip()
        if not no or not name:
            QMessageBox.warning(self, "错误", "合同编号和名称必填")
            return
            
        try:
            cid = getattr(self, 'current_editing_id', None)
            
            final_path = self.file_path
            if self.file_path and cid:
                target_dir = os.path.join(os.path.dirname(database.DB_PATH), "合同附件")
                if not os.path.abspath(self.file_path).startswith(os.path.abspath(target_dir)):
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    new_fname = f"{no}_{os.path.basename(self.file_path)}"
                    new_path = os.path.join(target_dir, new_fname)
                    shutil.copy(self.file_path, new_path)
                    final_path = new_path
                    database.save_contract_attachment(cid, os.path.basename(self.file_path), new_path)
            elif self.file_path and not cid:
                pass 

            contract_data = {
                'id': cid,
                'contract_number': no,
                'name': name,
                'category': self.input_category.currentText(),
                'supplier': self.input_supplier.currentText(),
                'sign_date': self.input_sign_date.text(),
                'end_date': self.input_end_date.text(),
                'amount': self.input_amount.value(),
                'remarks': self.input_remarks.text(),
                'status': '执行中',
                'attachment': final_path
            }
            database.save_contract(contract_data)
            
            if not cid and self.file_path:
                 contracts = database.fetch_contracts(filter_text=no)
                 if contracts:
                    new_cid = contracts[0][0]
                    target_dir = os.path.join(os.path.dirname(database.DB_PATH), "合同附件")
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    new_fname = f"{no}_{os.path.basename(self.file_path)}"
                    new_path = os.path.join(target_dir, new_fname)
                    shutil.copy(self.file_path, new_path)
                    database.save_contract_attachment(new_cid, os.path.basename(self.file_path), new_path)
                    contract_data['id'] = new_cid
                    contract_data['attachment'] = new_path
                    database.save_contract(contract_data)

            QMessageBox.information(self, "成功", "合同保存成功")
            self.load_data()
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def on_cell_clicked(self, row, column):
        # 附件合同列是第10列 (从0开始)
        if column == 10:
            item = self.table_contract.item(row, column)
            if item and item.text():
                full_path = item.data(Qt.UserRole)
                if full_path and os.path.exists(full_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
                else:
                    QMessageBox.warning(self, "提示", "文件不存在或路径无效")

    def load_data(self):
        if self.table_contract.columnCount() < 11:
            self.table_contract.setColumnCount(11)
            self.table_contract.setHorizontalHeaderLabels(["ID", "合同编号", "名称", "类别", "供应商", "签订日期", "截止日期", "金额", "已执行金额", "状态", "附件合同"])
            self.table_contract.setColumnHidden(0, True)
            self.table_contract.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.table_contract.horizontalHeader().setStretchLastSection(True)
            self.restore_column_widths()

        self.table_contract.setRowCount(0)
        contracts = database.fetch_contracts(
            filter_text=self.filter_text.text(),
            category=self.filter_cat.currentText(),
            supplier=self.filter_sup.currentText()
        )
        for row_data in contracts:
            row = self.table_contract.rowCount()
            self.table_contract.insertRow(row)
            # Data from DB:
            # 0: id, 1: no, 2: name, 3: cat, 4: sup, 5: sign, 6: end, 7: amount, 8: status, 9: attachment, 10: executed_amount
            
            self.table_contract.setItem(row, 0, QTableWidgetItem(str(row_data[0]))) # ID
            self.table_contract.setItem(row, 1, QTableWidgetItem(str(row_data[1]))) # No
            self.table_contract.setItem(row, 2, QTableWidgetItem(str(row_data[2]))) # Name
            self.table_contract.setItem(row, 3, QTableWidgetItem(str(row_data[3]))) # Cat
            self.table_contract.setItem(row, 4, QTableWidgetItem(str(row_data[4]))) # Sup
            self.table_contract.setItem(row, 5, QTableWidgetItem(str(row_data[5]))) # Sign
            self.table_contract.setItem(row, 6, QTableWidgetItem(str(row_data[6]))) # End
            self.table_contract.setItem(row, 7, QTableWidgetItem(str(row_data[7]))) # Amount
            
            # Executed Amount (Index 10)
            exec_amt = row_data[10] if len(row_data) > 10 and row_data[10] is not None else 0.0
            self.table_contract.setItem(row, 8, QTableWidgetItem(str(exec_amt)))

            self.table_contract.setItem(row, 9, QTableWidgetItem(str(row_data[8]))) # Status
            
            # Approval Doc Column (Index 9)
            doc_path = row_data[9] if len(row_data) > 9 else ""
            if doc_path:
                full_name = os.path.basename(doc_path)
                display_name = full_name
                
                contract_no = str(row_data[1])
                if full_name.startswith(f"{contract_no}_"):
                    display_name = full_name[len(contract_no)+1:]
                
                if display_name.lower().endswith(".pdf"):
                    display_name = display_name[:-4]
                    
                item_doc = QTableWidgetItem(display_name)
                item_doc.setData(Qt.UserRole, doc_path) 
                item_doc.setForeground(QColor("blue"))
                font = item_doc.font()
                font.setUnderline(True)
                item_doc.setFont(font)
                self.table_contract.setItem(row, 10, item_doc)
            else:
                self.table_contract.setItem(row, 10, QTableWidgetItem(""))
                    
        self.table_specs.setRowCount(0)
        self.current_contract_id = None

    def on_contract_selected(self, item):
        row = item.row()
        cid = int(self.table_contract.item(row, 0).text())
        self.current_contract_id = cid
        self.load_specs(cid)

    def on_context_menu(self, pos):
        item = self.table_contract.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        cid = int(self.table_contract.item(row, 0).text())
        self.table_contract.selectRow(row)
        self.on_contract_selected(item)
        
        menu = QMenu(self)
        edit_action = menu.addAction("修改合同")
        delete_action = menu.addAction("删除合同")
        
        action = menu.exec(self.table_contract.mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_contract(row)
        elif action == delete_action:
            self.delete_contract(cid)

    def edit_contract(self, row):
        cid = int(self.table_contract.item(row, 0).text())
        contract = database.get_contract_by_id(cid)
        if not contract:
            return
            
        self.input_contract_no.setText(contract[1])
        self.input_name.setText(contract[2])
        self.input_category.setCurrentText(contract[3])
        self.input_supplier.setCurrentText(contract[4])
        
        sign_date_str = contract[5]
        self.input_sign_date.setDate(QDate.fromString(sign_date_str, "yyyy-MM-dd") if sign_date_str else QDate.currentDate())
        
        end_date_str = contract[6]
        self.input_end_date.setDate(QDate.fromString(end_date_str, "yyyy-MM-dd") if end_date_str else QDate.currentDate())
        
        self.input_amount.setValue(contract[7] if contract[7] else 0.0)
        self.input_remarks.setText(contract[8] if contract[8] else "")
        
        doc_path = contract[10]
        if doc_path and os.path.exists(doc_path):
            self.file_path = doc_path
            self.lbl_file.setText(os.path.basename(doc_path))
        else:
            self.file_path = None
            self.lbl_file.setText("未选择文件")
            
        self.current_editing_id = cid
        self.btn_save.setText("更新合同")

    def delete_contract(self, cid):
        if QMessageBox.question(self, "确认", "确定删除该合同及其所有关联数据？") == QMessageBox.Yes:
            database.delete_contract(cid)
            self.load_data()
            self.clear_form()

    def load_specs(self, contract_id):
        self.table_specs.setRowCount(0)
        specs = database.fetch_contract_specs(contract_id)
        for sp in specs:
            row = self.table_specs.rowCount()
            self.table_specs.insertRow(row)
            
            self.table_specs.setItem(row, 0, QTableWidgetItem(str(sp[0])))
            self.table_specs.setItem(row, 1, QTableWidgetItem(str(sp[1])))
            self.table_specs.setItem(row, 2, QTableWidgetItem(str(sp[2])))
            self.table_specs.setItem(row, 3, QTableWidgetItem(str(sp[3])))
            self.table_specs.setItem(row, 4, QTableWidgetItem(str(sp[4])))
            total_item = QTableWidgetItem(str(sp[5]))
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.table_specs.setItem(row, 5, total_item)
            exec_item = QTableWidgetItem(str(sp[6]))
            exec_item.setFlags(exec_item.flags() & ~Qt.ItemIsEditable)
            self.table_specs.setItem(row, 6, exec_item)
            rem = float(sp[3]) - float(sp[6])
            rem_item = QTableWidgetItem(str(rem))
            rem_item.setFlags(rem_item.flags() & ~Qt.ItemIsEditable)
            self.table_specs.setItem(row, 7, rem_item)

    def add_spec_row(self):
        if not self.current_contract_id:
            QMessageBox.warning(self, "提示", "请先选择一个合同")
            return
        row = self.table_specs.rowCount()
        self.table_specs.insertRow(row)
        self.table_specs.setItem(row, 0, QTableWidgetItem("")) 
        self.table_specs.setItem(row, 1, QTableWidgetItem(""))
        self.table_specs.setItem(row, 2, QTableWidgetItem("个"))
        self.table_specs.setItem(row, 3, QTableWidgetItem("0"))
        self.table_specs.setItem(row, 4, QTableWidgetItem("0"))
        self.table_specs.setItem(row, 5, QTableWidgetItem("0"))
        self.table_specs.setItem(row, 6, QTableWidgetItem("0"))
        self.table_specs.setItem(row, 7, QTableWidgetItem("0"))

    def on_spec_changed(self, item):
        row = item.row()
        col = item.column()
        if col in (3, 4):
            try:
                item_qty = self.table_specs.item(row, 3)
                item_price = self.table_specs.item(row, 4)
                
                if item_qty is None or item_price is None:
                    return

                qty = float(item_qty.text() or 0)
                price = float(item_price.text() or 0)
                total = qty * price
                
                item_total = self.table_specs.item(row, 5)
                if item_total:
                    item_total.setText(f"{total:.2f}")
                
                item_exec = self.table_specs.item(row, 6)
                item_rem = self.table_specs.item(row, 7)
                
                if item_exec and item_rem:
                    exec_qty = float(item_exec.text() or 0)
                    item_rem.setText(f"{qty - exec_qty:.2f}")
            except ValueError:
                pass

    def save_specs(self):
        if not self.current_contract_id:
            return
        
        specs_data = []
        for row in range(self.table_specs.rowCount()):
            sid_item = self.table_specs.item(row, 0)
            sid = int(sid_item.text()) if sid_item.text() else None
            
            model = self.table_specs.item(row, 1).text()
            unit = self.table_specs.item(row, 2).text()
            try:
                qty = float(self.table_specs.item(row, 3).text())
                price = float(self.table_specs.item(row, 4).text())
                total = float(self.table_specs.item(row, 5).text())
            except ValueError:
                QMessageBox.warning(self, "错误", f"第 {row+1} 行数值格式错误")
                return
            
            if not model:
                continue
                
            specs_data.append((sid, model, unit, qty, price, total))
            
        try:
            database.save_contract_specs_transaction(self.current_contract_id, specs_data)
            QMessageBox.information(self, "成功", "规格明细已保存")
            self.load_specs(self.current_contract_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def delete_spec_row(self):
        rows = sorted(set(index.row() for index in self.table_specs.selectedIndexes()), reverse=True)
        for row in rows:
            self.table_specs.removeRow(row)

    def open_order_window(self, item):
        row = item.row()
        cid = int(self.table_contract.item(row, 0).text())
        cno = self.table_contract.item(row, 1).text()
        name = self.table_contract.item(row, 2).text()
        
        self.open_contract_signal.emit(cid, cno, name)


class PurchPlanSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择采购计划")
        self.resize(800, 500)
        self.selected_no = None
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter
        filter_layout = QHBoxLayout()
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("输入单号、任务名称或单位进行搜索...")
        self.filter_text.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.filter_text)
        layout.addLayout(filter_layout)
        
        # List
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["采购单号", "任务名称", "单位", "日期", "类别"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.on_ok)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def load_data(self):
        text = self.filter_text.text().strip()
        # Using database.fetch_orders(number_filter=...)
        # fetch_orders signature: number_filter, task_filter, unit_filter, month_filter
        # We want to search across multiple fields with one text
        # database.fetch_orders currently does strict AND. 
        # Let's use a specialized fetch or modify fetch_orders.
        # Let's use fetch_orders but try to pass text to multiple filters? No, that's AND.
        # We need OR logic for search bar.
        # Let's fetch all (or limit) and filter in Python if result set is small, 
        # OR add a new DB function `search_orders_fuzzy`.
        
        # For better performance, let's use a new DB function.
        orders = database.search_orders_fuzzy(text)
        
        self.table.setRowCount(0)
        for row in orders:
            # row: number, task_name, unit, date, category
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row[0]))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r, 3, QTableWidgetItem(row[3]))
            
            cat_name = database.category_display_from_code(row[4])
            self.table.setItem(r, 4, QTableWidgetItem(cat_name))

    def on_item_double_clicked(self, item):
        self.on_ok()

    def on_ok(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_no = self.table.item(row, 0).text()
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请先选择一条记录")

    def get_selected(self):
        return self.selected_no


class ContractOrderWidget(QWidget):
    back_signal = Signal()

    def __init__(self, contract_id, contract_no, contract_name, parent=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.contract_no = contract_no
        self.contract_name = contract_name
        
        self.specs_map = {} # ID -> (Model, Unit, Price, Remaining)
        self.spec_items = [] # List of (ID, DisplayText) for combos
        
        self.original_order_ids = set() # Track IDs loaded for editing

        self.init_ui()
        self.load_specs_data()
        self.load_orders()
        self.restore_column_widths()
        
        # Initial empty row
        self.add_input_row()

    def restore_column_widths(self):
        config = load_column_config()
        if "order_list" in config:
            widths = config["order_list"]
            for col, width in widths.items():
                if width > 0:
                    self.table.setColumnWidth(int(col), width)
                    
        # Input Table Widths
        if "order_input_table" in config:
            widths = config["order_input_table"]
            for col, width in widths.items():
                if width > 0:
                    self.input_table.setColumnWidth(int(col), width)

    def save_table_widths(self, *args):
        config = load_column_config()
        widths = {}
        for i in range(self.table.columnCount()):
            widths[str(i)] = self.table.columnWidth(i)
        config["order_list"] = widths
        save_column_config(config)

    def save_input_table_widths(self, *args):
        config = load_column_config()
        widths = {}
        for i in range(self.input_table.columnCount()):
            widths[str(i)] = self.input_table.columnWidth(i)
        config["order_input_table"] = widths
        save_column_config(config)

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- 1. Top Bar ---
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton("返回")
        self.btn_back.setFixedSize(80, 40)
        self.btn_back.clicked.connect(self.back_signal.emit)
        
        title_lbl = QLabel(f"订单执行 - {self.contract_no} {self.contract_name}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        top_bar.addWidget(self.btn_back)
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # --- 2. Batch Entry Area ---
        entry_group = QGroupBox("批量新增/编辑订单")
        entry_layout = QVBoxLayout(entry_group)
        
        # 2.1 Common Header Fields
        header_grid = QGridLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.order_no = QLineEdit()
        self.order_no.setPlaceholderText("订单编号 (批量应用)")
        
        self.sales_no = QLineEdit()
        self.prod_no = QLineEdit()
        
        # Purch Plan Selector
        self.purch_no = QLineEdit()
        self.purch_no.setPlaceholderText("双击选择采购计划")
        self.purch_no.mouseDoubleClickEvent = self.open_purch_plan_selector
        
        header_grid.addWidget(QLabel("日期:"), 0, 0)
        header_grid.addWidget(self.date_edit, 0, 1)
        header_grid.addWidget(QLabel("订单编号:"), 0, 2)
        header_grid.addWidget(self.order_no, 0, 3)
        header_grid.addWidget(QLabel("销售单号:"), 0, 4)
        header_grid.addWidget(self.sales_no, 0, 5)
        
        header_grid.addWidget(QLabel("生产单号:"), 1, 0)
        header_grid.addWidget(self.prod_no, 1, 1)
        header_grid.addWidget(QLabel("采购计划:"), 1, 2)
        header_grid.addWidget(self.purch_no, 1, 3)
        
        entry_layout.addLayout(header_grid)
        
        # 2.2 Toolbar
        tool_layout = QHBoxLayout()
        btn_add_row = QPushButton("添加行")
        btn_add_row.clicked.connect(lambda: self.add_input_row())
        
        btn_import = QPushButton("导入模板")
        btn_import.clicked.connect(self.import_template)
        
        btn_clear = QPushButton("清空录入")
        btn_clear.clicked.connect(self.clear_entry_form)
        
        tool_layout.addWidget(btn_add_row)
        tool_layout.addWidget(btn_import)
        tool_layout.addWidget(btn_clear)
        tool_layout.addStretch()
        
        entry_layout.addLayout(tool_layout)
        
        # 2.3 Input Table
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(8) 
        # Columns: Spec, Unit, Qty, Price, Total, Remark, Action, HIDDEN_ID
        self.input_table.setHorizontalHeaderLabels(["规格型号*", "单位", "数量*", "单价*", "总价", "备注", "操作", "ID"])
        self.input_table.setColumnHidden(7, True) # Hidden ID
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.input_table.horizontalHeader().setStretchLastSection(True)
        self.input_table.horizontalHeader().sectionResized.connect(self.save_input_table_widths)
        self.input_table.setMinimumHeight(200)
        entry_layout.addWidget(self.input_table)
        
        # 2.4 Save Button
        self.btn_save_all = QPushButton("保存所有记录")
        self.btn_save_all.setObjectName("primary")
        self.btn_save_all.setMinimumHeight(40)
        self.btn_save_all.clicked.connect(self.save_batch_orders)
        entry_layout.addWidget(self.btn_save_all)
        
        layout.addWidget(entry_group)
        
        # --- 3. Filter Area ---
        filter_group = QGroupBox("筛选查询")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(10, 5, 10, 5)
        
        self.filter_no = QLineEdit()
        self.filter_no.setPlaceholderText("订单编号")
        self.filter_no.textChanged.connect(self.load_orders)
        
        self.filter_spec = QLineEdit()
        self.filter_spec.setPlaceholderText("规格型号")
        self.filter_spec.textChanged.connect(self.load_orders)
        
        self.chk_date = QGroupBox("日期范围")
        self.chk_date.setCheckable(True)
        self.chk_date.setChecked(False)
        date_layout = QHBoxLayout(self.chk_date)
        date_layout.setContentsMargins(5, 5, 5, 5)
        
        self.filter_date_start = QDateEdit(QDate.currentDate().addMonths(-1))
        self.filter_date_start.setCalendarPopup(True)
        self.filter_date_start.setDisplayFormat("yyyy-MM-dd")
        self.filter_date_end = QDateEdit(QDate.currentDate())
        self.filter_date_end.setCalendarPopup(True)
        self.filter_date_end.setDisplayFormat("yyyy-MM-dd")
        
        date_layout.addWidget(QLabel("从"))
        date_layout.addWidget(self.filter_date_start)
        date_layout.addWidget(QLabel("到"))
        date_layout.addWidget(self.filter_date_end)
        
        self.chk_date.toggled.connect(self.load_orders)
        self.filter_date_start.dateChanged.connect(self.load_orders)
        self.filter_date_end.dateChanged.connect(self.load_orders)
        
        filter_layout.addWidget(QLabel("订单编号:"))
        filter_layout.addWidget(self.filter_no)
        filter_layout.addWidget(QLabel("规格:"))
        filter_layout.addWidget(self.filter_spec)
        filter_layout.addWidget(self.chk_date)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # --- 4. List ---
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels(["ID", "日期", "订单编号", "规格", "数量", "单价", "总价", "销售单", "生产单", "采购计划单号", "状态", "备注", "Spec_ID"])
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(12, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().sectionResized.connect(self.save_table_widths)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_context_menu)
        
        layout.addWidget(self.table)
        
        btn_del = QPushButton("删除选中记录")
        btn_del.clicked.connect(self.delete_order)
        layout.addWidget(btn_del)

    def open_purch_plan_selector(self, event):
        dialog = PurchPlanSelector(self)
        if dialog.exec() == QDialog.Accepted:
            selected = dialog.get_selected()
            if selected:
                self.purch_no.setText(selected)

    def load_specs_data(self):
        specs = database.fetch_contract_specs(self.contract_id)
        self.specs_map = {}
        self.spec_items = []
        for sp in specs:
            # id, model, unit, qty, price, total, exec
            sid, model, unit, qty, price, total, exec_qty = sp
            rem = qty - exec_qty
            label = f"{model} (余: {rem})"
            self.spec_items.append((sid, label))
            self.specs_map[sid] = (model, unit, price, rem)
            
        # Refresh combos in input table if any
        for row in range(self.input_table.rowCount()):
            combo = self.input_table.cellWidget(row, 0)
            if isinstance(combo, QComboBox):
                current_sid = combo.currentData()
                combo.blockSignals(True)
                combo.clear()
                for sid, label in self.spec_items:
                    combo.addItem(label, sid)
                if current_sid:
                    index = combo.findData(current_sid)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                combo.blockSignals(False)

    def add_input_row(self, spec_id=None, qty=0, price=0, remark="", oid=None, status="新增"):
        row = self.input_table.rowCount()
        self.input_table.insertRow(row)
        
        # 0: Spec Combo
        combo = QComboBox()
        combo.setEditable(True)
        # Add items
        for sid, label in self.spec_items:
            combo.addItem(label, sid)
        
        if spec_id:
            idx = combo.findData(spec_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        else:
            combo.setCurrentIndex(-1)
            
        combo.currentIndexChanged.connect(lambda idx, r=row: self.on_row_spec_changed(r))
        self.input_table.setCellWidget(row, 0, combo)
        
        # 1: Unit (ReadOnly)
        unit_item = QTableWidgetItem("")
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        self.input_table.setItem(row, 1, unit_item)
        
        # 2: Qty
        sb_qty = QDoubleSpinBox()
        sb_qty.setRange(-999999999.99, 999999999.99)
        sb_qty.setGroupSeparatorShown(True)
        sb_qty.setDecimals(2)
        sb_qty.setValue(qty)
        sb_qty.valueChanged.connect(lambda v, r=row: self.on_row_value_changed(r))
        self.input_table.setCellWidget(row, 2, sb_qty)
        
        # 3: Price
        sb_price = QDoubleSpinBox()
        sb_price.setRange(-999999999.99, 999999999.99)
        sb_price.setGroupSeparatorShown(True)
        sb_price.setDecimals(2)
        sb_price.setValue(price)
        sb_price.valueChanged.connect(lambda v, r=row: self.on_row_value_changed(r))
        self.input_table.setCellWidget(row, 3, sb_price)
        
        # 4: Total (ReadOnly)
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        self.input_table.setItem(row, 4, total_item)
        
        # 5: Remark
        remark_item = QTableWidgetItem(remark)
        self.input_table.setItem(row, 5, remark_item)
        
        # 6: Action
        btn_del = QPushButton("删除")
        btn_del.setStyleSheet("color: red;")
        # Pass button instance explicitly to avoid lambda capture issues or sender() ambiguity
        btn_del.clicked.connect(lambda checked=False, btn=btn_del: self.delete_input_row(btn))
        self.input_table.setCellWidget(row, 6, btn_del)
        
        # 7: ID (Hidden)
        id_item = QTableWidgetItem(str(oid) if oid else "")
        id_item.setData(Qt.UserRole, status)
        self.input_table.setItem(row, 7, id_item)
        
        # Trigger updates
        self.on_row_spec_changed(row)
        self.on_row_value_changed(row)

    def delete_input_row(self, btn_widget):
        # Find which row contains the button widget
        target_row = -1
        
        # Method 1: Use indexAt (more robust if widget is in layout)
        # But setCellWidget places it directly.
        # Check all rows
        for r in range(self.input_table.rowCount()):
            if self.input_table.cellWidget(r, 6) == btn_widget:
                target_row = r
                break
        
        if target_row >= 0:
            self.input_table.removeRow(target_row)

    def on_row_spec_changed(self, row_idx):
        # Try to find row by sender to handle row shifts
        sender = self.sender()
        target_row = -1
        
        if sender:
            for r in range(self.input_table.rowCount()):
                if self.input_table.cellWidget(r, 0) == sender:
                    target_row = r
                    break
        
        # Fallback to provided row_idx (useful for tests or initial calls)
        if target_row < 0:
            target_row = row_idx
            
        if target_row < 0 or target_row >= self.input_table.rowCount():
            return
 
        combo = self.input_table.cellWidget(target_row, 0)
        if not combo: return
        
        sid = combo.currentData()
        
        if sid in self.specs_map:
            model, unit, price, rem = self.specs_map[sid]
            # Update Unit
            if self.input_table.item(target_row, 1):
                self.input_table.item(target_row, 1).setText(unit)
            
            # Update Price (only if 0)
            sb_price = self.input_table.cellWidget(target_row, 3)
            if sb_price and sb_price.value() == 0:
                sb_price.setValue(price)
                
        self.on_row_value_changed(target_row)

    def on_row_value_changed(self, row_idx):
        # Find row by sender
        sender = self.sender()
        target_row = -1
        
        if sender:
            for r in range(self.input_table.rowCount()):
                w2 = self.input_table.cellWidget(r, 2)
                w3 = self.input_table.cellWidget(r, 3)
                if w2 == sender or w3 == sender:
                    target_row = r
                    break
        
        if target_row < 0:
            target_row = row_idx
            
        if target_row < 0 or target_row >= self.input_table.rowCount():
            return
            
        sb_qty = self.input_table.cellWidget(target_row, 2)
        sb_price = self.input_table.cellWidget(target_row, 3)
        if not sb_qty or not sb_price: return
        
        total = sb_qty.value() * sb_price.value()
        item_total = self.input_table.item(target_row, 4)
        if item_total:
            item_total.setText(f"{total:,.2f}")

    def clear_entry_form(self):
        self.date_edit.setDate(QDate.currentDate())
        self.order_no.clear()
        self.order_no.setReadOnly(False) # Unlock
        self.sales_no.clear()
        self.prod_no.clear()
        self.purch_no.clear()
        self.clear_input_rows()
        self.original_order_ids.clear() # Reset tracked IDs
        self.add_input_row() 

    def clear_input_rows(self):
        self.input_table.setRowCount(0)

    def save_batch_orders(self):
        common_order_no = self.order_no.text().strip()
        common_sales = self.sales_no.text().strip()
        common_prod = self.prod_no.text().strip()
        common_purch = self.purch_no.text().strip()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        
        orders_to_save = []
        current_ids = set()
        
        rows = self.input_table.rowCount()
        if rows == 0:
            return

        for r in range(rows):
            combo = self.input_table.cellWidget(r, 0)
            if not combo: continue
            sid = combo.currentData()
            if not sid:
                continue 
                
            sb_qty = self.input_table.cellWidget(r, 2)
            qty = sb_qty.value()
                
            sb_price = self.input_table.cellWidget(r, 3)
            price = sb_price.value()
            
            item_remark = self.input_table.item(r, 5)
            remark = item_remark.text() if item_remark else ""
            
            item_id = self.input_table.item(r, 7)
            oid = int(item_id.text()) if item_id and item_id.text() else None
            status = item_id.data(Qt.UserRole) or "新增"
            
            if oid:
                current_ids.add(oid)
            
            order_data = {
                'id': oid,
                'contract_id': self.contract_id,
                'spec_id': sid,
                'order_date': date_str,
                'order_no': common_order_no,
                'sales_order': common_sales,
                'prod_order': common_prod,
                'purch_plan_no': common_purch,
                'quantity': qty,
                'unit_price': price,
                'total_price': round(qty * price, 2),
                'status': status,
                'remarks': remark
            }
            orders_to_save.append(order_data)
            
        if not orders_to_save and not self.original_order_ids:
            QMessageBox.warning(self, "提示", "没有有效的数据可保存")
            return
            
        try:
            # 1. Handle Deletions (IDs in original but not in current)
            ids_to_delete = self.original_order_ids - current_ids
            deleted_count = 0
            for oid in ids_to_delete:
                database.delete_contract_order(oid)
                database.save_operation_log(common_order_no, "Order", str(oid), "Deleted", "User", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                deleted_count += 1
            
            # 2. Handle Upserts
            saved_count = 0
            for data in orders_to_save:
                is_update = bool(data.get('id'))
                database.save_contract_order(data)
                
                # Log
                op_type = "Update" if is_update else "Insert"
                database.save_operation_log(common_order_no, "Order", "", f"{op_type} Spec {data['spec_id']}", "User", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                saved_count += 1
                
            msg = f"成功保存 {saved_count} 条记录"
            if deleted_count > 0:
                msg += f"\n删除了 {deleted_count} 条原有记录"
                
            QMessageBox.information(self, "成功", msg)
            self.load_orders()
            self.clear_entry_form()
            
            # Highlight modified row? We just refreshed. 
            # Could try to find order_no and select.
            
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        self.table.selectRow(row)
        
        menu = QMenu(self)
        edit_action = menu.addAction("修改订单")
        delete_action = menu.addAction("删除订单")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_order(row)
        elif action == delete_action:
            self.delete_order()

    def edit_order(self, row):
        order_no = self.table.item(row, 2).text()
        
        # 1. Fetch all sibling orders
        orders = database.fetch_contract_orders_by_no_exact(self.contract_id, order_no)
        if not orders:
            QMessageBox.warning(self, "错误", f"未找到订单 {order_no} 的详细信息")
            return
            
        # 2. Populate Header (from first record)
        first_order = orders[0]
        # 0:id, 1:date, 2:no, 3:model, 4:qty, 5:price, 6:total, 
        # 7:sales, 8:prod, 9:purch, 10:status, 11:remarks, 12:spec_id
        
        date_str = first_order[1]
        qdate = QDate.fromString(date_str, "yyyy-MM-dd")
        if qdate.isValid():
            self.date_edit.setDate(qdate)
            
        self.order_no.setText(first_order[2])
        self.sales_no.setText(first_order[7])
        self.prod_no.setText(first_order[8])
        self.purch_no.setText(first_order[9])
        
        # Lock Order No
        self.order_no.setReadOnly(True)
        
        # 3. Populate Rows
        self.clear_input_rows()
        self.original_order_ids.clear()
        
        for order in orders:
            oid = order[0]
            spec_id = order[12]
            qty = float(order[4] or 0)
            price = float(order[5] or 0)
            status = order[10] or "新增"
            remark = order[11] or ""
            
            self.add_input_row(spec_id, qty, price, remark, oid, status)
            self.original_order_ids.add(oid)
        
        QMessageBox.information(self, "提示", f"订单 {order_no} 的 {len(orders)} 条记录已加载。修改后点击保存。")

    def delete_order(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not rows:
            return
        
        if QMessageBox.question(self, "确认", "确定删除选中记录？") != QMessageBox.Yes:
            return
            
        for row in rows:
            oid = int(self.table.item(row, 0).text())
            database.delete_contract_order(oid)
            
        self.load_orders()

    def import_template(self):
        # Simple implementation
        QMessageBox.information(self, "功能", "请使用Excel模板导入数据（待实现）")

    def load_orders(self):
        self.table.setRowCount(0)
        
        f_no = self.filter_no.text().strip()
        f_spec = self.filter_spec.text().strip()
        f_start = None
        f_end = None
        if self.chk_date.isChecked():
            f_start = self.filter_date_start.text()
            f_end = self.filter_date_end.text()
            
        orders = database.fetch_contract_orders(
            self.contract_id, 
            filter_no=f_no,
            date_from=f_start,
            date_to=f_end,
            filter_spec=f_spec
        )
        
        def parse_date_sort(row):
            d_str = row[1]
            if not d_str: return datetime.min
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(d_str, fmt)
                except ValueError:
                    continue
            return datetime.min

        orders.sort(key=parse_date_sort, reverse=True)

        for row_data in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 0:id, 1:date, 2:no, 3:model, 4:qty, 5:price, 6:total, 7:sales, 8:prod, 9:purch, 10:status, 11:remark, 12:spec_id
            self.table.setItem(row, 0, QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row, 1, QTableWidgetItem(str(row_data[1])))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data[2])))
            self.table.setItem(row, 3, QTableWidgetItem(str(row_data[3]))) 
            
            # Format Quantity
            qty_val = float(str(row_data[4]) or 0)
            self.table.setItem(row, 4, QTableWidgetItem(f"{qty_val:,.2f}")) 
            
            # Format Price
            price_val = float(str(row_data[5]) or 0)
            self.table.setItem(row, 5, QTableWidgetItem(f"{price_val:,.2f}")) 
            
            # Format Total
            total_val = float(str(row_data[6]) or 0)
            self.table.setItem(row, 6, QTableWidgetItem(f"{total_val:,.2f}")) 
            
            self.table.setItem(row, 7, QTableWidgetItem(str(row_data[7])))
            self.table.setItem(row, 8, QTableWidgetItem(str(row_data[8])))
            self.table.setItem(row, 9, QTableWidgetItem(str(row_data[9])))
            
            # Status
            status_item = QTableWidgetItem(str(row_data[10] or "新增"))
            if row_data[10] == "已入库":
                status_item.setForeground(QColor("green"))
            elif row_data[10] == "部分入库":
                status_item.setForeground(QColor("blue"))
            self.table.setItem(row, 10, status_item)
            
            self.table.setItem(row, 11, QTableWidgetItem(str(row_data[11]))) 
            self.table.setItem(row, 12, QTableWidgetItem(str(row_data[12])))


class SupplierManagerWidget(QWidget):
    suppliers_changed = Signal()
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Form area
        form_group = QGroupBox("新增/编辑供应商")
        form_layout = QGridLayout()
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("供应商简称 (必填)")
        self.input_full_name = QLineEdit()
        self.input_full_name.setPlaceholderText("供应商全称")
        self.input_bank_name = QLineEdit()
        self.input_bank_name.setPlaceholderText("开户行")
        self.input_bank_account = QLineEdit()
        self.input_bank_account.setPlaceholderText("账号")
        self.input_contact_person = QLineEdit()
        self.input_contact_person.setPlaceholderText("联系人")
        self.input_contact_phone = QLineEdit()
        self.input_contact_phone.setPlaceholderText("联系电话")
        self.input_remarks = QLineEdit()
        self.input_remarks.setPlaceholderText("备注")
        
        form_layout.addWidget(QLabel("简称:"), 0, 0)
        form_layout.addWidget(self.input_name, 0, 1)
        form_layout.addWidget(QLabel("全称:"), 0, 2)
        form_layout.addWidget(self.input_full_name, 0, 3)
        form_layout.addWidget(QLabel("开户行:"), 1, 0)
        form_layout.addWidget(self.input_bank_name, 1, 1)
        form_layout.addWidget(QLabel("账号:"), 1, 2)
        form_layout.addWidget(self.input_bank_account, 1, 3)
        form_layout.addWidget(QLabel("联系人:"), 2, 0)
        form_layout.addWidget(self.input_contact_person, 2, 1)
        form_layout.addWidget(QLabel("联系电话:"), 2, 2)
        form_layout.addWidget(self.input_contact_phone, 2, 3)
        form_layout.addWidget(QLabel("备注:"), 3, 0)
        form_layout.addWidget(self.input_remarks, 3, 1, 1, 3)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存/更新")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_clear = QPushButton("清空/新增")
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_delete = QPushButton("删除")
        self.btn_delete.clicked.connect(self.delete_data)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_save)
        
        form_vlayout = QVBoxLayout()
        form_vlayout.addLayout(form_layout)
        form_vlayout.addLayout(btn_layout)
        form_group.setLayout(form_vlayout)
        
        layout.addWidget(form_group)
        
        # Table area
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["简称", "全称", "开户行", "账号", "联系人", "联系电话", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemClicked.connect(self.on_table_clicked)
        
        layout.addWidget(self.table)
        
        self.load_data()
        
    def load_data(self):
        data = database.fetch_suppliers_details()
        self.table.setRowCount(0)
        for r in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(r):
                self.table.setItem(row, col, QTableWidgetItem(str(val) if val else ""))
                
    def save_data(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "供应商简称不能为空！")
            return
            
        data = {
            'name': name,
            'full_name': self.input_full_name.text().strip(),
            'bank_name': self.input_bank_name.text().strip(),
            'bank_account': self.input_bank_account.text().strip(),
            'contact_person': self.input_contact_person.text().strip(),
            'contact_phone': self.input_contact_phone.text().strip(),
            'remarks': self.input_remarks.text().strip(),
        }
        if database.upsert_supplier(data):
            QMessageBox.information(self, "成功", "保存成功！")
            self.load_data()
            self.clear_form()
            self.suppliers_changed.emit()
        else:
            QMessageBox.warning(self, "失败", "保存失败，可能是数据异常。")
            
    def delete_data(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请选择要删除的供应商！")
            return
        if QMessageBox.question(self, "确认", f"确定要删除供应商 '{name}' 吗？") == QMessageBox.Yes:
            if database.delete_supplier(name):
                QMessageBox.information(self, "成功", "删除成功！")
                self.load_data()
                self.clear_form()
                self.suppliers_changed.emit()
            else:
                QMessageBox.warning(self, "失败", "删除失败。")

    def clear_form(self):
        self.input_name.clear()
        self.input_full_name.clear()
        self.input_bank_name.clear()
        self.input_bank_account.clear()
        self.input_contact_person.clear()
        self.input_contact_phone.clear()
        self.input_remarks.clear()
        self.input_name.setReadOnly(False)
        
    def on_table_clicked(self, item):
        row = item.row()
        self.input_name.setText(self.table.item(row, 0).text())
        self.input_full_name.setText(self.table.item(row, 1).text())
        self.input_bank_name.setText(self.table.item(row, 2).text())
        self.input_bank_account.setText(self.table.item(row, 3).text())
        self.input_contact_person.setText(self.table.item(row, 4).text())
        self.input_contact_phone.setText(self.table.item(row, 5).text())
        self.input_remarks.setText(self.table.item(row, 6).text())
        self.input_name.setReadOnly(True) # Update mode, name is primary key

class ContractManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use TabWidget as the main container
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Management (List/Detail Stack)
        self.management_container = QWidget()
        mgmt_layout = QVBoxLayout(self.management_container)
        mgmt_layout.setContentsMargins(0,0,0,0)
        
        self.stack = QStackedWidget()
        mgmt_layout.addWidget(self.stack)
        
        # 1. List View
        self.list_widget = ContractListWidget()
        self.list_widget.open_contract_signal.connect(self.open_order_view)
        self.stack.addWidget(self.list_widget)
        
        self.order_widget = None
        
        self.tabs.addTab(self.management_container, "合同管理")
        
        # Tab 2: Report
        self.report_widget = ContractReportWidget()
        self.tabs.addTab(self.report_widget, "报表分析")
        
        # Tab 3: Supplier Management
        self.supplier_widget = SupplierManagerWidget()
        self.supplier_widget.suppliers_changed.connect(self.refresh_suppliers)
        self.tabs.addTab(self.supplier_widget, "供应商管理")
        
        # Connect tab change to refresh report
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def on_tab_changed(self, index):
        if self.tabs.widget(index) == self.report_widget:
            self.report_widget.load_data()
        elif hasattr(self, 'supplier_widget') and self.tabs.widget(index) == self.supplier_widget:
            self.supplier_widget.load_data()
        
    def open_order_view(self, contract_id, contract_no, contract_name):
        if self.order_widget:
            self.stack.removeWidget(self.order_widget)
            self.order_widget.deleteLater()
            
        self.order_widget = ContractOrderWidget(contract_id, contract_no, contract_name)
        self.order_widget.back_signal.connect(self.back_to_list)
        self.stack.addWidget(self.order_widget)
        self.stack.setCurrentWidget(self.order_widget)
        
    def back_to_list(self):
        self.stack.setCurrentWidget(self.list_widget)
        if self.order_widget:
            self.stack.removeWidget(self.order_widget)
            self.order_widget.deleteLater()
            self.order_widget = None
            
    def load_data(self):
        self.list_widget.load_data()
        # Also refresh report if visible? Or just wait for tab change.
        
    def refresh_suppliers(self):
        self.list_widget.refresh_suppliers()
        if hasattr(self, 'report_widget'):
            self.report_widget.refresh_suppliers()

    def refresh_categories(self):
        self.list_widget.refresh_categories()
