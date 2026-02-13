from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QFileDialog, QAbstractItemView, QStyledItemDelegate, QLineEdit,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QTabWidget, QFormLayout, QSpinBox
)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, QThread, Signal
from datetime import datetime
import database
import price_analysis
from export import OrderExporter
from print import OrderPrinter

class AnalysisWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(str)
    
    def run(self):
        try:
            # Pass a lambda to emit progress
            # Note: price_analysis.run_analysis_task needs to accept a callback
            msg = price_analysis.run_analysis_task(lambda p, t: self.progress.emit(p, t))
            self.finished.emit(msg)
        except Exception as e:
            self.finished.emit(f"分析失败: {str(e)}")

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
        # Visual feedback: Add a border or style
        editor.setStyleSheet("border: 2px solid #0078d7;") 
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
                model.setData(index, "", Qt.EditRole)
                return
            val = float(text)
            # Check range (optional, e.g., non-negative)
            if val < 0:
                 # Could warn here, but tricky inside delegate. Just accept for now.
                 pass
            model.setData(index, f"{val:.2f}", Qt.EditRole)
        except ValueError:
            pass # Ignore invalid input

class EditStandardItemDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑标准品名" if item_data else "新增标准品名")
        self.item_data = item_data # (id, name, spec, unit, avg_price, latest_price)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_spec = QLineEdit()
        self.inp_unit = QLineEdit()
        self.inp_price = QLineEdit() # Latest Price
        self.inp_price.setValidator(QDoubleValidator(0.0, 999999999.0, 2))
        
        if self.item_data:
            # item_data: (id, name, spec, unit, avg_price, latest_price, ...)
            self.inp_name.setText(str(self.item_data[1] or ""))
            self.inp_spec.setText(str(self.item_data[2] or ""))
            self.inp_unit.setText(str(self.item_data[3] or ""))
            self.inp_price.setText(str(self.item_data[5] or ""))
            
        form.addRow("品名:", self.inp_name)
        form.addRow("规格:", self.inp_spec)
        form.addRow("单位:", self.inp_unit)
        form.addRow("最新参考价:", self.inp_price)
        
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        try:
            price = float(self.inp_price.text() or 0)
        except:
            price = 0.0
        return {
            "name": self.inp_name.text().strip(),
            "spec": self.inp_spec.text().strip(),
            "unit": self.inp_unit.text().strip(),
            "latest_price": price
        }

class ViewMappingsDialog(QDialog):
    def __init__(self, standard_id, standard_name, parent=None):
        super().__init__(parent)
        self.standard_id = standard_id
        self.setWindowTitle(f"映射详情 - {standard_name}")
        self.resize(600, 400)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["原始品名", "原始规格", "置信度", "来源", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def load_data(self):
        mappings = price_analysis.fetch_mappings_by_standard_id(self.standard_id)
        self.table.setRowCount(len(mappings))
        for r, row in enumerate(mappings):
            # row: id, raw_name, raw_spec, confidence, source, created_at
            mid = row[0]
            self.table.setItem(r, 0, QTableWidgetItem(str(row[1])))
            self.table.setItem(r, 1, QTableWidgetItem(str(row[2])))
            self.table.setItem(r, 2, QTableWidgetItem(f"{float(row[3])*100:.0f}%"))
            self.table.setItem(r, 3, QTableWidgetItem(str(row[4])))
            
            btn_del = QPushButton("删除映射")
            btn_del.clicked.connect(lambda _, m=mid: self.delete_mapping(m))
            self.table.setCellWidget(r, 4, btn_del)

    def delete_mapping(self, mid):
        if QMessageBox.question(self, "确认", "确定删除此映射关系吗？") == QMessageBox.Yes:
            price_analysis.delete_mapping(mid)
            self.load_data()

class HistoricalQuotesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史报价与标准库管理")
        self.resize(900, 600)
        self.worker = None
        self.std_page = 1
        self.std_page_size = 20
        self.setup_ui()
        self.refresh_stats()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Data Import & Analysis
        self.tab_import = QWidget()
        self.setup_import_tab(self.tab_import)
        self.tabs.addTab(self.tab_import, "数据导入与分析")
        
        # Tab 2: Standard Library Management
        self.tab_manage = QWidget()
        self.setup_manage_tab(self.tab_manage)
        self.tabs.addTab(self.tab_manage, "标准库管理")
        
        # Close
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def setup_import_tab(self, parent):
        layout = QVBoxLayout(parent)
        
        # Stats
        self.lbl_stats = QLabel("加载中...")
        self.lbl_stats.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.lbl_stats)
        
        # Actions
        h = QHBoxLayout()
        btn_import = QPushButton("导入历史报价(Excel)")
        btn_import.clicked.connect(self.do_import)
        btn_import.setMinimumHeight(40)
        
        btn_clear = QPushButton("清空历史数据")
        btn_clear.clicked.connect(self.do_clear)
        btn_clear.setMinimumHeight(40)
        
        btn_analyze = QPushButton("立即执行后台分析")
        btn_analyze.clicked.connect(self.start_analysis)
        btn_analyze.setMinimumHeight(40)
        
        h.addWidget(btn_import)
        h.addWidget(btn_clear)
        h.addWidget(btn_analyze)
        layout.addLayout(h)
        
        # Analysis Progress Label
        self.lbl_analysis = QLabel("")
        self.lbl_analysis.setStyleSheet("color: blue; padding: 5px;")
        layout.addWidget(self.lbl_analysis)
        
        layout.addStretch()

    def setup_manage_tab(self, parent):
        layout = QVBoxLayout(parent)
        
        # Toolbar
        h = QHBoxLayout()
        h.addWidget(QLabel("搜索:"))
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("品名或规格...")
        self.inp_search.returnPressed.connect(self.load_standard_items)
        h.addWidget(self.inp_search)
        
        btn_search = QPushButton("查询")
        btn_search.clicked.connect(self.load_standard_items)
        h.addWidget(btn_search)
        layout.addLayout(h)
        
        # Table
        self.tbl_std = QTableWidget()
        self.tbl_std.setColumnCount(7)
        self.tbl_std.setHorizontalHeaderLabels(["ID", "品名", "规格", "单位", "统计均价", "最新参考价", "样本数"])
        self.tbl_std.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_std.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_std.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_std.setColumnHidden(0, True) # Hide ID
        layout.addWidget(self.tbl_std)
        
        # Pagination
        h_page = QHBoxLayout()
        btn_prev = QPushButton("上一页")
        btn_prev.clicked.connect(self.prev_page)
        btn_next = QPushButton("下一页")
        btn_next.clicked.connect(self.next_page)
        self.lbl_page = QLabel("第 1 页")
        h_page.addWidget(btn_prev)
        h_page.addWidget(self.lbl_page)
        h_page.addWidget(btn_next)
        h_page.addStretch()
        layout.addLayout(h_page)
        
        # Actions
        h_act = QHBoxLayout()
        btn_edit = QPushButton("编辑选中")
        btn_edit.clicked.connect(self.edit_selected_item)
        btn_map = QPushButton("查看映射")
        btn_map.clicked.connect(self.view_mappings)
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self.delete_selected_item)
        btn_export = QPushButton("导出标准库")
        btn_export.clicked.connect(self.do_export_standard_lib)
        
        h_act.addWidget(btn_edit)
        h_act.addWidget(btn_map)
        h_act.addWidget(btn_del)
        h_act.addWidget(btn_export)
        h_act.addStretch()
        layout.addLayout(h_act)
        
        # Initial Load
        self.load_standard_items()

    def load_standard_items(self):
        filter_text = self.inp_search.text().strip()
        items = price_analysis.fetch_standard_items(filter_text, self.std_page, self.std_page_size)
        
        self.tbl_std.setRowCount(len(items))
        for r, row in enumerate(items):
            # row: id, name, spec, unit, avg_price, latest_price, data_count, updated_at
            sid, name, spec, unit, avg, latest, count, updated = row
            
            self.tbl_std.setItem(r, 0, QTableWidgetItem(str(sid)))
            self.tbl_std.setItem(r, 1, QTableWidgetItem(str(name)))
            self.tbl_std.setItem(r, 2, QTableWidgetItem(str(spec)))
            self.tbl_std.setItem(r, 3, QTableWidgetItem(str(unit)))
            self.tbl_std.setItem(r, 4, QTableWidgetItem(f"{avg:,.2f}"))
            self.tbl_std.setItem(r, 5, QTableWidgetItem(f"{latest:,.2f}"))
            self.tbl_std.setItem(r, 6, QTableWidgetItem(str(count)))
            
        self.lbl_page.setText(f"第 {self.std_page} 页")

    def prev_page(self):
        if self.std_page > 1:
            self.std_page -= 1
            self.load_standard_items()

    def next_page(self):
        # Optimistic next page (if current page full)
        if self.tbl_std.rowCount() >= self.std_page_size:
            self.std_page += 1
            self.load_standard_items()

    def get_selected_id(self):
        row = self.tbl_std.currentRow()
        if row < 0:
            return None
        return int(self.tbl_std.item(row, 0).text())

    def get_selected_row_data(self):
        row = self.tbl_std.currentRow()
        if row < 0: return None
        # Return tuple matching price_analysis format mostly
        # id, name, spec, unit, avg, latest
        return (
            int(self.tbl_std.item(row, 0).text()),
            self.tbl_std.item(row, 1).text(),
            self.tbl_std.item(row, 2).text(),
            self.tbl_std.item(row, 3).text(),
            0, # avg placeholder
            float(self.tbl_std.item(row, 5).text().replace(",", ""))
        )

    def edit_selected_item(self):
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "提示", "请先选择一行")
            return
            
        dlg = EditStandardItemDialog(data, self)
        if dlg.exec():
            new_data = dlg.get_data()
            price_analysis.update_standard_item(
                data[0], new_data['name'], new_data['spec'], 
                new_data['unit'], new_data['latest_price']
            )
            self.load_standard_items()
            QMessageBox.information(self, "成功", "更新成功")

    def delete_selected_item(self):
        sid = self.get_selected_id()
        if not sid:
            QMessageBox.warning(self, "提示", "请先选择一行")
            return
            
        if QMessageBox.question(self, "确认", "确定删除此标准品名及其所有映射关系吗？") == QMessageBox.Yes:
            price_analysis.delete_standard_item(sid)
            self.load_standard_items()
            self.refresh_stats()

    def view_mappings(self):
        data = self.get_selected_row_data()
        if not data:
            QMessageBox.warning(self, "提示", "请先选择一行")
            return
            
        dlg = ViewMappingsDialog(data[0], data[1], self)
        dlg.exec()

    def do_export_standard_lib(self):
        filter_text = self.inp_search.text().strip()
        default_name = f"标准价格库_{datetime.now().strftime('%Y%m%d')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", default_name, "Excel Files (*.xlsx)")
        if not file_path:
            return
            
        count, msg = price_analysis.export_standard_items_to_excel(file_path, filter_text)
        if count > 0:
            QMessageBox.information(self, "成功", f"成功导出 {count} 条数据")
        else:
            QMessageBox.warning(self, "提示", f"导出失败或无数据: {msg}")

    def refresh_stats(self):
        stats = price_analysis.get_stats()
        if stats:
            msg = f"当前库中共有 {stats['total_records']} 条历史报价记录\n涉及 {stats['unique_items']} 种不同物资"
            if stats.get('pending_records', 0) > 0:
                msg += f"\n\n待处理记录: {stats['pending_records']} 条 (建议执行分析)"
            if stats.get('standard_items', 0) > 0:
                msg += f"\n标准品名库: {stats['standard_items']} 个"
            self.lbl_stats.setText(msg)
        else:
            self.lbl_stats.setText("获取统计信息失败")

    def do_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
            
        # Show wait cursor or progress
        from PySide6.QtGui import QCursor
        self.setCursor(QCursor(Qt.WaitCursor))
        
        count, msg = price_analysis.import_historical_quotes(file_path)
        
        self.setCursor(QCursor(Qt.ArrowCursor))
        
        if count > 0:
            QMessageBox.information(self, "导入成功", f"成功导入 {count} 条数据\n系统将自动在后台进行清洗分析。")
            self.refresh_stats()
            self.start_analysis()
        else:
            QMessageBox.warning(self, "导入失败", f"未导入任何数据。\n错误信息: {msg}")

    def start_analysis(self):
        if self.worker and self.worker.isRunning():
            return
            
        self.lbl_analysis.setText("正在后台分析历史数据，请稍候...")
        self.worker = AnalysisWorker()
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.start()
        
    def on_analysis_progress(self, current, total):
        self.lbl_analysis.setText(f"正在后台分析: {current}/{total}")
        
    def on_analysis_finished(self, msg):
        self.lbl_analysis.setText(msg)
        self.refresh_stats()

    def do_clear(self):
        ret = QMessageBox.question(self, "确认", "确定要清空所有历史报价数据吗？此操作不可恢复！", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            price_analysis.clear_history()
            self.refresh_stats()
            QMessageBox.information(self, "完成", "历史数据已清空")

class PlanExportWidget(QWidget):
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
        toolbar.addWidget(self.combo_month)
        
        btn_load = QPushButton("加载数据")
        btn_load.clicked.connect(self.load_data)
        toolbar.addWidget(btn_load)
        
        btn_save = QPushButton("保存修改")
        btn_save.clicked.connect(self.save_data)
        toolbar.addWidget(btn_save)
        
        # New Buttons
        btn_history = QPushButton("历史报价库")
        btn_history.clicked.connect(self.open_historical_quotes)
        toolbar.addWidget(btn_history)

        btn_smart = QPushButton("智能填充审核价")
        btn_smart.clicked.connect(self.smart_fill_prices)
        btn_smart.setStyleSheet("background-color: #e0f2f1; color: #00695c; font-weight: bold;")
        toolbar.addWidget(btn_smart)
        
        btn_learn = QPushButton("反向学习(保存价格)")
        btn_learn.clicked.connect(self.learn_prices)
        btn_learn.setToolTip("将当前表格中已有的审核价格保存到标准库，以便下次自动填充")
        toolbar.addWidget(btn_learn)
        
        btn_export = QPushButton("导出Excel")
        btn_export.clicked.connect(self.export_excel)
        toolbar.addWidget(btn_export)
        
        btn_print = QPushButton("打印")
        btn_print.clicked.connect(self.print_table)
        toolbar.addWidget(btn_print)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Search Area (moved to top, just below month toolbar)
        search = QHBoxLayout()
        search.addWidget(QLabel("序号:"))
        self.filter_seq = QLineEdit()
        self.filter_seq.setPlaceholderText("如 2601MPB-1 或 1-5")
        self.filter_seq.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_seq)

        search.addWidget(QLabel("采购标的:"))
        self.filter_item = QLineEdit()
        self.filter_item.setPlaceholderText("关键词")
        self.filter_item.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_item)

        search.addWidget(QLabel("主单编号:"))
        self.filter_order = QLineEdit()
        self.filter_order.setPlaceholderText("精确或模糊")
        self.filter_order.textChanged.connect(self.apply_filters)
        search.addWidget(self.filter_order)

        search.addWidget(QLabel("需求单位:"))
        self.combo_unit = QComboBox()
        self.combo_unit.setEditable(False)
        self.combo_unit.currentIndexChanged.connect(self.apply_filters)
        search.addWidget(self.combo_unit)

        self.btn_unit_multi = QPushButton("多选...")
        self.btn_unit_multi.clicked.connect(self._open_unit_multi_dialog)
        search.addWidget(self.btn_unit_multi)

        btn_clear = QPushButton("清空筛选")
        btn_clear.clicked.connect(self._clear_filters)
        search.addWidget(btn_clear)
        search.addStretch()
        layout.addLayout(search)

        self._unit_multi_selected = set()

        # Table
        # Columns for export preview (updated per requirements)
        self.columns = [
            "序号", "主单编号", "需求单位", "采购标的", "规格型号",
            "单位", "采购数量", "预算(万)",
            "采购方式", "采购渠道", "计划发放", "询价金额", "审核金额", "备注"
        ]
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed) 
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Set Delegate for Inquiry Amount (Index 11) and Audit Amount (Index 12)
        self.table.setItemDelegateForColumn(11, MoneyDelegate(self.table))
        self.table.setItemDelegateForColumn(12, MoneyDelegate(self.table))
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Adjust some widths
        self.table.setColumnWidth(0, 110) # 序号
        self.table.setColumnWidth(1, 150) # 主单编号
        self.table.setColumnWidth(2, 120) # 需求单位
        self.table.setColumnWidth(3, 160) # 采购标的
        self.table.setColumnWidth(4, 160) # 规格型号
        
        layout.addWidget(self.table)
        
        self.current_rows_data = [] # Store raw data for export
        self.modified_indices = set()

    def load_months(self):
        self.combo_month.clear()
        months = database.fetch_plan_months()
        self.combo_month.addItems(months)
        if months:
            self.combo_month.setCurrentIndex(0)

    def load_data(self):
        month = self.combo_month.currentText()
        if not month:
            return
            
        # database.fetch_monthly_details_for_export returns:
        # 0:o.number, 1:o.task_name, 2:o.category, 3:o.unit, 4:o.date,
        # 5:od.detail_no, 6:od.item_name, 7:od.purchase_item, 8:od.spec_model, 
        # 9:od.unit, 10:od.purchase_qty, 11:od.budget_wan, 12:od.purchase_method, 13:od.purchase_channel,
        # 14:od.plan_release, 15:od.inquiry_price, 16:od.supplier, 17:od.remark, 18:od.plan_time
        
        raw_data = database.fetch_monthly_details_for_export(month)
        self.current_rows_data = [list(r) for r in raw_data]
        self.modified_indices.clear()
        
        # Load units for filter
        units = database.fetch_units()
        self.combo_unit.blockSignals(True)
        self.combo_unit.clear()
        self.combo_unit.addItem("全部")
        for u in units:
            self.combo_unit.addItem(u)
        self.combo_unit.blockSignals(False)

        # Apply filters to refresh table
        self.apply_filters()
        QMessageBox.information(self, "完成", f"已加载 {len(raw_data)} 条数据")

    def open_historical_quotes(self):
        dlg = HistoricalQuotesDialog(self)
        dlg.exec()

    def smart_fill_prices(self):
        if not self.current_rows_data:
            return
            
        count = 0
        errors = []
        
        from PySide6.QtGui import QCursor
        self.setCursor(QCursor(Qt.WaitCursor))
        
        try:
            for idx, row in enumerate(self.current_rows_data):
                # Check if Audit Price is empty or 0
                # 19: audit_price
                current_audit = row[19] if len(row) > 19 else None
                
                # If already has value, skip? User might want to update.
                # Let's skip if non-empty string and not "0" and not "0.00"
                if current_audit and str(current_audit).strip() and float(str(current_audit).replace(",", "") or 0) > 0:
                    continue
                    
                item_name = str(row[7] or "") # purchase_item
                spec_model = str(row[8] or "") # spec_model
                
                try:
                    rec = price_analysis.get_recommendation(item_name, spec_model)
                except Exception as e:
                    errors.append(f"行 {idx+1}: {str(e)}")
                    continue
                
                if rec:
                    price = rec.get('price')
                    if price is None:
                        price = 0.0
                    
                    # Calculate Total Amount = Unit Price * Quantity
                    # 10:od.purchase_qty
                    qty_str = str(row[10] or "").strip()
                    try:
                        qty = float(qty_str.replace(",", ""))
                    except:
                        qty = 0.0
                        
                    total_amount = price * qty
                    
                    # Format to 2 decimals
                    price_str = f"{total_amount:.2f}"
                    
                    # Update data
                    if len(row) > 19:
                        row[19] = price_str
                    else:
                        # Should not happen given fetch query, but safety
                        row.append(price_str)
                        
                    self.modified_indices.add(idx)
                    count += 1
        except Exception as e:
            errors.append(f"总体错误: {str(e)}")
                
        self.setCursor(QCursor(Qt.ArrowCursor))
        
        if errors:
            QMessageBox.warning(self, "警告", f"智能填充完成，但发生以下错误:\n" + "\n".join(errors[:5]))
        
        if count > 0:
            self.apply_filters() # Refresh UI
            QMessageBox.information(self, "智能填充", f"已为 {count} 条记录填充了推荐价格。\n请检查并在确认无误后点击“保存修改”。")
        elif not errors:
            QMessageBox.information(self, "智能填充", "没有找到可填充的推荐价格，或所有记录已有价格。")

    def learn_prices(self):
        """
        Collect audit prices from the table and save to standard library.
        """
        if not self.current_rows_data:
            return

        # Ask for confirmation
        ret = QMessageBox.question(
            self, "确认反向学习", 
            "系统将把当前表格中所有有效的【审核金额】保存到标准价格库中。\n"
            "这样下次遇到相同的标的物时，就能自动推荐价格了。\n\n"
            "确定要执行吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        items_to_learn = []
        
        for row in self.current_rows_data:
            # 7:purchase_item, 8:spec_model, 9:unit, 10:purchase_qty, 19:audit_price
            item_name = str(row[7] or "").strip()
            spec_model = str(row[8] or "").strip()
            unit = str(row[9] or "").strip()
            
            # Audit Price is Total Amount, we need Unit Price for the library
            # audit_price (total) = unit_price * qty
            # So unit_price = audit_price / qty
            
            audit_total_str = str(row[19] if len(row) > 19 else "").replace(",", "").strip()
            qty_str = str(row[10] or "").replace(",", "").strip()
            
            try:
                audit_total = float(audit_total_str)
                qty = float(qty_str)
            except:
                continue
                
            if audit_total <= 0 or qty <= 0:
                continue
                
            unit_price = audit_total / qty
            
            items_to_learn.append({
                "name": item_name,
                "spec": spec_model,
                "unit": unit,
                "price": unit_price
            })
            
        if not items_to_learn:
            QMessageBox.information(self, "提示", "当前表格中没有有效的审核价格数据可供学习。")
            return
            
        # Call backend
        try:
            count, msg = price_analysis.learn_from_plan_items(items_to_learn)
            if count > 0:
                QMessageBox.information(self, "学习完成", f"成功学习并更新了 {count} 条标准价格记录！\n下次遇到这些物资时将自动推荐价格。")
            else:
                QMessageBox.warning(self, "失败", f"学习失败: {msg}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")

    def _prepare_export_data(self):
        # Header Info for printing/export
        # Since this is a monthly summary, we don't have a single order number.
        # We can set title to "月度采购计划汇总"
        month = self.combo_month.currentText()
        header_info = {
            "number": "汇总",
            "task_name": "月度汇总",
            "unit": "多部门",
            "yymm": month,
            "purchaser": "所有"
        }
        
        rows = []
        for r in range(self.table.rowCount()):
            row_data = []
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                row_data.append(it.text() if it else "")
            rows.append(row_data)
            
        return header_info, rows

    def export_excel(self):
        if self.table.rowCount() == 0:
            return
            
        month = self.combo_month.currentText()
        default_name = f"采购计划明细_{month}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出Excel", default_name, "Excel Files (*.xlsx)")
        
        if not file_path:
            return
            
        header_info, rows = self._prepare_export_data()
        
        try:
            exporter = OrderExporter(header_info, self.columns, rows, title=f"{month} 采购计划明细")
            exporter.export(file_path)
            QMessageBox.information(self, "成功", f"导出成功:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def print_table(self):
        if self.table.rowCount() == 0:
            return
            
        header_info, rows = self._prepare_export_data()
        
        # Remove "主单编号" from printing columns per requirement
        print_columns = [c for c in self.columns if c != "主单编号"]
        # Determine index of removed column to drop from row data
        try:
            drop_idx = self.columns.index("主单编号")
        except ValueError:
            drop_idx = None
        print_rows = []
        for r in rows:
            if drop_idx is None:
                print_rows.append(r)
            else:
                print_rows.append([r[i] for i in range(len(r)) if i != drop_idx])
        
        # Inject Group Headers for Printing
        # Replicates logic from export.py to ensure consistency
        processed_rows = []
        inserted_semi_header = False
        inserted_civil_header = False
        inserted_mach_header = False
        
        # Colors matching export.py
        COLOR_SEMI = "#F0F0F0"
        COLOR_CIVIL = "#DCE6F1"
        
        for row_data in print_rows:
            # detail_no is index 0
            detail_no = str(row_data[0]) if len(row_data) > 0 else ""
            
            is_semi = "MPB" in detail_no
            is_civil = "MP-" in detail_no or (detail_no.endswith("MP") if "MP" in detail_no else False) or ("MP" in detail_no and "MPB" not in detail_no and "MPJ" not in detail_no)
            is_mach = "MPJ" in detail_no
            
            if is_semi and not inserted_semi_header:
                processed_rows.append({"is_header": True, "text": "半成品MPB", "color": COLOR_SEMI})
                inserted_semi_header = True
                
            if is_civil and not inserted_civil_header:
                processed_rows.append({"is_header": True, "text": "民品MP", "color": COLOR_CIVIL})
                inserted_civil_header = True
            
            if is_mach and not inserted_mach_header:
                processed_rows.append({"is_header": True, "text": "机加件MPJ", "color": COLOR_CIVIL})
                inserted_mach_header = True
            
            processed_rows.append(row_data)
            
        rows = processed_rows
        
        month = self.combo_month.currentText()
        
        # Convert "2601" to "2026年1月份"
        title_month = month
        if len(month) == 4 and month.isdigit():
            yy = month[:2]
            mm = month[2:]
            title_month = f"20{yy}年{int(mm)}月份"
            
        printer = OrderPrinter(header_info, print_columns, rows)
        # Customize title
        printer.title = f"{title_month}民品采购计划表"
        printer.show_preview()

    def apply_filters(self):
        # Filter current_rows_data and render table
        seq_text = self.filter_seq.text().strip() if hasattr(self, 'filter_seq') else ""
        item_kw = self.filter_item.text().strip() if hasattr(self, 'filter_item') else ""
        order_kw = self.filter_order.text().strip() if hasattr(self, 'filter_order') else ""
        unit_sel = self.combo_unit.currentText() if hasattr(self, 'combo_unit') and self.combo_unit.count()>0 else "全部"
        unit_set = self._unit_multi_selected if hasattr(self, '_unit_multi_selected') else set()

        def match_seq(detail_no: str) -> bool:
            if not seq_text:
                return True
            import re
            m = re.match(r"^(\d+)\s*-\s*(\d+)$", seq_text)
            if m:
                try:
                    lo = int(m.group(1)); hi = int(m.group(2))
                    suf_m = re.search(r"-(\d+)$", detail_no or "")
                    if not suf_m:
                        return False
                    n = int(suf_m.group(1))
                    return lo <= n <= hi
                except:
                    return False
            return seq_text in (detail_no or "")

        def match_item(purchase_item: str) -> bool:
            if not item_kw:
                return True
            return item_kw in (purchase_item or "")

        def match_order(order_number: str) -> bool:
            if not order_kw:
                return True
            return order_kw in (order_number or "")

        def match_unit(unit_val: str) -> bool:
            if unit_set:
                return unit_val in unit_set
            if unit_sel and unit_sel != "全部":
                return unit_val == unit_sel
            return True

        rows = []
        # Use enumerate to capture the original index
        for idx, row in enumerate(self.current_rows_data):
            detail_no = str(row[5] or "")
            purchase_item = str(row[7] or "")
            order_number = str(row[0] or "")
            unit_val = str(row[3] or "")
            if match_seq(detail_no) and match_item(purchase_item) and match_order(order_number) and match_unit(unit_val):
                rows.append((idx, row))

        self.table.setRowCount(len(rows))
        self.table.blockSignals(True) # Block signals during load
        for r, (real_idx, row) in enumerate(rows):
            # Map to new columns:
            # 0 序号(detail_no), 1 主单编号(o.number), 2 需求单位(o.unit), 3 采购标的(purchase_item), 4 规格型号(spec_model)
            # 5 单位, 6 采购数量, 7 预算(万), 8 采购方式, 9 采购渠道, 10 计划发放, 11 询价金额, 12 审核金额, 13 备注
            
            # 0 序号
            item0 = QTableWidgetItem(str(row[5] or ""))
            item0.setData(Qt.UserRole, real_idx) # Store REAL index in UserRole
            item0.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) # Read only
            self.table.setItem(r, 0, item0)
            
            item1 = QTableWidgetItem(str(row[0] or ""))
            item1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 1, item1)
            
            item2 = QTableWidgetItem(str(row[3] or ""))
            item2.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 2, item2)
            
            item3 = QTableWidgetItem(str(row[7] or ""))
            item3.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 3, item3)
            
            item4 = QTableWidgetItem(str(row[8] or ""))
            item4.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 4, item4)
            
            item5 = QTableWidgetItem(str(row[9] or ""))
            item5.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 5, item5)
            
            item6 = QTableWidgetItem(str(row[10] or ""))
            item6.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 6, item6)
            
            item7 = QTableWidgetItem(str(row[11] or ""))
            item7.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 7, item7)
            
            item8 = QTableWidgetItem(str(row[12] or ""))
            item8.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 8, item8)
            
            item9 = QTableWidgetItem(str(row[13] or ""))
            item9.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 9, item9)
            
            item10 = QTableWidgetItem(str(row[14] or ""))
            item10.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 10, item10)
            
            # 11 询价金额 - EDITABLE
            item11 = QTableWidgetItem(str(row[15] or ""))
            item11.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.setItem(r, 11, item11)
            
            # 12 审核金额 - EDITABLE
            # index 19 is audit_price
            val_audit = row[19] if len(row) > 19 else ""
            item12 = QTableWidgetItem(str(val_audit or ""))
            # Highlight recommended values? Maybe green bg?
            item12.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.setItem(r, 12, item12)
            
            item13 = QTableWidgetItem(str(row[17] or ""))
            item13.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 13, item13)
            
        self.table.blockSignals(False)

    def on_item_changed(self, item):
        col = item.column()
        if col != 11 and col != 12:
            return
            
        row = item.row()
        # Get real index from column 0 item
        item0 = self.table.item(row, 0)
        if not item0: return
        
        real_idx = item0.data(Qt.UserRole)
        if real_idx is None: return
        
        new_val = item.text()
        
        # Update current_rows_data
        # Inquiry price is at index 15, Audit price is at index 19 (from updated fetch query)
        if 0 <= real_idx < len(self.current_rows_data):
             if col == 11:
                 self.current_rows_data[real_idx][15] = new_val
             elif col == 12:
                 # Check if index 19 exists, if not extend list (should not happen if fetch updated)
                 if len(self.current_rows_data[real_idx]) > 19:
                     self.current_rows_data[real_idx][19] = new_val
                 else:
                     # Fallback if list too short?
                     pass
             self.modified_indices.add(real_idx)

    def save_data(self):
        if not self.modified_indices:
            QMessageBox.information(self, "提示", "没有需要保存的修改")
            return
            
        try:
            success_count = 0
            fail_count = 0
            
            for idx in self.modified_indices:
                if idx >= len(self.current_rows_data):
                    continue
                    
                row_data = self.current_rows_data[idx]
                # 0:o.number, 5:od.detail_no, 15:od.inquiry_price, 19:od.audit_price
                order_number = row_data[0]
                detail_no = row_data[5]
                inquiry_price = row_data[15]
                audit_price = row_data[19] if len(row_data) > 19 else None
                
                if database.update_order_detail_prices(order_number, detail_no, inquiry_price, audit_price):
                    success_count += 1
                else:
                    fail_count += 1
                    
            if fail_count == 0:
                QMessageBox.information(self, "成功", f"成功保存 {success_count} 条记录")
                self.modified_indices.clear()
            else:
                QMessageBox.warning(self, "警告", f"保存完成，但有 {fail_count} 条记录失败")
                # Don't clear modified_indices completely? Or just reload?
                # Reload is safer
                self.load_data()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中发生错误: {str(e)}")

    def _open_unit_multi_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("选择需求单位")
        v = QVBoxLayout(dlg)
        lst = QListWidget()
        lst.setSelectionMode(QAbstractItemView.NoSelection)
        import database
        units = database.fetch_units()
        for u in units:
            it = QListWidgetItem(u)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if u in self._unit_multi_selected else Qt.Unchecked)
            lst.addItem(it)
        v.addWidget(lst)
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        v.addWidget(box)
        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        if dlg.exec():
            sel = set()
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == Qt.Checked:
                    sel.add(it.text())
            self._unit_multi_selected = sel
            if sel:
                self.combo_unit.setCurrentIndex(0)  # 全部
                self.combo_unit.setEditable(True)
                self.combo_unit.lineEdit().setText(f"多选({len(sel)})")
                self.combo_unit.setEditable(False)
            else:
                self.combo_unit.setEditable(True)
                self.combo_unit.lineEdit().setText("")
                self.combo_unit.setEditable(False)
            self.apply_filters()

    def _clear_filters(self):
        self.filter_seq.setText("")
        self.filter_item.setText("")
        self.filter_order.setText("")
        self._unit_multi_selected = set()
        if self.combo_unit.count()>0:
            self.combo_unit.setCurrentIndex(0)
        self.apply_filters()
