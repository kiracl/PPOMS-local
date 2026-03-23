# 🧩 Trae 项目级规则 - Web 版开发 (Vue 3 + Spring Boot) & Vibing Coding 约束

## 📌 核心哲学 (Vibing Coding Workflow)
为了保证代码质量与系统设计的一致性，必须严格遵循以下 AI 协作约束：

1. **先查文档后写代码 (Docs First)**：
   - 任何开发前，**必须**查阅 `project/docs/2webdesign/` 目录下的 `ARCHITECTURE.md`、`BUSINESS_PROCESS.md`、`DATABASE_SCHEMA.md` 和 `API_DEFINITION.md`。
   - 遇到业务疑问，优先从文档中寻找答案；文档未定义时再向用户确认，并同步更新文档。

2. **小步快跑，增量迭代 (Small & Iterative Commits)**：
   - 每个独立的功能点或组件开发完成后，**必须**进行本地验证（如启动服务、查看 UI、测试 API）。
   - 验证通过后，立即使用 `git add` 和 `git commit` 进行小颗粒度提交，确保代码版本可追溯，降低回退成本。

3. **消除幻觉 (Zero Hallucination)**：
   - 修改已有文件前，**必须**使用工具（`read` / `grep`）读取最新代码。
   - 绝不臆造类名、变量名或 API 路径，严格遵循已有的代码结构和接口定义。

4. **状态与进度同步 (Keep Roadmap Updated)**：
   - 复杂任务开始前，**必须**在回复中生成明确的 Todo List 规划步骤。
   - 阶段性完成时，主动更新 `project/docs/2webdesign/ROADMAP.md` 的进度状态。

---

## 🧪 技术栈与环境约定
- **前端**：Vue 3 + Vite + TypeScript + Element Plus (或 TailwindCSS)
- **后端**：Spring Boot 3.x + Java 17+ + Maven + MyBatis-Plus
- **数据库**：MySQL / PostgreSQL
- **架构**：模块化单体架构 (Modular Monolith)

## 📁 目录结构约束 (前后端分离)
- `project/frontend/`：前端 Vue 3 项目目录。
- `project/backend/`：后端 Spring Boot 多模块项目目录。
  - `ppoms-common/` (通用工具、异常处理、基础配置)
  - `ppoms-modules/` (业务模块，如采购、权限、CLI等)
  - `ppoms-bootstrap/` (启动类、统一打包)

---

## 🔧 一键任务模板 (Web 版 tasks.json 参考)
在初始化脚手架后，应确保提供以下快捷指令支持：
- **前端启动**：`cd project/frontend && npm install && npm run dev`
- **前端打包**：`cd project/frontend && npm run build`
- **后端编译**：`cd project/backend && mvn clean install`
- **后端启动**：`cd project/backend/ppoms-bootstrap && mvn spring-boot:run`
- **全栈检查**：`cd project/frontend && npm run lint && cd ../backend && mvn checkstyle:check`

---

## ✅ 代码质量与验收清单 (Checklist)
每次功能交付前，需自行对照以下清单：
- [ ] **前端检查**：TypeScript 类型定义完整，无 `any` 泛滥；组件拆分合理。
- [ ] **样式检查**：UI 还原度检查，**打印样式**（`@media print`）是否与旧版保持一致，表格列宽记忆功能是否迁移。
- [ ] **后端检查**：RESTful API 路径规范，入参出参校验完整（DTO）。
- [ ] **权限隔离**：权限检查（如采购经理可见全部，采购员仅见已分配；部门隔离是否生效）。
- [ ] **数据库对齐**：SQL 脚本或实体类字段与 `DATABASE_SCHEMA.md` 一致（如 `audit_status`, `execute_status` 等）。
- [ ] **部署对齐**：Ubuntu 部署脚本 `deploy.sh` 是否与最新的打包路径匹配。
