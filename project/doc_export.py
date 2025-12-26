from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWidgets import QApplication
from typing import List, Dict, Optional

from print import OrderPrinter


class DocumentExporter:
    def __init__(self, columns: List[str], rows: List, header_info: Dict, config: Optional[Dict] = None):
        self.columns = columns
        self.rows = rows
        self.header_info = dict(header_info or {})
        self.config = {
            "badge_enabled": False,
            "row_height": 40,
            "header_height": 38,
            "spacing_title": 60,
            "spacing_info": 30,
            "spacing_footer": 30,
            "footer_bottom_padding": 20,
        }
        if config:
            self.config.update(config)

    def preview(self):
        printer = OrderPrinter(self.header_info, self.columns, self.rows, self.config)
        printer.show_preview()

    def export_pdf(self, output_path: str):
        app = QApplication.instance() or QApplication([])
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Landscape)
        op = OrderPrinter(self.header_info, self.columns, self.rows, self.config)
        # Use same paint routine by opening a preview-less paint request
        op._paint_request(printer)
        if app and not QApplication.instance():
            app.quit()

    @staticmethod
    def sample(header_info_override: Optional[Dict] = None):
        cols = [
            "序号", "需求单位", "采购标的", "规格型号", "单位",
            "采购数量", "预算(万)", "采购方式", "采购渠道", "计划发放", "询价", "备注"
        ]
        rows = [
            ["2601MPJ-1", "四车间", "上板", "夹布胶木", "件", 50, "0.00", "询比采购", "线下采购", "李胜", "", "备注示例1"],
            ["2601MPJ-2", "四车间", "O形密封圈", "丁睛橡胶(NBR)", "件", 2500, "0.00", "询比采购", "线下采购", "李胜", "", "备注示例2"],
        ]
        header = {
            "number": "汇总",
            "task_name": "月度汇总",
            "unit": "多部门",
            "yymm": "2601",
            "category": "民品",
        }
        if header_info_override:
            header.update(header_info_override)
        return DocumentExporter(cols, rows, header)
