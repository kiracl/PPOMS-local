# PPOMS Web系统 - 快速开始 (Quick Start)

## 1. 准备环境 (Prerequisites)

请确保你的开发机器上已经安装了以下软件：

*   **Java**: JDK 17+ (推荐 Eclipse Adoptium)
*   **Node.js**: v18.16.0+ (推荐使用 nvm 管理)
*   **MySQL**: 8.0+
*   **Redis**: 7.0+
*   **Maven**: 3.8+
*   **IDE**: IntelliJ IDEA (后端) + VS Code (前端)
*   **Git**: 2.30+

## 2. 后端启动 (Backend)

1.  **克隆代码**:
    ```bash
    git clone https://gitlab.example.com/ppoms/backend.git
    cd backend
    ```

2.  **配置数据库**:
    *   在 MySQL 中创建一个名为 `ppoms_dev` 的空数据库。
    *   修改 `src/main/resources/application-dev.yml`:
        ```yaml
        spring:
          datasource:
            url: jdbc:mysql://localhost:3306/ppoms_dev?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
            username: root
            password: your_password
          redis:
            host: localhost
            port: 6379
        ```

3.  **运行迁移脚本**:
    *   使用 SQL 客户端（如 DBeaver）连接数据库。
    *   依次执行 `sql/init.sql` (建表) 和 `sql/data.sql` (初始数据)。

4.  **启动项目**:
    *   在 IDEA 中打开项目，等待 Maven 依赖下载完成。
    *   找到 `PpomsApplication.java`，右键 Run。
    *   看到 `Started PpomsApplication in ... seconds` 即为启动成功。
    *   访问 `http://localhost:8080/doc.html` 查看 Swagger 接口文档。

## 3. 前端启动 (Frontend)

1.  **克隆代码**:
    ```bash
    git clone https://gitlab.example.com/ppoms/frontend.git
    cd frontend
    ```

2.  **安装依赖**:
    ```bash
    npm install
    # 或者使用 pnpm (推荐)
    npm install -g pnpm
    pnpm install
    ```

3.  **启动开发服务器**:
    ```bash
    npm run dev
    ```

4.  **访问页面**:
    *   打开浏览器访问 `http://localhost:5173`。
    *   默认账号: `admin` / `123456`。

## 4. 常见问题 (FAQ)

### Q1: 启动后端报错 "Connection refused: connect"?
*   **A**: 检查 MySQL 和 Redis 服务是否已启动，且端口是否正确 (3306, 6379)。

### Q2: 前端登录提示 "Network Error"?
*   **A**: 检查后端是否启动成功 (8080端口)，以及前端 `vite.config.ts` 中的代理配置是否正确指向了后端地址。

### Q3: 验证码不显示?
*   **A**: 检查 Redis 连接是否正常，验证码通常存储在 Redis 中。
