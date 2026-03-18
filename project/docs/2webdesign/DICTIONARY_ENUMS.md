# PPOMS Web系统 - 数据字典与枚举定义 (V1.0)

## 1. 基础状态 (Common Status)

### 1.1 数据状态 (sys_common_status)
*   `0`: **正常 (Normal)**
*   `1`: **停用 (Disable)**

### 1.2 删除标记 (del_flag)
*   `0`: **未删除 (Exist)**
*   `2`: **已删除 (Deleted)**

## 2. 采购业务字典

### 2.1 计划状态 (plan_status)
*   `0`: **草稿 (Draft)** - 刚导入，仅自己可见。
*   `1`: **待审批 (Pending)** - 提交给经理，锁定不可改。
*   `2`: **已审批 (Approved)** - 经理同意，进入任务池。
*   `3`: **已驳回 (Rejected)** - 经理拒绝，退回修改。
*   `4`: **执行中 (Executing)** - 部分任务已分发。
*   `5`: **已完成 (Completed)** - 所有任务已执行完毕。

### 2.2 订单状态 (order_status)
*   `0`: **新增 (New)** - 刚生成，未生效。
*   `1`: **待发货 (Pending Delivery)** - 已确认，等供应商发货。
*   `2`: **部分入库 (Partial Inbound)** - 到了一部分货。
*   `3`: **已入库 (Inbound)** - 全部到货。
*   `4`: **已完成 (Finished)** - 流程结束（可能包含结算）。
*   `9`: **已作废 (Void)** - 订单取消。

### 2.3 采购方式 (purchase_method)
*   `VJ`: **询比价 (Inquiry)** - 默认方式。
*   `ZB`: **招标 (Tender)** - 金额巨大时使用。
*   `DY`: **单一来源 (Single Source)** - 独家供应。
*   `DD`: **定点采购 (Fixed Point)** - 常用物资，有协议价。
*   `DS`: **电商直购 (E-commerce)** - 京东/淘宝等。

### 2.4 采购渠道 (purchase_channel)
*   `OFFLINE`: **线下采购**
*   `JD`: **京东**
*   `TMALL`: **天猫**
*   `1688`: **阿里巴巴**

## 3. 供应链字典

### 3.1 供应商评级 (supplier_level)
*   `A`: **优秀** - 优先合作。
*   `B`: **良好** - 正常合作。
*   `C`: **合格** - 考察期。
*   `D`: **不合格** - 暂停合作。
*   `BLACK`: **黑名单** - 禁止交易。

## 4. 财务字典

### 4.1 发票类型 (invoice_type)
*   `PP`: **普票 (General VAT)**
*   `ZP`: **专票 (Special VAT)**
*   `DZ`: **电子发票 (Electronic)**

### 4.2 发票状态 (invoice_status)
*   `0`: **新增 (New)** - 刚录入。
*   `1`: **待入账 (Pending Account)** - 已关联入库，等待财务确认。
*   `2`: **已入账 (Accounted)** - 财务已确认，进入对账池。

### 4.3 对账状态 (reconciliation_status)
*   `0`: **待对账 (Pending)**
*   `1`: **对账中 (In Progress)** - 发给供应商确认中。
*   `2`: **已确认 (Confirmed)** - 双方金额无误。
*   `3`: **已结算 (Settled)** - 财务已付款。

## 5. 单位字典 (unit_options)
*   `t`: **吨**
*   `kg`: **千克**
*   `m`: **米**
*   `m2`: **平方米**
*   `m3`: **立方米**
*   `pc`: **个**
*   `set`: **套**
*   `box`: **箱**
*   `pair`: **双**
