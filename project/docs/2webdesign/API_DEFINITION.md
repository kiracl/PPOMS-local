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

### 3.1 月度计划 (Monthly Plan)
*   **URL**: `/api/purchase/plans`
*   **List**: `GET /api/purchase/plans` (params: page, size, month, status)
*   **Detail**: `GET /api/purchase/plans/{id}`
*   **Create**: `POST /api/purchase/plans`
    ```json
    {
      "planMonth": "202602",
      "items": [
        { "itemName": "螺纹钢", "spec": "HRB400E", "qty": 100, "unit": "吨" }
      ]
    }
    ```
*   **Audit**: `POST /api/purchase/plans/{id}/audit` (body: { status: 1, comment: "同意" })

### 3.2 采购订单 (Order)
*   **URL**: `/api/purchase/orders`
*   **List**: `GET /api/purchase/orders`
*   **Create**: `POST /api/purchase/orders`
*   **Detail**: `GET /api/purchase/orders/{id}`
*   **Export**: `POST /api/purchase/orders/export` (返回 Excel 文件流)

### 3.3 供应商 (Supplier)
*   `GET /api/purchase/suppliers/options` - 获取供应商下拉列表 (id, name)

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
