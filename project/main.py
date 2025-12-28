import sys
import os
import shutil
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QStackedWidget, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QFileDialog
from PySide6.QtCore import QDate, Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices


from ui_main import MainForm, SettingsDialog, EditOrderDialog
from ui_detail import DetailWidget
from ui_workbench import WorkbenchWidget
from ui_plan_release import PlanReleaseForm
from ui_recommendation import RecommendationWidget
from ui_monthly_plan import MonthlyPlanWidget
from ui_data_manager import DataManagerWidget
from ui_plan_export import PlanExportWidget
import database
from print import export_order_pdf


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("采购管理系统       生产管理部 蔡勒 V2.0.0008")
        
        # Main Container
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(container)
        
        # Sidebar (Left)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                height: 50px;
                padding-left: 20px;
            }
            QListWidget::item:selected {
                background-color: #34495e;
                border-left: 4px solid #3498db;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
        """)
        self.sidebar.addItem("工作台")
        self.sidebar.addItem("月度计划")
        self.sidebar.addItem("采购计划")
        self.sidebar.addItem("计划发放")
        self.sidebar.addItem("计划导出")
        self.sidebar.addItem("自动推荐")
        self.sidebar.addItem("数据管理")
        main_layout.addWidget(self.sidebar)
        
        # Right Content Area
        self.right_stack = QStackedWidget()
        main_layout.addWidget(self.right_stack)
        
        # 1. Workbench Page (Index 0)
        self.workbench = WorkbenchWidget()
        self.right_stack.addWidget(self.workbench)
        
        # 2. Monthly Plan Page (Index 1)
        self.monthly_plan = MonthlyPlanWidget()
        self.right_stack.addWidget(self.monthly_plan)
        
        # 3. Purchase Plan Page (Index 2)
        self.purchase_flow_widget = QWidget()
        self.purchase_layout = QVBoxLayout(self.purchase_flow_widget)
        self.purchase_layout.setContentsMargins(0, 0, 0, 0)
        
        self.form = MainForm()
        self.stack = QStackedWidget() # This is the stack used by existing logic (MainForm <-> DetailWidget)
        self.stack.addWidget(self.form)
        
        self.purchase_layout.addWidget(self.stack)
        self.right_stack.addWidget(self.purchase_flow_widget)
        
        # 4. Plan Release Page (Index 3)
        self.plan_release = PlanReleaseForm(self)
        self.right_stack.addWidget(self.plan_release)
        
        # 5. Plan Export Page (Index 4)
        self.plan_export = PlanExportWidget()
        self.right_stack.addWidget(self.plan_export)
        
        # 6. Recommendation Page (Index 5)
        self.recommendation = RecommendationWidget()
        self.right_stack.addWidget(self.recommendation)
        
        # 7. Data Manager Page (Index 6)
        self.data_manager = DataManagerWidget()
        self.right_stack.addWidget(self.data_manager)
        
        # Connect Sidebar
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        self.sidebar.setCurrentRow(0) # Default to Workbench
        
        # Connect Workbench Signals
        self.workbench.open_purchase_plan.connect(lambda: self.sidebar.setCurrentRow(2))
        self.workbench.open_plan_release.connect(lambda: self.sidebar.setCurrentRow(3))
        
        # Existing Connections
        self.form.button_generate.clicked.connect(self.generate_order)
        self.form.btn_search.clicked.connect(self.search_orders)
        self.form.table.cellDoubleClicked.connect(self.open_detail_from_table)
        self.form.table.cellClicked.connect(self.on_table_cell_clicked)
        self.form.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.form.table.customContextMenuRequested.connect(self.show_context_menu)
        menu = self.menuBar().addMenu("设置")
        act_units = menu.addAction("需求单位")
        act_units.triggered.connect(self.open_settings)
        act_purchasers = menu.addAction("采购员")
        act_purchasers.triggered.connect(self.open_purchaser_settings)
        act_status = menu.addAction("采购状态")
        act_status.triggered.connect(self.open_status_settings)
        act_months = menu.addAction("计划月份")
        act_months.triggered.connect(self.open_month_settings)
        
        tools = self.menuBar().addMenu("工具")
        act_validate = tools.addAction("校验明细序号")
        act_validate.triggered.connect(self.validate_current_order_details)
        act_reset = tools.addAction("清除测试数据并初始化")
        act_reset.triggered.connect(self.reset_test_data)
        self.current_order_number = ""
        self.load_history()
        self.refresh_units()
        self.refresh_months()
        self.detail_widget = None

    def on_sidebar_changed(self, index):
        self.right_stack.setCurrentIndex(index)
        if index == 0:
            self.workbench.refresh_stats()
        elif index == 1:
            self.monthly_plan.load_data()
        elif index == 3:
            self.plan_release.load_data()
        elif index == 4:
            self.plan_export.load_months()
        elif index == 6:
            self.data_manager.load_backups()

    def get_display_name(self, path):
        if not path:
            return ""
        filename = os.path.basename(path)
        # Format: {number}_{safe_name}_{timestamp}.pdf
        # Goal: extract safe_name, removing .pdf if present
        
        if not filename.lower().endswith('.pdf'):
            return filename
            
        # Remove .pdf extension
        base = filename[:-4]
        
        # Find separators
        first_us = base.find('_')
        last_us = base.rfind('_')
        
        if first_us != -1 and last_us != -1 and first_us < last_us:
            # Extract middle part
            name_part = base[first_us+1 : last_us]
            # Remove embedded .pdf if present (from old files)
            if name_part.lower().endswith('.pdf'):
                name_part = name_part[:-4]
            return name_part
            
        return base

    def load_history(self, number_filter=None, task_filter=None, unit_filter=None, month_filter=None):
        rows = database.fetch_orders(number_filter, task_filter, unit_filter, month_filter)
        self.form.table.setRowCount(0)
        for r in rows:
            rr = self.form.table.rowCount()
            self.form.table.insertRow(rr)
            # r: yymm, category, unit, date, task_name, number, approval_doc
            yymm = r[0]
            category_code = r[1]
            unit = r[2]
            date_str = r[3]
            task_name = r[4]
            number = r[5]
            approval_doc = r[6] if len(r) > 6 else ""
            
            category = database.category_display_from_code(category_code)
            count = database.count_details(number)
            total_inquiry = database.get_order_inquiry_total(number)
            
            # Use safe string conversion
            def safe_str(v):
                return str(v) if v is not None else ""
                
            status = database.get_order_processing_status(number)
            
            doc_display = self.get_display_name(approval_doc) if approval_doc else "点击上传"
            
            vals = [date_str, number, task_name, unit, category, yymm, f"{total_inquiry:,.2f}", count, status]
            for c, val in enumerate(vals):
                self.form.table.setItem(rr, c, QTableWidgetItem(safe_str(val)))
            
            # Column 9: Approval Doc
            item_doc = QTableWidgetItem(doc_display)
            item_doc.setTextAlignment(Qt.AlignCenter)
            if approval_doc:
                item_doc.setForeground(Qt.blue)
                item_doc.setToolTip(f"已上传: {doc_display}\n点击打开，右键可替换")
            else:
                item_doc.setForeground(Qt.gray)
                item_doc.setToolTip("点击上传审批单据PDF")
            self.form.table.setItem(rr, 9, item_doc)


    def search_orders(self):
        number = self.form.search_number.text().strip()
        task = self.form.search_task.text().strip()
        unit = self.form.search_unit.currentText().strip()
        month = self.form.search_month.currentText().strip()
        self.load_history(number, task, unit, month)

    def generate_order(self):
        yymm = self.form.combo_month.currentText()
        cat_disp = self.form.combo_category.currentText()
        unit = self.form.combo_unit.currentText()
        date_str = self.form.date_edit.date().toString("yyyy-MM-dd")
        task_name = self.form.edit_task.text().strip()
        if not task_name:
            QMessageBox.warning(self, "提示", "请先输入采购任务名称")
            self.form.edit_task.setFocus()
            return
        cat_code = database.category_code_from_display(cat_disp)
        # date8 = self.form.date_edit.date().toString("yyyyMMdd") # No longer used for ID generation
        number = database.next_main_number(yymm, cat_code)
        database.save_order(number, yymm, cat_code, unit, date_str, task_name)
        self.current_order_number = number
        self.form.order_number_value.setText(number)
        # Insert at the top (row 0) to match "newest first" sorting
        rr = 0
        self.form.table.insertRow(rr)
        cat_name = database.category_display_from_code(cat_code)
        # 新增订单时，金额和记录条数都为0
        for c, val in enumerate([date_str, number, task_name, unit, cat_name, yymm, "0.00", 0, "未发放"]):
            self.form.table.setItem(rr, c, QTableWidgetItem(str(val)))
        
        item_doc = QTableWidgetItem("点击上传")
        item_doc.setForeground(Qt.gray)
        item_doc.setTextAlignment(Qt.AlignCenter)
        item_doc.setToolTip("点击上传审批单据PDF")
        self.form.table.setItem(rr, 9, item_doc)
        
        QMessageBox.information(self, "生成", f"主单已生成: {number}")

    def open_detail_from_table(self, row, column):
        try:
            num_item = self.form.table.item(row, 1)
            if not num_item:
                return
            number = num_item.text()
            info = database.fetch_order_by_number(number)
            if not info:
                QMessageBox.warning(self, "错误", f"未找到单号 {number} 的信息")
                return
            yymm, cat_code, unit, date_str, task_name = info
            if self.detail_widget:
                self.stack.removeWidget(self.detail_widget)
                self.detail_widget.deleteLater()
            cat_name = database.category_display_from_code(cat_code)
            header = {"number": number, "task_name": task_name, "unit": unit, "category": cat_name, "date": date_str, "yymm": yymm}
            self.detail_widget = DetailWidget(yymm, cat_code, number, database.next_detail_number, header)
            self.detail_widget.back_btn.clicked.connect(self.back_to_main)
            self.stack.addWidget(self.detail_widget)
            self.stack.setCurrentWidget(self.detail_widget)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"打开明细失败: {str(e)}")

    def back_to_main(self):
        if self.detail_widget:
            number = self.detail_widget.main_number
            # count valid rows (采购标的 或 规格型号 非空)
            table = self.detail_widget.table
            count_valid = 0
            for r in range(table.rowCount()):
                pi = table.item(r, 1).text() if table.item(r, 1) else ""
                sm = table.item(r, 2).text() if table.item(r, 2) else ""
                if pi.strip() or sm.strip():
                    count_valid += 1
            
            # Recalculate inquiry total amount
            total_inquiry = database.get_order_inquiry_total(number)
            
            # update home table count cell and amount cell
            for r in range(self.form.table.rowCount()):
                num_item = self.form.table.item(r, 1)
                if num_item and num_item.text() == number:
                    self.form.table.setItem(r, 6, QTableWidgetItem(f"{total_inquiry:,.2f}"))
                    self.form.table.setItem(r, 7, QTableWidgetItem(str(count_valid)))
                    status = database.get_order_processing_status(number)
                    self.form.table.setItem(r, 8, QTableWidgetItem(status))
                    break
            self.stack.setCurrentIndex(0)
            self.stack.removeWidget(self.detail_widget)
            self.detail_widget.deleteLater()
            self.detail_widget = None
        # self.load_history()

    def validate_current_order_details(self):
        number = self.current_order_number
        if not number:
            # try selected
            r = self.form.table.currentRow()
            if r >= 0:
                it = self.form.table.item(r, 1)
                number = it.text() if it else ""
        if not number:
            QMessageBox.warning(self, "校验", "请先选择或生成主单")
            return
        ok, msg = database.validate_detail_sequence(number)
        if ok:
            QMessageBox.information(self, "校验", msg)
        else:
            QMessageBox.warning(self, "校验", msg)

    def reset_test_data(self):
        database.reset_test_data()
        self.current_order_number = ""
        self.load_history()
        self.plan_release.load_data()
        QMessageBox.information(self, "初始化", "已清除测试数据并重置计数器")

    # 打印功能已取消

    def refresh_units(self):
        units = database.fetch_units()
        self.form.set_units(units)

    def refresh_months(self):
        months = database.fetch_plan_months()
        self.form.set_months(months)
        self.workbench.set_months(months)

    def open_settings(self):
        dlg = SettingsDialog(database.fetch_units, database.add_unit, database.rename_unit)
        dlg.setWindowTitle("设置 - 需求单位")
        dlg.exec()
        self.refresh_units()

    def open_purchaser_settings(self):
        dlg = SettingsDialog(database.fetch_purchasers, database.add_purchaser, database.rename_purchaser)
        dlg.setWindowTitle("设置 - 采购员")
        dlg.exec()
        
    def open_status_settings(self):
        dlg = SettingsDialog(database.fetch_purchase_statuses, database.add_purchase_status, database.rename_purchase_status)
        dlg.setWindowTitle("设置 - 采购状态")
        dlg.exec()

    def open_month_settings(self):
        dlg = SettingsDialog(database.fetch_plan_months, database.add_plan_month, database.rename_plan_month)
        dlg.setWindowTitle("设置 - 计划月份")
        dlg.exec()
        self.refresh_months()

    def show_context_menu(self, pos):
        item = self.form.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        
        # Get order number from column 1
        num_item = self.form.table.item(row, 1)
        if not num_item:
            return
        number = num_item.text()
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        action_edit = menu.addAction("修改任务信息")
        action_edit.triggered.connect(lambda: self.edit_order_info(number))
        action_change_date = menu.addAction("修改日期")
        action_change_date.triggered.connect(lambda: self.change_order_date(number))
        menu.exec(self.form.table.viewport().mapToGlobal(pos))
        
    def edit_order_info(self, number):
        info = database.fetch_order_by_number(number)
        if not info:
            QMessageBox.warning(self, "错误", f"未找到单号 {number}")
            return
        
        yymm, category_code, unit, date_str, task_name = info
        
        current_info = {
            "number": number,
            "yymm": yymm,
            "category_code": category_code,
            "unit": unit,
            "task_name": task_name
        }
        
        dlg = EditOrderDialog(current_info, self)
        if dlg.exec():
            new_data = dlg.get_data()
            res = database.update_order_info(
                number,
                new_data['task_name'],
                new_data['unit'],
                new_data['category_code'],
                new_data['yymm']
            )
            
            if res['success']:
                QMessageBox.information(self, "成功", res['msg'])
                self.load_history() # Refresh list
            else:
                QMessageBox.critical(self, "失败", f"更新失败: {res['msg']}")

    def change_order_date(self, number):
        info = database.fetch_order_by_number(number)
        if not info:
            QMessageBox.warning(self, "错误", f"未找到单号 {number}")
            return
        yymm, cat_code, unit, old_date, task_name = info
        from ui_main import ChangeDateDialog
        dlg = ChangeDateDialog(number, old_date, self)
        if dlg.exec():
            new_date = dlg.get_date_str()
            # 基本校验：YYYY-MM-DD
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", new_date):
                QMessageBox.warning(self, "格式错误", "日期格式应为 YYYY-MM-DD")
                return
            try:
                ok = database.update_order_date(number, new_date)
                if ok:
                    # 操作日志
                    try:
                        import os
                        operator = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USERNAME', '')
                    except Exception:
                        operator = ""
                    from datetime import datetime
                    database.save_operation_log(number, "date", old_date or "", new_date, operator, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    # UI 刷新：列表与明细页
                    for r in range(self.form.table.rowCount()):
                        it = self.form.table.item(r, 1)
                        if it and it.text() == number:
                            self.form.table.setItem(r, 0, QTableWidgetItem(new_date))
                            break
                    if self.detail_widget and getattr(self.detail_widget, 'main_number', '') == number:
                        # DetailWidget header在构造时写入，直接更新其标签，如存在
                        try:
                            # ReleaseDetailWidget使用 h_date；DetailWidget自定义 header 需要内部更新方法，这里采用简单回退刷新
                            self.detail_widget.header_info['date'] = new_date
                        except Exception:
                            pass
                    QMessageBox.information(self, "成功", "日期已更新")
                else:
                    QMessageBox.warning(self, "未更新", "未找到对应记录或数据未变化")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")


    def on_table_cell_clicked(self, row, col):
        if col == 9: # Approval Doc
            num_item = self.form.table.item(row, 1)
            if not num_item: return
            number = num_item.text()
            
            # Check if file exists
            path = database.get_approval_doc(number)
            
            # 路径自适应：如果记录的路径不存在，尝试在当前exe所在目录的"审批单据"文件夹下查找
            final_path = path
            if path and not os.path.exists(path):
                if getattr(sys, "frozen", False):
                    app_dir = os.path.dirname(sys.executable)
                else:
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                
                local_candidate = os.path.join(app_dir, "审批单据", os.path.basename(path))
                if os.path.exists(local_candidate):
                    final_path = local_candidate
            
            if final_path and os.path.exists(final_path):
                self.handle_approval_doc_click(number, final_path)
            else:
                self.upload_approval_doc(number)

    def handle_approval_doc_click(self, number, path):
        box = QMessageBox(self)
        box.setWindowTitle("审批单据操作")
        box.setText(f"单号 {number} 已关联文件：\n{os.path.basename(path)}")
        btn_open = box.addButton("打开文件", QMessageBox.AcceptRole)
        btn_upload = box.addButton("重新上传", QMessageBox.ActionRole)
        btn_cancel = box.addButton("取消", QMessageBox.RejectRole)
        box.exec()
        
        if box.clickedButton() == btn_open:
            self.open_approval_doc(path)
        elif box.clickedButton() == btn_upload:
            self.upload_approval_doc(number)

    def upload_approval_doc(self, number):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择审批单据PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        # Check size < 10MB
        try:
            size = os.path.getsize(file_path)
            if size > 10 * 1024 * 1024:
                QMessageBox.warning(self, "文件过大", "文件大小超过10MB限制")
                return
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取文件: {e}")
            return
            
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        target_dir = os.path.join(base_dir, "审批单据")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        original_name = os.path.basename(file_path)
        # Simple sanitize
        name_root, _ = os.path.splitext(original_name)
        safe_name = "".join(c for c in name_root if c.isalnum() or c in "._- ").strip()
        if not safe_name: safe_name = "doc"
        
        timestamp = int(time.time())
        new_name = f"{number}_{safe_name}_{timestamp}.pdf"
        target_path = os.path.join(target_dir, new_name)
        
        try:
            shutil.copy2(file_path, target_path)
            
            if database.update_approval_doc(number, target_path):
                # 优先更新界面，避免日志记录失败导致界面不刷新
                self.refresh_row_approval_doc(number, target_path)
                
                try:
                    try:
                        operator = os.getlogin()
                    except:
                        operator = os.environ.get('USERNAME', 'User')
                    from datetime import datetime
                    database.save_operation_log(number, "approval_doc", "", new_name, operator, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                except Exception as log_e:
                    print(f"日志记录失败: {log_e}")
                
                QMessageBox.information(self, "成功", "上传成功")
            else:
                QMessageBox.critical(self, "失败", "数据库更新失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"上传失败: {e}")

    def open_approval_doc(self, path):
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
             QMessageBox.critical(self, "错误", f"无法打开文件: {e}")

    def refresh_row_approval_doc(self, number, path):
        for r in range(self.form.table.rowCount()):
            it = self.form.table.item(r, 1)
            if it and it.text() == number:
                display = self.get_display_name(path)
                item = self.form.table.item(r, 9)
                item.setText(display)
                item.setForeground(Qt.blue)
                item.setToolTip(f"已上传: {display}\n点击打开，右键可替换")
                break


def main():
    database.init_db()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
