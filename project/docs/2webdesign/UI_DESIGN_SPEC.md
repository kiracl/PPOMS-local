# PPOMS Web系统 - UI/UX 设计规范 (V1.0)

## 0. 设计哲学 (Design Philosophy)

**拒绝“古董级”ERP界面**。系统界面必须紧跟现代 Web 设计趋势，追求 **“轻量、通透、微质感”** 的视觉体验。

*   **扁平化 (Flat)**: 去除多余的渐变、阴影和纹理，强调内容本身。
*   **留白 (Whitespace)**: 增加内容间距，避免信息过载，提升阅读舒适度。
*   **圆角 (Rounded)**: 统一使用圆角设计，传递亲和力，减少工业软件的生硬感。
*   **微交互 (Micro-interactions)**: 在悬停、点击、加载时提供细腻的动效反馈。

**参考标杆**: Arco Design Pro, Ant Design Pro, TDesign.

## 1. 色彩系统 (Color System)

基于 Element Plus 默认色板进行现代化微调。

### 1.1 品牌色 (Brand Colors)
*   **Primary (主色)**: `#1677FF` (Tech Blue) - 比默认 Element Blue 更深邃、更具科技感的蓝色。
    *   *Hover*: `#4096FF`
    *   *Active*: `#0958D9`
*   **Success (成功)**: `#52C41A` (Vibrant Green)
*   **Warning (警告)**: `#FAAD14` (Warm Gold)
*   **Danger (危险)**: `#FF4D4F` (Soft Red) - 避免刺眼的纯红。

### 1.2 中性色 (Neutrals)
*   **主要文字**: `#1F1F1F` (近黑) - 提升对比度。
*   **常规文字**: `#434343`
*   **次要文字**: `#8C8C8C`
*   **失效文字**: `#BFBFBF`
*   **边框颜色**: `#D9D9D9` (浅灰)
*   **背景颜色**: `#F0F2F5` (极淡冷灰) - 用于页面大背景，与白色卡片形成层次。

## 2. 字体排版 (Typography)

*   **Font Family**: 优先使用无衬线字体，特定数字/代码使用等宽字体。
    *   `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';`

### 2.1 字号层级 (Modern Scale)
*   **Header 1 (页面标题)**: `24px`, Weight 600, Line Height 32px.
*   **Header 2 (区块标题)**: `18px`, Weight 600, Line Height 26px.
*   **Body (正文)**: `14px`, Weight 400, Line Height 22px.
*   **Small (辅助)**: `12px`, Weight 400, Line Height 20px.

## 3. 布局与容器 (Layout & Container)

### 3.1 卡片式设计 (Card Design)
*   **风格**: 所有内容区块（搜索栏、表格、表单）必须包裹在白色卡片中。
*   **圆角**: 统一 `border-radius: 8px`。
*   **阴影**: 默认无阴影或极淡阴影 (`box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03)`), Hover 时可加深。
*   **内边距**: 统一 `padding: 24px`。

### 3.2 间距 (Spacing)
拒绝拥挤。统一使用 `8px` 网格系统：
*   **xs**: `8px` (组件内)
*   **sm**: `16px` (组件间)
*   **md**: `24px` (区块间)
*   **lg**: `32px` (大模块间)

### 3.3 页面结构模板
所有业务页面统一采用 **“ProTable”** 布局结构：

1.  **Page Header (页头)**:
    *   白色背景，包含面包屑、页面标题、核心操作按钮（如“返回”）。
    *   高度 `64px`，底部带 1px 分割线。
2.  **Content Area (内容区)**:
    *   背景色 `#F0F2F5`，内边距 `24px`。
    *   **Filter Card (筛选区)**: 白色卡片，表单项 Label 对齐，Input 宽度统一。
    *   **Data Card (数据区)**: 白色卡片，上方是 Toolbar（左侧标题/按钮，右侧工具），下方是表格。

## 4. 组件风格 (Component Style)

### 4.1 按钮 (Buttons)
*   **圆角**: `border-radius: 6px` (微圆角，比半圆更现代)。
*   **高度**: `32px` (Default), `24px` (Small), `40px` (Large)。
*   **阴影**: Primary 按钮带微弱阴影，增加立体感。

### 4.2 表格 (Table)
*   **表头**: 背景色 `#FAFAFA` (极淡灰)，字体加粗。
*   **行高**: `54px` (宽松模式)，避免密密麻麻的 Excel 感。
*   **Hover**: 行悬停背景色 `#E6F7FF` (淡蓝)。
*   **操作列**: 图标按钮 (Icon Button) 代替文字链接，或使用“更多”下拉菜单。

### 4.3 表单 (Forms)
*   **输入框**:
    *   高度 `32px`。
    *   `border-radius: 6px`。
    *   Hover 时边框变蓝，Focus 时带淡蓝光晕 (`box-shadow`).
*   **对齐**: Label 右对齐，`color: #606266`。

### 4.4 弹窗 (Dialog/Modal)
*   **遮罩**: 模糊背景 (`backdrop-filter: blur(4px)`)，增加高级感。
*   **圆角**: `border-radius: 12px`。
*   **头部**: 简洁标题，无底色。
*   **底部**: 按钮右对齐。

## 5. 交互与动效 (Animation)

*   **过渡**: 任何状态变化（Hover, Modal Open, Tab Switch）必须有 `transition: all 0.3s cubic-bezier(...)`。
*   **加载**: 使用骨架屏 (Skeleton) 代替简单的 Loading 转圈，减少等待焦虑。
*   **反馈**: 操作成功时，除了 Message 提示，最好伴随轻微的元素状态变化（如按钮变绿）。

## 6. 移动端适配 (Responsive)
*   虽然主要是 PC 端系统，但必须支持 **1280px** 以上分辨率无横向滚动条。
*   在小屏幕下，表格自动开启横向滚动，搜索栏自动折叠。

