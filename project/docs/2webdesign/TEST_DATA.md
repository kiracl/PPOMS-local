# PPOMS Web系统 - 预置测试数据 (Test Data)

为了确保开发环境的一致性，请在初始化数据库后执行以下 SQL 插入基础测试数据。

## 1. 系统管理数据

### 1.1 部门 (sys_dept)
```sql
INSERT INTO sys_dept (id, parent_id, dept_name, order_num, leader) VALUES
(100, 0, 'PPOMS集团', 0, 'CEO'),
(101, 100, '采购部', 1, '张经理'),
(102, 100, '生产部', 2, '李主管'),
(103, 100, '财务部', 3, '王会计'),
(104, 100, '仓库', 4, '赵库管');
```

### 1.2 角色 (sys_role)
```sql
INSERT INTO sys_role (id, role_name, role_code, description) VALUES
(1, '超级管理员', 'admin', '拥有所有权限'),
(2, '采购经理', 'purch_mgr', '采购审批权限'),
(3, '采购员', 'purchaser', '采购执行权限'),
(4, '库管员', 'stock_mgr', '入库操作权限'),
(5, '财务专员', 'finance', '发票结算权限');
```

### 1.3 用户 (sys_user)
*   密码统一为 `123456` (BCrypt: `$2a$10$7JB720yubVSZv5w8vnGk6u...`)

```sql
INSERT INTO sys_user (id, username, password, real_name, dept_id) VALUES
(1, 'admin', '$2a$10$7JB720yubVSZv5w8vnGk6u...', '管理员', 100),
(2, 'zhang_mgr', '$2a$10$7JB720yubVSZv5w8vnGk6u...', '张经理', 101),
(3, 'li_purch', '$2a$10$7JB720yubVSZv5w8vnGk6u...', '李采购', 101),
(4, 'zhao_stock', '$2a$10$7JB720yubVSZv5w8vnGk6u...', '赵库管', 104);
```

### 1.4 用户-角色关联 (sys_user_role)
```sql
INSERT INTO sys_user_role (user_id, role_id) VALUES
(1, 1), -- admin -> admin
(2, 2), -- zhang -> purch_mgr
(3, 3), -- li -> purchaser
(4, 4); -- zhao -> stock_mgr
```

## 2. 基础业务数据

### 2.1 供应商 (suppliers)
```sql
INSERT INTO suppliers (name) VALUES
('上海宝钢股份有限公司'),
('江苏沙钢集团'),
('五金机电批发中心'),
('京东工业品');
```

### 2.2 计划月份 (plan_months)
```sql
INSERT INTO plan_months (name) VALUES ('2601'), ('2602'), ('2603');
```

### 2.3 价格库样本 (recommendations)
```sql
INSERT INTO recommendations (item_name, plan_release, weight, purchase_method) VALUES
('螺纹钢 HRB400E Φ20', '李采购', 100, '询比价'),
('水泥 P.O 42.5', '李采购', 90, '定点采购'),
('手套', '王行政', 50, '电商直购');
```

## 3. 测试用例场景

### 场景 A: 采购全流程
1.  **登录**: 使用 `admin` 账号登录。
2.  **计划**: 在“月度计划”模块导入一条数据：
    *   月份: 2602, 部门: 生产部, 物资: 螺纹钢, 数量: 10吨.
3.  **任务**: 切换 `zhang_mgr` 账号，将该计划指派给 `li_purch`。
4.  **订单**: 切换 `li_purch` 账号，生成采购订单，选择供应商“上海宝钢”。
5.  **入库**: 切换 `zhao_stock` 账号，对该订单进行入库，数量: 10.
6.  **结果**: 订单状态应变为“已完成”，入库单列表应有一条新记录。
