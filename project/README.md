# 采购计划管理系统 (PPOMS)

## 简介
PPOMS (Procurement Production Operation Management System) 是一套专为生产管理部设计的轻量级桌面应用程序。旨在解决传统 Excel 管理模式下数据分散、版本混乱、统计滞后等痛点，实现从“月度预算”到“采购执行”的全流程闭环管理。

## 技术栈
- Python 3.10+
- PySide6 (UI)
- SQLite (Database)
- PyInstaller (Packaging)

## 快速开始

### GUI 界面启动
1. 确保安装了虚拟环境并激活。
2. 安装依赖：`pip install -r requirements.txt`
3. 运行程序：`python main.py`

### CLI 命令行工具 (V2.0)
系统提供了一个强大的命令行接口 (`cli.py`)，允许在无界面的情况下自动化地创建主单和添加明细，并且**完全继承了 GUI 的智能推荐与状态流转逻辑**。

#### 1. 创建采购主单 (Create Master Order)
生成一个新的采购任务（自动生成 `CG-xxxx` 编号）。

**命令格式：**
```bash
python cli.py order create --month <计划月份> --category <类别代码> --unit <需求单位> --name <任务名称>
```

**示例：**
```bash
python cli.py order create --month 2603 --category MPJ --unit "信息部" --name "3月服务器采购"
# 预期输出: SUCCESS: Order created. Number: CG-2603MPJ0001
```

#### 2. 添加采购明细 (Add Detail Item)
向指定的主单中添加一条物资明细。系统会自动分配递增的序号（如 `2603MPJ-1`），并触发**智能推荐**（自动填充采购方式、采购途径、发放人）。

**命令格式：**
```bash
python cli.py order add-item --order <主单编号> --name <采购标的> --spec <规格型号> --qty <采购数量> --unit <单位> [--price <单价>] [--remark <备注>]
```

**示例：**
```bash
python cli.py order add-item --order CG-2603MPJ0001 --name "笔记本电脑" --spec "ThinkPad T14" --qty 5 --unit "台" --price 8500
# 预期输出: 
# SUCCESS: Item added. Sequence: 2603MPJ-1
#   Details: Name=笔记本电脑, Method=框架协议, Channel=能建商城, Purchaser=李胜
```

> **注意：** `--price` 和 `--remark` 为选填项。

## 项目文档
详细的产品需求、数据库设计和架构文档请参考 `docs/` 目录：
- [产品需求文档 (PRD)](docs/PPOMS_PRD_V2.4.0.md)
- [Web端设计文档](docs/2webdesign/)