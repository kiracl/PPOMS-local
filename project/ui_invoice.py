
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QDialog, 
    QGroupBox, QFileDialog, QFormLayout, QDialogButtonBox, QAbstractItemView,
    QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QBrush
import database
import xml.etree.ElementTree as ET
import os

class XMLParser:
    @staticmethod
    def parse_invoice(file_path):
        """
        Parse generic China VAT Invoice XML
        Returns (header_dict, items_list)
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            header = {}
            items = []
            
            # Define field mappings (lowercase)
            field_map = {
                'invoice_code': ['fpdm', 'invoicecode', 'dm', 'eiid'], # Added eiid
                'invoice_number': ['fphm', 'invoicenumber', 'hm'],
                'date': ['kprq', 'invoicedate', 'date', 'issuetime', 'requesttime'], # Added requesttime
                'seller_name': ['xsf_mc', 'sellername'],
                'seller_tax_id': ['xsf_nsrsbh', 'sellertaxid', 'selleridnum'],
                'buyer_name': ['gmf_mc', 'buyername'],
                'buyer_tax_id': ['gmf_nsrsbh', 'buyertaxid', 'buyeridnum'],
                'amount_excluding_tax': ['hjbhsje', 'amountwithouttax', 'totalamwithouttax'],
                'tax_amount': ['hjse', 'taxamount', 'totaltaxam'],
                'total_amount': ['jshj', 'totalamount', 'totaltax-includedamount'],
                'remarks': ['bz', 'remarks'],
                'invoice_type': ['fplx', 'invoicetype']
            }
            
            # Flattened search for header fields
            for elem in root.iter():
                tag = elem.tag.lower()
                # Strip namespace if present: {url}tag -> tag
                if '}' in tag:
                    tag = tag.split('}', 1)[1]
                
                if not elem.text: continue
                text = elem.text.strip()
                if not text: continue
                
                for field, tags in field_map.items():
                    # Only set if not already set (priority to first occurrence usually, or use specific order?)
                    # For dates: IssueTime (YYYY-MM-DD) is better than RequestTime (YYYY-MM-DD HH:MM:SS) usually, 
                    # but RequestTime is fine too.
                    if field not in header and tag in tags:
                        header[field] = text
                        
            # Special check for InvoiceType in standard EInvoice (Digital)
            if 'invoice_type' not in header:
                # Look for GeneralOrSpecialVAT -> LabelName
                for elem in root.iter():
                    tag = elem.tag.lower()
                    if '}' in tag: tag = tag.split('}', 1)[1]
                    if tag == 'generalorspecialvat':
                        for sub in elem:
                            sub_tag = sub.tag.lower()
                            if '}' in sub_tag: sub_tag = sub_tag.split('}', 1)[1]
                            if sub_tag == 'labelname' and sub.text:
                                header['invoice_type'] = sub.text.strip()
                                break
                        if 'invoice_type' in header: break
            
            # Helper for float conversion
            def to_float(s):
                try: return float(s)
                except: return 0.0

            # Convert amounts
            for f in ['amount_excluding_tax', 'tax_amount', 'total_amount']:
                if f in header:
                    header[f] = to_float(header[f])
                else:
                    header[f] = 0.0

            # Items search
            # Find 'Spxx' or 'Items' or 'EInvoiceData' container
            spxx = None
            for elem in root.iter():
                tag = elem.tag.lower()
                if '}' in tag: tag = tag.split('}', 1)[1]
                if tag in ['spxx', 'items', 'einvoicedata']:
                    spxx = elem
                    # Prefer spxx/items if found, but accept einvoicedata as fallback
                    if tag in ['spxx', 'items']: break
            
            if spxx:
                for child in spxx:
                    # Search direct children of the row element
                    item = {}
                    for sub in child.iter(): 
                        if sub == child: continue 
                        
                        sub_tag = sub.tag.lower()
                        if '}' in sub_tag: sub_tag = sub_tag.split('}', 1)[1]
                        
                        if not sub.text: continue
                        val = sub.text.strip()
                        
                        if sub_tag in ['spmc', 'itemname']: item['item_name'] = val
                        elif sub_tag in ['ggxh', 'spec', 'specmod']: item['spec_model'] = val
                        elif sub_tag in ['dw', 'unit', 'meaunits']: item['unit'] = val
                        elif sub_tag in ['sl', 'quantity']: item['quantity'] = to_float(val)
                        elif sub_tag in ['dj', 'unitprice', 'unprice']: item['unit_price'] = to_float(val)
                        elif sub_tag in ['je', 'amount']: item['amount'] = to_float(val)
                        elif sub_tag in ['slv', 'taxrate']: item['tax_rate'] = to_float(val)
                        elif sub_tag in ['se', 'tax', 'comtaxam']: item['tax_amount'] = to_float(val)
                    
                    if item and 'item_name' in item:
                        items.append(item)
                        
            header['file_path'] = file_path
            # Defaults
            if 'invoice_type' not in header: header['invoice_type'] = "增值税发票"
            if 'invoice_code' not in header: 
                # If code is missing but we have number (Digital Invoice), use empty string
                # Or try to extract from header['eiid'] if mapped
                header['invoice_code'] = "" 
            
            # Digital Invoice Special: If code is empty and number is 20 digits, it's valid.
            
            return header, items
            
        except Exception as e:
            raise Exception(f"解析XML失败: {str(e)}")

class LinkInboundSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择关联入库记录")
        self.resize(1000, 600)
        self.selected_inbound = None # (id, no)
        
        layout = QVBoxLayout(self)
        
        # Filter
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索入库单/合同号/规格...")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "入库单号", "入库日期", "合同编号", "订单编号", 
            "规格型号", "入库数量", "仓储单号", "状态"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)
        
        # Legend
        lbl_legend = QLabel("注：灰色记录表示已关联其他发票明细；按住Ctrl或Shift可多选")
        lbl_legend.setStyleSheet("color: gray;")
        layout.addWidget(lbl_legend)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept_selection)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.load_data()
        
    def load_data(self):
        text = self.search_input.text().strip()
        # fetch_inbound_orders_for_linking returns (..., is_linked)
        rows = database.fetch_inbound_orders_for_linking(text)
        
        # Sort: Not Linked First, Linked Last. Then Date Desc.
        # r[-1] is is_linked (bool)
        # False < True. So False comes first.
        rows.sort(key=lambda x: (x[-1], x[2]), reverse=False) 
        # Wait: x[-1] False=0, True=1. Ascending -> False first. Correct.
        # Date x[2] Descending -> Need reverse=True for Date?
        # Let's do complex sort key
        rows.sort(key=lambda x: (x[-1], x[2]), reverse=False) 
        # Linked (1) > Unlinked (0). So Unlinked first.
        # But we want Unlinked first. So x[-1] ASC is correct.
        # Date we want DESC.
        # Python sort is stable.
        rows.sort(key=lambda x: x[2], reverse=True) # Sort by date desc
        rows.sort(key=lambda x: x[-1], reverse=False) # Stable sort by linked status (0 then 1)
        
        self.table.setRowCount(0)
        for r in rows:
            # r: id, no, date, contract, order, spec, qty, wh, is_linked
            is_linked = r[-1]
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            vals = list(r[:-1]) + ["已关联" if is_linked else "未关联"]
            
            for i, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                if is_linked:
                    item.setForeground(QBrush(QColor("gray")))
                    # Optional: Disable selection? User might want to change link?
                    # "已经关联的记录灰色靠后排" -> Gray and at bottom.
                    # Usually implies read-only or warning.
                    # Let's allow selection but warn? Or just visual?
                    # Visual is safer.
                
                self.table.setItem(row, i, item)
            
            self.table.item(row, 0).setData(Qt.UserRole, (r[0], r[1])) # ID, No
            
    def accept_selection(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        
        selected = []
        for idx in rows:
            row = idx.row()
            data = self.table.item(row, 0).data(Qt.UserRole) # (id, no)
            if data:
                selected.append(data)
                
        self.selected_inbound = selected
        self.accept()

class InvoiceDetailDialog(QDialog):
    def __init__(self, invoice_id, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.setWindowTitle("发票详情")
        self.resize(1100, 700)
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Invoice Info (Group)
        info_group = QGroupBox("发票主记录")
        form = QFormLayout(info_group)
        self.lbl_type = QLabel()
        self.lbl_code = QLabel()
        self.lbl_number = QLabel()
        self.lbl_date = QLabel()
        self.lbl_seller = QLabel()
        self.lbl_amount = QLabel()
        self.lbl_status = QLabel()
        self.lbl_import_time = QLabel()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("发票类型:"))
        row1.addWidget(self.lbl_type)
        row1.addWidget(QLabel("发票代码:"))
        row1.addWidget(self.lbl_code)
        row1.addWidget(QLabel("发票号码:"))
        row1.addWidget(self.lbl_number)
        row1.addWidget(QLabel("开票日期:"))
        row1.addWidget(self.lbl_date)
        form.addRow(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("销售方:"))
        row2.addWidget(self.lbl_seller)
        row2.addWidget(QLabel("价税合计:"))
        row2.addWidget(self.lbl_amount)
        row2.addWidget(QLabel("状态:"))
        row2.addWidget(self.lbl_status)
        row2.addWidget(QLabel("导入时间:"))
        row2.addWidget(self.lbl_import_time)
        form.addRow(row2)
        
        layout.addWidget(info_group)
        
        # 2. Items (Table)
        items_group = QGroupBox("发票明细 (双击'仓库单号'列关联入库记录)")
        vbox_items = QVBoxLayout(items_group)
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(11) # Added ID (Hidden), InboundID (Hidden)
        self.table_items.setHorizontalHeaderLabels([
            "ID", "项目名称", "规格型号", "单位", "数量", 
            "单价", "金额", "税率", "税额", "仓库单号", "关联ID"
        ])
        self.table_items.setColumnHidden(0, True) # Item ID
        self.table_items.setColumnHidden(10, True) # Inbound ID
        
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_items.horizontalHeader().setStretchLastSection(True)
        self.table_items.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_items.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_items.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        vbox_items.addWidget(self.table_items)
        layout.addWidget(items_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_export = QPushButton("导出明细")
        btn_export.clicked.connect(self.export_details)
        btn_layout.addWidget(btn_export)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
    def load_data(self):
        # 1. Header
        conn = database._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM invoices WHERE id=?", (self.invoice_id,))
            row = cur.fetchone()
            # Mapping based on updated schema:
            # id, uuid, code, number, date, seller, seller_tax, buyer, buyer_tax, amt_ex, tax, total, status, mat_no, file, created, remark, invoice_type
            if row:
                self.lbl_type.setText(row[17] if len(row)>17 else "")
                self.lbl_code.setText(row[2])
                self.lbl_number.setText(row[3])
                self.lbl_date.setText(row[4])
                self.lbl_seller.setText(row[5])
                self.lbl_amount.setText(f"{row[10]:,.2f}")
                self.lbl_status.setText(row[12])
                self.lbl_import_time.setText(row[15])
                
                # Style status
                status = row[12]
                if status == '新增':
                    self.lbl_status.setStyleSheet("color: blue; font-weight: bold;")
                elif status == '待入账':
                    self.lbl_status.setStyleSheet("color: orange; font-weight: bold;")
                elif status == '已入账':
                    self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
        finally:
            conn.close()
            
        # 2. Items
        items = database.fetch_invoice_items(self.invoice_id)
        self.table_items.setRowCount(0)
        for r in items:
            # id, item_name, spec_model, unit, quantity, unit_price, amount, tax_rate, tax_amount, inbound_id, inbound_no
            row = self.table_items.rowCount()
            self.table_items.insertRow(row)
            
            # ID
            self.table_items.setItem(row, 0, QTableWidgetItem(str(r[0])))
            # Name
            self.table_items.setItem(row, 1, QTableWidgetItem(str(r[1])))
            # Spec
            self.table_items.setItem(row, 2, QTableWidgetItem(str(r[2])))
            # Unit
            self.table_items.setItem(row, 3, QTableWidgetItem(str(r[3])))
            # Qty
            self.table_items.setItem(row, 4, QTableWidgetItem(f"{r[4]:,.2f}"))
            # Price
            self.table_items.setItem(row, 5, QTableWidgetItem(f"{r[5]:,.2f}"))
            # Amount
            self.table_items.setItem(row, 6, QTableWidgetItem(f"{r[6]:,.2f}"))
            # Rate
            self.table_items.setItem(row, 7, QTableWidgetItem(f"{r[7]*100:.0f}%" if r[7]<1 else f"{r[7]:.2f}"))
            # Tax
            self.table_items.setItem(row, 8, QTableWidgetItem(f"{r[8]:,.2f}"))
            
            # Warehouse No (Inbound No)
            # Make it look like a link or button-like?
            # Or just text. Double click triggers edit.
            inbound_no = r[10] or "点击选择..."
            item_wh = QTableWidgetItem(inbound_no)
            if not r[10]:
                item_wh.setForeground(QBrush(QColor("blue")))
            self.table_items.setItem(row, 9, item_wh)
            
            # Inbound ID (Hidden)
            self.table_items.setItem(row, 10, QTableWidgetItem(str(r[9] or "")))

    def on_cell_double_clicked(self, row, col):
        if col == 9: # Warehouse No column
            dlg = LinkInboundSelectionDialog(self)
            if dlg.exec():
                if dlg.selected_inbound:
                    # selected_inbound is list of (id, no)
                    selected = dlg.selected_inbound
                    
                    inbound_ids = [str(s[0]) for s in selected]
                    inbound_nos = [str(s[1]) for s in selected]
                    
                    inbound_id_str = ",".join(inbound_ids)
                    inbound_no_str = "，".join(inbound_nos)
                    
                    item_id = int(self.table_items.item(row, 0).text())
                    
                    try:
                        database.link_invoice_item_to_inbound(item_id, inbound_id_str, inbound_no_str)
                        self.load_data() # Refresh
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"关联失败: {e}")

    def export_details(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出明细", "", "Excel Files (*.xlsx)")
        if not file_path:
            return
            
        try:
            import pandas as pd
            
            # Fetch data
            items = database.fetch_invoice_items(self.invoice_id)
            # items columns: id, item_name, spec_model, unit, quantity, unit_price, amount, tax_rate, tax_amount, inbound_id, inbound_no
            
            data = []
            for r in items:
                data.append({
                    "项目名称": r[1],
                    "规格型号": r[2],
                    "单位": r[3],
                    "数量": r[4],
                    "单价": r[5],
                    "金额": r[6],
                    "税率": r[7], # Keep raw for Excel, or format? User asked for table export. Raw is better for calc, but format matches UI.
                    "税额": r[8],
                    "仓库单号": r[10] if r[10] else ""
                })
                
            df = pd.DataFrame(data)
            
            # Optional: Format columns if needed, but basic export is usually enough.
            # Let's format Tax Rate to percentage string for clarity if it's < 1
            # But converting to string makes it hard to calc. Let's keep as is or follow user preference.
            # User requirement: "导出明细到Excel表格".
            # UI shows percentage.
            
            # Let's try to make it look like the table.
            df['税率'] = df['税率'].apply(lambda x: f"{x*100:.0f}%" if isinstance(x, (float, int)) and x < 1 else x)
            
            df.to_excel(file_path, index=False)
            
            QMessageBox.information(self, "成功", "导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

class InvoiceManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索发票号/销售方...")
        self.search_input.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_input)
        
        btn_import = QPushButton("导入发票(XML)")
        btn_import.clicked.connect(self.import_xml)
        toolbar.addWidget(btn_import)
        
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "导入时间", "发票类型", "发票代码", "发票号码", "开票日期", "销售方", 
            "价税合计", "状态", "操作"
        ])
        self.table.setColumnHidden(0, True)
        
        # Interactive Resize
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.open_detail)
        
        # Default widths
        self.table.setColumnWidth(1, 140) # Import Time
        self.table.setColumnWidth(2, 100) # Type
        self.table.setColumnWidth(3, 120) # Code
        self.table.setColumnWidth(4, 120) # Number
        self.table.setColumnWidth(5, 100) # Date
        self.table.setColumnWidth(6, 200) # Seller
        self.table.setColumnWidth(7, 100) # Total
        self.table.setColumnWidth(8, 80)  # Status
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
    def load_data(self):
        text = self.search_input.text().strip()
        rows = database.fetch_invoices(text)
        
        self.table.setRowCount(0)
        for r in rows:
            # id, code, number, date, seller, total, status, mat_no, created, type
            # We want: ID, Created, Type, Code, Number, Date, Seller, Total, Status
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Map DB result to Table Columns
            # DB: 0:id, 1:code, 2:num, 3:date, 4:seller, 5:total, 6:status, 7:mat_no, 8:created, 9:type
            
            # 0: ID
            self.table.setItem(row, 0, QTableWidgetItem(str(r[0])))
            # 1: Created
            self.table.setItem(row, 1, QTableWidgetItem(str(r[8])))
            # 2: Type
            self.table.setItem(row, 2, QTableWidgetItem(str(r[9] if len(r)>9 else "")))
            # 3: Code
            self.table.setItem(row, 3, QTableWidgetItem(str(r[1])))
            # 4: Number
            self.table.setItem(row, 4, QTableWidgetItem(str(r[2])))
            # 5: Date
            self.table.setItem(row, 5, QTableWidgetItem(str(r[3])))
            # 6: Seller
            self.table.setItem(row, 6, QTableWidgetItem(str(r[4])))
            # 7: Total (Formatted)
            total = r[5] if r[5] else 0.0
            self.table.setItem(row, 7, QTableWidgetItem(f"{total:,.2f}"))
            # 8: Status
            item_status = QTableWidgetItem(str(r[6]))
            if r[6] == '新增':
                item_status.setForeground(QColor("blue"))
            elif r[6] == '待入账':
                item_status.setForeground(QColor("orange"))
            elif r[6] == '已入账':
                item_status.setForeground(QColor("green"))
            self.table.setItem(row, 8, item_status)
            
            # 9: Action
            btn_delete = QPushButton("删除")
            btn_delete.setStyleSheet("color: red;")
            btn_delete.clicked.connect(lambda _, oid=r[0]: self.delete_invoice(oid))
            
            # Create a container widget to center the button
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(2, 2, 2, 2)
            h_layout.addWidget(btn_delete)
            h_layout.setAlignment(Qt.AlignCenter)
            
            self.table.setCellWidget(row, 9, container)
            
            # Store ID in col 0
            self.table.item(row, 0).setData(Qt.UserRole, r[0])

    def import_xml(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择发票XML", "", "XML Files (*.xml)")
        if not file_path:
            return
            
        try:
            header, items = XMLParser.parse_invoice(file_path)
            
            # Show summary and confirm
            msg = f"解析结果:\n\n"
            msg += f"发票代码: {header.get('invoice_code')}\n"
            msg += f"发票号码: {header.get('invoice_number')}\n"
            msg += f"开票日期: {header.get('date')}\n"
            msg += f"销售方: {header.get('seller_name')}\n"
            msg += f"价税合计: {header.get('total_amount')}\n"
            msg += f"明细行数: {len(items)}\n\n"
            msg += "确认导入吗？"
            
            if QMessageBox.question(self, "确认导入", msg) != QMessageBox.Yes:
                return

            # Save
            invoice_id = database.save_invoice(header, items)
            QMessageBox.information(self, "成功", "发票导入成功")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            
    def open_detail(self, item):
        row = item.row()
        invoice_id = self.table.item(row, 0).data(Qt.UserRole)
        dlg = InvoiceDetailDialog(invoice_id, self)
        dlg.exec()
        self.load_data() # Refresh in case status changed
        
    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        invoice_id = self.table.item(row, 0).data(Qt.UserRole)
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        act_del = menu.addAction("删除发票")
        act_del.triggered.connect(lambda: self.delete_invoice(invoice_id))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
        
    def delete_invoice(self, invoice_id):
        if QMessageBox.question(self, "确认", "确定要删除该发票记录吗？") == QMessageBox.Yes:
            try:
                database.delete_invoice(invoice_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
