from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFileDialog, QProgressBar, QAbstractItemView
)
from PySide6.QtCore import Qt
import pandas as pd
import database

class MonthlyPlanWidget(QWidget):
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
        self.combo_month.currentTextChanged.connect(self.load_data)
        toolbar.addWidget(self.combo_month)
        
        btn_refresh = QPushButton("刷新统计")
        btn_refresh.clicked.connect(self.load_data)
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
        
        btn_save = QPushButton("保存变更")
        btn_save.clicked.connect(self.save_all)
        toolbar.addWidget(btn_save)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "标的名称", "规格型号", "单位", "需求部门", 
            "计划数量", "计划预算(万)", "执行数量", "执行金额", "执行进度", "备注"
        ])
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Adjust column widths
        self.table.setColumnWidth(1, 150) # Item Name
        self.table.setColumnWidth(2, 120) # Spec
        self.table.setColumnWidth(3, 60)  # Unit
        self.table.setColumnWidth(4, 100) # Dept
        self.table.setColumnWidth(5, 80)  # Plan Qty
        self.table.setColumnWidth(6, 100) # Plan Budget
        self.table.setColumnWidth(7, 80)  # Exec Qty
        self.table.setColumnWidth(8, 100) # Exec Amt
        self.table.setColumnWidth(9, 150) # Progress
        self.table.setColumnWidth(10, 150) # Remark
        
        self.table.setColumnHidden(0, True) # Hide ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        self._loading = False

    def load_months(self):
        self.combo_month.clear()
        months = database.fetch_plan_months()
        self.combo_month.addItems(months)
        if months:
            self.combo_month.setCurrentIndex(0)
            self.load_data() # Explicitly load for first time
            
    def load_data(self):
        self._loading = True
        month = self.combo_month.currentText()
        if not month:
            self.table.setRowCount(0)
            self._loading = False
            return
            
        data = database.fetch_monthly_plans_with_stats(month)
        self.table.setRowCount(len(data))
        
        for r, row in enumerate(data):
            # row: id, item_name, spec, unit, plan_qty, plan_budget, dept, remarks, exec_qty, exec_amt
            row_id, item_name, spec, unit, plan_qty, plan_budget, dept, remarks, exec_qty, exec_amt = row
            
            self.set_item(r, 0, str(row_id))
            self.set_item(r, 1, item_name)
            self.set_item(r, 2, spec)
            self.set_item(r, 3, unit)
            
            # Dept as Combo
            self.table.setCellWidget(r, 4, self.create_dept_combo(dept))
            
            self.set_item(r, 5, str(plan_qty) if plan_qty is not None else "0")
            self.set_item(r, 6, str(plan_budget) if plan_budget is not None else "0")
            
            # Read only execution stats
            item_exec_qty = QTableWidgetItem(str(exec_qty))
            item_exec_qty.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 7, item_exec_qty)
            
            item_exec_amt = QTableWidgetItem(f"{exec_amt:,.2f}")
            item_exec_amt.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 8, item_exec_amt)
            
            # Progress Bar
            progress = 0
            try:
                pq = float(plan_qty) if plan_qty else 0
                if pq > 0:
                    progress = min(100, int((exec_qty / pq) * 100))
            except:
                progress = 0
            
            pbar = QProgressBar()
            pbar.setValue(progress)
            pbar.setAlignment(Qt.AlignCenter)
            pbar.setTextVisible(True)
            pbar.setFormat(f"%p% ({exec_qty}/{plan_qty})")
            if progress >= 100:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }") # Green
            else:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #3498db; }") # Blue
            self.table.setCellWidget(r, 9, pbar)
            
            self.set_item(r, 10, remarks)
            
        self._loading = False

    def set_item(self, row, col, text):
        item = QTableWidgetItem(str(text) if text is not None else "")
        self.table.setItem(row, col, item)

    def create_dept_combo(self, current_text=""):
        combo = QComboBox()
        combo.setEditable(True) # Allow custom input if needed, or strictly select? Usually strictly select but user might want flexibility
        # Based on user request "needs to pick from settings-units", so we load units.
        # But if the current value is not in the list, we should probably add it or allow it.
        # Let's make it editable for flexibility, or strictly selection. 
        # Requirement says "pick from settings-units", usually implies strict selection but editable is safer for existing data.
        combo.addItems(database.fetch_units())
        combo.setCurrentText(current_text)
        return combo

    def save_all(self):
        month = self.combo_month.currentText()
        if not month:
            return
        
        # Helper to safely get text from item
        def safe_text(r, c):
            it = self.table.item(r, c)
            return it.text().strip() if it else ""
            
        for r in range(self.table.rowCount()):
            row_id = safe_text(r, 0)
            item_name = safe_text(r, 1)
            spec = safe_text(r, 2)
            unit = safe_text(r, 3)
            
            # Dept from Combo
            dept_widget = self.table.cellWidget(r, 4)
            if isinstance(dept_widget, QComboBox):
                dept = dept_widget.currentText().strip()
            else:
                dept = safe_text(r, 4)
            
            try:
                plan_qty = float(safe_text(r, 5) or "0")
            except:
                plan_qty = 0.0
                
            try:
                plan_budget = float(safe_text(r, 6) or "0")
            except:
                plan_budget = 0.0
                
            remarks = safe_text(r, 10)
            
            # Skip empty rows (no item name) to avoid inserting garbage
            if not item_name and not spec:
                continue

            if not row_id: # New row
                database.save_monthly_plan(None, month, item_name, spec, unit, plan_qty, plan_budget, dept, remarks)
            else:
                database.save_monthly_plan(int(row_id), month, item_name, spec, unit, plan_qty, plan_budget, dept, remarks)
                
        QMessageBox.information(self, "成功", "保存成功")
        self.load_data()

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.set_item(r, 0, "") # No ID
        # Initialize other items to avoid None issues
        for c in [1, 2, 3, 5, 6, 10]:
            self.set_item(r, c, "")
            
        # Dept Combo
        self.table.setCellWidget(r, 4, self.create_dept_combo("仓储中心"))
        
        pbar = QProgressBar()
        pbar.setValue(0)
        self.table.setCellWidget(r, 9, pbar)

    def delete_row(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "提示", "请先选择一行")
            return
            
        row_id = self.table.item(r, 0).text()
        if row_id:
            if QMessageBox.question(self, "确认", "确定删除该行计划吗？") == QMessageBox.Yes:
                database.delete_monthly_plan(int(row_id))
                self.table.removeRow(r)
        else:
            self.table.removeRow(r)

    def import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
            
        try:
            df = pd.read_excel(path)
            # Normalize column names (strip spaces)
            df.columns = df.columns.str.strip()
            
            if "标的名称" not in df.columns:
                QMessageBox.critical(self, "错误", "Excel中必须包含列：标的名称")
                return
            
            month = self.combo_month.currentText()
            if not month:
                QMessageBox.warning(self, "提示", "请先选择计划月份")
                return

            rows_to_insert = []
            
            for _, row in df.iterrows():
                item_name = str(row.get("标的名称", "")).strip()
                if not item_name or str(item_name).lower() == 'nan': continue
                
                spec = str(row.get("规格型号", ""))
                if str(spec).lower() == 'nan': spec = ""
                
                unit = str(row.get("单位", ""))
                if str(unit).lower() == 'nan': unit = ""
                
                try:
                    qty = float(row.get("计划数量", 0))
                except:
                    qty = 0
                
                try:
                    budget = float(row.get("计划预算", 0))
                except:
                    budget = 0
                    
                dept = str(row.get("需求部门", ""))
                if str(dept).lower() == 'nan': dept = ""
                
                rem = str(row.get("备注", ""))
                if str(rem).lower() == 'nan': rem = ""
                
                rows_to_insert.append((month, item_name, spec, unit, qty, budget, dept, rem))
                
            if rows_to_insert:
                database.import_monthly_plans(rows_to_insert)
                QMessageBox.information(self, "成功", f"成功导入 {len(rows_to_insert)} 条数据")
                self.load_data()
            else:
                QMessageBox.information(self, "提示", "未找到有效数据")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
