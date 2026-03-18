# PPOMS Web系统 - 登录与权限设计 (JWT + RBAC)

## 1. 认证流程 (Authentication)

### 1.1 登录 (POST /api/auth/login)
1.  **前端**: 提交 `{ username, password, captcha }`.
2.  **后端**:
    *   校验验证码 (Redis).
    *   查询数据库 `sys_user`，比对密码 (BCrypt).
    *   生成 JWT Token (包含 `userId`, `username`, `roles`, `permissions`, `expireTime`).
    *   存入 Redis: `login_tokens:<userId>` -> Token (用于踢人下线或单点登录).
    *   返回 `{ token: "Bearer eyJhbGciOi..." }`.

### 1.2 Token 校验 (JwtAuthenticationTokenFilter)
1.  **前端**: 请求头 `Authorization: Bearer <token>`.
2.  **后端**:
    *   解析 Token，校验签名与过期时间.
    *   从 Redis 获取用户信息 (UserDetail).
    *   将 Authentication 对象存入 SecurityContext.
    *   放行请求.

### 1.3 刷新 Token (POST /api/auth/refresh)
*   **场景**: Token 过期前自动刷新.
*   **前端**: 拦截器检测 Token 即将过期，静默调用刷新接口.
*   **后端**: 校验旧 Token 有效性，生成新 Token 返回.

## 2. 授权流程 (Authorization - RBAC)

### 2.1 角色与权限模型
*   **用户 (User)**: 多对多关联角色.
*   **角色 (Role)**: 多对多关联菜单/权限 (`sys_menu`).
*   **菜单 (Menu)**:
    *   **目录 (M)**: 一级菜单 (如“采购管理”).
    *   **菜单 (C)**: 具体页面 (如“采购订单”).
    *   **按钮 (F)**: 页面操作 (如“新增”、“删除”、“导出”).

### 2.2 前端权限控制
1.  **动态路由**:
    *   登录成功后，调用 `/api/system/menu/getRouters`.
    *   后端根据用户角色查询可见菜单树，返回路由配置 JSON.
    *   前端使用 `router.addRoute` 动态加载路由.
2.  **按钮级权限**:
    *   自定义指令 `v-hasPermi="['system:user:add']"`.
    *   判断当前用户权限集合 (`store.permissions`) 是否包含该标识.

### 2.3 后端权限控制 (Spring Security)
1.  **URL 拦截**: 配置 `SecurityFilterChain`，放行白名单 (如 `/login`, `/captchaImage`)，其他请求需认证.
2.  **注解拦截**:
    *   `@PreAuthorize("@ss.hasPermi('system:user:list')")`: 方法级权限控制.
    *   `@PreAuthorize("@ss.hasRole('admin')")`: 角色级控制.

## 3. 数据权限设计 (Data Scope)

### 3.1 权限类型
1.  **全部数据权限**: 查看所有数据 (admin).
2.  **本部门及以下数据权限**: 查看本部门及子部门数据 (dept_leader).
3.  **本部门数据权限**: 仅查看本部门数据 (dept_member).
4.  **仅本人数据权限**: 只能查看自己创建的数据 (common_user).
5.  **自定义数据权限**: 指定特定部门.

### 3.2 实现机制 (MyBatis拦截器/AOP)
1.  在 Service 方法上添加注解 `@DataScope(deptAlias = "d", userAlias = "u")`.
2.  AOP 切面解析注解，获取当前用户的数据权限类型.
3.  动态拼接 SQL 过滤条件:
    *   类型 1: 不拼接.
    *   类型 2: `AND d.id IN (SELECT id FROM sys_dept WHERE id = ? OR find_in_set(?, ancestors))`
    *   类型 3: `AND d.id = ?`
    *   类型 4: `AND u.id = ?`
4.  将 SQL 注入到 MyBatis 的 `BaseEntity` 参数中 (`params.dataScope`).

## 4. 部门设计 (sys_dept)
*   **树形结构**: 使用 `parent_id` 和 `ancestors` (祖级列表，如 `0,100,101`) 字段，方便快速查询子部门.
*   **层级**: 公司 -> 部门 -> 小组.
