import sys
import markdown
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QLabel, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

# Define the manual structure and content
MANUAL_CONTENT = {
    "系统简介": """
# 采购计划管理系统 (PPOMS) 操作手册

欢迎使用采购计划管理系统！本系统专为生产管理部设计，旨在实现从“月度预算”到“采购执行”的全流程闭环管理。

## 核心模块概览
- **工作台**: 核心数据与指标的快速概览。
- **月度计划**: 宏观预算的制定与整体执行进度的监控。
- **采购计划**: 采购任务主单与明细的具体录入（支持智能推荐与逻辑联动）。
- **计划发放**: 将录入好的计划分发给具体的采购执行人。
- **计划进度**: 追踪已发放计划的执行状态，支持批量更新。
- **合同台账**: 采购合同的录入与执行订单的生成。
- **入库管理**: 采购物资的到货登记与合同状态反向联动。
- **AI 助手**: 基于大模型的智能问答辅助。

点击左侧目录树查看各个模块的具体操作说明。
""",

    "工作台": """
# 工作台 (Dashboard)

工作台是系统的首页，为您提供关键数据的全局视角。

### 功能说明
1. **指标卡片**: 展示“本月计划总数”、“总采购预算（万元）”、“待处理计划数”等核心指标。
2. **分类统计**: 按“民品”、“机加件”、“半成品”分类展示数量和金额分布。
3. **快捷跳转**: 双击某些统计卡片（如“待处理计划”）可直接跳转到对应的操作模块（如“计划发放”）。
4. **月份筛选**: 顶部提供下拉框，可切换查看不同月份的统计数据。
""",

    "月度计划": """
# 月度计划管理

用于管理每月的宏观采购预算，并实时监控其实际采购进度。

### 核心操作
- **导入计划**: 点击“导入计划”按钮，选择符合模板格式的 Excel 文件进行批量导入。
- **自动匹配执行**: 系统会自动根据 `计划月份` + `标的名称` + `规格型号` 去“采购计划”明细中匹配已录入的实际数量和金额。
- **进度查看**: 列表中有“执行进度”进度条，直观展示该预算项完成了多少（100% 会显示为绿色）。
""",

    "采购计划 (录入与管理)": """
# 采购计划 (主单与明细管理)

这是系统的核心业务模块，用于创建具体的采购申请单据。

### 1. 创建主单
1. 在左侧面板选择“计划月份”、“标的类别”、“需求单位”，填写“采购任务名称”。
2. 点击**“生成”**按钮，系统会自动生成 `CG-xxxx` 格式的主单编号（不同类别流水号独立）。

### 2. 录入明细
双击右侧列表中的主单，进入明细界面。
- **添加行**: 手动添加一行空数据，系统会自动分配如 `2603MPJ-1` 的递增序号。
- **数据导入**: 点击“数据导入”，使用标准模板批量导入明细。
- **智能推荐**: 输入“采购标的”后，系统会查询历史知识库，**自动为您填充**“采购方式”、“采购途径”和“计划发放人”。
- **逻辑联动**: 
  - 选择“询比采购” -> 自动填“线下采购”
  - 选择“框架协议” -> 自动填“能建商城”

### 3. 保存与校验
- 点击**“保存”**将数据写入数据库。
- 点击顶部工具栏的**“工具”->“校验明细序号”**，可检查当前单据的流水号是否连续、有无重复。
""",

    "计划发放": """
# 计划发放

对已经录入好但尚未指派采购员的计划进行统一分发。

### 操作步骤
1. 左侧列表展示所有包含“未发放”明细的主单。
2. 选中一个主单，右侧会按**采购员维度**分组展示待发放的明细。
3. 确认无误后，点击底部的**“确认发放”**按钮。
4. 系统会将这些明细标记为“已发放”，它们随后会出现在采购员的待办列表中（并在“计划进度”模块中可追踪）。
""",

    "计划进度 (状态追踪)": """
# 计划进度

用于宏观追踪全公司已发放计划的执行情况，并支持快速批量更新状态。

### 1. 进度看板 (图表)
- 饼图展示当前各项状态（如“询价中”、“已完成”）的占比分布。
- 柱状图对比各个采购员的总任务量与已完成量，方便效能评估。

### 2. 状态更新列表 (批量操作)
- **层级展示**: 采用“主单 -> 明细”的两级树状结构。
- **级联勾选**: 勾选主单，即可全选其下属的所有明细；勾选部分明细，主单呈“半选”状态。
- **批量更新**: 勾选需要推进状态的明细，在顶部下拉框选择“目标状态”（如：`已下单待收货`），点击“批量更新状态”，即可一键同步至数据库。
""",

    "合同与入库": """
# 合同与入库管理

实现从采购合同签订到物资入库的闭环状态流转。

### 1. 合同台账
- 记录合同基础信息及包含的物资明细与总数。
- **开具执行订单**: 基于合同，生成具体的执行单。系统会严格校验，防止超额执行。

### 2. 入库管理
- 物资到货后，在此模块登记入库。
- 选择关联的“执行订单”，录入本次入库数量。
- **状态反向联动**:
  - 录入部分数量 -> 订单状态自动变更为**“部分入库”（蓝色）**。
  - 录入全部数量 -> 订单状态自动变更为**“已入库”（绿色）**，且该订单将不可再被选中进行入库。
""",

    "CLI 命令行工具 (V2.0)": """
# CLI 命令行工具 (CLI 2.0)

系统提供了强大的无界面命令行接口 (`cli.py`)，非常适合进行自动化脚本集成或高级数据录入。CLI **完全继承了 GUI 端的智能推荐与联动逻辑**。

请在系统的虚拟环境 (venv) 下执行以下命令：

### 1. 创建主单
```bash
python cli.py order create --month <计划月份> --category <类别代码> --unit <需求单位> --name <任务名称>
```
**示例：**
```bash
python cli.py order create --month 2603 --category MPJ --unit "生产管理部" --name "3月服务器采购"
# 预期输出: SUCCESS: Order created. Number: CG-2603MPJ0001
```

### 2. 添加明细 (触发智能推荐)
系统会自动分配递增序号（如 `2603MPJ-1`），并根据“名称”自动填充采购员和途径。
```bash
python cli.py order add-item --order <主单编号> --name <采购标的> --spec <规格型号> --qty <采购数量> --unit <单位> [--price <单价>] [--remark <备注>]
```
**示例：**
```bash
python cli.py order add-item --order CG-2603MPJ0001 --name "笔记本电脑" --spec "T14" --qty 5 --unit "台"
```

### 3. 批量更新进度状态
```bash
python cli.py order update-status --status "<目标状态>" --details <明细编号1> <明细编号2> ...
```
**可选状态**：未启动, 询价中, 定点审批中, 合同流转中, 已下单待收货, 部分到货, 已完成
**示例：**
```bash
python cli.py order update-status --status "已完成" --details 2603MPJ-1 2603MPJ-2
```
"""
}

class UserManualWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        header_frame.setMaximumHeight(50)  # Restrict header height to avoid large whitespace
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 0, 15, 0) # Reduce vertical margins in header
        title = QLabel("📖 系统操作手册")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        self.layout.addWidget(header_frame)
        
        # Splitter for Tree and Content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Navigation Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                border-right: 1px solid #dee2e6;
                background-color: #ffffff;
                font-size: 14px;
            }
            QTreeWidget::item { padding: 8px; }
            QTreeWidget::item:selected { background-color: #e9ecef; color: #0d6efd; font-weight: bold; }
        """)
        
        # Right: Markdown Browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self.on_anchor_clicked)
        self.browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: #ffffff;
                padding: 10px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
        """)
        
        splitter.addWidget(self.tree)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)
        
        self.layout.addWidget(splitter)
        
        self._populate_tree()
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        # Select first item by default
        if self.tree.topLevelItemCount() > 0:
            first_item = self.tree.topLevelItem(0)
            self.tree.setCurrentItem(first_item)
            self.on_item_clicked(first_item, 0)

    def _populate_tree(self):
        for title in MANUAL_CONTENT.keys():
            item = QTreeWidgetItem([title])
            self.tree.addTopLevelItem(item)
            
    def on_item_clicked(self, item, column):
        title = item.text(0)
        content = MANUAL_CONTENT.get(title, "")
        
        # Convert Markdown to HTML
        html_content = markdown.markdown(
            content, 
            extensions=['fenced_code', 'tables']
        )
        
        # Inject CSS for better markdown rendering
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{ 
                font-family: 'Microsoft YaHei', sans-serif; 
                color: #333; 
                line-height: 1.5; 
                font-size: 14px; 
                margin: 0; 
                padding: 0; 
            }}
            h1 {{ 
                color: #2c3e50; 
                border-bottom: 2px solid #eee; 
                padding-bottom: 5px; 
                font-size: 22px; 
                margin-top: 0; 
            }}
            h2 {{ color: #34495e; margin-top: 15px; font-size: 18px; }}
            h3 {{ color: #0d6efd; font-size: 15px; margin-top: 10px; }}
            p {{ margin-top: 5px; margin-bottom: 10px; }}
            code {{ background-color: #f1f3f5; padding: 2px 5px; border-radius: 4px; font-family: Consolas, monospace; color: #d63384; }}
            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 6px; overflow-x: auto; border: 1px solid #e9ecef; margin-top: 5px; margin-bottom: 10px; }}
            pre code {{ background-color: transparent; color: #212529; padding: 0; }}
            ul {{ padding-left: 20px; margin-top: 5px; margin-bottom: 10px; }}
            li {{ margin-bottom: 3px; }}
            a {{ color: #0d6efd; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        self.browser.setHtml(styled_html)

    def on_anchor_clicked(self, url: QUrl):
        # Handle internal or external links if added in the future
        QDesktopServices.openUrl(url)