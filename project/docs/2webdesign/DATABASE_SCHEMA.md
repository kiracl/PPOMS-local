# PPOMS Web系统 - 数据库设计规范 (MySQL)

## 1. 命名规范
*   **表名**: 小写字母 + 下划线，建议以 `biz_` 开头表示业务表，`sys_` 开头表示系统表。
*   **字段名**: 小写字母 + 下划线，主键统一为 `id` (bigint)。
*   **索引**: `idx_<字段名>`。
*   **外键**: `fk_<从表>_<主表>`。

## 2. 基础表设计 (System)

### 2.1 用户与权限 (sys_user, sys_role, sys_menu)

```sql
CREATE TABLE `sys_user` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(64) NOT NULL COMMENT '用户名',
  `password` varchar(128) NOT NULL COMMENT '加密密码',
  `real_name` varchar(64) DEFAULT NULL COMMENT '真实姓名',
  `dept_id` bigint DEFAULT NULL COMMENT '部门ID',
  `status` tinyint(1) DEFAULT '1' COMMENT '状态(1:正常,0:禁用)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE `sys_role` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_name` varchar(64) NOT NULL COMMENT '角色名称',
  `role_code` varchar(64) NOT NULL COMMENT '角色编码',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

CREATE TABLE `sys_menu` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `parent_id` bigint DEFAULT '0' COMMENT '父菜单ID',
  `menu_name` varchar(64) NOT NULL COMMENT '菜单名称',
  `path` varchar(128) DEFAULT NULL COMMENT '路由路径',
  `component` varchar(128) DEFAULT NULL COMMENT '组件路径',
  `perms` varchar(128) DEFAULT NULL COMMENT '权限标识(如: system:user:add)',
  `icon` varchar(64) DEFAULT NULL COMMENT '图标',
  `order_num` int DEFAULT '0' COMMENT '排序',
  `menu_type` char(1) DEFAULT 'M' COMMENT '类型(M:目录,C:菜单,F:按钮)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='菜单权限表';

CREATE TABLE `sys_user_role` (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_id`,`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

CREATE TABLE `sys_role_menu` (
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_id`,`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色菜单关联表';
```

### 2.2 部门表 (sys_dept)

```sql
CREATE TABLE `sys_dept` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `parent_id` bigint DEFAULT '0' COMMENT '父部门ID',
  `dept_name` varchar(64) NOT NULL COMMENT '部门名称',
  `order_num` int DEFAULT '0' COMMENT '排序',
  `leader` varchar(64) DEFAULT NULL COMMENT '负责人',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `status` tinyint(1) DEFAULT '1' COMMENT '状态(1:正常,0:停用)',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';
```

## 3. 业务核心表设计 (Business)

### 3.1 月度计划 (monthly_plans)

```sql
CREATE TABLE `monthly_plans` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `plan_month` varchar(10) DEFAULT NULL COMMENT '计划月份 (e.g. 2601)',
  `department` varchar(100) DEFAULT NULL COMMENT '部门',
  `item_name` varchar(200) DEFAULT NULL COMMENT '物资名称',
  `spec_model` varchar(200) DEFAULT NULL COMMENT '规格型号',
  `unit` varchar(20) DEFAULT NULL COMMENT '单位',
  `plan_qty` decimal(12,2) DEFAULT NULL COMMENT '计划数量',
  `plan_budget` decimal(14,2) DEFAULT NULL COMMENT '预算',
  `remarks` text COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度计划表';
```

### 3.2 采购订单 (orders, order_details)

```sql
CREATE TABLE `orders` (
  `number` varchar(50) NOT NULL COMMENT '订单主单号 (e.g. CG-2601MPB-0001)',
  `yymm` varchar(10) DEFAULT NULL COMMENT '年月 (e.g. 2601)',
  `category` varchar(20) DEFAULT NULL COMMENT '类别 (e.g. MPB)',
  `task_name` varchar(200) DEFAULT NULL COMMENT '任务名称',
  `unit` varchar(100) DEFAULT NULL COMMENT '需求单位',
  `dept_id` bigint DEFAULT NULL COMMENT '所属部门ID (用于权限隔离)',
  `creator_id` bigint DEFAULT NULL COMMENT '录入员ID',
  `approval_report_path` varchar(255) DEFAULT NULL COMMENT '审批报告PDF路径',
  `date` date DEFAULT NULL COMMENT '订单日期',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购需求主单表';

CREATE TABLE `order_details` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_number` varchar(50) DEFAULT NULL COMMENT '关联主单号',
  `detail_no` varchar(50) DEFAULT NULL COMMENT '明细单号 (e.g. 2601MPB-1)',
  `item_name` varchar(200) DEFAULT NULL COMMENT '物资名称 (Display)',
  `purchase_item` varchar(200) DEFAULT NULL COMMENT '采购物资名称 (Standard)',
  `spec_model` varchar(200) DEFAULT NULL COMMENT '规格型号',
  `unit` varchar(20) DEFAULT NULL COMMENT '单位',
  `purchase_qty` decimal(12,2) DEFAULT NULL COMMENT '采购数量',
  `budget_wan` decimal(12,4) DEFAULT NULL COMMENT '预算(万)',
  `purchase_method` varchar(50) DEFAULT NULL COMMENT '采购方式',
  `purchase_channel` varchar(50) DEFAULT NULL COMMENT '采购渠道',
  `plan_release` varchar(50) DEFAULT NULL COMMENT '计划下达人(采购员)',
  `assign_status` varchar(20) DEFAULT '待分配' COMMENT '分配状态(待分配/已分配)',
  `execute_status` varchar(20) DEFAULT '未发放' COMMENT '执行状态(未发放/跟进中/采购中/已入库)',
  `inquiry_price` varchar(50) DEFAULT NULL COMMENT '询价结果',
  `audit_price` varchar(50) DEFAULT NULL COMMENT '审核价格',
  `supplier` varchar(200) DEFAULT NULL COMMENT '供应商',
  `remark` text COMMENT '备注',
  `plan_time` date DEFAULT NULL COMMENT '计划时间',
  `tax_rate` varchar(20) DEFAULT NULL COMMENT '税率',
  PRIMARY KEY (`id`),
  KEY `idx_order_number` (`order_number`),
  KEY `idx_detail_no` (`detail_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购需求明细表';
```

### 3.3 任务分发 (release_orders)

```sql
CREATE TABLE `release_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `source_order_number` varchar(50) DEFAULT NULL COMMENT '源单号',
  `purchaser` varchar(50) DEFAULT NULL COMMENT '采购员',
  `status` varchar(20) DEFAULT NULL COMMENT '状态 (未发放/已发放)',
  `release_date` date DEFAULT NULL COMMENT '发放日期',
  PRIMARY KEY (`id`),
  KEY `idx_source_order` (`source_order_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务分发表';
```

### 3.4 价格库 (recommendations, historical_quotes)

```sql
CREATE TABLE `recommendations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_name` varchar(200) DEFAULT NULL COMMENT '物资名称',
  `plan_release` varchar(50) DEFAULT NULL COMMENT '默认下达人',
  `weight` int DEFAULT 100 COMMENT '权重',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `purchase_method` varchar(50) DEFAULT NULL COMMENT '默认采购方式',
  `purchase_channel` varchar(50) DEFAULT NULL COMMENT '默认采购渠道',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标准物资库';

CREATE TABLE `historical_quotes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_name` varchar(200) DEFAULT NULL,
  `spec_model` varchar(200) DEFAULT NULL,
  `audit_price` decimal(12,2) DEFAULT NULL,
  `supplier` varchar(200) DEFAULT NULL,
  `quote_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='历史报价库';
```

### 3.5 合同管理 (contracts, contract_orders, contract_specs)

```sql
CREATE TABLE `contracts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `contract_number` varchar(50) DEFAULT NULL COMMENT '合同编号',
  `name` varchar(200) DEFAULT NULL COMMENT '合同名称',
  `category` varchar(50) DEFAULT NULL COMMENT '合同类别',
  `supplier` varchar(200) DEFAULT NULL COMMENT '供应商',
  `sign_date` date DEFAULT NULL COMMENT '签订日期',
  `end_date` date DEFAULT NULL COMMENT '结束日期',
  `amount` decimal(14,2) DEFAULT NULL COMMENT '合同总额',
  `status` varchar(20) DEFAULT NULL COMMENT '状态',
  `attachment` varchar(255) DEFAULT NULL COMMENT '附件路径',
  `remarks` text COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_contract_number` (`contract_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同主表';

CREATE TABLE `contract_specs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `contract_id` bigint DEFAULT NULL,
  `spec_model` varchar(200) DEFAULT NULL COMMENT '规格型号',
  `unit` varchar(20) DEFAULT NULL,
  `quantity` decimal(12,2) DEFAULT NULL COMMENT '合同总数',
  `unit_price` decimal(12,2) DEFAULT NULL COMMENT '单价',
  `total_price` decimal(14,2) DEFAULT NULL COMMENT '总价',
  `executed_qty` decimal(12,2) DEFAULT 0 COMMENT '已执行数量',
  PRIMARY KEY (`id`),
  KEY `idx_contract_id` (`contract_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同规格表';

CREATE TABLE `contract_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `contract_id` bigint DEFAULT NULL,
  `spec_id` bigint DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `order_no` varchar(50) DEFAULT NULL COMMENT '执行单号',
  `quantity` decimal(12,2) DEFAULT NULL,
  `unit_price` decimal(12,2) DEFAULT NULL,
  `total_price` decimal(14,2) DEFAULT NULL,
  `sales_order` varchar(50) DEFAULT NULL COMMENT '销售单号',
  `prod_order` varchar(50) DEFAULT NULL COMMENT '生产单号',
  `purch_plan_no` varchar(50) DEFAULT NULL COMMENT '采购计划号',
  `status` varchar(20) DEFAULT '新增' COMMENT '状态',
  `remarks` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_contract_spec` (`contract_id`, `spec_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同执行订单表';
```

### 3.6 入库管理 (inbound_orders)

```sql
CREATE TABLE `inbound_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `inbound_no` varchar(50) DEFAULT NULL COMMENT '入库单号',
  `contract_order_id` bigint DEFAULT NULL,
  `contract_no` varchar(50) DEFAULT NULL,
  `order_no` varchar(50) DEFAULT NULL,
  `purch_plan_no` varchar(50) DEFAULT NULL,
  `spec_model` varchar(200) DEFAULT NULL,
  `order_qty` decimal(12,2) DEFAULT NULL,
  `inbound_qty` decimal(12,2) DEFAULT NULL COMMENT '本次入库数量',
  `warehouse_no` varchar(50) DEFAULT NULL COMMENT '仓库单号',
  `inbound_date` date DEFAULT NULL,
  `operator` varchar(50) DEFAULT NULL,
  `remarks` text,
  `invoice_id` bigint DEFAULT NULL COMMENT '关联发票ID',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_inbound_no` (`inbound_no`),
  KEY `idx_contract_order` (`contract_order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单表';
```

### 3.7 发票管理 (invoices, invoice_items)

```sql
CREATE TABLE `invoices` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uuid` varchar(50) DEFAULT NULL,
  `invoice_code` varchar(50) DEFAULT NULL,
  `invoice_number` varchar(50) DEFAULT NULL COMMENT '发票号码',
  `date` date DEFAULT NULL COMMENT '开票日期',
  `seller_name` varchar(200) DEFAULT NULL,
  `seller_tax_id` varchar(50) DEFAULT NULL,
  `buyer_name` varchar(200) DEFAULT NULL,
  `buyer_tax_id` varchar(50) DEFAULT NULL,
  `amount_excluding_tax` decimal(14,2) DEFAULT NULL,
  `tax_amount` decimal(14,2) DEFAULT NULL,
  `total_amount` decimal(14,2) DEFAULT NULL COMMENT '价税合计',
  `status` varchar(20) DEFAULT '新增' COMMENT '状态',
  `material_inbound_no` varchar(50) DEFAULT NULL COMMENT '材料入库单号',
  `file_path` varchar(255) DEFAULT NULL,
  `remarks` text,
  `invoice_type` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票主表';

CREATE TABLE `invoice_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invoice_id` bigint DEFAULT NULL,
  `item_name` varchar(200) DEFAULT NULL,
  `spec_model` varchar(200) DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL,
  `quantity` decimal(12,2) DEFAULT NULL,
  `unit_price` decimal(12,2) DEFAULT NULL,
  `amount` decimal(14,2) DEFAULT NULL,
  `tax_rate` decimal(6,4) DEFAULT NULL,
  `tax_amount` decimal(14,2) DEFAULT NULL,
  `inbound_id` bigint DEFAULT NULL COMMENT '关联入库ID',
  `inbound_no` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_invoice_id` (`invoice_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票明细表';
```

### 3.8 对账与结算 (reconciliations, reconciliation_details, settlements)

```sql
CREATE TABLE `reconciliations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reconciliation_no` varchar(50) DEFAULT NULL COMMENT '对账单号',
  `supplier` varchar(200) DEFAULT NULL,
  `status` varchar(20) DEFAULT '待对账' COMMENT '状态',
  `total_amount` decimal(14,2) DEFAULT NULL,
  `remarks` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_recon_no` (`reconciliation_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对账单表';

CREATE TABLE `reconciliation_details` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reconciliation_id` bigint DEFAULT NULL,
  `invoice_item_id` bigint DEFAULT NULL,
  `inbound_order_id` bigint DEFAULT NULL,
  `quantity` decimal(12,2) DEFAULT NULL,
  `amount_excl_tax` decimal(14,2) DEFAULT NULL,
  `amount_incl_tax` decimal(14,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_recon_id` (`reconciliation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对账明细表';

CREATE TABLE `settlements` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reconciliation_id` bigint DEFAULT NULL,
  `settlement_date` date DEFAULT NULL,
  `amount` decimal(14,2) DEFAULT NULL,
  `method` varchar(50) DEFAULT NULL,
  `operator_id` bigint DEFAULT NULL,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结算记录表';
```

### 3.9 价格审核 (quote_audit_records, quote_audit_details)

```sql
CREATE TABLE `quote_audit_records` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT '未审核',
  `remark` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报价审核记录表';

CREATE TABLE `quote_audit_details` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `record_id` bigint DEFAULT NULL,
  `detail_no` varchar(50) DEFAULT NULL,
  `order_number` varchar(50) DEFAULT NULL,
  `demand_unit` varchar(100) DEFAULT NULL,
  `item_name` varchar(200) DEFAULT NULL,
  `spec_model` varchar(200) DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL,
  `qty` decimal(12,2) DEFAULT NULL,
  `budget` decimal(12,4) DEFAULT NULL,
  `purchase_method` varchar(50) DEFAULT NULL,
  `purchase_channel` varchar(50) DEFAULT NULL,
  `plan_release` varchar(50) DEFAULT NULL,
  `inquiry_price` decimal(12,2) DEFAULT NULL,
  `audit_price` decimal(12,2) DEFAULT NULL,
  `remark` text,
  PRIMARY KEY (`id`),
  KEY `idx_record_id` (`record_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报价审核明细表';
```

### 3.10 知识库与AI (knowledge_docs, knowledge_chunks, ai_config)

```sql
CREATE TABLE `knowledge_docs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) DEFAULT NULL,
  `filepath` varchar(255) DEFAULT NULL,
  `doc_type` varchar(20) DEFAULT NULL,
  `upload_time` datetime DEFAULT NULL,
  `chunk_count` int DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档表';

CREATE TABLE `knowledge_chunks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `doc_id` bigint DEFAULT NULL,
  `chunk_index` int DEFAULT NULL,
  `content` longtext,
  PRIMARY KEY (`id`),
  KEY `idx_doc_id` (`doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库内容分块表';

CREATE TABLE `ai_config` (
  `config_key` varchar(50) NOT NULL,
  `provider` varchar(50) DEFAULT NULL,
  `base_url` varchar(255) DEFAULT NULL,
  `api_key` varchar(255) DEFAULT NULL,
  `model_name` varchar(100) DEFAULT NULL,
  `system_prompt` text,
  PRIMARY KEY (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI配置表';
```

### 3.11 辅助表 (suppliers, contract_categories, plan_months, table_column_configs)

```sql
CREATE TABLE `suppliers` (
  `name` varchar(200) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商列表';

CREATE TABLE `contract_categories` (
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同类别列表';

CREATE TABLE `plan_months` (
  `name` varchar(10) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计划月份列表';

CREATE TABLE `table_column_configs` (
  `table_key` varchar(100) NOT NULL,
  `column_index` int NOT NULL,
  `width` int DEFAULT NULL,
  PRIMARY KEY (`table_key`, `column_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表格列宽配置';
```
