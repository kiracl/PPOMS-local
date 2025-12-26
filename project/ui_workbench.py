from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QHBoxLayout, QLineEdit, QComboBox
from PySide6.QtCore import Signal
from datetime import datetime
import database

class ClickableFrame(QFrame):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

class WorkbenchWidget(QWidget):
    open_purchase_plan = Signal()
    open_plan_release = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Header (Title + Filter)
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("工作台")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch(1)
        
        # Filter
        filter_label = QLabel("计划月份:")
        self.combo_month = QComboBox()
        self.combo_month.setFixedWidth(100)
        
        header_layout.addWidget(filter_label)
        header_layout.addWidget(self.combo_month)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Stats Cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        # Row 0: Total Plans, Total Amount
        # Span 3 cols each (assuming 6 col grid)
        self.lbl_total_plans = self.create_card("本月计划总数", "0", "#3B82F6", cards_layout, 0, 0, 1, 3, self.open_purchase_plan.emit)
        self.lbl_total_amount = self.create_card("总采购额(元)", "0.00", "#8B5CF6", cards_layout, 0, 3, 1, 3)
        
        # Row 1: Pending Plans, Processed Plans
        self.lbl_pending_plans = self.create_card("待处理计划", "0", "#F59E0B", cards_layout, 1, 0, 1, 3, self.open_plan_release.emit)
        self.lbl_processed_plans = self.create_card("已处理计划", "0", "#10B981", cards_layout, 1, 3, 1, 3)
        
        # Row 2: Category Counts (Civil, Machined, Semi)
        # Span 2 cols each
        self.lbl_civil_plans = self.create_card("民品计划总数", "0", "#06B6D4", cards_layout, 2, 0, 1, 2)
        self.lbl_machined_plans = self.create_card("机加件计划总数", "0", "#F59E0B", cards_layout, 2, 2, 1, 2)
        self.lbl_semi_plans = self.create_card("半成品计划总数", "0", "#6366F1", cards_layout, 2, 4, 1, 2)
        
        # Row 3: Category Amounts
        self.lbl_civil_amount = self.create_card("民品采购金额", "0.00", "#06B6D4", cards_layout, 3, 0, 1, 2)
        self.lbl_machined_amount = self.create_card("机加件采购金额", "0.00", "#F59E0B", cards_layout, 3, 2, 1, 2)
        self.lbl_semi_amount = self.create_card("半成品采购金额", "0.00", "#6366F1", cards_layout, 3, 4, 1, 2)
        
        layout.addLayout(cards_layout)
        layout.addStretch(1)
        
        # Connections
        self.combo_month.currentTextChanged.connect(self.refresh_stats)
        
        # Initial Load will be handled when months are set by main window
        
    def set_months(self, months):
        current = self.combo_month.currentText()
        self.combo_month.blockSignals(True)
        self.combo_month.clear()
        self.combo_month.addItems(months)
        
        # Try to preserve selection, or default to current month
        if current in months:
            self.combo_month.setCurrentText(current)
        else:
            # Default to current month if available
            now_yymm = datetime.now().strftime("%y%m")
            if now_yymm in months:
                self.combo_month.setCurrentText(now_yymm)
            elif months:
                self.combo_month.setCurrentIndex(0)
                
        self.combo_month.blockSignals(False)
        self.refresh_stats()

    def create_card(self, title, value, color, layout, r, c, rowspan, colspan, on_double_click=None):
        frame = ClickableFrame()
        if on_double_click:
            frame.doubleClicked.connect(on_double_click)
            
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        fl = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6B7280; font-size: 14px; border: none; background: transparent;")
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        
        fl.addWidget(lbl_title)
        fl.addWidget(lbl_value)
        
        layout.addWidget(frame, r, c, rowspan, colspan)
        return lbl_value

    def refresh_stats(self):
        yymm = self.combo_month.currentText().strip()
        
        # Fetch from database
        try:
            (total, pending, processed, civil, machined, semi,
             total_amt, civil_amt, machined_amt, semi_amt) = database.get_workbench_stats(yymm)
             
            self.lbl_total_plans.setText(str(total))
            self.lbl_pending_plans.setText(str(pending))
            self.lbl_processed_plans.setText(str(processed))
            
            self.lbl_civil_plans.setText(str(civil))
            self.lbl_machined_plans.setText(str(machined))
            self.lbl_semi_plans.setText(str(semi))
            
            # Amounts
            self.lbl_total_amount.setText(f"{total_amt:,.2f}")
            self.lbl_civil_amount.setText(f"{civil_amt:,.2f}")
            self.lbl_machined_amount.setText(f"{machined_amt:,.2f}")
            self.lbl_semi_amount.setText(f"{semi_amt:,.2f}")
            
        except Exception as e:
            print(f"Error fetching stats: {e}")
            self.lbl_total_plans.setText("-")
            self.lbl_pending_plans.setText("-")
            self.lbl_processed_plans.setText("-")
            self.lbl_total_amount.setText("-")
            self.lbl_civil_plans.setText("-")
            self.lbl_machined_plans.setText("-")
            self.lbl_semi_plans.setText("-")
            self.lbl_civil_amount.setText("-")
            self.lbl_machined_amount.setText("-")
            self.lbl_semi_amount.setText("-")
