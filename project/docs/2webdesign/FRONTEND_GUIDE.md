# PPOMS Web系统 - 前端开发规范 (Vue 3 + TS)

## 1. 技术栈
*   **框架**: Vue 3 (Composition API)
*   **构建工具**: Vite
*   **语言**: TypeScript
*   **UI组件库**: Element Plus
*   **状态管理**: Pinia
*   **路由**: Vue Router 4
*   **HTTP请求**: Axios
*   **CSS预处理**: SCSS

## 2. 目录结构

```
src/
├── api/                # API 接口定义 (按模块划分)
│   ├── auth.ts
│   ├── purchase.ts
│   └── ...
├── assets/             # 静态资源 (图片/字体/全局样式)
├── components/         # 公共组件
│   ├── layout/         # 布局组件 (Sidebar, Header)
│   └── common/         # 通用业务组件 (如上传组件, 富文本)
├── hooks/              # 自定义组合式函数 (useAuth, useTable)
├── router/             # 路由配置
├── store/              # Pinia 状态管理
│   ├── modules/
│   │   ├── user.ts
│   │   └── permission.ts
│   └── index.ts
├── types/              # TypeScript 类型定义
├── utils/              # 工具函数 (request.ts, validate.ts)
├── views/              # 页面视图 (按模块划分)
│   ├── login/
│   ├── dashboard/
│   ├── purchase/
│   │   ├── plan/
│   │   ├── order/
│   │   └── audit/
│   └── system/
└── App.vue
└── main.ts
```

## 3. 编码规范

### 3.1 组件命名
*   **文件名**: 使用 PascalCase (如 `PurchaseOrder.vue`).
*   **组件名**: 在 `defineOptions` 中定义，保持与文件名一致.
*   **目录名**: 使用 kebab-case (如 `purchase-order`).

### 3.2 TypeScript 使用
*   尽量不使用 `any`，为 props 和 API 响应定义 interface.
*   使用 `Type-Only Imports` (`import type { User } from ...`).

### 3.3 状态管理 (Pinia)
*   使用 Setup Store 语法 (`defineStore('id', () => { ... })`).
*   模块化管理，避免单一 Store 过大.

### 3.4 样式
*   使用 SCSS.
*   使用 BEM 命名规范或 CSS Modules 避免样式冲突.
*   尽量使用 Element Plus 提供的 CSS 变量进行主题定制.

## 4. 核心功能实现指南

### 4.1 登录与权限控制
*   **登录**: 调用 `/api/auth/login` 获取 JWT Token，存储在 `localStorage` 和 Pinia 中.
*   **路由守卫**: `router.beforeEach` 校验 Token，无 Token 跳转登录页.
*   **动态路由**: 根据后端返回的用户权限列表 (`sys_menu`)，动态生成路由表并通过 `router.addRoute` 挂载.
*   **按钮权限**: 自定义指令 `v-permission="['system:user:add']"` 控制按钮显隐.

### 4.2 Axios 封装
*   **请求拦截器**: 统一添加 `Authorization: Bearer <token>` 头.
*   **响应拦截器**:
    *   处理全局错误 (401 未登录 -> 跳转登录, 403 无权限 -> 提示, 500 服务器错误).
    *   统一解包响应数据 (`res.data.data`).

### 4.3 表格组件封装
*   封装通用的 `ProTable` 组件，集成：
    *   分页 (Pagination).
    *   搜索表单 (Search Form).
    *   工具栏 (Toolbar).
    *   列配置 (Column Config).
    *   加载状态 (Loading).

## 5. 打印功能开发规范 (Printing)

本系统涉及多个业务单据的打印（如：采购订单、入库单、对账单）。为了避免“牵一发而动全身”的样式污染，必须遵循以下原则：

### 5.1 独立组件，独立样式
*   **禁止共用**: 严禁创建一个通用的 `PrintTemplate.vue` 来处理所有单据。
*   **独立文件**: 每个打印业务必须有独立的 Vue 组件。
    *   `PurchaseOrderPrint.vue`
    *   `InboundOrderPrint.vue`
    *   `ReconciliationPrint.vue`
*   **样式隔离**: 必须使用 `<style scoped>` 或 CSS Modules，确保打印样式只在当前组件生效。

### 5.2 打印实现方案
*   推荐使用 `print-js` 或 `vue-print-nb` 插件。
*   **CSS 媒体查询**: 在组件样式中显式定义 `@media print` 规则。
    ```css
    @media print {
      .no-print { display: none; }
      .print-container { width: 100%; font-size: 12pt; }
      /* 强制背景色打印 */
      body { -webkit-print-color-adjust: exact; }
    }
    ```

### 5.3 模板复用原则
*   如果确实有公共部分（如公司 Header/Logo），可以提取为 `PrintHeader.vue` **子组件**。
*   但**主体表格结构**和**排版样式**必须在各自的父组件中独立定义，**禁止**将主体结构提取为公共组件。

## 6. UI 设计风格
*   **布局**: 采用经典的左侧侧边栏 + 顶部导航栏布局 (`LayoutVertical`).
*   **主题**: 默认蓝白色系，支持暗黑模式切换.
*   **交互**: 尽量使用弹窗 (`Dialog`) 或抽屉 (`Drawer`) 进行表单编辑，避免频繁跳转页面.
