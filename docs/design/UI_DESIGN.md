# AI Daily Brief - UI 设计规范

## 项目概述

- **产品名称**: AI Daily Brief（AI 每日简报）
- **目标用户**: AI 研究者、开发者
- **设计风格**: 深色科技风、简洁高效、信息密度优先
- **设计理念**: 专业、高效、沉浸式阅读体验

---

## 1. 配色方案

### 1.1 核心色板

基于现有深色主题进行扩展，采用深蓝色调为主基调，营造专业科技感。

```
主色系 (Primary)
├── Primary-900    #0f172a    页面主背景
├── Primary-800    #1e1b4b    页面次背景、渐变终点
├── Primary-700    #1e293b    卡片背景（悬停态）
├── Primary-600    #334155    边框、分隔线
└── Primary-500    #475569    禁用状态

辅色系 (Secondary)
├── Secondary-50   #f8fafc    主文字
├── Secondary-100   #f1f5f9    标题文字
├── Secondary-200   #e2e8f0    次级标题
├── Secondary-300   #cbd5e1    正文文字
├── Secondary-400   #94a3b8    辅助文字
└── Secondary-500   #64748b    占位文字

强调色系 (Accent)
├── Accent-Main     #38bdf8    主强调色（链接、高亮）
├── Accent-Hover    #0ea5e9    链接悬停
├── Accent-Light    #7dd3fc    强调背景
└── Accent-Glow     rgba(56, 189, 248, 0.15)    发光效果

状态色系 (Status)
├── Success         #22c55e    成功状态
├── Warning         #f59e0b    警告状态
├── Error           #ef4444    错误状态
└── Info            #3b82f6    信息状态
```

### 1.2 语义化配色映射

| 用途 | 变量名 | 色值 | 说明 |
|------|--------|------|------|
| 页面背景 | `--bg-page` | `#0f172a` | 主背景色 |
| 容器背景 | `--bg-container` | `rgba(255,255,255,0.03)` | 卡片/容器背景 |
| 卡片背景 | `--bg-card` | `rgba(255,255,255,0.05)` | 卡片默认背景 |
| 卡片悬停 | `--bg-card-hover` | `rgba(255,255,255,0.08)` | 卡片悬停态 |
| 主文字 | `--text-primary` | `#f8fafc` | 标题、重要文字 |
| 次文字 | `--text-secondary` | `#94a3b8` | 正文、描述文字 |
| 辅助文字 | `--text-muted` | `#64748b` | 时间、标签等 |
| 链接 | `--color-link` | `#38bdf8` | 可点击链接 |
| 链接悬停 | `--color-link-hover` | `#0ea5e9` | 链接交互态 |
| 边框 | `--border-default` | `rgba(255,255,255,0.1)` | 默认边框 |
| 边框高亮 | `--border-highlight` | `rgba(56,189,248,0.3)` | 焦点边框 |

---

## 2. 卡片式简报列表布局

### 2.1 卡片组件结构

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ TAG                                           2024-01-15 │ │ ← 元信息行
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Claude 3.5 Sonnet 发布，性能超越 GPT-4o                   │ │ ← 标题
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Anthropic 发布 Claude 3.5 Sonnet，在多项基准测试中...    │ │ ← 摘要（2行截断）
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 阅读全文 →                                      5 min read│ │ ← 操作行
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 卡片样式规范

```css
/* 卡片容器 */
.brief-card {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s ease;
}

.brief-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-highlight);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

/* 元信息行 */
.brief-card__meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-default);
}

.brief-card__tag {
    font-size: 12px;
    padding: 4px 8px;
    background: var(--Accent-Glow);
    color: var(--color-link);
    border-radius: 4px;
}

.brief-card__date {
    font-size: 13px;
    color: var(--text-muted);
}

/* 标题 */
.brief-card__title {
    padding: 16px;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.4;
    color: var(--text-primary);
}

/* 摘要 */
.brief-card__summary {
    padding: 0 16px 16px;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* 操作行 */
.brief-card__actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-top: 1px solid var(--border-default);
    background: rgba(0, 0, 0, 0.2);
}

.brief-card__link {
    color: var(--color-link);
    font-size: 14px;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.brief-card__link:hover {
    color: var(--color-link-hover);
}

.brief-card__read-time {
    font-size: 12px;
    color: var(--text-muted);
}
```

### 2.3 列表布局

```css
/* 列表容器 */
.brief-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    padding: 20px 0;
}

/* 列表头部 */
.brief-list__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-default);
}

.brief-list__title {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
}

.brief-list__count {
    font-size: 14px;
    color: var(--text-muted);
}
```

---

## 3. 字体层级与间距规范

### 3.1 字体层级

```
字体族
├── 中文: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"
├── 英文: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto
└── 等宽: "SF Mono", "Fira Code", Consolas, monospace

字号层级
├── Display    48px / 3rem      页面大标题（首页Hero）
├── H1         32px / 2rem      页面主标题
├── H2         24px / 1.5rem    区块标题
├── H3         20px / 1.25rem   卡片标题
├── H4         18px / 1.125rem  小标题
├── Body-L     16px / 1rem      大正文
├── Body-M     14px / 0.875rem  标准正文
├── Body-S     13px / 0.8125rem 辅助正文
├── Caption    12px / 0.75rem   标签、时间戳
└── Overline   11px / 0.6875rem 上标、徽章

字重
├── Regular    400    正文
├── Medium     500    小标题
├── Semibold   600    标题
└── Bold       700    强调标题

行高
├── Tight      1.25   标题
├── Normal     1.5    正文
└── Relaxed    1.75   长文本阅读
```

### 3.2 间距系统

采用 4px 基准网格，使用 8 点系统。

```
间距变量
├── --space-1    4px     极小间距
├── --space-2    8px     元素内间距（紧凑）
├── --space-3    12px    元素内间距（标准）
├── --space-4    16px    组件内边距
├── --space-5    20px    列表项间距
├── --space-6    24px    区块内边距
├── --space-8    32px    区块间距
├── --space-10   40px    区块间距（大）
├── --space-12   48px    页面边距
└── --space-16   64px    页面区块间距

组件内边距映射
├── Card Padding        var(--space-4)     16px
├── Section Padding     var(--space-6)     24px
├── Page Padding        var(--space-4)     16px (移动端)
│                       var(--space-6)     24px (平板)
│                       var(--space-8)     32px (桌面)
└── Container Max-width 1200px
```

### 3.3 CSS 变量定义

```css
:root {
    /* ========== 配色系统 ========== */
    /* 背景 */
    --bg-page: #0f172a;
    --bg-page-secondary: #1e1b4b;
    --bg-container: rgba(255, 255, 255, 0.03);
    --bg-card: rgba(255, 255, 255, 0.05);
    --bg-card-hover: rgba(255, 255, 255, 0.08);
    --bg-elevated: rgba(30, 41, 59, 0.8);

    /* 文字 */
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --text-inverse: #0f172a;

    /* 强调色 */
    --color-accent: #38bdf8;
    --color-accent-hover: #0ea5e9;
    --color-accent-light: #7dd3fc;
    --color-accent-glow: rgba(56, 189, 248, 0.15);

    /* 链接 */
    --color-link: #38bdf8;
    --color-link-hover: #0ea5e9;
    --color-link-visited: #818cf8;

    /* 状态 */
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    --color-info: #3b82f6;

    /* 边框 */
    --border-default: rgba(255, 255, 255, 0.1);
    --border-subtle: rgba(255, 255, 255, 0.05);
    --border-highlight: rgba(56, 189, 248, 0.3);

    /* ========== 字体系统 ========== */
    --font-family-base: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Segoe UI", Roboto, sans-serif;
    --font-family-mono: "SF Mono", "Fira Code", Consolas, "Liberation Mono", monospace;

    --font-size-xs: 11px;
    --font-size-sm: 12px;
    --font-size-md: 13px;
    --font-size-base: 14px;
    --font-size-lg: 16px;
    --font-size-xl: 18px;
    --font-size-2xl: 20px;
    --font-size-3xl: 24px;
    --font-size-4xl: 32px;
    --font-size-5xl: 48px;

    --font-weight-regular: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    --line-height-tight: 1.25;
    --line-height-normal: 1.5;
    --line-height-relaxed: 1.75;

    /* ========== 间距系统 ========== */
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --space-10: 40px;
    --space-12: 48px;
    --space-16: 64px;

    /* ========== 圆角系统 ========== */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    /* ========== 阴影系统 ========== */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.25);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.3);
    --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.35);
    --shadow-glow: 0 0 20px var(--color-accent-glow);

    /* ========== 动效系统 ========== */
    --transition-fast: 150ms ease;
    --transition-normal: 200ms ease;
    --transition-slow: 300ms ease;

    /* ========== 布局系统 ========== */
    --container-max-width: 1200px;
    --container-padding: var(--space-4);
    --header-height: 64px;
    --sidebar-width: 280px;

    /* ========== Z-Index 层级 ========== */
    --z-dropdown: 100;
    --z-sticky: 200;
    --z-fixed: 300;
    --z-modal-backdrop: 400;
    --z-modal: 500;
    --z-popover: 600;
    --z-tooltip: 700;
}
```

---

## 4. 响应式断点方案

### 4.1 断点定义

采用移动优先（Mobile First）设计策略。

```css
/* 断点变量（CSS Custom Properties 用于 JS 读取） */
:root {
    --breakpoint-sm: 640px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 1024px;
    --breakpoint-xl: 1280px;
    --breakpoint-2xl: 1536px;
}

/* 媒体查询 Mixin（SCSS 语法参考） */
// 移动设备（默认，无需媒体查询）
// 小屏手机
@mixin mobile {
    @media (max-width: 639px) { @content; }
}

// 大屏手机 /小平板
@mixin sm {
    @media (min-width: 640px) { @content; }
}

// 平板竖屏
@mixin md {
    @media (min-width: 768px) { @content; }
}

// 平板横屏 / 小笔记本
@mixin lg {
    @media (min-width: 1024px) { @content; }
}

// 桌面显示器
@mixin xl {
    @media (min-width: 1280px) { @content; }
}

// 大屏显示器
@mixin 2xl {
    @media (min-width: 1536px) { @content; }
}
```

### 4.2 响应式布局规范

| 断点 | 名称 | 宽度范围 | 栅格列数 | 容器宽度 | 边距 | 用途 |
|------|------|----------|----------|----------|------|------|
| xs | 超小屏 | < 640px | 4列 | 100% | 16px | 手机 |
| sm | 小屏 | 640-767px | 4列 | 100% | 20px | 大手机 |
| md | 中屏 | 768-1023px | 8列 | 100% | 24px | 平板竖屏 |
| lg | 大屏 | 1024-1279px | 12列 | 1000px | 24px | 平板横屏 |
| xl | 超大屏 | 1280-1535px | 12列 | 1200px | 32px | 桌面 |
| 2xl | 超超大屏 | >= 1536px | 12列 | 1400px | 32px | 大屏显示器 |

### 4.3 组件响应式示例

```css
/* 卡片列表响应式 */
.brief-list {
    display: grid;
    gap: var(--space-4);
    grid-template-columns: 1fr; /* 默认单列 */
}

/* 小屏手机：单列 */
@media (min-width: 640px) {
    .brief-list {
        grid-template-columns: repeat(2, 1fr); /* 双列 */
    }
}

/* 平板：双列 */
@media (min-width: 768px) {
    .brief-list {
        grid-template-columns: repeat(2, 1fr);
        gap: var(--space-5);
    }
}

/* 桌面：三列 */
@media (min-width: 1024px) {
    .brief-list {
        grid-template-columns: repeat(3, 1fr);
        gap: var(--space-6);
    }
}

/* 大屏：四列 */
@media (min-width: 1280px) {
    .brief-list {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* 页面容器响应式 */
.container {
    width: 100%;
    max-width: var(--container-max-width);
    margin: 0 auto;
    padding: 0 var(--space-4); /* 移动端 16px */
}

@media (min-width: 768px) {
    .container {
        padding: 0 var(--space-6); /* 平板 24px */
    }
}

@media (min-width: 1024px) {
    .container {
        padding: 0 var(--space-8); /* 桌面 32px */
    }
}

/* 字体响应式 */
.page-title {
    font-size: var(--font-size-3xl); /* 24px 移动端 */
}

@media (min-width: 768px) {
    .page-title {
        font-size: var(--font-size-4xl); /* 32px 平板 */
    }
}

@media (min-width: 1024px) {
    .page-title {
        font-size: var(--font-size-5xl); /* 48px 桌面 */
    }
}

/* 导航栏响应式 */
.nav {
    height: 56px; /* 移动端高度 */
    padding: 0 var(--space-4);
}

@media (min-width: 768px) {
    .nav {
        height: var(--header-height); /* 64px 桌面高度 */
        padding: 0 var(--space-6);
    }
}

/* 移动端隐藏/显示工具类 */
.hide-mobile {
    display: none;
}

@media (min-width: 768px) {
    .hide-mobile {
        display: block;
    }
}

.show-mobile {
    display: block;
}

@media (min-width: 768px) {
    .show-mobile {
        display: none;
    }
}
```

---

## 5. 组件库扩展

### 5.1 标签组件

```css
.tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    border-radius: var(--radius-full);
    transition: all var(--transition-fast);
}

/* 标签变体 */
.tag--default {
    background: var(--bg-card);
    color: var(--text-secondary);
    border: 1px solid var(--border-default);
}

.tag--primary {
    background: var(--color-accent-glow);
    color: var(--color-accent);
}

.tag--success {
    background: rgba(34, 197, 94, 0.15);
    color: var(--color-success);
}

.tag--warning {
    background: rgba(245, 158, 11, 0.15);
    color: var(--color-warning);
}

.tag--error {
    background: rgba(239, 68, 68, 0.15);
    color: var(--color-error);
}
```

### 5.2 按钮组件

```css
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-3) var(--space-4);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    border-radius: var(--radius-md);
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* 按钮变体 */
.btn--primary {
    background: var(--color-accent);
    color: var(--text-inverse);
}

.btn--primary:hover:not(:disabled) {
    background: var(--color-accent-hover);
}

.btn--secondary {
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-default);
}

.btn--secondary:hover:not(:disabled) {
    background: var(--bg-card-hover);
    border-color: var(--border-highlight);
}

.btn--ghost {
    background: transparent;
    color: var(--text-secondary);
}

.btn--ghost:hover:not(:disabled) {
    background: var(--bg-card);
    color: var(--text-primary);
}

/* 按钮尺寸 */
.btn--sm {
    padding: var(--space-2) var(--space-3);
    font-size: var(--font-size-sm);
}

.btn--lg {
    padding: var(--space-4) var(--space-6);
    font-size: var(--font-size-lg);
}
```

### 5.3 输入框组件

```css
.input {
    width: 100%;
    padding: var(--space-3) var(--space-4);
    font-size: var(--font-size-base);
    font-family: inherit;
    color: var(--text-primary);
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
}

.input::placeholder {
    color: var(--text-muted);
}

.input:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 3px var(--color-accent-glow);
}

.input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* 输入框尺寸 */
.input--sm {
    padding: var(--space-2) var(--space-3);
    font-size: var(--font-size-sm);
}

.input--lg {
    padding: var(--space-4) var(--space-5);
    font-size: var(--font-size-lg);
}
```

### 5.4 骨架屏加载

```css
.skeleton {
    background: linear-gradient(
        90deg,
        var(--bg-card) 25%,
        var(--bg-card-hover) 50%,
        var(--bg-card) 75%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: var(--radius-md);
}

@keyframes skeleton-loading {
    0% {
        background-position: 200% 0;
    }
    100% {
        background-position: -200% 0;
    }
}

/* 骨架屏组件 */
.skeleton-card {
    height: 200px;
}

.skeleton-title {
    height: 24px;
    width: 70%;
    margin-bottom: var(--space-3);
}

.skeleton-text {
    height: 16px;
    width: 100%;
    margin-bottom: var(--space-2);
}

.skeleton-text--short {
    width: 60%;
}
```

---

## 6. 深色模式适配说明

当前设计为纯深色主题，后续如需支持浅色模式，建议采用以下方案：

```css
/* 浅色模式变量覆盖 */
@media (prefers-color-scheme: light) {
    :root {
        --bg-page: #ffffff;
        --bg-page-secondary: #f8fafc;
        --bg-container: rgba(0, 0, 0, 0.02);
        --bg-card: rgba(0, 0, 0, 0.03);
        --bg-card-hover: rgba(0, 0, 0, 0.05);

        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;

        --color-accent: #0ea5e9;
        --color-accent-hover: #0284c7;

        --border-default: rgba(0, 0, 0, 0.1);
        --border-highlight: rgba(14, 165, 233, 0.3);
    }
}
```

---

## 7. 设计文件清单

| 文件 | 用途 | 格式 |
|------|------|------|
| `variables.css` | CSS 变量定义 | CSS |
| `reset.css` | 样式重置 | CSS |
| `typography.css` | 字体排版 | CSS |
| `components.css` | 组件样式 | CSS |
| `utilities.css` | 工具类 | CSS |

---

## 8. 设计资源

- **图标库**: Lucide Icons / Heroicons（线性风格）
- **字体**: 系统原生字体栈，无需额外加载
- **配色工具**: Tailwind CSS Color Palette
- **设计参考**: GitHub Dark / Linear / Vercel Dashboard

---

*文档版本: 1.0.0*
*最后更新: 2024-01-15*