# 基于 Python (PySide6 + SQLite) 的本地桌面单机系统开发总结与规范

这份文档总结了我们在开发 `PPOMS-local`（基于 Python 的本地版系统）过程中沉淀的经验、项目规则和最佳实践。这份规范可以作为未来开发类似 **“轻量级、无网络依赖、即开即用”** 的 Python 桌面应用程序的脚手架和指导手册。

---

## 1. 核心技术栈选型与理由

对于“企业内网单机使用、对部署要求极低（最好是单文件 exe）、有丰富的表格与打印需求”的场景，这套技术栈经过了实战检验：

- **编程语言**: Python 3.10+ (生态丰富，开发效率高)
- **GUI 框架**: PySide6 (即 Qt for Python 6，性能极佳，原生支持复杂表格模型、打印和样式表)
- **数据库**: SQLite3 (无需安装，单文件存储，支持基础的 SQL 和并发读取)
- **打包工具**: PyInstaller (可将 Python 环境、依赖和资源文件打包成一个 `.exe`)
- **数据可视化**: Matplotlib / PySide6-Charts (用于生成统计图表)
- **文档渲染**: Markdown (用于内置的操作手册)

---

## 2. 标准项目目录结构 (Scaffolding)

为了保证代码的可维护性和模块化，强烈建议所有类似项目采用以下目录结构：

```text
project_name/
├── .trae/                      # IDE 配置文件 (如 tasks.json, rules)
├── venv/                       # Python 虚拟环境 (必须在 .gitignore 中忽略)
├── resources/                  # 静态资源目录
│   ├── icons/                  # 图标文件 (.png, .svg)
│   ├── styles/                 # 样式表 (.qss)
│   └── resources.qrc           # Qt 资源配置文件
├── ui/                         # Qt Designer 设计的界面文件 (.ui)
├── generated/                  # 自动生成的 Python 代码 (勿手动修改)
│   ├── ui_*.py                 # 由 pyside6-uic 生成
│   └── resources_rc.py         # 由 pyside6-rcc 生成
├── db/                         # 数据库相关
│   ├── database.py             # SQLite 连接池与基础封装
│   └── schema.sql              # 数据库初始化建表脚本
├── models/                     # 业务数据模型 (类似 MVC 中的 M)
├── controllers/                # 业务逻辑控制器 (解耦 UI 与数据)
├── views/                      # 业务视图逻辑 (继承 generated 中的 UI 类)
├── main.py                     # 应用程序启动入口
├── requirements.txt            # 项目依赖清单
└── build.spec                  # PyInstaller 打包配置文件
```

---

## 3. 核心开发规范与约束 (Vibing Coding Rules)

在 AI 辅助开发 (Vibing Coding) 过程中，应始终遵循以下原则：

### 3.1 界面与逻辑分离 (UI/Logic Decoupling)
- **严禁手写 UI 代码**：所有的界面布局、控件拖拽**必须**使用 Qt Designer 完成，保存为 `.ui` 文件。
- **自动生成**：使用 `pyside6-uic` 将 `.ui` 转换为 `.py` 文件，存放在 `generated/` 目录下。**永远不要手动修改 `generated/` 目录下的任何文件**。
- **继承实现**：在 `views/` 目录下创建子类，继承生成的 UI 类，并在子类中实现信号槽（事件）绑定和业务逻辑。

### 3.2 数据库操作规范 (SQLite Best Practices)
- **统一入口**：所有数据库访问必须通过 `database.py` 中封装好的函数或类（如使用 `sqlite3.connect` 并开启 `check_same_thread=False`）。
- **参数化查询**：**严禁使用字符串拼接 SQL**，必须使用参数化查询（`?` 占位符）以防止 SQL 注入并处理特殊字符。
- **连接管理**：确保每次操作后正确执行 `commit()` 和 `close()`，推荐使用 Python 的上下文管理器 (`with` 语句)。

### 3.3 用户体验细节规范 (UX Checkpoints)
- **表格列宽记忆**：系统中所有包含重要数据的表格 (`QTableWidget` 或 `QTableView`)，必须支持用户拖拽列宽后的自动记忆。将列宽配置序列化后存入 SQLite 的配置表中。
- **状态反馈**：耗时操作（如导出 Excel、生成复杂图表）必须有进度条或等待提示 (`QProgressDialog` 或改变鼠标指针状态)。
- **错误捕获**：全局捕获未处理的异常 (`sys.excepthook`)，并通过友好的 `QMessageBox` 提示用户，同时记录到本地 `error.log`，防止程序静默崩溃。

---

## 4. 自动化脚本与工作流 (Task Templates)

在开发过程中，建议将以下常用命令配置到 IDE 的任务运行器中（如 `.trae/tasks.json`）：

| 任务名称 | 命令 (Windows 环境) |
| :--- | :--- |
| **① 创建虚拟环境** | `python -m venv venv && .\venv\Scripts\activate && pip install -U pip` |
| **② 安装依赖** | `.\venv\Scripts\activate && pip install -r requirements.txt` |
| **③ 生成 UI 代码** | `.\venv\Scripts\activate && pyside6-uic ui\*.ui -o generated\` |
| **④ 编译资源文件** | `.\venv\Scripts\activate && pyside6-rcc resources\resources.qrc -o generated\resources_rc.py` |
| **⑤ 运行测试** | `.\venv\Scripts\activate && python main.py` |
| **⑥ 导出依赖** | `.\venv\Scripts\activate && pip freeze > requirements.txt` |

---

## 5. 打包与分发 (Deployment)

桌面应用最终交付给用户的形态通常是一个独立的 `.exe` 文件。

### 5.1 PyInstaller 打包参数
推荐使用 `.spec` 文件进行打包配置，以处理复杂的资源路径映射：

```bash
# 常用基础打包命令
pyinstaller main.py ^
  --onefile ^
  --noconsole ^
  --name "App_Name" ^
  --icon "resources/icons/app.ico" ^
  --add-data "schema.sql;." ^
  --add-data "resources;resources"
```

### 5.2 资源路径动态解析陷阱
打包为单文件后，程序运行时会被解压到系统的临时目录（`_MEIPASS`）。因此，代码中所有读取本地文件（如图标、配置文件）的相对路径都会失效。
**必须**使用以下辅助函数来动态获取资源绝对路径：

```python
import sys
import os

def resource_path(relative_path):
    """ 获取资源绝对路径，适用于开发环境和 PyInstaller 打包环境 """
    try:
        # PyInstaller 创建临时文件夹,将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 非打包环境下使用当前工作目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
```

---

## 6. 适用场景与局限性

**适用场景**：
- 财务、库管、生产车间等内网隔离环境。
- 只有 1-2 个人使用，无需复杂的多人并发写入和严格的数据权限隔离。
- 用户不懂如何安装环境，需要“下载即用”的傻瓜式体验。

**局限性（何时该考虑升级为 Web 版）**：
- 当团队需要多人异地协作，或者同一时间有超过 3 个人频繁写入数据时（SQLite 的文件锁机制会导致并发写入性能极差甚至锁死）。
- 当需要复杂的角色权限管理（RBAC）、多层级部门数据隔离时。
- 当系统需要与企业微信、钉钉等外部网络平台对接审批流时。
