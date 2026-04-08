import re

file_path = r'd:\13生产管理部\90System\06PPOMS-local\project\ui_settlement.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find index of "class ReconciliationEditor(QWidget):"
idx = content.find('class ReconciliationEditor(QWidget):')
if idx != -1:
    new_content = content[:idx] + """class ReconciliationEditor(QWidget):
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
        self.btn_complete = QPushButton("完成对账")
        self.btn_complete.setObjectName("primary")
        self.btn_complete.clicked.connect(self.complete_reconciliation)
        
        self.btn_export = QPushButton("导出明细")
        self.btn_export.clicked.connect(self.export_details)
        
        self.btn_settle = QPushButton("完成结算")
        self.btn_settle.clicked.connect(self.complete_settlement)
        
        header_layout.addWidget(self.btn_complete)
        header_layout.addWidget(self.btn_settle)
        header_layout.addWidget(self.btn_export)
        self.layout.addLayout(header_layout)
        
        # Form Info
        form_group = QGroupBox("基本信息")
        form_layout = QHBoxLayout(form_group)
        self.input_no = QLineEdit()
        self.input_no.setReadOnly(True)
        self.input_supplier = QLineEdit()
        self.input_supplier.setReadOnly(True)
        self.input_status = QLineEdit()
        self.input_status.setReadOnly(True)
        
        form_layout.addWidget(QLabel("单号:"))
        form_layout.addWidget(self.input_no)
        form_layout.addWidget(QLabel("供应商:"))
        form_layout.addWidget(self.input_supplier)
        form_layout.addWidget(QLabel("状态:"))
        form_layout.addWidget(self.input_status)
        self.layout.addWidget(form_group)
        
        # Splitter for Dual Pane
        splitter = QSplitter(Qt.Vertical)
        
        # Top Pane: Invoices
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        h_top = QHBoxLayout()
        h_top.addWidget(QLabel("<b>待核销发票池 (左/上)</b>"))
        h_top.addStretch()
        self.btn_add_invoice = QPushButton("关联发票")
        self.btn_add_invoice.clicked.connect(self.add_invoice)
        self.btn_remove_invoice = QPushButton("移除发票(暂未实现)")
        self.btn_remove_invoice.clicked.connect(self.remove_invoice)
        h_top.addWidget(self.btn_add_invoice)
        h_top.addWidget(self.btn_remove_invoice)
        top_layout.addLayout(h_top)
        
        self.table_invoices = QTableWidget()
        self.table_invoices.setColumnCount(8)
        self.table_invoices.setHorizontalHeaderLabels(["ID", "发票号", "品名", "规格", "数量", "单价", "金额(未税)", "未匹配金额"])
        self.table_invoices.setColumnHidden(0, True)
        self.table_invoices.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_invoices.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_invoices.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_invoices.horizontalHeader().setStretchLastSection(True)
        top_layout.addWidget(self.table_invoices)
        splitter.addWidget(top_widget)
        
        # Middle actions
        mid_widget = QWidget()
        mid_layout = QHBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 5, 0, 5)
        self.btn_auto_match = QPushButton("一键自动匹配")
        self.btn_auto_match.clicked.connect(self.auto_match)
        self.btn_manual_match = QPushButton("↓ 手动连线绑定")
        self.btn_manual_match.clicked.connect(self.manual_match)
        self.btn_unbind = QPushButton("↑ 解除绑定")
        self.btn_unbind.clicked.connect(self.unbind_match)
        mid_layout.addStretch()
        mid_layout.addWidget(self.btn_auto_match)
        mid_layout.addWidget(self.btn_manual_match)
        mid_layout.addWidget(self.btn_unbind)
        mid_layout.addStretch()
        splitter.addWidget(mid_widget)
        
        # Bottom Pane: Inbounds
        bot_widget = QWidget()
        bot_layout = QVBoxLayout(bot_widget)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.addWidget(QLabel("<b>待对账入库池 (右/下)</b>"))
        
        self.table_inbounds = QTableWidget()
        self.table_inbounds.setColumnCount(8)
        self.table_inbounds.setHorizontalHeaderLabels(["选择", "ID", "入库单号", "业务品名", "业务规格", "数量", "总金额", "匹配状态"])
        self.table_inbounds.setColumnHidden(1, True)
        self.table_inbounds.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_inbounds.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table_inbounds.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_inbounds.horizontalHeader().setStretchLastSection(True)
        bot_layout.addWidget(self.table_inbounds)
        splitter.addWidget(bot_widget)
        
        self.layout.addWidget(splitter)
        
    def load_data(self, rec_id, mode="edit"):
        self.current_id = rec_id
        self.mode = mode
        
        recs = database.fetch_reconciliations()
        rec = next((r for r in recs if r[0] == rec_id), None)
        if not rec: return
        
        self.input_no.setText(rec[1])
        self.input_supplier.setText(rec[2])
        self.input_status.setText(rec[3])
        
        if rec[3] == '已对账' and mode == 'edit':
            self.mode = 'view'
            
        is_edit = (self.mode == 'edit' and rec[3] == '待对账')
        self.btn_complete.setVisible(is_edit)
        self.btn_add_invoice.setVisible(is_edit)
        self.btn_remove_invoice.setVisible(is_edit)
        self.btn_auto_match.setVisible(is_edit)
        self.btn_manual_match.setVisible(is_edit)
        self.btn_unbind.setVisible(is_edit)
        
        self.btn_settle.setVisible(rec[3] == '已对账')
        
        self.refresh_tables()
        
    def refresh_tables(self):
        if not self.current_id: return
        
        # Load Invoices
        inv_data = database.fetch_recon_invoice_items(self.current_id)
        self.table_invoices.setRowCount(0)
        for r in inv_data:
            row = self.table_invoices.rowCount()
            self.table_invoices.insertRow(row)
            
            iid, inv_no, name, spec, qty, price, amt, tax, matched = r
            unmatched = amt - matched
            
            self.table_invoices.setItem(row, 0, QTableWidgetItem(str(iid)))
            self.table_invoices.setItem(row, 1, QTableWidgetItem(str(inv_no)))
            self.table_invoices.setItem(row, 2, QTableWidgetItem(str(name)))
            self.table_invoices.setItem(row, 3, QTableWidgetItem(str(spec)))
            self.table_invoices.setItem(row, 4, QTableWidgetItem(f"{qty:.2f}"))
            self.table_invoices.setItem(row, 5, QTableWidgetItem(f"{price:.2f}"))
            self.table_invoices.setItem(row, 6, QTableWidgetItem(f"{amt:.2f}"))
            
            un_item = QTableWidgetItem(f"{unmatched:.2f}")
            if unmatched <= 0.01:
                un_item.setForeground(QColor("green"))
            else:
                un_item.setForeground(QColor("red"))
            self.table_invoices.setItem(row, 7, un_item)
            
        # Load Inbounds
        ib_data = database.fetch_recon_inbounds(self.current_id)
        self.table_inbounds.setRowCount(0)
        for r in ib_data:
            row = self.table_inbounds.rowCount()
            self.table_inbounds.insertRow(row)
            
            ib_id, ib_no, name, spec, qty, price, total, is_matched = r
            
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table_inbounds.setItem(row, 0, chk)
            
            self.table_inbounds.setItem(row, 1, QTableWidgetItem(str(ib_id)))
            self.table_inbounds.setItem(row, 2, QTableWidgetItem(str(ib_no)))
            self.table_inbounds.setItem(row, 3, QTableWidgetItem(str(name)))
            self.table_inbounds.setItem(row, 4, QTableWidgetItem(str(spec)))
            self.table_inbounds.setItem(row, 5, QTableWidgetItem(f"{qty:.2f}"))
            self.table_inbounds.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
            
            status_text = "已匹配" if is_matched > 0 else "未匹配"
            st_item = QTableWidgetItem(status_text)
            if is_matched > 0:
                st_item.setForeground(QColor("blue"))
                for c in range(2, 8):
                    if self.table_inbounds.item(row, c):
                        self.table_inbounds.item(row, c).setBackground(QColor("#e6f7ff"))
            self.table_inbounds.setItem(row, 7, st_item)

    def add_invoice(self):
        supplier = self.input_supplier.text()
        dlg = InvoiceSelectionDialog(supplier, self)
        if dlg.exec():
            ids = dlg.get_selected_ids()
            if ids:
                database.link_invoices_to_recon(self.current_id, ids)
                self.refresh_tables()
                
    def remove_invoice(self):
        QMessageBox.warning(self, "提示", "请在发票管理模块或直接通过解除绑定处理（暂未实现按明细移除整张发票）")
        
    def auto_match(self):
        QMessageBox.information(self, "提示", "自动匹配触发：寻找金额与数量一致的明细进行连线。")
        inv_count = self.table_invoices.rowCount()
        ib_count = self.table_inbounds.rowCount()
        for i in range(inv_count):
            un_amt = float(self.table_invoices.item(i, 7).text())
            if un_amt <= 0.01: continue
            
            iid = int(self.table_invoices.item(i, 0).text())
            for j in range(ib_count):
                if self.table_inbounds.item(j, 7).text() == "已匹配": continue
                ib_amt = float(self.table_inbounds.item(j, 6).text())
                
                if abs(un_amt - ib_amt) < 0.01:
                    ib_id = int(self.table_inbounds.item(j, 1).text())
                    database.bind_recon_items(self.current_id, iid, [ib_id])
                    un_amt -= ib_amt
                    if un_amt <= 0.01: break
        
        self.refresh_tables()

    def manual_match(self):
        row_inv = self.table_invoices.currentRow()
        if row_inv < 0:
            QMessageBox.warning(self, "提示", "请先在上方选中一行发票明细")
            return
            
        iid = int(self.table_invoices.item(row_inv, 0).text())
        un_amt = float(self.table_invoices.item(row_inv, 7).text())
        
        selected_ibs = []
        sum_ib = 0.0
        for i in range(self.table_inbounds.rowCount()):
            if self.table_inbounds.item(i, 0).checkState() == Qt.Checked:
                if self.table_inbounds.item(i, 7).text() == "已匹配":
                    QMessageBox.warning(self, "提示", f"第 {i+1} 行入库记录已被匹配，请勿重复勾选")
                    return
                selected_ibs.append(int(self.table_inbounds.item(i, 1).text()))
                sum_ib += float(self.table_inbounds.item(i, 6).text())
                
        if not selected_ibs:
            QMessageBox.warning(self, "提示", "请在下方勾选至少一条入库记录")
            return
            
        if sum_ib - un_amt > 1.0: # Tolerance 1.0
            QMessageBox.warning(self, "提示", f"入库总金额 ({sum_ib:.2f}) 大于发票未匹配金额 ({un_amt:.2f})，无法绑定")
            return
            
        database.bind_recon_items(self.current_id, iid, selected_ibs)
        QMessageBox.information(self, "成功", "绑定成功！")
        self.refresh_tables()
        
    def unbind_match(self):
        selected_ibs = []
        for i in range(self.table_inbounds.rowCount()):
            if self.table_inbounds.item(i, 0).checkState() == Qt.Checked:
                if self.table_inbounds.item(i, 7).text() == "已匹配":
                    selected_ibs.append(int(self.table_inbounds.item(i, 1).text()))
                    
        if not selected_ibs:
            QMessageBox.warning(self, "提示", "请在下方勾选已匹配的入库记录来解除绑定")
            return
            
        for ib in selected_ibs:
            database.unbind_recon_inbound(self.current_id, ib)
            
        QMessageBox.information(self, "成功", "解绑成功！")
        self.refresh_tables()
        
    def complete_reconciliation(self):
        if not self.current_id: return
        
        for i in range(self.table_inbounds.rowCount()):
            if self.table_inbounds.item(i, 7).text() != "已匹配":
                QMessageBox.warning(self, "提示", "待对账池中还有未匹配的入库记录，无法完成对账！")
                return
                
        if QMessageBox.question(self, "确认", "确定要完成对账吗？完成后将进入结算流程。") == QMessageBox.Yes:
            data = {
                'id': self.current_id,
                'supplier': self.input_supplier.text(),
                'status': '已对账',
                'total_amount': 0,
                'remarks': ''
            }
            database.upsert_reconciliation(data)
            self.back_signal.emit()
            
    def export_details(self):
        QMessageBox.information(self, "提示", "导出明细功能暂未对接双边池报表。")
        
    def complete_settlement(self):
        if not self.current_id: return
        
        if QMessageBox.question(self, "确认", "将生成付款申请单进入结算流程？") == QMessageBox.Yes:
            data = {
                'id': self.current_id,
                'reconciliation_no': self.input_no.text(),
                'supplier': self.input_supplier.text(),
                'status': '结算中',
                'total_amount': 0,
                'remarks': ''
            }
            database.upsert_reconciliation(data)
            self.back_signal.emit()

class InvoiceSelectionDialog(QDialog):
    def __init__(self, supplier, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"选择发票 - {supplier}")
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["选择", "ID", "发票号", "销售方", "金额", "日期", "状态"])
        self.table.setColumnHidden(1, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        data = database.fetch_unlinked_invoices_for_supplier(supplier)
        
        self.table.setRowCount(0)
        for row in data:
            r_idx = self.table.rowCount()
            self.table.insertRow(r_idx)
            
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table.setItem(r_idx, 0, chk)
            
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row[0])))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row[1])))
            self.table.setItem(r_idx, 3, QTableWidgetItem(str(row[2]))) # Supplier
            self.table.setItem(r_idx, 4, QTableWidgetItem(str(row[3]))) # Amount
            self.table.setItem(r_idx, 5, QTableWidgetItem(str(row[4]))) # Date
                
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected_ids(self):
        ids = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                ids.append(int(self.table.item(i, 1).text()))
        return ids
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        print("Replacement successful")
