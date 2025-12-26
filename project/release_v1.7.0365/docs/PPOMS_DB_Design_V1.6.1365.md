# PPOMS 数据库设计文档 V1.6.1365

## 1. 概述
本各档描述了 **生产采购订单管理系统 (PPOMS)** 的数据库设计方案。系统采用 **SQLite** 作为存储引擎，数据库文件名为 `purchase.db`。设计遵循轻量级、单文件部署原则，支持系统的核心业务流程，包括采购计划管理、订单执行跟踪、月度计划编制及自动推荐功能。

- **数据库版本**: V1.6.1365
- **数据库文件**: `purchase.db`
- **字符集**: UTF-8

---

## 2. 数据库表清单

| 表名 | 中文名称 | 业务模块 | 类型 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **orders** | 采购订单主表 | 采购管理 | 核心 | 存储采购任务单的主体信息（单号、日期、类别等） |
| **order_details** | 订单明细表 | 采购管理 | 核心 | 存储具体的采购物资明细、规格、预算及执行状态 |
| **release_orders** | 采购下发记录表 | 采购管理 | 核心 | 记录按采购员拆分后的任务下发状态 |
| **monthly_plans** | 月度计划表 | 计划管理 | 核心 | 存储各部门提交的月度采购预算与需求计划 |
| **recommendations** | 智能推荐库 | 辅助功能 | 辅助 | 存储物资的历史采购属性（采购员、渠道等），用于自动填充 |
| **counter** | 单据计数器 | 系统基础 | 辅助 | 记录各类别订单的流水号，确保单号唯一 |
| **detail_counter** | 明细计数器 | 系统基础 | 辅助 | (保留表) 记录明细行序号生成规则 |
| **units** | 单位/部门字典 | 基础数据 | 字典 | 存储申请单位/部门名称 |
| **purchasers** | 采购员字典 | 基础数据 | 字典 | 存储系统有效的采购员名单 |
| **purchase_status** | 采购状态字典 | 基础数据 | 字典 | 定义采购流程的状态流转节点 |
| **plan_months** | 计划月份字典 | 基础数据 | 字典 | 定义可选的计划月份（如 2601, 2602） |
| **print_config** | 打印配置表 | 系统配置 | 配置 | 存储各模块的打印列宽、显隐等JSON配置 |
| **main_layout** | 主表布局配置 | 系统配置 | 配置 | 存储主界面的表格列宽配置 |
| **detail_layout** | 明细布局配置 | 系统配置 | 配置 | 存储明细界面的表格列宽配置 |

---

## 3. 详细设计

### 3.1. orders (采购订单主表)
> 业务主键：`number`

| 字段名 | 数据类型 | 长度 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **number** | TEXT | 20 | 是 | - | **PK**, 订单编号 (如 CG-2601MP0001) |
| yymm | TEXT | 6 | 是 | - | 计划月份 (如 2601) |
| category | TEXT | 10 | 是 | - | 类别代码 (MP:民品, MPJ:机加, MPB:半成品) |
| unit | TEXT | 50 | 否 | - | 申请单位 |
| date | TEXT | 10 | 否 | - | 申请日期 (YYYY-MM-DD) |
| task_name | TEXT | 100 | 否 | - | 任务名称/项目摘要 |

### 3.2. order_details (订单明细表)
> 业务主键：`id` (自增)，逻辑关联：`order_number`

| 字段名 | 数据类型 | 长度 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **id** | INTEGER | - | 是 | AUTO | **PK**, 自增主键 |
| order_number | TEXT | 20 | 是 | - | **FK**, 关联 orders.number |
| detail_no | TEXT | 20 | 是 | - | 明细序号 (如 2601MP-1) |
| item_name | TEXT | 100 | 否 | - | 物品名称 (项目名称) |
| purchase_item | TEXT | 100 | 否 | - | 采购内容 |
| spec_model | TEXT | 100 | 否 | - | 规格型号/技术要求 |
| purchase_cycle | TEXT | 50 | 否 | - | 采购周期 |
| stock_count | TEXT | 20 | 否 | - | 库存数量 |
| purchase_qty | TEXT | 20 | 否 | - | 采购数量 |
| unit | TEXT | 20 | 否 | - | 单位 (个/套/kg等) |
| unit_price | TEXT | 20 | 否 | - | 预算单价 (元) |
| budget_wan | TEXT | 20 | 否 | - | 预算总价 (万元) |
| purchase_method | TEXT | 50 | 否 | - | 采购方式 (询比价/直接采购等) |
| purchase_channel | TEXT | 50 | 否 | - | 采购渠道 (网购/实体/厂家) |
| plan_time | TEXT | 20 | 否 | - | 计划到货时间 |
| demand_unit | TEXT | 50 | 否 | - | 需求单位/使用人 |
| plan_release | TEXT | 50 | 否 | - | 计划下达给(采购员) |
| progress_req | TEXT | 100 | 否 | - | 进度要求 |
| supplier | TEXT | 100 | 否 | - | 供方名称 |
| inquiry_price | TEXT | 20 | 否 | - | 询价/合同金额 (元) |
| tax_rate | TEXT | 20 | 否 | - | 税率 |
| actual_status | TEXT | 50 | 否 | - | 实际进度状态 |
| purchase_body | TEXT | 50 | 否 | - | 采购主体 |
| add_adjust | TEXT | 50 | 否 | - | 增补/调整标识 |
| remark | TEXT | 200 | 否 | - | 备注 |

### 3.3. release_orders (采购下发记录表)
> 用于追踪按采购员维度的任务包状态

| 字段名 | 数据类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | INTEGER | 是 | AUTO | **PK**, 自增主键 |
| source_order_number | TEXT | 是 | - | **FK**, 关联 orders.number |
| purchaser | TEXT | 是 | - | 采购员姓名 (对应 order_details.plan_release) |
| release_date | TEXT | 否 | - | 下发日期 (YYYY-MM-DD) |
| status | TEXT | 否 | '未发放' | 下发状态 (未发放/已发放) |
| record_count | INTEGER | 否 | - | 该采购员在该单据下的明细条数 |

> **约束**: `UNIQUE(source_order_number, purchaser)` 确保同一单据同一采购员只有一条下发记录。

### 3.4. monthly_plans (月度计划表)
> 独立模块，用于月度预算管理，逻辑上通过物品名称与订单明细关联进行统计

| 字段名 | 数据类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | INTEGER | 是 | AUTO | **PK**, 自增主键 |
| plan_month | TEXT | 否 | - | 计划月份 (如 2601) |
| item_name | TEXT | 否 | - | 物品名称 |
| spec_model | TEXT | 否 | - | 规格型号 |
| unit | TEXT | 否 | - | 单位 |
| plan_qty | REAL | 否 | - | 计划数量 |
| plan_budget | REAL | 否 | - | 计划预算 (万元) |
| department | TEXT | 否 | - | 需求部门 |
| remarks | TEXT | 否 | - | 备注 |

### 3.5. recommendations (智能推荐库)
> 用于输入联想和自动填充

| 字段名 | 数据类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | INTEGER | 是 | AUTO | **PK**, 自增主键 |
| item_name | TEXT | 否 | - | 物品名称 (匹配关键词) |
| plan_release | TEXT | 否 | - | 推荐采购员 |
| weight | INTEGER | 否 | - | 权重 (排序依据) |
| is_active | INTEGER | 否 | 1 | 是否启用 (1:启用, 0:禁用) |
| purchase_method | TEXT | 否 | - | 推荐采购方式 |
| purchase_channel | TEXT | 否 | - | 推荐采购渠道 |

### 3.6. counter (单据计数器)
> 复合主键：(yymm, category)

| 字段名 | 数据类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| **yymm** | TEXT | 是 | **PK**, 计划月份 |
| **category** | TEXT | 是 | **PK**, 类别代码 |
| seq | INTEGER | 是 | 当前最大流水号 |

### 3.7. 基础字典表 (units, purchasers, purchase_status, plan_months)
此四张表结构相同，均为单列主键表。

| 表名 | 字段名 | 类型 | 说明 |
| :--- | :--- | :--- | :--- |
| **units** | name | TEXT | **PK**, 单位名称 |
| **purchasers** | name | TEXT | **PK**, 采购员姓名 |
| **purchase_status** | name | TEXT | **PK**, 状态名称 |
| **plan_months** | name | TEXT | **PK**, 月份名称 |

### 3.8. 配置表 (print_config, main_layout, detail_layout)

| 表名 | 字段 | 类型 | 说明 |
| :--- | :--- | :--- | :--- |
| **print_config** | module (PK) | TEXT | 模块名 (如 'plan_export') |
| | config_json | TEXT | JSON格式的列宽和显示配置 |
| **main_layout** | col_index (PK) | INTEGER | 列索引 |
| | width | INTEGER | 列宽 (像素) |
| **detail_layout** | col_index (PK) | INTEGER | 列索引 |
| | width | INTEGER | 列宽 (像素) |

---

## 4. 表关系图 (ER Diagram)

```mermaid
erDiagram
    orders ||--|{ order_details : "包含 (1:n)"
    orders ||--|{ release_orders : "生成下发记录 (1:n)"
    
    orders {
        string number PK
        string yymm
        string category
        string unit
    }
    
    order_details {
        int id PK
        string order_number FK
        string detail_no
        string plan_release "对应 purchasers.name"
    }
    
    release_orders {
        int id PK
        string source_order_number FK
        string purchaser
        string status
    }
    
    monthly_plans {
        int id PK
        string plan_month
        string item_name
        string spec_model
    }
    
    %% 逻辑关联：月度计划通过名称规格与订单明细进行统计匹配
    monthly_plans ..|{ order_details : "逻辑统计关联 (name+spec)"
```

---

## 5. 数据字典

### 5.1. 订单类别代码 (Category)
| 代码 | 名称 | 说明 |
| :--- | :--- | :--- |
| **MP** | 民品 | 通用物资、办公用品等 |
| **MPJ** | 机加件 | 机械加工类定制件 |
| **MPB** | 半成品 | 生产过程中的半成品物资 |

### 5.2. 采购下发状态 (Release Status)
| 状态值 | 说明 |
| :--- | :--- |
| **未发放** | 初始状态，采购员尚未接收或处理任务 |
| **已发放** | 任务已确认并下达给采购员 |

### 5.3. 采购进度状态 (Purchase Status)
| 状态值 | 说明 |
| :--- | :--- |
| **未发放** | 任务在计划阶段 |
| **已发放** | 任务已分配 |
| **采购中** | 正在询价或合同签订中 |
| **已完成** | 物资已到货验收 |

---

## 6. 设计规范

### 6.1. 命名规范
- **表名**: 使用全小写英文字母，单词间用下划线分隔，通常使用复数形式 (如 `orders`, `units`)。
- **字段名**: 全小写，下划线分隔 (snake_case)。
- **主键**: 业务表推荐使用 `id` 自增整数；核心单据使用 `number` 字符串作为业务主键。

### 6.2. 索引原则
- SQLite 会自动为主键 (`PRIMARY KEY`) 创建索引。
- `orders.number` 作为查询核心，已设为主键。
- `order_details.order_number` 用于频繁的关联查询，虽未显式建索引，但在 SQLite 中整型 ID 关联效率尚可；若数据量级增长，建议追加索引。
- 计数器表 `counter` 使用复合主键 `(yymm, category)` 以优化特定类别的并发获取性能。

### 6.3. 数据一致性
- **级联删除**: 当前代码逻辑中 (`save_order_details_transaction`)，在保存明细时会先根据 `order_number` 删除旧明细再全量插入，以确保明细数据的完整性和顺序性。
- **并发控制**: SQLite 默认为文件锁。系统在写操作时显式获取连接并 commit，利用 SQLite 的事务机制保证原子性。
