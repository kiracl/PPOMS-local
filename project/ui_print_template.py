from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
    QGroupBox, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt
import database

class PrintTemplateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module = "plan_release" # We can make this dynamic if needed
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.form_layout = QFormLayout(content)
        self.form_layout.setSpacing(20)
        
        # --- Basic Settings ---
        group_basic = QGroupBox("基本设置")
        layout_basic = QFormLayout(group_basic)
        layout_basic.setVerticalSpacing(10)
        
        self.title_edit = QLineEdit()
        layout_basic.addRow("标题文字:", self.title_edit)
        
        self.rows_per_page_spin = QSpinBox()
        self.rows_per_page_spin.setRange(1, 50)
        layout_basic.addRow("每页行数:", self.rows_per_page_spin)
        
        self.row_height_spin = QSpinBox()
        self.row_height_spin.setRange(20, 200)
        layout_basic.addRow("行高 (px):", self.row_height_spin)
        
        self.header_height_spin = QSpinBox()
        self.header_height_spin.setRange(20, 200)
        layout_basic.addRow("表头高度 (px):", self.header_height_spin)
        
        self.form_layout.addRow(group_basic)
        
        # --- Font Settings ---
        group_font = QGroupBox("字体大小 (pt)")
        layout_font = QFormLayout(group_font)
        layout_font.setVerticalSpacing(10)
        
        self.font_title_spin = QSpinBox()
        self.font_title_spin.setRange(8, 72)
        layout_font.addRow("标题字体:", self.font_title_spin)
        
        self.font_header_spin = QSpinBox()
        self.font_header_spin.setRange(6, 36)
        layout_font.addRow("表头信息字体:", self.font_header_spin)
        
        self.font_table_header_spin = QSpinBox()
        self.font_table_header_spin.setRange(6, 36)
        layout_font.addRow("表格列头字体:", self.font_table_header_spin)
        
        self.font_cell_spin = QSpinBox()
        self.font_cell_spin.setRange(6, 36)
        layout_font.addRow("表格内容字体:", self.font_cell_spin)
        
        self.font_footer_spin = QSpinBox()
        self.font_footer_spin.setRange(6, 36)
        layout_font.addRow("页脚字体:", self.font_footer_spin)
        
        self.form_layout.addRow(group_font)
        
        # --- Margin Settings ---
        group_margin = QGroupBox("边距设置 (比例 0.0-0.5)")
        layout_margin = QFormLayout(group_margin)
        layout_margin.setVerticalSpacing(10)
        
        self.margin_x_spin = QDoubleSpinBox()
        self.margin_x_spin.setRange(0.0, 0.5)
        self.margin_x_spin.setSingleStep(0.01)
        layout_margin.addRow("左右边距:", self.margin_x_spin)
        
        self.margin_y_spin = QDoubleSpinBox()
        self.margin_y_spin.setRange(0.0, 0.5)
        self.margin_y_spin.setSingleStep(0.01)
        layout_margin.addRow("上下边距:", self.margin_y_spin)
        
        self.form_layout.addRow(group_margin)
        
        # --- Footer Settings ---
        group_footer = QGroupBox("页脚标签")
        layout_footer = QFormLayout(group_footer)
        layout_footer.setVerticalSpacing(10)
        
        self.footer_1_edit = QLineEdit()
        layout_footer.addRow("左侧标签:", self.footer_1_edit)
        
        self.footer_2_edit = QLineEdit()
        layout_footer.addRow("中间标签:", self.footer_2_edit)
        
        self.footer_3_edit = QLineEdit()
        layout_footer.addRow("右侧标签:", self.footer_3_edit)
        
        self.form_layout.addRow(group_footer)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # --- Actions ---
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_config)
        
        self.btn_reset = QPushButton("恢复默认")
        self.btn_reset.clicked.connect(self.reset_config)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(btn_layout)
        
        self.setStyleSheet("""
            QPushButton#primary { background-color: #2F80ED; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }
            QGroupBox { font-weight: bold; margin-top: 10px; padding-top: 20px; }
        """)

    def get_default_config(self):
        return {
            "title": "采购计划表",
            "rows_per_page": 13,
            "row_height": 45,
            "header_height": 45, # Default matching row height
            "font_title": 24,
            "font_header": 12,
            "font_table_header": 11,
            "font_cell": 10,
            "font_footer": 12,
            "margin_x": 0.03,
            "margin_y": 0.05,
            "footer_1": "审核：",
            "footer_2": "签收：",
            "footer_3": "编制："
        }

    def load_config(self):
        config = database.get_print_config(self.module)
        defaults = self.get_default_config()
        
        # Merge defaults
        for k, v in defaults.items():
            if k not in config:
                config[k] = v
                
        self.title_edit.setText(config["title"])
        self.rows_per_page_spin.setValue(config["rows_per_page"])
        self.row_height_spin.setValue(config["row_height"])
        self.header_height_spin.setValue(config.get("header_height", 45))
        
        self.font_title_spin.setValue(config["font_title"])
        self.font_header_spin.setValue(config["font_header"])
        self.font_table_header_spin.setValue(config["font_table_header"])
        self.font_cell_spin.setValue(config["font_cell"])
        self.font_footer_spin.setValue(config["font_footer"])
        
        self.margin_x_spin.setValue(config["margin_x"])
        self.margin_y_spin.setValue(config["margin_y"])
        
        self.footer_1_edit.setText(config["footer_1"])
        self.footer_2_edit.setText(config["footer_2"])
        self.footer_3_edit.setText(config["footer_3"])

    def save_config(self):
        config = {
            "title": self.title_edit.text(),
            "rows_per_page": self.rows_per_page_spin.value(),
            "row_height": self.row_height_spin.value(),
            "header_height": self.header_height_spin.value(),
            "font_title": self.font_title_spin.value(),
            "font_header": self.font_header_spin.value(),
            "font_table_header": self.font_table_header_spin.value(),
            "font_cell": self.font_cell_spin.value(),
            "font_footer": self.font_footer_spin.value(),
            "margin_x": self.margin_x_spin.value(),
            "margin_y": self.margin_y_spin.value(),
            "footer_1": self.footer_1_edit.text(),
            "footer_2": self.footer_2_edit.text(),
            "footer_3": self.footer_3_edit.text()
        }
        database.save_print_config(self.module, config)
        QMessageBox.information(self, "成功", "打印模板配置已保存")

    def reset_config(self):
        reply = QMessageBox.question(self, "确认", "确定要恢复默认设置吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            config = self.get_default_config()
            database.save_print_config(self.module, config)
            self.load_config()
