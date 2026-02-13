import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, 
    QSplitter, QFrame, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import database
import pandas as pd

# Matplotlib integration
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Set font for matplotlib to support Chinese
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

class ContractReportWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- 1. Top Filter Area ---
        filter_layout = QHBoxLayout()
        
        self.combo_year = QComboBox()
        self.combo_year.addItem("全部年份")
        current_year = datetime.datetime.now().year
        for y in range(current_year, current_year - 5, -1):
            self.combo_year.addItem(str(y))
            
        self.combo_supplier = QComboBox()
        self.combo_supplier.addItem("全部供应商")
        self.combo_supplier.addItems(database.fetch_suppliers())
        
        self.combo_category = QComboBox()
        self.combo_category.addItem("全部类别")
        self.combo_category.addItems(database.fetch_contract_categories())
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.load_data)
        
        self.btn_export = QPushButton("导出报表")
        self.btn_export.clicked.connect(self.export_report)
        
        filter_layout.addWidget(QLabel("年份:"))
        filter_layout.addWidget(self.combo_year)
        filter_layout.addWidget(QLabel("供应商:"))
        filter_layout.addWidget(self.combo_supplier)
        filter_layout.addWidget(QLabel("类别:"))
        filter_layout.addWidget(self.combo_category)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addWidget(self.btn_export)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # --- 2. KPI Cards ---
        kpi_layout = QHBoxLayout()
        self.card_total = self.create_kpi_card("合同总额", "¥ 0.00", "#007bff")
        self.card_exec = self.create_kpi_card("累计执行", "¥ 0.00", "#28a745")
        self.card_inv = self.create_kpi_card("累计开票", "¥ 0.00", "#17a2b8")
        self.card_settled = self.create_kpi_card("累计结算", "¥ 0.00", "#ffc107") # Using yellow for settled as 'completed' ish
        
        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_exec)
        kpi_layout.addWidget(self.card_inv)
        kpi_layout.addWidget(self.card_settled)
        
        layout.addLayout(kpi_layout)
        
        # --- 3. Charts Area ---
        splitter = QSplitter(Qt.Vertical)
        
        chart_container = QWidget()
        chart_layout = QHBoxLayout(chart_container)
        
        # Bar Chart: Top 10 Contracts
        self.fig_bar = Figure(figsize=(5, 4), dpi=100)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        chart_layout.addWidget(self.canvas_bar, stretch=2)
        
        # Pie Chart: Status Distribution
        self.fig_pie = Figure(figsize=(4, 4), dpi=100)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        chart_layout.addWidget(self.canvas_pie, stretch=1)
        
        splitter.addWidget(chart_container)
        
        # --- 4. Detail Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "合同编号", "合同名称", "供应商", "类别", "签订日期", 
            "合同金额", "执行金额", "开票金额", "结算金额"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        splitter.addWidget(self.table)
        
        layout.addWidget(splitter)
        
        # Connect signals
        self.combo_year.currentTextChanged.connect(self.load_data)
        self.combo_supplier.currentTextChanged.connect(self.load_data)
        self.combo_category.currentTextChanged.connect(self.load_data)

    def create_kpi_card(self, title, value, color):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"QFrame {{ background-color: {color}; border-radius: 8px; color: white; }}")
        vbox = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet("font-size: 20px; font-weight: bold;")
        lbl_val.setAlignment(Qt.AlignCenter)
        lbl_val.setObjectName("value_label") # For finding later
        
        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        return frame

    def update_kpi_card(self, card, value):
        lbl = card.findChild(QLabel, "value_label")
        if lbl:
            lbl.setText(value)

    def load_data(self):
        year = self.combo_year.currentText()
        year = year if year != "全部年份" else None
        
        supplier = self.combo_supplier.currentText()
        supplier = supplier if supplier != "全部供应商" else None
        
        category = self.combo_category.currentText()
        category = category if category != "全部类别" else None
        
        data = database.fetch_contract_statistics(year, supplier, category)
        
        # 1. Update KPI
        total_amt = sum(d['total_amount'] for d in data)
        exec_amt = sum(d['executed_amount'] for d in data)
        inv_amt = sum(d['invoiced_amount'] for d in data)
        settled_amt = sum(d['settled_amount'] for d in data)
        
        self.update_kpi_card(self.card_total, f"¥ {total_amt:,.2f}")
        self.update_kpi_card(self.card_exec, f"¥ {exec_amt:,.2f}")
        self.update_kpi_card(self.card_inv, f"¥ {inv_amt:,.2f}")
        self.update_kpi_card(self.card_settled, f"¥ {settled_amt:,.2f}")
        
        # 2. Update Table
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        for d in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(d['contract_number']))
            self.table.setItem(row, 1, QTableWidgetItem(d['contract_name']))
            self.table.setItem(row, 2, QTableWidgetItem(d['supplier']))
            self.table.setItem(row, 3, QTableWidgetItem(d['category']))
            self.table.setItem(row, 4, QTableWidgetItem(d['sign_date']))
            
            # Numeric items for sorting
            item_total = QTableWidgetItem(f"{d['total_amount']:,.2f}")
            item_total.setData(Qt.UserRole, d['total_amount'])
            self.table.setItem(row, 5, item_total)
            
            item_exec = QTableWidgetItem(f"{d['executed_amount']:,.2f}")
            item_exec.setData(Qt.UserRole, d['executed_amount'])
            self.table.setItem(row, 6, item_exec)
            
            item_inv = QTableWidgetItem(f"{d['invoiced_amount']:,.2f}")
            item_inv.setData(Qt.UserRole, d['invoiced_amount'])
            self.table.setItem(row, 7, item_inv)
            
            item_set = QTableWidgetItem(f"{d['settled_amount']:,.2f}")
            item_set.setData(Qt.UserRole, d['settled_amount'])
            self.table.setItem(row, 8, item_set)
            
        self.table.setSortingEnabled(True)
        
        # 3. Update Charts
        self.plot_bar_chart(data)
        self.plot_pie_chart(total_amt, exec_amt, settled_amt)

    def plot_bar_chart(self, data):
        self.fig_bar.clear()
        ax = self.fig_bar.add_subplot(111)
        
        # Sort by total amount and take top 10
        sorted_data = sorted(data, key=lambda x: x['total_amount'], reverse=True)[:10]
        if not sorted_data:
            self.canvas_bar.draw()
            return
            
        names = [d['contract_name'] for d in sorted_data]
        totals = [d['total_amount'] for d in sorted_data]
        execs = [d['executed_amount'] for d in sorted_data]
        settled = [d['settled_amount'] for d in sorted_data]
        
        x = range(len(names))
        width = 0.25
        
        ax.bar([i - width for i in x], totals, width, label='合同总额', color='#007bff')
        ax.bar(x, execs, width, label='执行金额', color='#28a745')
        ax.bar([i + width for i in x], settled, width, label='结算金额', color='#ffc107')
        
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.set_title('Top 10 合同资金情况')
        ax.legend()
        
        self.fig_bar.tight_layout()
        self.canvas_bar.draw()

    def plot_pie_chart(self, total, executed, settled):
        self.fig_pie.clear()
        ax = self.fig_pie.add_subplot(111)
        
        if total == 0:
            self.canvas_pie.draw()
            return
            
        # Segments: Settled, Executed (Unsettled), Unexecuted
        # Executed (Unsettled) = Executed - Settled
        # Unexecuted = Total - Executed
        
        executed_unsettled = max(0, executed - settled)
        unexecuted = max(0, total - executed)
        
        sizes = [settled, executed_unsettled, unexecuted]
        labels = ['已结算', '执行中(未结)', '未执行']
        colors = ['#ffc107', '#28a745', '#e0e0e0']
        
        # Filter out zeros
        final_sizes = []
        final_labels = []
        final_colors = []
        
        for s, l, c in zip(sizes, labels, colors):
            if s > 0:
                final_sizes.append(s)
                final_labels.append(l)
                final_colors.append(c)
        
        if final_sizes:
            ax.pie(final_sizes, labels=final_labels, colors=final_colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('资金状态分布')
        
        self.fig_pie.tight_layout()
        self.canvas_pie.draw()

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", f"合同报表_{datetime.date.today()}.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
            
        try:
            # Extract data from table
            rows = []
            for r in range(self.table.rowCount()):
                row_data = []
                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    # Try to get raw data if available, else text
                    if item.data(Qt.UserRole):
                        row_data.append(item.data(Qt.UserRole))
                    else:
                        row_data.append(item.text())
                rows.append(row_data)
                
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            
            df = pd.DataFrame(rows, columns=headers)
            df.to_excel(path, index=False)
            QMessageBox.information(self, "成功", "导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
