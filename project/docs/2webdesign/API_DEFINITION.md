# PPOMS Web系统 - API 接口定义 (V1.0)

## 1. 认证模块 (Auth)

### 1.1 登录
*   **URL**: `POST /api/auth/login`
*   **Request**:
    ```json
    {
      "username": "admin",
      "password": "encrypted_password",
      "captcha": "xy12"  // 可选
    }
    ```
*   **Response**:
    ```json
    {
      "code": 200,
      "msg": "success",
      "data": {
        "token": "Bearer eyJhbGciOi..."
      }
    }
    ```

### 1.2 获取用户信息
*   **URL**: `GET /api/auth/user-info`
*   **Response**:
    ```json
    {
      "code": 200,
      "data": {
        "user": { "id": 1, "username": "admin", "avatar": "..." },
        "roles": ["admin"],
        "permissions": ["system:user:add", "purchase:plan:list"]
      }
    }
    ```

### 1.3 退出登录
*   **URL**: `POST /api/auth/logout`

## 2. 系统管理模块 (System)

### 2.1 用户管理
*   `GET /api/system/users` - 分页查询用户 (params: page, size, username, deptId)
*   `POST /api/system/users` - 新增用户
*   `PUT /api/system/users/{id}` - 修改用户
*   `DELETE /api/system/users/{id}` - 删除用户
*   `PUT /api/system/users/{id}/reset-pwd` - 重置密码

### 2.2 部门管理
*   `GET /api/system/depts` - 获取部门树
*   `POST /api/system/depts` - 新增部门
*   `PUT /api/system/depts/{id}` - 修改部门
*   `DELETE /api/system/depts/{id}` - 删除部门

### 2.3 字典管理
*   `GET /api/system/dict/data/{dictType}` - 根据类型获取字典数据 (用于前端下拉框)

## 3. 采购业务模块 (Purchase)

### 3.1 采购需求录入与审批 (Purchase Request)
*   **URL**: `/api/purchase/requests`
*   **List**: `GET /api/purchase/requests` (params: page, size, month, auditStatus)
*   **Create**: `POST /api/purchase/requests` (支持上传审批报告 PDF，返回主单 number)
    ```json
    {
      "yymm": "2603",
      "category": "MP",
      "taskName": "3月工具采购",
      "unit": "生产部",
      "approvalReportPath": "/uploads/pdf/xxx.pdf",
      "items": [
        { "itemName": "扳手", "specModel": "10寸", "purchaseQty": 10, "unit": "把" }
      ]
    }
    ```
*   **Audit**: `POST /api/purchase/requests/{number}/audit` 
    *   body: `{ "action": "approve" | "reject", "remark": "退回原因" }`
*   **Assign**: `POST /api/purchase/requests/assign` 
    *   body: `{ "detailIds": [1,2], "purchaser": "张三" }`
*   **Release**: `POST /api/purchase/requests/release` (发放计划，使采购员可见)

### 3.2 采购员任务池与进度 (Purchase Task)
*   **List**: `GET /api/purchase/tasks` (仅返回当前登录采购员已被发放的明细)
*   **Update Status**: `PUT /api/purchase/tasks/status`
    ```json
    {
      "detailIds": [1, 2],
      "executeStatus": "采购中",
      "followUpRemark": "已联系供应商，预计下周发货"
    }
    ```

### 3.3 计划导出与打印
*   `GET /api/purchase/export/monthly` (按月度/分类导出 Excel 文件流)
*   `GET /api/purchase/print/{number}` (获取打印所需的数据结构)

## 4. 供应链模块 (Supply)

### 4.1 入库单 (Inbound)
*   `GET /api/supply/inbounds` - 分页查询入库单
*   `POST /api/supply/inbounds` - 新增入库单
    ```json
    {
      "orderId": 1001,
      "inboundDate": "2026-02-14",
      "items": [
        { "orderDetailId": 501, "qty": 50 }
      ]
    }
    ```

## 5. 财务模块 (Finance)

### 5.1 发票管理
*   `GET /api/finance/invoices`
*   `POST /api/finance/invoices` - 录入发票并关联入库单

### 5.2 对账单
*   `POST /api/finance/reconciliations/generate` - 生成对账单
    ```json
    {
      "supplierId": 201,
      "startDate": "2026-01-01",
      "endDate": "2026-01-31"
    }
    ```

## 6. AI 助手模块 (AI)

### 6.1 智能对话
*   **URL**: `POST /api/ai/chat`
*   **Request**:
    ```json
    {
      "message": "帮我查一下上个月A供应商的供货总额",
      "history": [...] // 上下文
    }
    ```
*   **Response**: (Stream or JSON)
    ```json
    {
      "answer": "上个月A供应商供货总额为 500,000 元。",
      "sql": "SELECT sum(...) FROM ...", // 可选，用于展示思考过程
      "chartData": { ... } // 可选，用于前端绘图
    }
    ```

### 6.2 知识库检索
*   `POST /api/ai/knowledge/search` (body: { query: "合同审批流程" })
