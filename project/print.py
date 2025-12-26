from PySide6.QtGui import QTextDocument, QPageLayout, QPageSize, QPainter, QFont, QPen, QColor, QTextOption
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtCore import Qt, QRectF, QRect, QDate, QPointF
from datetime import datetime


def fmt_mmdd(s):
    val = str(s or "").strip()
    if not val:
        return ""
    fmts = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%y%m%d",
        "%m-%d",
        "%m/%d",
        "%m.%d",
        "%m%d",
        "%Y年%m月%d日",
        "%Y年%m月%d号",
        "%Y年%m月%d",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(val, f)
            return dt.strftime("%m-%d")
        except Exception:
            pass
    import re
    digits = re.findall(r"\d+", val)
    joined = "".join(digits)
    if len(joined) >= 8:
        m = int(joined[-4:-2])
        d = int(joined[-2:])
        return f"{m:02d}-{d:02d}"
    if len(joined) >= 4:
        m = int(joined[-4:-2])
        d = int(joined[-2:])
        return f"{m:02d}-{d:02d}"
    return ""

def export_order_pdf(output_path: str, title: str, header_info: dict, columns: list, rows: list):
    # Old HTML method (kept for compatibility if needed, or can be ignored)
    doc = QTextDocument()
    html = [
        "<html><head><meta charset='utf-8'><style>",
        "table{border-collapse:collapse;width:100%;font-size:10pt}",
        "th,td{border:1px solid #333;padding:4px;white-space:nowrap}",
        "h1{font-size:14pt;margin:0 0 8px 0}",
        "</style></head><body>",
    ]
    html.append(f"<h1>{title}</h1>")
    info_line = f"计划月份: {header_info.get('yymm','')} | 类别: {header_info.get('category','')} | 需求单位: {header_info.get('unit','')}"
    html.append(f"<div>{info_line}</div>")
    html.append("<table><thead><tr>")
    for c in columns:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")
    for r in rows:
        html.append("<tr>")
        for cell in r:
            html.append(f"<td>{'' if cell is None else str(cell)}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    html.append("</body></html>")
    doc.setHtml("".join(html))
    printer = QPrinter()
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    printer.setPageOrientation(QPageLayout.Landscape)
    printer.setPageSize(QPageSize(QPageSize.A4))
    doc.print(printer)


class OrderPrinter:
    def __init__(self, header_info: dict, columns: list, rows: list, config: dict = None):
        self.header_info = header_info
        self.columns = columns
        self.rows = rows
        
        # Default config
        self.config = {
            "title": "采购计划表",
            "rows_per_page": 13,
            "row_height": 45,
            "header_height": 45,
            "font_title": 24,
            "font_header": 12,
            "font_table_header": 11,
            "font_cell": 10,
            "font_footer": 12,
            "margin_x": 0.03,
            "margin_y": 0.05,
            "footer_1": "审核：",
            "footer_2": "签收：",
            "footer_3": "编制：",
            "footer_bottom_padding": 20,
            "badge_enabled": True,
            "badge_width": 120,
            "badge_height": 40,
            "badge_offset_x": 0,
            "badge_offset_y": 10,
            "badge_font": 16,
            "badge_radius": 8,
            "badge_font_family": "SimHei",
            "badge_font_weight": 87
        }
        
        # Override with provided config
        if config:
            for k, v in config.items():
                self.config[k] = v
                
        self.title = self.config["title"]
        self.rows_per_page = self.config["rows_per_page"]
        
    def show_preview(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Landscape)
        
        preview = QPrintPreviewDialog(printer)
        preview.setWindowTitle("打印预览")
        preview.resize(1200, 800)
        preview.paintRequested.connect(self._paint_request)
        preview.exec()

    def _paint_request(self, printer):
        printer.setFullPage(True) # Ensure we control margins
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        
        page_rect = printer.pageRect(QPrinter.DevicePixel).toRect()
        width = page_rect.width()
        height = page_rect.height()
        
        # Calculate DPI scale factor relative to standard 96 DPI
        # QPrinter.HighResolution typically uses 600 or 1200 DPI
        dpi = printer.logicalDpiX()
        scale_factor = dpi / 96.0
        
        # Helper to scale user "px" values to printer "dots"
        def s(val):
            return int(val * scale_factor)

        # Margins (Reduced margins to allow more space)
        # Margins are percentages, so no scaling needed for calculation, but resulting pixels are large
        margin_x = int(width * self.config["margin_x"]) 
        margin_y = int(height * self.config["margin_y"]) 
        content_width = width - 2 * margin_x
        
        # Fonts
        # QFont uses points, which are resolution independent, so NO scaling needed for size value
        font_title = QFont("SimSun", self.config["font_title"], QFont.Bold) 
        font_header = QFont("SimSun", self.config["font_header"]) 
        font_table_header = QFont("SimSun", self.config["font_table_header"], QFont.Bold) 
        font_cell = QFont("SimSun", self.config["font_cell"]) 
        font_footer = QFont("SimSun", self.config["font_footer"]) 
        
        # Metrics
        # Scale "px" settings to printer dots
        row_height = s(self.config["row_height"]) 
        header_height = s(self.config.get("header_height", self.config["row_height"]))
        
        # Scale spacings
        spacing_title = s(60)
        spacing_info = s(30)
        spacing_footer = s(30)
        
        # Scale fixed heights for layout rects
        h_title = s(60)
        h_info = s(30)
        h_footer = s(80)
        
        # Pre-calculate pagination with dynamic heights
        # Column widths
        # Default weights for normal plan
        default_weights = [1.5, 2, 2, 1, 0.6, 1.0, 1.0, 1.2, 1.2, 1.2, 1.2, 1.0, 0.6, 1.5]
        
        # If columns count mismatch (export/print variants), adjust weights
        if len(self.columns) == 12:
            # 序号, 需求单位, 采购标的, 规格型号, 单位, 采购数量, 预算(万), 采购方式, 采购渠道, 计划发放, 询价金额, 备注
            weights = [0.9, 1.6, 2.0, 2.0, 0.7, 1.0, 1.0, 1.2, 1.2, 1.0, 1.2, 1.5]
        elif len(self.columns) == len(default_weights):
            weights = default_weights
        else:
            # Fallback: equal width
            weights = [1.0] * len(self.columns)
            
        total_weight = sum(weights)
        col_widths = [int(w * content_width / total_weight) for w in weights]
        
        pages_content = []
        current_row_idx = 0
        total_rows = len(self.rows)
        
        # Simulate printing to calculate pages
        # Create a dummy painter for font metrics or assume standard
        # We are inside paint_request, so we have 'painter'
        
        while current_row_idx < total_rows:
            page_rows = []
            slots_used = 0
            # Use fixed capacity per page
            max_slots = self.rows_per_page
            
            while current_row_idx < total_rows:
                row_data = self.rows[current_row_idx]
                
                # Special handling for Group Header (dict)
                if isinstance(row_data, dict) and row_data.get("is_header"):
                    # Header takes 1 line height usually
                    if slots_used + 1 > max_slots:
                        if slots_used == 0:
                            page_rows.append((row_data, 1))
                            slots_used += 1
                            current_row_idx += 1
                        break
                    
                    page_rows.append((row_data, 1))
                    slots_used += 1
                    current_row_idx += 1
                    continue
                    
                max_lines = 1
                for col_idx, w in enumerate(col_widths):
                    val = row_data[col_idx]
                    text = str(val) if val is not None else ""
                    fm = painter.fontMetrics()
                    rect_needed = fm.boundingRect(QRect(0, 0, w, 10000), Qt.TextWordWrap, text)
                    # Height needed logic
                    needed_h = rect_needed.height() + s(10) # padding
                    slots = (needed_h + row_height - 1) // row_height
                    if slots > max_lines:
                        max_lines = int(slots)
                
                if slots_used + max_lines > max_slots:
                    # Can't fit, break to next page
                    # Unless it's the ONLY row and it's too huge? 
                    # Assume we handle huge rows by capping or splitting? 
                    # For now, just break. If slots_used == 0 and max_lines > max_slots, force fit 1 but it will overflow.
                    if slots_used == 0:
                        # Force fit single huge row
                        page_rows.append((row_data, max_lines))
                        slots_used += max_lines
                        current_row_idx += 1
                    break
                
                page_rows.append((row_data, max_lines))
                slots_used += max_lines
                current_row_idx += 1
            
            pages_content.append(page_rows)
            
        total_pages = len(pages_content)
        if total_pages == 0: total_pages = 1
        
        # Iterate pages
        for page_idx, page_rows_data in enumerate(pages_content):
            if page_idx > 0:
                printer.newPage()
            
            y = margin_y
            # Category Badge
            if self.config.get("badge_enabled", True):
                bw = s(self.config.get("badge_width", 120))
                bh = s(self.config.get("badge_height", 40))
                bx = margin_x + s(self.config.get("badge_offset_x", 0))
                by = y + s(self.config.get("badge_offset_y", 10))
                painter.save()
                painter.setPen(Qt.NoPen)
                # pure black rounded rect, no border
                painter.setBrush(QColor("black"))
                painter.drawRoundedRect(QRectF(bx, by, bw, bh), s(self.config.get("badge_radius", 8)), s(self.config.get("badge_radius", 8)))
                painter.setPen(QPen(QColor("white"), 0))
                badge_font = QFont(self.config.get("badge_font_family", "SimHei"), self.config.get("badge_font", 16), QFont.Bold)
                try:
                    badge_font.setWeight(int(self.config.get("badge_font_weight", 87)))
                except Exception:
                    pass
                badge_font.setBold(True)
                painter.setFont(badge_font)
                cat_text = str(self.header_info.get("category", ""))
                if "MPJ" in cat_text: cat_text = "机加件"
                elif "MPB_WX" in cat_text: cat_text = "外销模块"
                elif "MPB" in cat_text: cat_text = "半成品"
                elif "民品" not in cat_text and cat_text: cat_text = cat_text
                else: cat_text = "民品"
                painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, cat_text)
                painter.restore()
            
            # 1. Title
            painter.setFont(font_title)
            title_rect = QRectF(margin_x, y, content_width, h_title) 
            painter.drawText(title_rect, Qt.AlignCenter, self.title)
            y += spacing_title 
            
            # 2. Header Info
            painter.setFont(font_header)
            info_y = y
            info_h = h_info
            info_str_1 = f"主单编号：{self.header_info.get('number', '')}"
            info_str_2 = f"采购任务名称：{self.header_info.get('task_name', '')}"
            info_str_3 = f"需求单位：{self.header_info.get('unit', '')}"
            info_str_4 = f"发放日期：{fmt_mmdd(self.header_info.get('date', ''))}"
            
            w_no = content_width * 0.21
            w_task = content_width * 0.39
            w_unit = content_width * 0.16
            w_month = content_width * 0.12
            
            painter.drawText(QRectF(margin_x, info_y, w_no, info_h), Qt.AlignLeft | Qt.AlignVCenter, info_str_1)
            
            option = QTextOption()
            option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            task_rect = QRectF(margin_x + w_no, info_y, w_task, info_h)
            fm = painter.fontMetrics()
            needed = fm.boundingRect(QRect(0, 0, int(w_task), 10000), Qt.TextWordWrap, info_str_2).height() + s(6)
            used_info_h = max(info_h, needed)
            task_rect.setHeight(used_info_h)
            painter.drawText(task_rect, info_str_2, option)
            
            unit_rect = QRectF(margin_x + w_no + w_task, info_y, w_unit, info_h)
            painter.drawText(unit_rect, Qt.AlignLeft | Qt.AlignVCenter, info_str_3)
            
            total_records = len(self.rows)
            current_page = page_idx + 1
            info_str_5 = f"总计:{total_records}条  {current_page}/{total_pages}"
            right_edge = int(margin_x + content_width)
            reserved_total_w = s(140)
            total_x = right_edge - reserved_total_w
            month_x = margin_x + w_no + w_task + w_unit
            month_rect = QRectF(month_x, info_y, w_month, used_info_h)
            painter.drawText(month_rect, Qt.AlignLeft | Qt.AlignVCenter, info_str_4)
            total_rect = QRectF(total_x, info_y, reserved_total_w, used_info_h)
            painter.drawText(total_rect, Qt.AlignRight | Qt.AlignVCenter, info_str_5)
            y += used_info_h + s(10)
            
            # 3. Table Header
            painter.setFont(font_table_header)
            pen = QPen(Qt.black, 4) 
            painter.setPen(pen)
            
            x = margin_x
            for i, col_name in enumerate(self.columns):
                w = col_widths[i]
                rect = QRectF(x, y, w, header_height)
                painter.drawRect(rect)
                display_name = col_name
                if "询价" in col_name:
                    display_name = "询价"
                painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, display_name)
                x += w
            y += header_height
            
            # Use fixed capacity per page
            max_slots_dynamic = self.rows_per_page

            # 4. Rows
            painter.setFont(font_cell)
            pen_grid = QPen(Qt.black, 2)
            
            slots_used_on_page = 0
            for row_data, lines in page_rows_data:
                current_h = lines * row_height
                
                # Draw Group Header
                if isinstance(row_data, dict) and row_data.get("is_header"):
                    rect = QRectF(margin_x, y, content_width, current_h)
                    
                    # Fill Background
                    color_hex = row_data.get("color", "#F0F0F0")
                    painter.fillRect(rect, QColor(color_hex))
                    
                    # Draw Border
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawRect(rect)
                    
                    # Draw Text (Left Aligned with padding)
                    painter.setFont(font_table_header)
                    text = row_data.get("text", "")
                    # Padding left
                    text_rect = rect.adjusted(s(10), 0, 0, 0) 
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
                    
                    y += current_h
                    slots_used_on_page += lines
                    continue
                
                x = margin_x
                for col_idx, w in enumerate(col_widths):
                    rect = QRectF(x, y, w, current_h)
                    painter.setPen(pen_grid)
                    painter.drawRect(rect)
                    val = row_data[col_idx]
                    text = str(val) if val is not None else ""
                    option = QTextOption()
                    option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
                    if self.columns[col_idx] == "规格型号":
                        option.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        painter.drawText(rect.adjusted(s(6), 0, 0, 0), text, option)
                    else:
                        option.setAlignment(Qt.AlignCenter)
                        painter.drawText(rect, text, option)
                    x += w
                y += current_h
                slots_used_on_page += lines
                if slots_used_on_page >= max_slots_dynamic:
                    break
            
            # Fill remaining slots up to capacity
            remaining_slots = max_slots_dynamic - slots_used_on_page
            if remaining_slots > 0:
                for _ in range(remaining_slots):
                    x = margin_x
                    for w in col_widths:
                        rect = QRectF(x, y, w, row_height)
                        painter.setPen(pen_grid)
                        painter.drawRect(rect)
                        x += w
                    y += row_height

            # 5. Footer
            # Fixed bottom footer
            footer_top_y = height - margin_y - h_footer - s(self.config.get("footer_bottom_padding", 20))
            y = max(y + spacing_footer, footer_top_y)
            painter.setFont(font_footer)
            rect_left = QRectF(margin_x, y, content_width / 3, h_footer)
            painter.drawText(rect_left, Qt.AlignLeft | Qt.AlignTop, self.config["footer_1"])
            rect_center = QRectF(margin_x, y, content_width, h_footer) 
            painter.drawText(rect_center, Qt.AlignHCenter | Qt.AlignTop, self.config["footer_2"])
            rect_right = QRectF(margin_x + content_width * 2/3, y, content_width / 3, h_footer)
            painter.drawText(rect_right, Qt.AlignRight | Qt.AlignTop, self.config["footer_3"])

            
        painter.end()
