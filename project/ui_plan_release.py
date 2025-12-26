from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QTabWidget,
    QComboBox,
    QDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer

class PlanReleaseForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tab_release = QWidget()
        self.tab_print_template = QWidget()
        
        self.tabs.addTab(self.tab_release, "发放列表")
        self.tabs.addTab(self.tab_print_template, "打印模板")
        
        layout.addWidget(self.tabs)
        
        # --- Tab 1: Plan Release List ---
        self.setup_release_tab()
        
        # --- Tab 2: Print Template ---
        self.setup_print_template_tab()

    def setup_release_tab(self):
        # Use a stacked layout for the tab content to switch between list and detail
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self.tab_release)
        layout.addWidget(self.stack)
        
        # Page 1: List View
        self.page_list = QWidget()
        self.setup_list_page()
        self.stack.addWidget(self.page_list)
        
    def setup_list_page(self):
        layout = QVBoxLayout(self.page_list)
        
        # Top Filter Section
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setHorizontalSpacing(8)
        
        self.search_number = QLineEdit()
        self.search_number.setPlaceholderText("主单编号")
        
        self.search_purchaser = QLineEdit()
        self.search_purchaser.setPlaceholderText("采购员")
        
        self.search_task = QLineEdit()
        self.search_task.setPlaceholderText("采购任务名称")
        
        self.search_month = QLineEdit()
        self.search_month.setPlaceholderText("计划月份")
        
        self.search_unit = QLineEdit()
        self.search_unit.setPlaceholderText("需求单位")
        
        self.btn_search = QPushButton("搜索")
        self.btn_search.setObjectName("primary")
        self.btn_search.clicked.connect(self.load_data)
        
        # Layout filters evenly
        filter_layout.addWidget(self.search_number, 0, 0)
        filter_layout.addWidget(self.search_purchaser, 0, 1)
        filter_layout.addWidget(self.search_task, 0, 2)
        filter_layout.addWidget(self.search_month, 0, 3)
        filter_layout.addWidget(self.search_unit, 0, 4)
        filter_layout.addWidget(self.btn_search, 0, 5)
        
        layout.addWidget(filter_frame)
        
        # Table List
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "发放日期",
            "主单编号",
            "采购员",
            "采购任务名称",
            "需求单位",
            "计划月份",
            "记录条数",
            "处理状态",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.sectionResized.connect(self.on_header_resized)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(300)
        self._resize_timer.timeout.connect(self._flush_resize)
        self._pending_resize = None
        self.apply_saved_widths()
        
        layout.addWidget(self.table)
        
        self.table.doubleClicked.connect(self.open_detail)
        
        self.setStyleSheet(
            """
            QTableWidget { background: #FFFFFF; }
            QHeaderView::section { background: #ECECEC; padding: 6px; }
            QPushButton#primary { background: #2F80ED; color: #fff; padding: 5px 15px; border-radius: 4px; }
            """
        )

    def apply_saved_widths(self):
        import database
        widths = database.get_plan_release_column_widths()
        for col, w in widths.items():
            if 0 <= col < self.table.columnCount() and int(w) > 20:
                self.table.setColumnWidth(col, int(w))

    def on_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        self._pending_resize = (int(logicalIndex), int(newSize))
        self._resize_timer.start()

    def _flush_resize(self):
        if not self._pending_resize:
            return
        col, w = self._pending_resize
        self._pending_resize = None
        try:
            import database
            database.set_plan_release_column_width(col, w)
            database.set_layout_version("plan_release", "v1")
        except Exception:
            pass

    def setup_print_template_tab(self):
        from ui_print_template import PrintTemplateWidget
        layout = QVBoxLayout(self.tab_print_template)
        self.print_template_widget = PrintTemplateWidget(self)
        layout.addWidget(self.print_template_widget)

    def back_to_release_list(self):
        if hasattr(self, 'detail_page'):
            self.stack.removeWidget(self.detail_page)
            self.detail_page.deleteLater()
            del self.detail_page
        self.stack.setCurrentWidget(self.page_list)
        self.load_data()

    def open_release_detail_page(self, order_number, purchaser):
        self.detail_page = ReleaseDetailWidget(order_number, purchaser, self)
        self.stack.addWidget(self.detail_page)
        self.stack.setCurrentWidget(self.detail_page)


        
    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)
        
    def load_data(self):
        import database
        self.table.setRowCount(0)
        
        rows = database.fetch_release_orders(
            number_filter=self.search_number.text().strip(),
            purchaser_filter=self.search_purchaser.text().strip(),
            task_filter=self.search_task.text().strip(),
            month_filter=self.search_month.text().strip(),
            unit_filter=self.search_unit.text().strip(),
        )
        
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            # row: release_date, source_order_number, purchaser, task_name, unit, yymm, record_count, status
            for i, val in enumerate(row):
                self.table.setItem(r, i, QTableWidgetItem(str(val)))

    def open_detail(self, index):
        row = index.row()
        order_number = self.table.item(row, 1).text()
        purchaser = self.table.item(row, 2).text()
        
        # Switch to detail page instead of dialog
        self.open_release_detail_page(order_number, purchaser)


class ReleaseDetailWidget(QWidget):
    def __init__(self, order_number, purchaser, parent=None):
        super().__init__(parent)
        self.order_number = order_number
        self.purchaser = purchaser
        self.main_window = parent if hasattr(parent, "back_to_release_list") else None
        
        import database
        info = database.fetch_order_by_number(order_number)
        # yymm, category, unit, date, task_name
        if info:
            yymm, cat_code, unit, date_str, task_name = info
            cat_name = database.category_display_from_code(cat_code)
        else:
            yymm = unit = date_str = task_name = cat_name = ""
        
        layout = QVBoxLayout(self)
        
        # Header Info (Simplified version of Purchase Plan Detail)
        # 顶部区域：信息条 + 右侧操作按钮
        top_container = QFrame()
        top_container.setFrameShape(QFrame.NoFrame)
        top_h = QHBoxLayout(top_container)
        top_h.setContentsMargins(8, 6, 8, 6)
        top_h.setSpacing(8)
        
        # Left Info Area
        top = QFrame()
        top.setObjectName("detailHeader")
        top.setFrameShape(QFrame.StyledPanel)
        top_layout = QGridLayout(top)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setHorizontalSpacing(6)
        top_layout.setVerticalSpacing(6)
        
        self.h_number = QLabel(order_number)
        self.h_task = QLabel(task_name)
        self.h_yymm = QLabel(yymm)
        self.h_unit = QLabel(unit)
        self.h_category = QLabel(cat_name)
        self.h_date = QLabel(date_str)
        self.h_purchaser = QLabel(purchaser)
        
        for l in [self.h_number, self.h_task, self.h_yymm, self.h_unit, self.h_category, self.h_date, self.h_purchaser]:
            l.setObjectName("headerValue")
        
        LABEL_WIDTH = 90
        def pair(title: str, value_lbl: QLabel):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)
            lab = QLabel(f"{title}：")
            lab.setObjectName("headerLabel")
            lab.setFixedWidth(LABEL_WIDTH)
            h.addWidget(lab)
            h.addWidget(value_lbl, 1)
            return w

        top_layout.addWidget(pair("主单编号", self.h_number), 0, 0)
        top_layout.addWidget(pair("采购任务名称", self.h_task), 0, 1)
        top_layout.addWidget(pair("计划月份", self.h_yymm), 0, 2)
        top_layout.addWidget(pair("需求单位", self.h_unit), 1, 0)
        top_layout.addWidget(pair("标的类别", self.h_category), 1, 1)
        top_layout.addWidget(pair("日期", self.h_date), 1, 2)
        top_layout.addWidget(pair("采购员", self.h_purchaser), 2, 0)
        
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 1)
        top_layout.setColumnStretch(2, 1)

        
        # Right Actions Area
        actions_wrap = QFrame()
        actions_h = QHBoxLayout(actions_wrap)
        actions_h.setContentsMargins(0, 0, 0, 0)
        actions_h.setSpacing(8)
        
        self.btn_print = QPushButton("打印")
        self.btn_confirm = QPushButton("确认\n发放")
        self.btn_back = QPushButton("返回")
        
        for b in [self.btn_print, self.btn_confirm, self.btn_back]:
            b.setFixedSize(64, 64)
            
        self.btn_print.setObjectName("actPrint")
        self.btn_confirm.setObjectName("actSave") # Use save style (blue) or custom
        self.btn_back.setObjectName("actBack")
        
        actions_h.addWidget(self.btn_print)
        actions_h.addWidget(self.btn_confirm)
        actions_h.addWidget(self.btn_back)
        
        top_h.addWidget(top, 1)
        top_h.addWidget(actions_wrap, 0)
        layout.addWidget(top_container)

        # Table
        cols = [
            "序号", "采购标的", "规格型号", "采购数量", "单位", 
            "单价(元)", "总价(元)", "采购方式", "采购途径", 
            "计划发放", "进度要求", "询价(报价)", "税率", "备注"
        ]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Configure Table for Auto-Wrap and Auto-Row-Height
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.table)
        
        self.setStyleSheet(
            """
            QFrame#detailHeader { background: #F4F6F8; border: 1px solid #DFE3E8; border-radius: 8px; }
            QLabel#headerLabel { color: #6B7280; }
            QLabel#headerValue { color: #111827; font-weight: 600; }
            QPushButton { padding: 8px 16px; border-radius: 6px; font-weight: 600; }
            QPushButton#actSave { background: #0EA5E9; color: #fff; border-radius: 12px; }
            QPushButton#actPrint { background: #6366F1; color: #fff; border-radius: 12px; }
            QPushButton#actBack { background: #EF4444; color: #fff; border-radius: 12px; }
            QTableWidget { background: #FFFFFF; }
            QHeaderView::section { background: #ECECEC; padding: 6px; }
            """
        )
        
        self.load_data()
        
        self.btn_back.clicked.connect(self.go_back)
        self.btn_confirm.clicked.connect(self.confirm_release)
        self.btn_print.clicked.connect(self.print_order)

    def load_data(self):
        import database
        self.table.setRowCount(0)
        rows = database.fetch_release_details(self.order_number, self.purchaser)
        
        for row in rows:
            # Append to end (FIFO) to match DB order (Ascending ID)
            r = self.table.rowCount()
            self.table.insertRow(r)
            # row contains all mapped columns in order from fetch_release_details
            for i, val in enumerate(row):
                self.table.setItem(r, i, QTableWidgetItem(str(val if val is not None else "")))
                
    def confirm_release(self):
        import database
        # Ask for confirmation
        reply = QMessageBox.question(self, "确认发放", "确定要将此单据标记为已发放吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.update_release_status(self.order_number, self.purchaser, "已发放")
            QMessageBox.information(self, "成功", "状态已更新")
            # Optional: Refresh UI or go back
            
    def go_back(self):
        if self.main_window and hasattr(self.main_window, "back_to_release_list"):
            self.main_window.back_to_release_list()
            
    def print_order(self):
        from print import OrderPrinter
        import database
        
        # 1. Gather Header Info
        info = database.fetch_order_by_number(self.order_number)
        header_info = {
            "number": self.order_number,
            "purchaser": self.purchaser
        }
        if info:
            # info: yymm, category, unit, date, task_name
            header_info["yymm"] = info[0]
            header_info["category"] = database.category_display_from_code(info[1])
            header_info["unit"] = info[2]
            header_info["date"] = info[3]
            header_info["task_name"] = info[4]
            
        # 2. Gather Columns
        columns = []
        for c in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(c)
            columns.append(item.text() if item else "")
            
        # 3. Gather Rows
        rows = []
        for r in range(self.table.rowCount()):
            row_data = []
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                row_data.append(it.text() if it else "")
            rows.append(row_data)
            
        # 4. Print
        # Load dynamic config
        config = database.get_print_config("plan_release")
        printer = OrderPrinter(header_info, columns, rows, config)
        printer.show_preview()
