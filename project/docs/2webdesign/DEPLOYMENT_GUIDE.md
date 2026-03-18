# PPOMS Web系统 - 部署运维指南 (V1.0)

## 1. 部署环境

*   **操作系统**: Ubuntu 22.04 LTS / CentOS 7.9
*   **依赖**: Docker, Docker Compose
*   **硬件要求**: 4核 CPU, 8G RAM (建议)

## 2. Docker Compose 配置 (docker-compose.yml)

```yaml
version: '3.8'

services:
  # 1. 数据库
  mysql:
    image: mysql:8.0
    container_name: ppoms-mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: your_secure_password
      MYSQL_DATABASE: ppoms_cloud
      TZ: Asia/Shanghai
    volumes:
      - ./data/mysql:/var/lib/mysql
      - ./init:/docker-entrypoint-initdb.d
    ports:
      - "3306:3306"

  # 2. 缓存
  redis:
    image: redis:7.0
    container_name: ppoms-redis
    restart: always
    command: redis-server --requirepass your_redis_password
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"

  # 3. 后端 (Spring Boot)
  backend:
    image: ppoms-backend:latest
    container_name: ppoms-backend
    restart: always
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/ppoms_cloud?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
      SPRING_DATASOURCE_PASSWORD: your_secure_password
      SPRING_REDIS_HOST: redis
      SPRING_REDIS_PASSWORD: your_redis_password
    depends_on:
      - mysql
      - redis
    ports:
      - "8080:8080"

  # 4. 前端 (Nginx)
  frontend:
    image: ppoms-frontend:latest
    container_name: ppoms-frontend
    restart: always
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
  redis_data:
```

## 3. Nginx 配置 (frontend/nginx.conf)

```nginx
server {
    listen       80;
    server_name  localhost;

    # 前端静态资源
    location / {
        root   /usr/share/nginx/html;
        index  index.html index.htm;
        try_files $uri $uri/ /index.html; # Vue Router History Mode
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://backend:8080/; # 注意结尾斜杠
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 4. 后端 Dockerfile (backend/Dockerfile)

```dockerfile
# Build Stage
FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Run Stage
FROM openjdk:17-jdk-slim
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## 5. 前端 Dockerfile (frontend/Dockerfile)

```dockerfile
# Build Stage
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Run Stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 6. 部署步骤

1.  **准备环境**: 安装 Docker 和 Docker Compose.
2.  **克隆代码**: `git clone ...`
3.  **配置环境**: 修改 `docker-compose.yml` 中的数据库密码。
4.  **构建并启动**:
    ```bash
    docker-compose up -d --build
    ```
5.  **查看日志**:
    ```bash
    docker-compose logs -f backend
    ```
6.  **访问**: 打开浏览器访问 `http://localhost`。

## 7. 备份策略 (Cron Job)

建议在宿主机设置定时任务，每天凌晨 2 点备份数据库：

```bash
0 2 * * * docker exec ppoms-mysql mysqldump -u root -p'password' ppoms_cloud > /backup/ppoms_$(date +\%F).sql
```
