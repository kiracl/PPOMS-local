from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QListWidget,
    QSplitter,
    QFrame,
)
from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtWidgets import QHeaderView, QAbstractItemView


class MainForm(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter)

        top = QFrame()
        top.setFrameShape(QFrame.StyledPanel)
        self.layout = QGridLayout(top)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setHorizontalSpacing(8)
        self.layout.setVerticalSpacing(6)
        self.label_month = QLabel("计划月份")
        self.combo_month = QComboBox()
        self.label_category = QLabel("标的类别")
        self.combo_category = QComboBox()
        self.combo_category.addItems(["民品(MP)", "机加件(MPJ)", "半成品(MPB)", "外销模块(MPB_WX)"])
        self.combo_category.currentTextChanged.connect(self.on_category_changed)
        self.label_unit = QLabel("需求单位")
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["生产部", "采购部", "仓储部"])
        self.label_date = QLabel("日期")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.label_task = QLabel("采购任务名称")
        self.edit_task = QLineEdit()
        self.edit_task.setPlaceholderText("请输入采购任务名称")
        self.order_number_label = QLabel("主单编号")
        self.order_number_value = QLineEdit("")
        self.order_number_value.setReadOnly(True)
        self.button_generate = QPushButton("生成")
        for lbl in [self.label_task, self.label_category, self.label_unit, self.label_date, self.label_month, self.order_number_label]:
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # 第一行：采购任务名称、标的类别、需求单位、日期
        self.layout.addWidget(self.label_task, 0, 0)
        self.layout.addWidget(self.edit_task, 0, 1)
        self.layout.addWidget(self.label_category, 0, 2)
        self.layout.addWidget(self.combo_category, 0, 3)
        self.layout.addWidget(self.label_unit, 0, 4)
        self.layout.addWidget(self.combo_unit, 0, 5)
        self.layout.addWidget(self.label_date, 0, 6)
        self.layout.addWidget(self.date_edit, 0, 7)
        # 第二行：计划月份、主单编号、占位、生成
        self.layout.addWidget(self.label_month, 1, 0)
        self.layout.addWidget(self.combo_month, 1, 1)
        self.layout.addWidget(self.order_number_label, 1, 2)
        self.layout.addWidget(self.order_number_value, 1, 3)
        spacer = QWidget()
        self.layout.addWidget(spacer, 1, 4, 1, 2)
        self.button_generate.setObjectName("primary")
        self.layout.addWidget(self.button_generate, 1, 7)

        # 搜索条件控件
        self.label_filter = QLabel("筛选条件")
        self.label_filter.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.search_number = QLineEdit()
        self.search_number.setPlaceholderText("主单编号")
        
        self.search_task = QLineEdit()
        self.search_task.setPlaceholderText("采购任务")
        
        self.search_month = QComboBox()
        self.search_month.setEditable(True)
        self.search_month.setPlaceholderText("计划月份")
        
        self.search_unit = QComboBox()
        self.search_unit.setEditable(True)
        self.search_unit.setPlaceholderText("需求单位")
        
        self.btn_search = QPushButton("搜索")
        self.btn_search.setObjectName("primary")

        # 布局容器
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        # Labels for filters
        self.label_filter_month = QLabel("计划月份")
        self.label_filter_month.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.label_filter_unit = QLabel("需求单位")
        self.label_filter_unit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 添加控件到水平布局
        # Layout logic requested:
        # 主单编号 1/4 = 4/16
        # 采购任务 1/2 = 8/16
        # 计划月份 1/16
        # 需求单位 3/16
        
        # We can use stretch factors in QHBoxLayout
        
        # self.search_number.setFixedWidth(120) # Remove fixed width
        
        filter_layout.addWidget(self.search_number, 4) # Stretch factor 4
        filter_layout.addWidget(self.search_task, 8) # Stretch factor 8
        
        filter_layout.addWidget(self.label_filter_month)
        filter_layout.addWidget(self.search_month, 1) # Stretch factor 1
        
        filter_layout.addWidget(self.label_filter_unit)
        filter_layout.addWidget(self.search_unit, 3) # Stretch factor 3

        # 第三行布局：
        # 0列: 标签 "筛选条件"
        # 1-6列: 合并，放置水平排列的四个输入框
        # 7列: 按钮 "搜索"
        self.layout.addWidget(self.label_filter, 2, 0)
        self.layout.addWidget(filter_container, 2, 1, 1, 6)  # 跨越 col 1 到 6
        self.layout.addWidget(self.btn_search, 2, 7)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        self.layout.setColumnStretch(2, 1)
        self.layout.setColumnStretch(3, 3)
        self.layout.setColumnStretch(4, 1)
        self.layout.setColumnStretch(5, 3)
        self.layout.setColumnStretch(6, 1)
        self.layout.setColumnStretch(7, 3)

        splitter.addWidget(top)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "日期",
            "主单编号",
            "采购任务名称",
            "需求单位",
            "标的类别",
            "计划月份",
            "采购金额(元)",
            "记录条数",
            "处理状态",
            "审批单据",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        # for i in range(7):
        #     header.setSectionResizeMode(i, QHeaderView.Stretch)
        header.sectionResized.connect(self.on_header_resized)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(300)
        self._pending_resize = None
        self.apply_saved_widths()
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        splitter.addWidget(self.table)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setStyleSheet(
            """
            QWidget { background: #F1F1F1; font-size: 11px; }
            QFrame { background: #F7F7F7; border: 1px solid #E0E0E0; border-radius: 6px; }
            QLabel { color: #222; }
            QComboBox, QLineEdit, QDateEdit { background: #FFFFFF; border: 1px solid #9E9E9E; padding: 3px; border-radius: 4px; }
            QPushButton#primary { background: #2F80ED; color: #fff; padding: 5px 10px; border-radius: 4px; }
            QPushButton { background: #E0E0E0; color: #333; padding: 5px 10px; border-radius: 4px; }
            QTableWidget { background: #FFFFFF; }
            QHeaderView::section { background: #ECECEC; padding: 6px; }
            """
        )

    def on_category_changed(self, text):
        if "半成品(MPB)" in text:
            self.combo_unit.setCurrentText("仓储中心")

    def set_units(self, units):
        self.combo_unit.clear()
        self.combo_unit.addItems(units)
        
        # Update search filter combo
        current_search = self.search_unit.currentText()
        self.search_unit.clear()
        self.search_unit.addItem("") # Empty option
        self.search_unit.addItems(units)
        self.search_unit.setCurrentText(current_search)

    def set_months(self, months):
        current = self.combo_month.currentText()
        self.combo_month.clear()
        self.combo_month.addItems(months)
        if current in months:
            self.combo_month.setCurrentText(current)
            
        # Update search filter combo
        current_search_month = self.search_month.currentText()
        self.search_month.clear()
        self.search_month.addItem("") # Empty option
        self.search_month.addItems(months)
        self.search_month.setCurrentText(current_search_month)

    def apply_saved_widths(self):
        import database
        widths = database.get_main_column_widths()
        for col, w in widths.items():
            if 0 <= col < self.table.columnCount() and int(w) > 20:
                self.table.setColumnWidth(col, int(w))

    def on_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        self._pending_resize = (int(logicalIndex), int(newSize))
        self._resize_timer.timeout.connect(self._flush_resize)
        self._resize_timer.start()

    def _flush_resize(self):
        if not self._pending_resize:
            return
        col, w = self._pending_resize
        self._pending_resize = None
        import database
        database.set_main_column_width(col, w)
        database.set_layout_version("main", "v1")


class EditOrderDialog(QDialog):
    def __init__(self, current_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改采购任务信息")
        self.resize(500, 300)
        self.current_info = current_info
        
        layout = QGridLayout(self)
        layout.setVerticalSpacing(15)
        
        # Current Number (Read-only)
        layout.addWidget(QLabel("当前单号:"), 0, 0)
        self.lbl_number = QLabel(current_info['number'])
        self.lbl_number.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(self.lbl_number, 0, 1)
        
        # Task Name
        layout.addWidget(QLabel("采购任务名称:"), 1, 0)
        self.edit_task = QLineEdit(current_info['task_name'])
        layout.addWidget(self.edit_task, 1, 1)
        
        # Unit
        layout.addWidget(QLabel("需求单位:"), 2, 0)
        self.combo_unit = QComboBox()
        import database
        self.combo_unit.addItems(database.fetch_units())
        self.combo_unit.setCurrentText(current_info['unit'])
        layout.addWidget(self.combo_unit, 2, 1)
        
        # Category
        layout.addWidget(QLabel("标的类别:"), 3, 0)
        self.combo_category = QComboBox()
        self.combo_category.addItems(["民品(MP)", "机加件(MPJ)", "半成品(MPB)", "外销模块(MPB_WX)"])
        # Select current category
        cat_disp = database.category_display_from_code(current_info['category_code'])
        for i in range(self.combo_category.count()):
            if cat_disp in self.combo_category.itemText(i):
                self.combo_category.setCurrentIndex(i)
                break
        layout.addWidget(self.combo_category, 3, 1)
        
        # Month
        layout.addWidget(QLabel("计划月份:"), 4, 0)
        self.combo_month = QComboBox()
        self.combo_month.addItems(database.fetch_plan_months())
        self.combo_month.setCurrentText(current_info['yymm'])
        layout.addWidget(self.combo_month, 4, 1)
        
        # Warning Label
        self.lbl_warning = QLabel("")
        self.lbl_warning.setStyleSheet("color: red; font-size: 10px;")
        self.lbl_warning.setWordWrap(True)
        layout.addWidget(self.lbl_warning, 5, 0, 1, 2)
        
        # Buttons
        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("保存修改")
        self.btn_save.setObjectName("primary")
        self.btn_cancel = QPushButton("取消")
        btn_box.addStretch()
        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(self.btn_cancel)
        layout.addLayout(btn_box, 6, 0, 1, 2)
        
        # Connect
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.combo_category.currentTextChanged.connect(self.check_changes)
        self.combo_month.currentTextChanged.connect(self.check_changes)
        
    def check_changes(self):
        import database
        new_cat_text = self.combo_category.currentText()
        new_cat_code = database.category_code_from_display(new_cat_text)
        new_yymm = self.combo_month.currentText()
        
        if new_cat_code != self.current_info['category_code'] or new_yymm != self.current_info['yymm']:
            self.lbl_warning.setText(f"注意：修改类别或月份将自动生成新单号（如 CG-{new_yymm}{new_cat_code}...），原单号将失效，相关明细会自动重命名！")
        else:
            self.lbl_warning.setText("")
            
    def get_data(self):
        import database
        return {
            "task_name": self.edit_task.text().strip(),
            "unit": self.combo_unit.currentText(),
            "category_code": database.category_code_from_display(self.combo_category.currentText()),
            "yymm": self.combo_month.currentText()
        }


class ChangeDateDialog(QDialog):
    def __init__(self, order_number: str, old_date: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改日期")
        self.resize(360, 160)
        lay = QGridLayout(self)
        lay.setVerticalSpacing(12)
        lay.addWidget(QLabel("当前单号:"), 0, 0)
        self.lbl_number = QLabel(order_number)
        self.lbl_number.setStyleSheet("font-weight: bold; color: #555;")
        lay.addWidget(self.lbl_number, 0, 1)
        lay.addWidget(QLabel("原日期:"), 1, 0)
        self.lbl_old = QLabel(old_date or "")
        lay.addWidget(self.lbl_old, 1, 1)
        lay.addWidget(QLabel("新日期:"), 2, 0)
        from PySide6.QtWidgets import QDateEdit
        from PySide6.QtCore import QDate
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        lay.addWidget(self.date_edit, 2, 1)
        btns = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_ok.setObjectName("primary")
        self.btn_cancel = QPushButton("取消")
        btns.addStretch()
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        lay.addLayout(btns, 3, 0, 1, 2)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
    def get_date_str(self) -> str:
        return self.date_edit.date().toString("yyyy-MM-dd")

class SettingsDialog(QDialog):
    def __init__(self, fetch_units_fn, add_unit_fn, rename_unit_fn):
        super().__init__()
        self.setWindowTitle("设置")
        self.fetch_units_fn = fetch_units_fn
        self.add_unit_fn = add_unit_fn
        self.rename_unit_fn = rename_unit_fn
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        self.input = QLineEdit()
        btns = QHBoxLayout()
        self.btn_add = QPushButton("添加")
        self.btn_rename = QPushButton("重命名")
        self.btn_close = QPushButton("关闭")
        lay.addWidget(self.list)
        lay.addWidget(self.input)
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_rename)
        btns.addWidget(self.btn_close)
        lay.addLayout(btns)
        self.btn_add.clicked.connect(self.add_unit)
        self.btn_rename.clicked.connect(self.rename_unit)
        self.btn_close.clicked.connect(self.accept)
        self.reload()

    def reload(self):
        self.list.clear()
        for name in self.fetch_units_fn():
            self.list.addItem(name)

    def add_unit(self):
        name = self.input.text().strip()
        if self.add_unit_fn(name):
            self.reload()
            self.input.clear()

    def rename_unit(self):
        item = self.list.currentItem()
        if not item:
            return
        new_name = self.input.text().strip()
        if self.rename_unit_fn(item.text(), new_name):
            self.reload()
            self.input.clear()
