# PPOMS Web系统 - 后端开发规范 (Spring Boot)

## 1. 技术栈
*   **语言**: Java 17
*   **框架**: Spring Boot 3.2+
*   **微服务**: Spring Cloud Alibaba (Nacos, Gateway, Sentinel) - 可选
*   **ORM**: MyBatis-Plus
*   **数据库**: MySQL 8.0
*   **缓存**: Redis
*   **工具**: Lombok, Hutool

## 2. 项目结构

```
src/
├── main/
│   ├── java/
│   │   ├── com.ppoms.
│   │   │   ├── admin/              # 系统管理模块
│   │   │   ├── auth/               # 认证模块
│   │   │   ├── purchase/           # 采购业务模块
│   │   │   ├── common/             # 通用模块
│   │   │   │   ├── annotation/     # 自定义注解
│   │   │   │   ├── config/         # 全局配置
│   │   │   │   ├── constant/       # 常量定义
│   │   │   │   ├── core/           # 核心类 (Result, Page)
│   │   │   │   ├── exception/      # 全局异常处理
│   │   │   │   ├── utils/          # 工具类
│   │   │   │   └── security/       # Spring Security 扩展
│   │   │   └── Application.java    # 启动类
│   ├── resources/
│   │   ├── mapper/                 # MyBatis XML 文件
│   │   ├── application.yml         # 主配置文件
│   │   └── application-dev.yml     # 开发环境配置
└── test/
```

## 3. 开发规范

### 3.1 实体类 (Entity)
*   **表名**: `sys_user` -> `SysUser`.
*   **继承**: 继承 `BaseEntity` (包含 `createTime`, `updateTime`, `createBy`, `updateBy`).
*   **主键**: `Long` 类型，使用 `@TableId(type = IdType.AUTO)`.
*   **逻辑删除**: 字段 `del_flag`，注解 `@TableLogic`.

### 3.2 响应结构 (Result)
*   统一使用 `R<T>` 类封装响应:
    *   `code`: 状态码 (200, 500, 401).
    *   `msg`: 提示信息.
    *   `data`: 业务数据 (T).

### 3.3 控制层 (Controller)
*   使用 `@RestController` 和 `@RequestMapping`.
*   参数校验使用 `@Validated`.
*   Swagger 注解: `@Tag(name = "模块名称")`, `@Operation(summary = "接口描述")`.

### 3.4 异常处理 (GlobalExceptionHandler)
*   统一捕获 `BusinessException` (自定义业务异常).
*   统一捕获 `MethodArgumentNotValidException` (参数校验失败).
*   统一捕获 `Exception` (未知系统错误).

## 4. 核心功能实现指南

### 4.1 认证与授权 (Security + JWT)
*   **登录**: `/auth/login` 接口验证用户名密码，成功生成 JWT Token.
*   **拦截**: `JwtAuthenticationTokenFilter` 拦截请求，解析 Header 中的 Token.
*   **用户上下文**: 解析成功后，将 `UserDetails` 设置到 `SecurityContextHolder`.
*   **权限校验**: 使用 `@PreAuthorize("@ss.hasPermi('system:user:add')")` 注解控制方法访问权限.

### 4.2 数据权限 (DataScope)
*   **实现**: 自定义注解 `@DataScope`.
*   **AOP**: 切面类 `DataScopeAspect` 在执行 SQL 前拼接权限过滤条件 (如 `dept_id IN (...)` 或 `user_id = ...`).

### 4.3 事务管理
*   **声明式事务**: 使用 `@Transactional(rollbackFor = Exception.class)`.
*   **多数据源**: 如需读写分离，使用 MyBatis-Plus 动态数据源.

### 4.4 定时任务 (Quartz/Spring Task)
*   **场景**: 每日自动检查合同到期、每月生成采购计划提醒.
*   **注解**: `@Scheduled(cron = "0 0 0 * * ?")`.
