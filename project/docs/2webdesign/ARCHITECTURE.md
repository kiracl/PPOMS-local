# PPOMS Web系统 架构设计文档 (V1.0)

## 1. 系统概述
PPOMS (Procurement Production Operation Management System) Web版旨在将原有的桌面端单机应用升级为支持多用户、权限分离、前后端分离的企业级微服务应用。系统采用 **Java (Spring Boot/Cloud)** + **Vue 3** + **MySQL** 技术栈，实现采购全生命周期的数字化管理。

## 2. 技术架构

### 2.1 总体架构
采用前后端分离架构，后端基于 Spring Cloud Alibaba 微服务体系（视规模可简化为 Spring Boot 单体模块化），前端基于 Vue 3 + Element Plus。

*   **前端**: Vue 3, Vite, TypeScript, Pinia (状态管理), Element Plus (UI组件库), Echarts (数据可视化).
*   **后端**: Java 17+, Spring Boot 3.x, MyBatis-Plus, Spring Security + JWT.
*   **数据库**: MySQL 8.0 (继承自 SQLite 的平移结构).
*   **缓存**: Redis (用于缓存 Token、字典数据、智能推荐规则).
*   **消息队列**: RabbitMQ (可选，用于异步解耦，如审批通知、日志记录).
*   **部署**: Docker + Kubernetes (或 Docker Compose).

### 2.2 模块划分 (微服务/模块设计)
1.  **认证中心 (Auth Service)**: 用户登录、JWT 签发与校验、权限管理 (RBAC).
2.  **系统管理 (Admin Service)**: 用户、部门、角色、数据字典、智能推荐规则维护.
3.  **采购计划服务 (Plan Service)**: 月度计划导入与对碰、采购申请、计划下达、CLI 接口转 REST API.
4.  **执行与进度服务 (Progress Service)**: 计划状态流转、进度工作台汇总、批处理更新接口.
5.  **合同与供应链服务 (Supply Service)**: 合同台账、执行订单、入库登记及状态联动.
6.  **财务服务 (Finance Service)**: 发票管理、对账结算、付款记录.
7.  **AI 网关服务 (AI Gateway)**: 统一对接 DeepSeek, Kimi, OpenAI, Ollama 等多模型引擎，提供业务层面的对话和数据查询能力.

## 3. 核心业务流程设计

### 3.1 用户与权限体系 (RBAC)
*   **角色**: 系统管理员、采购经理、采购员、库管员、财务专员、总经理.
*   **数据权限**:
    *   **采购员**: 只能查看/操作自己负责的采购任务和订单.
    *   **采购经理**: 查看全部门数据，审批采购计划.
    *   **库管员**: 仅操作入库模块.
    *   **财务**: 仅操作发票与结算模块.

### 3.2 采购主流程
1.  **计划导入**: 生产部导入月度物资需求计划 (Excel) -> 生成 `MonthlyPlan`.
2.  **任务分配**: 采购经理将计划项分配给具体采购员 -> 生成 `PurchaseTask`.
3.  **询价/核价**: 采购员录入询价结果 -> 系统自动比对历史价格/标准价 -> 经理审批.
4.  **合同/订单**: 确认价格后生成采购合同或直接生成采购订单 (`PurchaseOrder`).
5.  **入库**: 物资到货，库管员关联订单进行入库录入 -> 生成 `InboundRecord` (扣减订单未执行数量).
6.  **发票**: 采购员收到发票，录入并关联入库单 -> 生成 `Invoice`.
7.  **对账**: 定期生成对账单 (`Reconciliation`) -> 供应商确认.
8.  **结算**: 财务付款 -> 更新对账单状态为“已结算”.

## 4. 数据库设计 (MySQL)

### 4.1 系统基础表
*   `sys_user`: 用户表 (id, username, password, dept_id, status).
*   `sys_role`: 角色表 (id, role_name, role_code).
*   `sys_menu`: 菜单权限表 (id, parent_id, path, component, permission).
*   `sys_user_role`: 用户角色关联.
*   `sys_role_menu`: 角色菜单关联.
*   `sys_dept`: 部门表 (id, dept_name, parent_id).

### 4.2 业务核心表
*   `biz_monthly_plan`: 月度计划主表.
*   `biz_purchase_order`: 采购订单 (order_no, contract_id, supplier_id, total_amount, status).
*   `biz_order_detail`: 订单明细 (item_name, spec, qty, price).
*   `biz_contract`: 合同台账.
*   `biz_inbound`: 入库单 (关联 biz_purchase_order).
*   `biz_invoice`: 发票 (关联 biz_inbound).
*   `biz_reconciliation`: 对账单.
*   `biz_settlement`: 结算记录.
*   `biz_price_library`: 标准价格库.

## 5. 接口设计规范 (RESTful)
*   **通用响应**: `{ code: 200, msg: "success", data: ... }`
*   **分页**: `GET /api/v1/orders?page=1&size=10&keyword=...`
*   **新建**: `POST /api/v1/orders`
*   **更新**: `PUT /api/v1/orders/{id}`
*   **删除**: `DELETE /api/v1/orders/{id}`

## 6. AI 智能化设计
*   **后端**: 集成 LangChain for Java 或直接调用 LLM API.
*   **功能**:
    *   **Text-to-SQL**: 将自然语言转为 MyBatis-Plus `QueryWrapper` 或原生 SQL.
    *   **RAG**: 将上传的 PDF/Word 制度文档解析存入向量数据库 (如 Milvus 或 PgVector)，提供知识问答.

## 7. 安全设计
*   **认证**: Spring Security + JWT.
*   **密码**: BCrypt 加密存储.
*   **数据隔离**: MyBatis-Plus 租户插件 (如果需要多租户) 或 数据权限拦截器.
*   **审计**: AOP 记录关键操作日志 (操作人、IP、时间、变更内容).
