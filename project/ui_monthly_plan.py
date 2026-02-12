from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFileDialog, QProgressBar, QAbstractItemView,
    QTabWidget, QStyledItemDelegate, QLineEdit, QMenu, QApplication
)
from PySide6.QtGui import QDoubleValidator, QAction
from PySide6.QtCore import Qt, Signal
import pandas as pd
import database
import os

class MoneyDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        try:
            if not value: return ""
            val_str = str(value).replace(",", "")
            if not val_str: return ""
            f = float(val_str)
            return f"{f:,.2f}"
        except:
            return str(value)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        validator = QDoubleValidator(parent)
        validator.setDecimals(2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.EditRole)
        if text:
            editor.setText(str(text).replace(",", ""))
        else:
            editor.setText("")

    def setModelData(self, editor, model, index):
        text = editor.text().strip()
        try:
            if not text:
                model.setData(index, "0.00", Qt.EditRole)
                return
            val = float(text)
            model.setData(index, f"{val:.2f}", Qt.EditRole)
        except ValueError:
            pass 

class MonthlyPlanViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("计划月份:"))
        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(100)
        self.combo_month.currentTextChanged.connect(self.load_data)
        toolbar.addWidget(self.combo_month)
        
        btn_refresh = QPushButton("刷新统计")
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "标的名称", "规格型号", "单位", "需求部门", 
            "计划数量", "计划预算(万)", "执行数量", "执行金额", "执行进度", "备注"
        ])
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        # Delegates
        self.table.setItemDelegateForColumn(4, MoneyDelegate(self.table)) # Plan Qty (using MoneyDelegate for formatting if needed, though usually integer/float)
        self.table.setItemDelegateForColumn(5, MoneyDelegate(self.table)) # Budget
        self.table.setItemDelegateForColumn(6, MoneyDelegate(self.table)) # Exec Qty
        self.table.setItemDelegateForColumn(7, MoneyDelegate(self.table)) # Exec Amt
        
        layout.addWidget(self.table)
        
    def load_months(self):
        current = self.combo_month.currentText()
        self.combo_month.blockSignals(True)
        self.combo_month.clear()
        months = database.fetch_plan_months()
        self.combo_month.addItems(months)
        if current in months:
            self.combo_month.setCurrentText(current)
        elif months:
            self.combo_month.setCurrentIndex(0)
        self.combo_month.blockSignals(False)
        self.load_data()

    def load_data(self):
        month = self.combo_month.currentText()
        if not month:
            self.table.setRowCount(0)
            return
            
        data = database.fetch_monthly_plans_with_stats(month)
        
        # Filter: Only show records where plan_qty != 0
        filtered_data = []
        for row in data:
            # row: id, item_name, spec, unit, plan_qty, plan_budget, dept, remarks, exec_qty, exec_amt
            try:
                pq = float(row[4]) if row[4] else 0
            except:
                pq = 0
            if abs(pq) > 0.0001:
                filtered_data.append(row)
                
        self.table.setRowCount(len(filtered_data))
        
        for r, row in enumerate(filtered_data):
            # row: id, item_name, spec, unit, plan_qty, plan_budget, dept, remarks, exec_qty, exec_amt
            item_name, spec, unit, plan_qty, plan_budget, dept, remarks, exec_qty, exec_amt = row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]
            
            self.set_item(r, 0, item_name)
            self.set_item(r, 1, spec)
            self.set_item(r, 2, unit)
            self.set_item(r, 3, dept)
            self.set_item(r, 4, plan_qty) # Formatted by delegate
            self.set_item(r, 5, plan_budget)
            self.set_item(r, 6, exec_qty)
            self.set_item(r, 7, exec_amt)
            
            # Progress
            progress = 0
            try:
                pq = float(plan_qty) if plan_qty else 0
                if pq > 0:
                    progress = min(100, int((exec_qty / pq) * 100))
            except:
                pass
                
            pbar = QProgressBar()
            pbar.setValue(progress)
            pbar.setAlignment(Qt.AlignCenter)
            pbar.setFormat(f"%p% ({exec_qty:g}/{pq:g})")
            if progress >= 100:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
            else:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #3498db; }")
            self.table.setCellWidget(r, 8, pbar)
            
            self.set_item(r, 9, remarks)

    def set_item(self, row, col, value):
        text = str(value) if value is not None else ""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)

class MonthlyPlanEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dirty = False
        self.ignore_changes = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("计划月份:"))
        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(100)
        # Handle click/change manually to support "Cancel switch"
        # We use an event filter or a custom behavior? 
        # Easier: Connect to activated (user interaction) which triggers before index change? 
        # No, currentTextChanged is post-facto.
        # We'll use a wrapper method for changing logic.
        # But QComboBox signals are emitted after change.
        # We can store 'current_month' and revert if needed.
        self.combo_month.currentIndexChanged.connect(self.on_month_changed)
        toolbar.addWidget(self.combo_month)
        
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh_data)
        toolbar.addWidget(btn_refresh)
        
        btn_add = QPushButton("新增行")
        btn_add.clicked.connect(self.add_row)
        toolbar.addWidget(btn_add)
        
        btn_del = QPushButton("删除行")
        btn_del.clicked.connect(self.delete_row)
        toolbar.addWidget(btn_del)
        
        btn_import = QPushButton("导入Excel")
        btn_import.clicked.connect(self.import_excel)
        toolbar.addWidget(btn_import)
        
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_data)
        toolbar.addWidget(btn_save)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Loading Label
        self.lbl_loading = QLabel("正在加载...")
        self.lbl_loading.setVisible(False)
        layout.addWidget(self.lbl_loading)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "标的名称", "规格型号", "单位", "需求部门", 
            "计划数量", "计划预算(万)", "备注"
        ])
        self.table.setColumnHidden(0, True) # Hide ID
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        
        # Delegates
        self.table.setItemDelegateForColumn(5, MoneyDelegate(self.table)) # Qty
        self.table.setItemDelegateForColumn(6, MoneyDelegate(self.table)) # Budget
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
        
        self.current_month_text = ""
        
    def load_months(self):
        self.combo_month.blockSignals(True)
        self.combo_month.clear()
        months = database.fetch_plan_months()
        self.combo_month.addItems(months)
        if months:
            self.combo_month.setCurrentIndex(0)
            self.current_month_text = months[0]
            self.load_data(months[0])
        self.combo_month.blockSignals(False)
        
    def on_month_changed(self, index):
        new_month = self.combo_month.itemText(index)
        if new_month == self.current_month_text:
            return
            
        if self.is_dirty:
            reply = QMessageBox.question(
                self, "未保存修改", 
                "当前修改未保存，是否保存？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.save_data()
                # If save failed (e.g. validation), revert combo?
                # For simplicity, assume save success or we proceed.
                pass
            elif reply == QMessageBox.Cancel:
                # Revert combo
                self.combo_month.blockSignals(True)
                self.combo_month.setCurrentText(self.current_month_text)
                self.combo_month.blockSignals(False)
                return
            elif reply == QMessageBox.No:
                pass # Discard
                
        self.current_month_text = new_month
        self.load_data(new_month)

    def load_data(self, month):
        self.lbl_loading.setVisible(True)
        self.lbl_loading.repaint() # Force update
        self.ignore_changes = True
        
        # Fetch data for this month
        data = database.fetch_monthly_plans_with_stats(month)
        
        if not data:
            # Empty month. Logic:
            # If we have rows in the table (from previous month), keep them but reset values.
            # If table is empty (fresh start), it stays empty.
            if self.table.rowCount() > 0:
                # We are carrying over structure
                for r in range(self.table.rowCount()):
                    self.table.setItem(r, 0, QTableWidgetItem("")) # Clear ID
                    self.table.setItem(r, 5, QTableWidgetItem("0.00")) # Reset Qty
                    self.table.setItem(r, 6, QTableWidgetItem("0.00")) # Reset Budget
                    self.table.item(r, 5).setBackground(Qt.yellow) # Highlight as new/reset
                    self.table.item(r, 6).setBackground(Qt.yellow)
            else:
                self.table.setRowCount(0)
        else:
            self.table.setRowCount(len(data))
            for r, row in enumerate(data):
                # row: id, item_name, spec, unit, plan_qty, plan_budget, dept, remarks, ...
                self.set_item(r, 0, str(row[0]))
                self.set_item(r, 1, row[1])
                self.set_item(r, 2, row[2])
                self.set_item(r, 3, row[3])
                
                # Dept combo
                combo = QComboBox()
                combo.setEditable(True)
                combo.addItems(database.fetch_units())
                combo.setCurrentText(row[6] or "")
                # We need to capture changes in combo to set dirty flag
                combo.currentTextChanged.connect(self.set_dirty)
                self.table.setCellWidget(r, 4, combo)
                
                self.set_item(r, 5, row[4]) # Qty
                self.set_item(r, 6, row[5]) # Budget
                self.set_item(r, 7, row[7]) # Remark

        self.is_dirty = False
        self.ignore_changes = False
        self.lbl_loading.setVisible(False)

    def set_item(self, row, col, value):
        text = str(value) if value is not None else ""
        item = QTableWidgetItem(text)
        self.table.setItem(row, col, item)

    def on_item_changed(self, item):
        if not self.ignore_changes:
            self.set_dirty()
            
    def set_dirty(self):
        self.is_dirty = True
        
    def refresh_data(self):
        if self.is_dirty:
            if QMessageBox.question(self, "提示", "刷新将丢失未保存的修改，确定吗？", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        self.load_data(self.current_month_text)

    def add_row(self):
        self.ignore_changes = True
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.set_item(r, 0, "")
        for c in [1, 2, 3, 5, 6, 7]:
            self.set_item(r, c, "")
            
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(database.fetch_units())
        self.table.setCellWidget(r, 4, combo)
        combo.currentTextChanged.connect(self.set_dirty)
        
        self.ignore_changes = False
        self.set_dirty()
        
    def delete_row(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not rows:
            QMessageBox.warning(self, "提示", "请选择要删除的行")
            return
            
        if QMessageBox.question(self, "确认", f"确定删除选中的 {len(rows)} 行吗？") == QMessageBox.Yes:
            self.ignore_changes = True
            for r in rows:
                row_id = self.table.item(r, 0).text()
                if row_id:
                    database.delete_monthly_plan(int(row_id))
                self.table.removeRow(r)
            self.ignore_changes = False
            self.set_dirty() # Technically deletion is immediate for DB if ID exists? 
            # Wait, if I delete from DB immediately, I don't need to save.
            # But "Data Persistence" requirement says "All entered records permanent".
            # If I follow the pattern: UI edit -> Save button -> DB.
            # Then Delete should also be: UI remove -> Save button -> DB Delete?
            # Existing code did immediate delete.
            # Let's stick to immediate delete for rows with IDs to avoid complexity of tracking deleted IDs.
            # But for "Data Persistence" consistency, maybe I should batch?
            # The prompt says "Save button... All entered records permanent".
            # Immediate delete is fine as long as user confirms.
            
    def save_data(self):
        self.lbl_loading.setVisible(True)
        month = self.combo_month.currentText()
        if not month: return
        
        for r in range(self.table.rowCount()):
            row_id = self.table.item(r, 0).text()
            item_name = self.table.item(r, 1).text().strip()
            spec = self.table.item(r, 2).text().strip()
            unit = self.table.item(r, 3).text().strip()
            
            dept_widget = self.table.cellWidget(r, 4)
            dept = dept_widget.currentText().strip() if dept_widget else ""
            
            qty_str = self.table.item(r, 5).text().replace(",", "")
            budget_str = self.table.item(r, 6).text().replace(",", "")
            
            try:
                qty = float(qty_str) if qty_str else 0.0
            except:
                qty = 0.0
                
            try:
                budget = float(budget_str) if budget_str else 0.0
            except:
                budget = 0.0
                
            remarks = self.table.item(r, 7).text().strip()
            
            if not item_name and not spec: continue
            
            rid = int(row_id) if row_id else None
            database.save_monthly_plan(rid, month, item_name, spec, unit, qty, budget, dept, remarks)
            
        self.is_dirty = False
        self.lbl_loading.setVisible(False)
        QMessageBox.information(self, "成功", "保存成功")
        self.load_data(month) # Reload to get IDs

    def show_context_menu(self, pos):
        menu = QMenu(self)
        action_all = menu.addAction("全选")
        action_all.triggered.connect(self.table.selectAll)
        action_inv = menu.addAction("反选")
        action_inv.triggered.connect(self.invert_selection)
        menu.exec(self.table.viewport().mapToGlobal(pos))
        
    def invert_selection(self):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            # Check if the row is selected by checking the item in a visible column (e.g., column 1)
            item = self.table.item(r, 1)
            if item and item.isSelected():
                # Deselect row
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it: it.setSelected(False)
            else:
                # Select row
                self.table.selectRow(r)
        self.table.blockSignals(False)

    def import_excel(self):
        # Menu for Import or Download Template
        menu = QMenu(self)
        act_import = menu.addAction("导入Excel数据")
        act_template = menu.addAction("下载导入模板")
        
        action = menu.exec(self.cursor().pos())
        if action == act_template:
            self.download_template()
        elif action == act_import:
            self.do_import()
            
    def download_template(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存模板", "半成品计划导入模板.xlsx", "Excel Files (*.xlsx)")
        if not path: return
        
        data = {
            "标的名称": ["示例物品"],
            "规格型号": ["SPEC-001"],
            "单位": ["个"],
            "需求部门": ["生产部"],
            "计划数量": [100],
            "计划预算": [5000],
            "备注": ["说明"]
        }
        df = pd.DataFrame(data)
        try:
            df.to_excel(path, index=False)
            QMessageBox.information(self, "成功", "模板已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def do_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel Files (*.xlsx *.xls)")
        if not path: return
        
        try:
            df = pd.read_excel(path)
            df.columns = df.columns.str.strip()
            required = ["标的名称"]
            if not all(col in df.columns for col in required):
                QMessageBox.warning(self, "错误", "缺少必要列: 标的名称")
                return
            
            # Append to table
            self.ignore_changes = True
            for _, row in df.iterrows():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.set_item(r, 0, "")
                self.set_item(r, 1, str(row.get("标的名称", "")).strip())
                self.set_item(r, 2, str(row.get("规格型号", "")).strip())
                self.set_item(r, 3, str(row.get("单位", "")).strip())
                
                combo = QComboBox()
                combo.setEditable(True)
                combo.addItems(database.fetch_units())
                combo.setCurrentText(str(row.get("需求部门", "")).strip())
                self.table.setCellWidget(r, 4, combo)
                combo.currentTextChanged.connect(self.set_dirty)
                
                self.set_item(r, 5, str(row.get("计划数量", 0)))
                self.set_item(r, 6, str(row.get("计划预算", 0)))
                self.set_item(r, 7, str(row.get("备注", "")).strip())
                
            self.ignore_changes = False
            self.set_dirty()
            QMessageBox.information(self, "成功", "数据已导入到表格，请检查后保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

class MonthlyPlanWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.viewer = MonthlyPlanViewer()
        self.editor = MonthlyPlanEditor()
        
        self.tabs.addTab(self.viewer, "半成品月度计划")
        self.tabs.addTab(self.editor, "半成品月度计划录入")
        
        # When switching tabs, maybe refresh?
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)
        
    def load_data(self):
        self.viewer.load_months()
        self.editor.load_months()
        
    def on_tab_changed(self, index):
        if index == 0:
            self.viewer.load_months()
        else:
            self.editor.load_months()
