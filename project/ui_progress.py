import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QMessageBox,
    QProgressBar, QGridLayout, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt
import database
from collections import defaultdict
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

STATUS_OPTIONS = [
    "未启动", "询价中", "定点审批中", "合同流转中", 
    "已下单待收货", "部分到货", "已完成"
]

class ProgressDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Top filters
        filter_layout = QHBoxLayout()
        self.combo_month = QComboBox()
        self.combo_month.addItem("全部")
        self.combo_month.addItems(database.fetch_plan_months())
        
        self.combo_purchaser = QComboBox()
        self.combo_purchaser.addItem("全部")
        self.combo_purchaser.addItems(database.fetch_purchasers())
        
        self.btn_refresh = QPushButton("刷新图表")
        
        filter_layout.addWidget(QLabel("计划月份:"))
        filter_layout.addWidget(self.combo_month)
        filter_layout.addWidget(QLabel("采购员:"))
        filter_layout.addWidget(self.combo_purchaser)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addStretch()
        
        self.layout.addLayout(filter_layout)
        
        # Summary Cards
        self.cards_layout = QHBoxLayout()
        self.lbl_total = self._create_card("总计划数", "0")
        self.lbl_completed = self._create_card("已完成", "0")
        self.lbl_rate = self._create_card("整体完成率", "0%")
        self.layout.addLayout(self.cards_layout)
        
        # Charts Area
        charts_layout = QHBoxLayout()
        
        # Chart 1: Status Distribution (Pie Chart)
        self.fig_pie = Figure(figsize=(5, 4), dpi=100)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        charts_layout.addWidget(self.canvas_pie)
        
        # Chart 2: Purchaser Performance (Bar Chart)
        self.fig_bar = Figure(figsize=(6, 4), dpi=100)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        charts_layout.addWidget(self.canvas_bar)
        
        self.layout.addLayout(charts_layout)
        self.layout.setStretchFactor(charts_layout, 1)
        
        self.btn_refresh.clicked.connect(self.refresh_data)
        
    def _create_card(self, title, value):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                padding: 10px;
            }
            QLabel#title { color: #6c757d; font-size: 14px; }
            QLabel#value { color: #212529; font-size: 24px; font-weight: bold; }
        """)
        layout = QVBoxLayout(frame)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("title")
        lbl_val = QLabel(value)
        lbl_val.setObjectName("value")
        lbl_val.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        self.cards_layout.addWidget(frame)
        return lbl_val

    def refresh_data(self):
        month = self.combo_month.currentText()
        purchaser = self.combo_purchaser.currentText()
        
        total, completed, status_dist, purchaser_stats = database.get_progress_stats(month, purchaser)
        
        self.lbl_total.setText(str(total))
        self.lbl_completed.setText(str(completed))
        rate = (completed / total * 100) if total > 0 else 0
        self.lbl_rate.setText(f"{rate:.1f}%")
        
        # Update Pie Chart
        self.fig_pie.clear()
        ax_pie = self.fig_pie.add_subplot(111)
        if status_dist:
            labels = list(status_dist.keys())
            sizes = list(status_dist.values())
            ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax_pie.set_title('当前状态分布')
        else:
            ax_pie.text(0.5, 0.5, '暂无数据', ha='center', va='center')
        self.canvas_pie.draw()
        
        # Update Bar Chart
        self.fig_bar.clear()
        ax_bar = self.fig_bar.add_subplot(111)
        if purchaser_stats:
            names = list(purchaser_stats.keys())
            totals = [v['total'] for v in purchaser_stats.values()]
            completions = [v['completed'] for v in purchaser_stats.values()]
            
            x = range(len(names))
            ax_bar.bar(x, totals, label='总任务', color='#e9ecef')
            ax_bar.bar(x, completions, label='已完成', color='#20c997')
            
            ax_bar.set_xticks(x)
            ax_bar.set_xticklabels(names, rotation=45, ha='right')
            ax_bar.set_title('采购员执行进度对比')
            ax_bar.legend()
            self.fig_bar.tight_layout()
        else:
            ax_bar.text(0.5, 0.5, '暂无数据', ha='center', va='center')
        self.canvas_bar.draw()


class ProgressList(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.combo_month = QComboBox()
        self.combo_month.addItem("全部")
        self.combo_month.addItems(database.fetch_plan_months())
        
        self.combo_purchaser = QComboBox()
        self.combo_purchaser.addItem("全部")
        self.combo_purchaser.addItems(database.fetch_purchasers())
        
        self.btn_load = QPushButton("加载数据")
        
        self.combo_target_status = QComboBox()
        self.combo_target_status.addItems(STATUS_OPTIONS)
        self.btn_batch_update = QPushButton("批量更新状态")
        self.btn_batch_update.setStyleSheet("background-color: #0d6efd; color: white; font-weight: bold;")
        
        toolbar.addWidget(QLabel("计划月份:"))
        toolbar.addWidget(self.combo_month)
        toolbar.addWidget(QLabel("采购员:"))
        toolbar.addWidget(self.combo_purchaser)
        toolbar.addWidget(self.btn_load)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("目标状态:"))
        toolbar.addWidget(self.combo_target_status)
        toolbar.addWidget(self.btn_batch_update)
        
        self.layout.addLayout(toolbar)
        
        # TreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["勾选/编号", "名称/标的", "规格型号", "数量", "单位", "采购员", "当前状态"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 200)
        self.tree.setAlternatingRowColors(True)
        self.layout.addWidget(self.tree)
        
        self.btn_load.clicked.connect(self.load_data)
        self.btn_batch_update.clicked.connect(self.batch_update)
        self.tree.itemChanged.connect(self.on_item_changed)
        
        self._is_updating_tree = False
        
    def load_data(self):
        self._is_updating_tree = True
        self.tree.clear()
        
        month = self.combo_month.currentText()
        purchaser = self.combo_purchaser.currentText()
        
        plans = database.fetch_all_released_plans(month, purchaser)
        
        # Group by Master Order
        orders = defaultdict(list)
        for p in plans:
            orders[p['order_number']].append(p)
            
        for order_no, details in orders.items():
            task_name = details[0]['task_name']
            yymm = details[0]['yymm']
            
            # Create Parent Item
            parent = QTreeWidgetItem(self.tree)
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.Unchecked)
            parent.setText(0, order_no)
            parent.setText(1, task_name)
            parent.setText(2, f"月份: {yymm}")
            
            # Calculate progress
            completed = sum(1 for d in details if d['status'] == '已完成')
            total = len(details)
            parent.setText(6, f"进度: {completed}/{total}")
            
            # Make parent bold
            font = parent.font(0)
            font.setBold(True)
            for i in range(7):
                parent.setFont(i, font)
                parent.setBackground(i, Qt.lightGray)
            
            # Add Children
            for d in details:
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
                child.setText(0, d['detail_no'])
                child.setText(1, d['item_name'])
                child.setText(2, d['spec'])
                child.setText(3, str(d['qty']))
                child.setText(4, d['unit'])
                child.setText(5, d['purchaser'])
                child.setText(6, d['status'])
                
                # Store DB ID in user data for updates
                child.setData(0, Qt.UserRole, d['detail_id'])
                
                # Color code status
                if d['status'] == '已完成':
                    child.setForeground(6, Qt.darkGreen)
                elif d['status'] == '未启动':
                    child.setForeground(6, Qt.gray)
                else:
                    child.setForeground(6, Qt.blue)
                    
        self.tree.expandAll()
        self._is_updating_tree = False
        
    def on_item_changed(self, item, column):
        if self._is_updating_tree or column != 0:
            return
            
        self._is_updating_tree = True
        
        # Parent changed -> Update all children
        if item.parent() is None:
            state = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)
        # Child changed -> Update parent status
        else:
            parent = item.parent()
            checked_count = 0
            for i in range(parent.childCount()):
                if parent.child(i).checkState(0) == Qt.Checked:
                    checked_count += 1
                    
            if checked_count == 0:
                parent.setCheckState(0, Qt.Unchecked)
            elif checked_count == parent.childCount():
                parent.setCheckState(0, Qt.Checked)
            else:
                parent.setCheckState(0, Qt.PartiallyChecked)
                
        self._is_updating_tree = False

    def batch_update(self):
        target_status = self.combo_target_status.currentText()
        selected_ids = []
        
        # Gather all checked child items
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    detail_id = child.data(0, Qt.UserRole)
                    if detail_id:
                        selected_ids.append(detail_id)
                        
        if not selected_ids:
            QMessageBox.warning(self, "提示", "请先勾选需要更新的明细！")
            return
            
        reply = QMessageBox.question(self, "确认", f"确定将选中的 {len(selected_ids)} 条记录状态更新为【{target_status}】吗？")
        if reply == QMessageBox.Yes:
            database.update_detail_status_batch(selected_ids, target_status)
            QMessageBox.information(self, "成功", "状态更新成功！")
            self.load_data()


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.dashboard = ProgressDashboard()
        self.list_view = ProgressList()
        
        self.tabs.addTab(self.dashboard, "📈 进度看板")
        self.tabs.addTab(self.list_view, "📝 状态更新列表")
        
        layout.addWidget(self.tabs)
        
        # Connect tab change to refresh dashboard if switching to it
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Initial load
        self.list_view.load_data()
        self.dashboard.refresh_data()
        
    def on_tab_changed(self, index):
        if index == 0: # Dashboard tab
            self.dashboard.refresh_data()
