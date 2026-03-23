# PPOMS Web系统 - 部署与运维指南 (Ubuntu)

## 1. 部署环境要求
*   **操作系统**: Ubuntu 22.04 LTS (或以上版本).
*   **依赖环境**: JDK 17, MySQL 8.0, Redis 6.x, Nginx, Node.js (构建前端用).

## 2. 迭代发布策略 (Modular Monolith)
由于系统采用模块化单体架构，我们采取**增量迭代、平滑升级**的策略。
核心原则：**新模块上线绝不能影响已运行模块的稳定性。**

### 2.1 自动化发布脚本 (`deploy.sh`)
提供统一的 Bash 脚本实现构建、备份、部署、重启与回退。

```bash
#!/bin/bash
# PPOMS 自动化发布与回退脚本
# 用法: 
#   ./deploy.sh deploy  (部署最新版本)
#   ./deploy.sh rollback (回退到上一个版本)

APP_NAME="ppoms-web"
DEPLOY_DIR="/opt/ppoms"
BACKUP_DIR="/opt/ppoms/backup"
JAR_NAME="ppoms-server.jar"
TIME=$(date +%Y%md%H%M)

deploy() {
    echo "1. 停止当前服务..."
    systemctl stop ppoms
    
    echo "2. 备份当前版本..."
    mkdir -p $BACKUP_DIR
    if [ -f "$DEPLOY_DIR/$JAR_NAME" ]; then
        mv $DEPLOY_DIR/$JAR_NAME $BACKUP_DIR/${JAR_NAME}_$TIME.bak
    fi
    
    echo "3. 部署新版本..."
    cp target/$JAR_NAME $DEPLOY_DIR/
    
    echo "4. 启动服务..."
    systemctl start ppoms
    echo "部署完成！"
}

rollback() {
    echo "1. 寻找最近的备份..."
    LATEST_BAK=$(ls -t $BACKUP_DIR/${JAR_NAME}_* | head -1)
    if [ -z "$LATEST_BAK" ]; then
        echo "未找到备份文件，无法回退！"
        exit 1
    fi
    
    echo "2. 停止当前服务..."
    systemctl stop ppoms
    
    echo "3. 执行回退..."
    cp $LATEST_BAK $DEPLOY_DIR/$JAR_NAME
    
    echo "4. 重新启动..."
    systemctl start ppoms
    echo "成功回退到版本: $LATEST_BAK"
}

case "$1" in
    deploy) deploy ;;
    rollback) rollback ;;
    *) echo "Usage: $0 {deploy|rollback}" ;;
esac
```

## 3. 灰度与迭代建议
1. **数据库向下兼容**: 迭代增加新表或新字段时，严禁修改或删除已上线模块依赖的旧字段（Add-only 策略），确保旧代码仍能跑通。
2. **API 版本控制**: 涉及旧功能改造时，保留 `/api/v1/xxx`，新接口挂载至 `/api/v2/xxx`，让前端按需平滑迁移。
3. **前端动态路由**: Vue 路由从后端动态拉取，新上线的模块只要在后端配好权限，前端刷新即可加载出新菜单。