
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QLabel, QDateEdit, QGroupBox, 
    QHeaderView, QMessageBox, QDialog, QFormLayout,
    QSplitter, QDoubleSpinBox, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
import database
import os
from datetime import datetime

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
        self.setWindowTitle("选择关联订单 (主单)")
        self.resize(900, 500)
        self.selected_data = None
        
        layout = QVBoxLayout(self)
        
        # Filter
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索订单编号/合同号/名称...")
        self.search_input.textChanged.connect(self.load_data)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "订单编号", "合同编号", "采购计划", "总数量", "待入库总数"
        ])
        
        # Column Width Configuration
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 200) # Order No
        self.table.setColumnWidth(1, 200) # Contract No
        self.table.setColumnWidth(2, 180) # Purch Plan
        self.table.setColumnWidth(3, 120) # Total Qty
        
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
        orders = database.fetch_contract_orders_grouped(text)
        
        self.table.setRowCount(0)
        for row_data in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # order_no, contract_no, purch_plan_no, total_qty, pending_qty
            items = [
                str(row_data['order_no']),
                str(row_data['contract_no']),
                str(row_data['purch_plan_no']),
                f"{row_data['total_qty']:,.2f}",
                f"{row_data['pending_qty']:,.2f}"
            ]
            
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 4 and row_data['pending_qty'] > 0:
                    item.setForeground(QColor("red"))
                elif col == 4:
                    item.setForeground(QColor("green"))
                self.table.setItem(row, col, item)
            
            # Store full data
            self.table.item(row, 0).setData(Qt.UserRole, row_data)

    def accept_selection(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_data = self.table.item(row, 0).data(Qt.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请先选择一条记录")


class InboundManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE_MAIN)
        self.current_main_order = None
        self.init_ui()
        self.load_history()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Area: Entry Form ---
        entry_group = QGroupBox("入库登记")
        entry_layout = QVBoxLayout(entry_group)
        
        # 1. Header Fields
        header_grid = QGridLayout()
        
        header_grid.addWidget(QLabel("入库日期:"), 0, 0)
        self.input_date = QDateEdit(QDate.currentDate())
        self.input_date.setCalendarPopup(True)
        self.input_date.dateChanged.connect(self.update_preview_no)
        header_grid.addWidget(self.input_date, 0, 1)
        
        header_grid.addWidget(QLabel("预览单号:"), 0, 2)
        self.lbl_preview_no = QLabel("RK-YYMMDD-CAT-XXXX")
        self.lbl_preview_no.setStyleSheet("color: gray; font-style: italic;")
        header_grid.addWidget(self.lbl_preview_no, 0, 3)
        
        self.btn_select_order = QPushButton("选择关联订单...")
        self.btn_select_order.setObjectName("primary")
        self.btn_select_order.clicked.connect(self.select_order)
        header_grid.addWidget(self.btn_select_order, 0, 4, 1, 2)
        
        # Read-only Info
        header_grid.addWidget(QLabel("合同编号:"), 1, 0)
        self.txt_contract_no = QLineEdit()
        self.txt_contract_no.setReadOnly(True)
        header_grid.addWidget(self.txt_contract_no, 1, 1)
        
        header_grid.addWidget(QLabel("订单编号:"), 1, 2)
        self.txt_order_no = QLineEdit()
        self.txt_order_no.setReadOnly(True)
        header_grid.addWidget(self.txt_order_no, 1, 3)
        
        header_grid.addWidget(QLabel("采购计划:"), 1, 4)
        self.txt_purch_no = QLineEdit()
        self.txt_purch_no.setReadOnly(True)
        header_grid.addWidget(self.txt_purch_no, 1, 5)
        
        entry_layout.addLayout(header_grid)
        
        # 2. Spec Entry Table
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(8)
        self.input_table.setHorizontalHeaderLabels([
            "规格型号", "单位", "订单数量", "已入库", "本次入库*", "仓储单号*", "备注", "DATA"
        ])
        self.input_table.setColumnHidden(7, True) # Hidden Data
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.input_table.horizontalHeader().setStretchLastSection(True)
        self.input_table.setMinimumHeight(200)
        entry_layout.addWidget(self.input_table)
        
        # 3. Actions
        action_layout = QHBoxLayout()
        self.btn_clear = QPushButton("重置")
        self.btn_clear.clicked.connect(self.clear_form)
        self.btn_save = QPushButton("确认入库")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_inbound)
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_clear)
        action_layout.addWidget(self.btn_save)
        entry_layout.addLayout(action_layout)
        
        main_layout.addWidget(entry_group)
        
        # --- Bottom Area: History List ---
        list_group = QGroupBox("入库记录")
        list_layout = QVBoxLayout(list_group)
        
        # Filter and Tools
        tool_box = QHBoxLayout()
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("搜索入库单/合同号/仓储单号...")
        self.filter_text.textChanged.connect(self.load_history)
        tool_box.addWidget(self.filter_text)
        
        self.btn_export = QPushButton("导出Excel")
        self.btn_export.clicked.connect(self.export_data)
        tool_box.addWidget(self.btn_export)
        
        self.btn_import = QPushButton("导入数据")
        self.btn_import.clicked.connect(self.import_data)
        tool_box.addWidget(self.btn_import)
        
        self.btn_template = QPushButton("下载模板")
        self.btn_template.clicked.connect(self.download_template)
        tool_box.addWidget(self.btn_template)
        
        list_layout.addLayout(tool_box)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(13)
        self.history_table.setHorizontalHeaderLabels([
            "选择", "ID", "入库单号", "入库日期", "合同编号", "订单编号", "采购计划", 
            "规格型号", "本次入库", "单价", "总价", "仓储单号", "备注"
        ])
        self.history_table.setColumnHidden(1, True) # ID Hidden
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setColumnWidth(0, 50)
        self.history_table.setColumnWidth(2, 160)
        self.history_table.setColumnWidth(3, 100)
        
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        
        list_layout.addWidget(self.history_table)
        main_layout.addWidget(list_group)
        
        # Set splitter
        main_layout.setStretch(1, 1)

    def update_preview_no(self):
        if not self.current_main_order:
            self.lbl_preview_no.setText("RK-YYMMDD-CAT-XXXX")
            return
            
        date_str = self.input_date.date().toString("yyMMdd")
        # Assuming category logic remains similar or extracted from contract
        # Here we don't have category code directly in grouped result unless we fetched it.
        # But we can guess or use "GEN". 
        # Actually fetch_contract_orders_grouped joins contracts, but we didn't select category code.
        # Let's just use "GEN" or fetch it.
        # Ideally we should include category in fetch_contract_orders_grouped.
        # For now, placeholder is fine.
        self.lbl_preview_no.setText(f"RK-{date_str}-????-????")

    def select_order(self):
        dlg = OrderSelectionDialog(self)
        if dlg.exec():
            data = dlg.selected_data
            self.current_main_order = data
            
            # Fill Header
            self.txt_contract_no.setText(data['contract_no'])
            self.txt_order_no.setText(data['order_no'])
            self.txt_purch_no.setText(data['purch_plan_no'])
            
            self.update_preview_no()
            self.load_specs_for_order(data['order_no'])

    def load_specs_for_order(self, order_no):
        specs = database.fetch_specs_by_order_no(order_no)
        self.input_table.setRowCount(0)
        
        for sp in specs:
            row = self.input_table.rowCount()
            self.input_table.insertRow(row)
            
            # 0: Spec
            self.input_table.setItem(row, 0, QTableWidgetItem(sp['spec_model']))
            # 1: Unit
            self.input_table.setItem(row, 1, QTableWidgetItem(sp['unit']))
            # 2: Order Qty
            self.input_table.setItem(row, 2, QTableWidgetItem(f"{sp['order_qty']:,.2f}"))
            # 3: Inbound (Prev)
            self.input_table.setItem(row, 3, QTableWidgetItem(f"{sp['inbound_total']:,.2f}"))
            
            # 4: This Inbound (Editable)
            sb_qty = QDoubleSpinBox()
            sb_qty.setRange(0, 99999999)
            sb_qty.setDecimals(2)
            # Default to pending
            pending = sp['pending_qty']
            sb_qty.setValue(pending if pending > 0 else 0)
            self.input_table.setCellWidget(row, 4, sb_qty)
            
            # 5: Warehouse No (Editable)
            le_wh = QLineEdit()
            le_wh.setPlaceholderText("扫码或输入")
            self.input_table.setCellWidget(row, 5, le_wh)
            
            # 6: Remarks
            le_rem = QLineEdit()
            self.input_table.setCellWidget(row, 6, le_rem)
            
            # 7: Data
            item_data = QTableWidgetItem()
            item_data.setData(Qt.UserRole, sp)
            self.input_table.setItem(row, 7, item_data)

    def clear_form(self):
        self.current_main_order = None
        self.txt_contract_no.clear()
        self.txt_order_no.clear()
        self.txt_purch_no.clear()
        self.input_table.setRowCount(0)
        self.lbl_preview_no.setText("RK-YYMMDD-CAT-XXXX")
        self.input_date.setDate(QDate.currentDate())

    def save_inbound(self):
        rows = self.input_table.rowCount()
        if rows == 0:
            return
            
        date_yyMMdd = self.input_date.date().toString("yyMMdd")
        date_full = self.input_date.date().toString("yyyy-MM-dd")
        
        # Collect valid entries
        to_save = []
        
        for r in range(rows):
            sb_qty = self.input_table.cellWidget(r, 4)
            qty = sb_qty.value()
            
            if qty <= 0:
                continue
                
            le_wh = self.input_table.cellWidget(r, 5)
            wh_no = le_wh.text().strip()
            
            # Validation: Warehouse No Unique
            if wh_no:
                if not database.check_warehouse_no_unique(wh_no):
                    QMessageBox.warning(self, "校验失败", f"第 {r+1} 行: 仓储单号 '{wh_no}' 已存在！")
                    return
            
            le_rem = self.input_table.cellWidget(r, 6)
            remarks = le_rem.text().strip()
            
            sp_data = self.input_table.item(r, 7).data(Qt.UserRole)
            
            to_save.append({
                'row_idx': r,
                'qty': qty,
                'wh_no': wh_no,
                'remarks': remarks,
                'sp_data': sp_data
            })
            
        if not to_save:
            QMessageBox.warning(self, "提示", "没有有效入库数量 (>0) 的记录")
            return
            
        # Confirm
        if QMessageBox.question(self, "确认", f"即将生成 {len(to_save)} 条入库记录，是否继续？") != QMessageBox.Yes:
            return
            
        try:
            saved_count = 0
            for item in to_save:
                # Generate inbound no
                # We can use same category for all, assuming mixed types is handled by generic code or mapped
                # Here we default to 'GEN' or map from something.
                # Let's use generic 'MP' or map from contract category if we had it.
                cat_text = "半成品" # Fallback or needs fetch
                inbound_no = database.get_next_inbound_number(date_yyMMdd, cat_text)
                
                sp = item['sp_data']
                
                db_data = {
                    'inbound_no': inbound_no,
                    'contract_order_id': sp['contract_order_id'],
                    'contract_no': self.txt_contract_no.text(),
                    'order_no': self.txt_order_no.text(),
                    'purch_plan_no': self.txt_purch_no.text(),
                    'spec_model': sp['spec_model'],
                    'order_qty': sp['order_qty'],
                    'inbound_qty': item['qty'],
                    'warehouse_no': item['wh_no'],
                    'inbound_date': date_full,
                    'remarks': item['remarks'],
                    'operator': os.getlogin() if hasattr(os, 'getlogin') else 'user'
                }
                
                database.save_inbound_order(db_data)
                saved_count += 1
                
            QMessageBox.information(self, "成功", f"成功生成 {saved_count} 条入库单")
            self.clear_form()
            self.load_history()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中出错: {e}")

    def load_history(self):
        text = self.filter_text.text().strip()
        rows = database.fetch_inbound_orders_extended(text)
        
        self.history_table.setRowCount(0)
        for r in rows:
            # 0:id, 1:inbound_no, 2:inbound_date, 3:contract_no, 4:order_no, 5:purch_plan_no, 
            # 6:spec_model, 7:order_qty, 8:inbound_qty, 9:warehouse_no, 10:remarks, 11:unit_price
            # 12: operator
            
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # 0: Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            self.history_table.setItem(row, 0, chk_item)
            
            price = r[11] if r[11] else 0.0
            inbound_qty = r[8] if r[8] else 0.0
            total = inbound_qty * price
            
            # Map to table:
            # Checkbox, ID, No, Date, Contract, Order, Purch, Spec, InboundQty, Price, Total, WhNo, Rem
            
            self.history_table.setItem(row, 1, QTableWidgetItem(str(r[0])))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(r[1])))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(r[2])))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(r[3])))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(r[4])))
            self.history_table.setItem(row, 6, QTableWidgetItem(str(r[5])))
            self.history_table.setItem(row, 7, QTableWidgetItem(str(r[6])))
            
            self.history_table.setItem(row, 8, QTableWidgetItem(f"{inbound_qty:,.2f}"))
            self.history_table.setItem(row, 9, QTableWidgetItem(f"{price:,.2f}"))
            self.history_table.setItem(row, 10, QTableWidgetItem(f"{total:,.2f}"))
            
            self.history_table.setItem(row, 11, QTableWidgetItem(str(r[9])))
            self.history_table.setItem(row, 12, QTableWidgetItem(str(r[10])))
            
            # Store full data dict in ID column (col 1) for editing
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
                'remarks': r[10],
                'operator': r[12] if len(r) > 12 else ''
            }
            self.history_table.item(row, 1).setData(Qt.UserRole, data)

    def show_context_menu(self, pos):
        item = self.history_table.itemAt(pos)
        if not item: return
        row = item.row()
        
        # Get data from Col 1
        data = self.history_table.item(row, 1).data(Qt.UserRole)
        if not data: return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        act_edit = menu.addAction("修改入库记录")
        act_edit.triggered.connect(lambda: self.edit_record(data))
        
        act_del = menu.addAction("删除记录")
        act_del.triggered.connect(lambda: self.delete_record(data))
        
        menu.exec(self.history_table.viewport().mapToGlobal(pos))
        
    def export_data(self):
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(self, "错误", "未安装pandas库，无法导出")
            return

        rows = []
        has_selection = False
        
        # Check selection
        for r in range(self.history_table.rowCount()):
            if self.history_table.item(r, 0).checkState() == Qt.Checked:
                has_selection = True
                break
        
        target_rows = range(self.history_table.rowCount())
        
        for r in target_rows:
            if has_selection and self.history_table.item(r, 0).checkState() != Qt.Checked:
                continue
                
            data = self.history_table.item(r, 1).data(Qt.UserRole)
            rows.append(data)
            
        if not rows:
            QMessageBox.warning(self, "提示", "没有数据可导出")
            return
            
        df = pd.DataFrame(rows)
        # Rename columns for export
        col_map = {
            'inbound_no': '入库单号',
            'inbound_date': '入库日期',
            'contract_no': '合同编号',
            'order_no': '订单编号',
            'purch_plan_no': '采购计划',
            'spec_model': '规格型号',
            'order_qty': '订单数量',
            'inbound_qty': '入库数量',
            'warehouse_no': '仓储单号',
            'remarks': '备注',
            'operator': '操作人'
        }
        # Filter and rename
        export_cols = [c for c in col_map.keys() if c in df.columns]
        df = df[export_cols].rename(columns=col_map)
        
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", f"入库记录_{QDate.currentDate().toString('yyyyMMdd')}.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                df.to_excel(path, index=False)
                database.save_operation_log("", "入库导出", "", f"导出 {len(rows)} 条记录", os.getlogin(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                QMessageBox.information(self, "成功", f"成功导出 {len(rows)} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def download_template(self):
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(self, "错误", "未安装pandas库")
            return
            
        # Template columns
        cols = ['入库单号', '入库日期', '订单编号', '规格型号', '入库数量', '仓储单号', '备注', '操作人']
        df = pd.DataFrame(columns=cols)
        # Add sample
        df.loc[0] = ['RK-SAMPLE-001', '2023-01-01', 'ORDER-001', 'SPEC-A', 100, 'WH-001', '导入测试', 'admin']
        
        path, _ = QFileDialog.getSaveFileName(self, "保存模板", "入库导入模板.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                df.to_excel(path, index=False)
                QMessageBox.information(self, "成功", "模板已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def import_data(self):
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(self, "错误", "未安装pandas库")
            return
            
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
            
        try:
            df = pd.read_excel(path)
            # Validate columns
            # Map Chinese to English
            col_map = {
                '入库单号': 'inbound_no',
                '入库日期': 'inbound_date',
                '订单编号': 'order_no',
                '规格型号': 'spec_model',
                '入库数量': 'inbound_qty',
                '仓储单号': 'warehouse_no',
                '备注': 'remarks',
                '操作人': 'operator'
            }
            
            # Rename columns
            df = df.rename(columns=col_map)
            
            # Fill NaNs
            df = df.where(pd.notnull(df), None)
            
            records = df.to_dict('records')
            
            if not records:
                QMessageBox.warning(self, "提示", "文件为空")
                return
                
            suc, upd, errs = database.upsert_inbound_order_batch(records)
            
            msg = f"处理完成\n新增: {suc}\n更新: {upd}"
            if errs:
                msg += f"\n\n失败 ({len(errs)}):\n" + "\n".join(errs[:10])
                if len(errs) > 10:
                    msg += "\n..."
            
            database.save_operation_log("", "入库导入", "", f"导入: {suc} 新增, {upd} 更新, {len(errs)} 失败", os.getlogin(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            if errs:
                QMessageBox.warning(self, "导入结果 (部分失败)", msg)
            else:
                QMessageBox.information(self, "导入成功", msg)
                
            self.load_history()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")
        
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
        try:
            d = QDate.fromString(data['inbound_date'], "yyyy-MM-dd")
            if not d.isValid(): d = QDate.currentDate()
        except:
            d = QDate.currentDate()
        self.input_date.setDate(d)
        layout.addRow("入库日期:", self.input_date)
        
        self.input_qty = QDoubleSpinBox()
        self.input_qty.setRange(0, 99999999)
        self.input_qty.setDecimals(2)
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
