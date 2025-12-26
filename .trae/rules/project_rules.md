<!-- 保存为：.trae/project-rules.md -->
<!-- Trae 会自动识别项目级规则，无需手动导入 -->

# 🧩 Trae 项目级规则 - Python 桌面开发（PySide6 + SQLite）
## 📌 触发词（任意输入框可用）
`pygui` / `桌面` / `ui` / `打包`
---

## 🧪 环境约定
- Python 3.10+（Trae 自带 pyenv）
- 虚拟环境：`venv`
- 依赖文件：`requirements.txt`
- 数据库：SQLite（绿色单文件）
- 打包：PyInstaller 单文件 exe
---

## 📁 项目骨架（固定结构）
```
project/
├─ .trae/                   # Trae 配置（勿删）
├─ venv/                    # 虚拟环境（gitignore）
├─ resources/               # 图标/qrc/样式
├─ ui/                      # QtDesigner .ui 文件
├─ generated/               # pyside6-uic 生成代码
├─ database.py              # SQLite 封装
├─ models.py                # 数据模型
├─ main.py                  # 程序入口
├─ requirements.txt
└─ README.md
```

---

## 🔧 一键任务模板（复制到 .trae/tasks.json）

```json
[
  {
    "label": "① 创建虚拟环境",
    "type": "shell",
    "command": "python -m venv venv && source venv/bin/activate && pip install -U pip",
    "group": "build",
    "presentation": { "reveal": "always" }
  },
  {
    "label": "② 安装依赖",
    "type": "shell",
    "command": "source venv/bin/activate && pip install -r requirements.txt",
    "group": "build",
    "presentation": { "reveal": "always" }
  },
  {
    "label": "③ 运行程序",
    "type": "shell",
    "command": "source venv/bin/activate && python main.py",
    "group": "build",
    "presentation": { "reveal": "always" }
  },
  {
    "label": "④ 生成 UI 代码",
    "type": "shell",
    "command": "source venv/bin/activate && pyside6-uic ui/*.ui -o generated/",
    "group": "build",
    "presentation": { "reveal": "always" }
  },
  {
    "label": "⑤ 打包 exe",
    "type": "shell",
    "command": "source venv/bin/activate && pyinstaller --onefile --noconsole --add-data 'purchase.db:.' main.py",
    "group": "build",
    "presentation": { "reveal": "always" }
  },
  {
    "label": "⑥ 初始化数据库",
    "type": "shell",
    "command": "source venv/bin/activate && python -c \"import database; database.init_db()\"",
    "group": "build",
    "presentation": { "reveal": "always" }
  }
]
```

---

## 🎯 快速开始（复制到终端即可）

```bash
# 1. 创建项目骨架
mkdir -p project/{ui,generated,resources} && cd project

# 2. 一键安装环境
trae run 任务：① 创建虚拟环境
trae run 任务：② 安装依赖

# 3. 拖完界面后生成代码
trae run 任务：④ 生成 UI 代码

# 4. 运行看效果
trae run 任务：③ 运行程序

# 5. 打包分发
trae run 任务：⑥ 初始化数据库
trae run 任务：⑤ 打包 exe
```

---

## 🧼 代码质量模板（触发词：`lint`）
```bash
source venv/bin/activate && pip install black flake8
black . && flake8 --max-line-length=88 .
```

---

## 🛠️ 常用命令速查（触发词：`cmd`）
| 目的 | 命令 |
|---|---|
| 新建 .ui | `pyside6-designer ui/main.ui` |
| 生成 Python | `pyside6-uic ui/main.ui -o generated/ui_main.py` |
| 资源编译 | `pyside6-rcc resources.qrc -o generated/resources_rc.py` |
| 查看依赖 | `pip freeze > requirements.txt` |

---

## 📦 打包参数（触发词：`spec`）
```bash
pyinstaller main.spec \
  --onefile \
  --noconsole \
  --add-data "purchase.db:." \
  --add-data "resources/:resources/" \
  --name PurchaseGUI
```

---

## ✅ 验收清单（触发词：`check`）
- [ ] 虚拟环境已创建
- [ ] requirements.txt 最新
- [ ] 数据库初始化成功
- [ ] UI 代码已生成且无红线
- [ ] 程序能运行
- [ ] exe 单文件生成成功
- [ ] 不跳号验证通过
