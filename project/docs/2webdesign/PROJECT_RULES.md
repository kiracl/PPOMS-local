# PPOMS Web系统 - 项目开发与协作规则 (V1.0)

## 1. 代码管理规范 (Git Flow)

### 1.1 分支策略
*   **`main`**: 主分支，仅用于生产环境发布，永远保持稳定。禁止直接 Push，只能通过 PR (Pull Request) 合并。
*   **`develop`**: 开发分支，包含最新的功能代码，用于测试环境部署。
*   **`feature/xxx`**: 功能分支，从 `develop` 检出，开发完成后提 PR 合并回 `develop`。命名示例：`feature/login-page`, `feature/purchase-order-api`.
*   **`hotfix/xxx`**: 紧急修复分支，从 `main` 检出，修复后合并回 `main` 和 `develop`。
*   **`release/xxx`**: 发布分支，用于发版前的预发布测试。

### 1.2 提交信息规范 (Commit Message)
遵循 **Conventional Commits** 规范，格式：`<type>(<scope>): <subject>`

*   **Type**:
    *   `feat`: 新功能
    *   `fix`: 修复 Bug
    *   `docs`: 文档变更
    *   `style`: 代码格式调整（不影响逻辑）
    *   `refactor`: 代码重构（无新功能或 Bug 修复）
    *   `perf`: 性能优化
    *   `test`: 测试用例
    *   `chore`: 构建/工具链变动
*   **Example**:
    *   `feat(auth): add jwt token validation logic`
    *   `fix(order): resolve null pointer exception in order detail`

## 2. 接口开发规范 (API Design)

### 2.1 路径命名
*   使用 **RESTful** 风格，名词复数，小写，连字符分隔。
*   `GET /api/v1/users` (获取用户列表)
*   `POST /api/v1/users` (创建用户)
*   `GET /api/v1/users/{id}` (获取详情)
*   `PUT /api/v1/users/{id}` (全量更新)
*   `DELETE /api/v1/users/{id}` (删除)

### 2.2 参数与响应
*   **日期时间**: 统一使用 `yyyy-MM-dd HH:mm:ss` 字符串格式交互，或 ISO 8601。后端实体类建议使用 `LocalDateTime`。
*   **金额**: 统一使用 `BigDecimal`，前端接收为字符串或数字（注意精度丢失，建议字符串）。
*   **分页**:
    *   请求: `page` (页码, 从1开始), `size` (每页条数).
    *   响应: `{ total: 100, records: [...] }`.

### 2.3 异常处理
*   禁止在 Controller 层直接 `try-catch` 吞掉异常。
*   业务逻辑错误抛出自定义 `BusinessException(code, msg)`。
*   系统级异常由全局异常处理器统一捕获并记录日志。

## 3. 数据库开发规范

### 3.1 变更流程
*   **禁止手动修改生产库**。
*   所有表结构变更必须编写 SQL 脚本，存放在 `src/main/resources/db/migration` 目录下（如使用 Flyway）。
*   脚本命名: `V1.0.1__add_user_table.sql`.

### 3.2 SQL 规范
*   **禁止使用 `SELECT *`**，必须明确指定字段。
*   **禁止在循环中执行 SQL**，必须在 Service 层批量处理。
*   **软删除**: 业务数据一律使用 `deleted` 或 `status` 字段标记删除，不可物理删除。

## 4. 前端开发规范

### 4.1 组件化
*   通用组件（如上传、富文本、复杂选择器）必须封装到 `src/components`。
*   页面级组件拆分：如果一个 Vue 文件超过 500 行，必须拆分为子组件。

### 4.2 状态管理
*   **Pinia**: 仅存储全局状态（用户信息、权限、主题、字典缓存）。
*   **Local State**: 页面内部的数据交互（如表单数据、表格数据）直接在组件内使用 `ref/reactive`，不要滥用 Pinia。

### 4.3 防止重复提交
*   所有修改/提交类的按钮，在请求发起时必须置为 `loading` 状态，请求结束（无论成功失败）后恢复。

## 5. 测试与验收规范

### 5.1 后端测试
*   **单元测试**: 核心业务逻辑（如金额计算、库存扣减）必须编写 JUnit 测试用例，覆盖率要求 > 80%。
*   **接口测试**: 提交代码前必须使用 Postman 或 Swagger 自测通过。

### 5.2 前端测试
*   自测流程：功能正常 -> 样式无错乱 -> 控制台无报错 -> 移动端/缩放适配（可选）。

### 5.3 Code Review
*   所有 PR 必须经过至少一名其他成员 Review 后方可合并。
*   关注点：代码规范、潜在 Bug、SQL 性能、安全漏洞。

## 7. 版本与发布规范 (Versioning)

### 7.1 版本号命名 (SemVer)
遵循 **Semantic Versioning 2.0.0**: `Major.Minor.Patch`

*   **Major (主版本)**: 架构升级或不兼容的 API 变更 (e.g. 1.0.0 -> 2.0.0)。
*   **Minor (次版本)**: 新增向下兼容的功能 (e.g. 1.1.0 -> 1.2.0)。
*   **Patch (修订号)**: 向下兼容的 Bug 修复 (e.g. 1.1.1 -> 1.1.2)。

### 7.2 更新日志 (CHANGELOG.md)
每次发布新版本前，必须在根目录更新 `CHANGELOG.md`，格式如下：

```markdown
## [1.1.0] - 2026-03-15

### Added
- 新增“供应商黑名单”功能。
- 采购订单支持导出 PDF。

### Fixed
- 修复发票金额计算精度丢失问题。
- 解决登录页在 IE11 下样式错乱。

### Changed
- 优化了菜单加载速度，改为后端懒加载。
```

### 7.3 发布流程
1.  **Freeze**: 冻结 `develop` 分支，禁止提交新功能。
2.  **Test**: 在测试环境进行全量回归测试。
3.  **Tag**: 在 Git 打上版本标签 (e.g. `v1.1.0`)。
4.  **Merge**: 将 `develop` 合并至 `main`。
5.  **Deploy**: 触发 CI/CD 流水线发布至生产环境。
