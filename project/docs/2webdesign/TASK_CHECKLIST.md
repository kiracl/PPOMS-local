# PPOMS Web系统 - 开发任务清单 (Task Checklist)

本清单用于追踪 "Solo Mode" 开发进度。每完成一项，请打钩 `[x]`。

## 🟢 Phase 1: 基础设施搭建 (Infrastructure)

### 1.1 后端初始化 (Spring Boot)
- [ ] **项目创建**: 使用 Spring Initializr 创建项目 (Java 17, Spring Boot 3.x).
- [ ] **依赖配置**: 修改 `pom.xml`，添加 MyBatis-Plus, MySQL, Druid, Hutool, Lombok.
- [ ] **多环境配置**: 创建 `application.yml`, `application-dev.yml`, `application-prod.yml`.
- [ ] **统一响应**: 创建 `R<T>` (Result) 类和 `ErrorCode` 枚举.
- [ ] **全局异常**: 实现 `GlobalExceptionHandler` 处理业务异常.
- [ ] **Swagger/Knife4j**: 集成 Knife4j 用于 API 文档生成.

### 1.2 数据库与持久层
- [ ] **数据库脚本**: 执行 `DATABASE_SCHEMA.md` 中的 SQL 建表语句.
- [ ] **代码生成器**: 配置 MyBatis-Plus Generator (可选) 或手动创建 BaseEntity.
- [ ] **实体类**: 创建 `SysUser`, `SysRole`, `SysMenu` 等基础实体.
- [ ] **Mapper**: 创建对应的 Mapper 接口.

### 1.3 认证授权 (Security)
- [ ] **Spring Security**: 引入依赖并创建 `SecurityConfig`.
- [ ] **JWT 工具类**: 实现 `JwtUtils` (生成/解析 Token).
- [ ] **过滤器**: 实现 `JwtAuthenticationTokenFilter`.
- [ ] **登录接口**: 实现 `AuthController.login()` 和 `logout()`.
- [ ] **权限注解**: 开启 `@EnableMethodSecurity`，测试 `@PreAuthorize`.

### 1.4 前端初始化 (Vue 3)
- [ ] **脚手架**: 使用 `npm create vite@latest` 创建项目 (Vue3 + TS).
- [ ] **基础库**: 安装 `element-plus`, `axios`, `pinia`, `vue-router`, `sass`.
- [ ] **目录结构**: 按照 `FRONTEND_GUIDE.md` 创建 `api`, `store`, `views`, `components` 目录.
- [ ] **Axios 封装**: 创建 `utils/request.ts`，配置拦截器 (Token 注入, 401 处理).
- [ ] **环境配置**: 创建 `.env.development` 和 `.env.production`.

### 1.5 登录与主页
- [ ] **登录页**: 开发 `views/login/index.vue`，实现表单验证与 API 调用.
- [ ] **Layout**: 开发 `layout/index.vue` (Sidebar, Navbar, AppMain).
- [ ] **路由守卫**: 实现 `permission.ts`，处理动态路由与 Token 校验.

## 🔵 Phase 2: 系统管理模块 (System)

### 2.1 用户管理
- [ ] **后端 API**: 实现 `SysUserController` (CRUD, 分页, 重置密码).
- [ ] **前端页面**: 开发 `views/system/user/index.vue` (表格, 搜索, 弹窗表单).
- [ ] **联调**: 验证增删改查功能.

### 2.2 角色与菜单
- [ ] **后端 API**: 实现 `SysRoleController` 和 `SysMenuController`.
- [ ] **前端页面**: 开发角色管理与菜单管理页面.
- [ ] **权限分配**: 实现角色-菜单关联接口与前端树形选择器.

### 2.3 字典管理
- [ ] **后端 API**: 实现 `SysDictController` (字典类型与字典数据).
- [ ] **前端组件**: 封装 `<DictSelect />` 组件，自动加载字典数据.
- [ ] **页面**: 开发字典管理页面.

## 🟠 Phase 3: 采购业务核心 (Purchase)

### 3.1 供应商管理
- [ ] **表结构**: 确认 `base_suppliers` 表存在.
- [ ] **API**: 实现供应商 CRUD.
- [ ] **页面**: 供应商列表与详情页.

### 3.2 月度计划
- [ ] **表结构**: 确认 `purchase_plans` 和 `purchase_plan_items`.
- [ ] **API**: 实现计划的主子表保存逻辑 (`@Transactional`).
- [ ] **页面**: 计划列表页 (状态徽章显示).
- [ ] **详情/编辑页**: 复杂的动态表格 (Dynamic Table) 实现，支持行编辑.

### 3.3 采购订单
- [ ] **API**: 实现订单生成逻辑 (从计划生成或手工创建).
- [ ] **打印**: 实现订单打印页面 (遵循独立组件规则).
- [ ] **导出**: 集成 EasyExcel 实现订单导出.

## 🟣 Phase 4: 供应链与财务 (Supply & Finance)

### 4.1 入库管理
- [ ] **API**: 实现入库单逻辑 (关联订单, 更新执行状态).
- [ ] **页面**: 入库单录入页面.

### 4.2 发票与对账
- [ ] **API**: 实现发票录入与对账单生成.
- [ ] **页面**: 对账单确认页面.

## 🔴 Phase 5: AI 增强 (Smart Features)

### 5.1 Text-to-SQL 服务化
- [ ] **集成**: 将 Python 版的 Text-to-SQL 逻辑迁移或封装为 API.
- [ ] **API**: `POST /api/ai/chat`.
- [ ] **前端**: 开发悬浮式 AI 助手组件.

### 5.2 知识库
- [ ] **API**: 实现知识库检索接口 (RAG).
- [ ] **前端**: 知识库问答界面.
