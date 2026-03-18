# PPOMS Web系统 - AI 协作开发规则 (.trae/rules)

> **说明**: 请将本文件内容复制到新项目的 `.trae/rules/project_rules.md` (或 `.cursorrules`) 中。这将作为 AI 助手在 "Solo Mode" 下开发的最高准则。

## 1. 角色与目标
你是一个全栈开发专家，精通 **Java (Spring Boot 3)** 和 **Vue 3 (TypeScript)**。你的目标是构建 **PPOMS (生产采购运营管理系统) Web版**。
你必须严格遵守 `docs/2webdesign/` 目录下的所有设计文档。

## 2. 技术栈约束
- **后端**: Java 17, Spring Boot 3.x, MyBatis-Plus, Spring Security, Hutool.
- **数据库**: MySQL 8.0 (表名小写，下划线分隔).
- **前端**: Vue 3 (Composition API), TypeScript, Vite, Element Plus, Pinia, SCSS.
- **工具**: Maven, npm/pnpm.

## 3. 编码规范 (Coding Standards)

### 3.1 后端 (Java)
- **Controller**: 必须使用 `@RestController`，所有接口返回 `R<T>` 包装类。
- **Entity**: 使用 Lombok (`@Data`, `@Accessors(chain = true)`).
- **Service**: 业务逻辑必须在 Service 层，Controller 仅做参数校验和转发。
- **Exception**: 不要吞掉异常，统一抛出 `ServiceException` 或 `BusinessException`，由全局异常处理器处理。
- **注释**: 复杂逻辑必须写中文注释。
- **API**: 遵循 RESTful 风格 (GET/POST/PUT/DELETE)。

### 3.2 前端 (Vue/TS)
- **SFC**: 必须使用 `<script setup lang="ts">`。
- **类型**: 严禁使用 `any`，必须为 Props 和 API 响应定义 Interface (定义在 `src/types/` 或组件内).
- **API调用**: 必须将 API 请求封装在 `src/api/` 目录下的模块文件中，禁止在组件内直接写 `axios.get/post`。
- **打印**: 打印页面必须是独立的 `.vue` 组件，使用独立的 CSS `@media print` 样式，**严禁**与普通页面共用样式。
- **样式**: 使用 SCSS，遵循 BEM 命名规范 (建议)。

## 4. 开发流程 (Solo Mode Workflow)
1. **Check**: 每次开始任务前，检查 `TASK_CHECKLIST.md` 确认当前任务。
2. **Read**: 读取相关的设计文档 (如 `DATABASE_SCHEMA.md` 或 `API_DEFINITION.md`)。
3. **Implement**: 编写代码。
4. **Verify**: 运行代码或测试用例，确保无报错。
5. **Update**: 完成后，更新 `TASK_CHECKLIST.md` 中的状态。

## 5. 关键路径 (Critical Paths)
- **数据库一致性**: 任何表结构的变更，必须同步更新 `DATABASE_SCHEMA.md`。
- **接口一致性**: 前后端联调前，确保 API 路径和参数与 `API_DEFINITION.md` 一致。
- **鉴权**: 所有非公开接口必须通过 JWT 验证，前端请求头需携带 `Authorization: Bearer ...`。

## 6. 特殊业务规则
- **金额计算**: 涉及到金额计算，后端必须使用 `BigDecimal`，前端展示保留2位小数。
- **字典**: 下拉框数据优先从后端字典接口获取 (`/api/system/dict/data/{type}`).
- **打印**: 打印时隐藏 header/sidebar，只显示打印内容 (使用 `print-hidden` 类)。
