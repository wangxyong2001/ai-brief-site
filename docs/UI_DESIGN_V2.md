# AI Daily Brief v4 - UI Design Specification V2

## Executive Summary

This document defines the visual and interaction design for AI Daily Brief v4, featuring:
- Rich design aesthetics beyond generic templates
- Article detail pages with LLM-processed Chinese content
- Category-based navigation system
- Dark/Light mode with smooth transitions
- Interactive filtering and search capabilities
- Mobile-first responsive design

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Information Density** | Maximize content value per screen area - users want quick AI news scanning |
| **Visual Hierarchy** | Clear distinction between primary content, navigation, and metadata |
| **Progressive Disclosure** | Summary first, detail on demand - click to expand full article |
| **Ambient Feedback** | Subtle hover states, loading indicators, success confirmations |
| **Brand Consistency** | Deep blue tech aesthetic with cyan accent - AI/tech domain signal |

### 1.2 Target Experience

```
User Journey Flow:
─────────────────────────────────────────────────────────
Landing → Browse Categories → Scan Articles → Click Detail → Read Chinese Summary → Navigate Back
   │            │                  │              │                │                  │
   ▼            ▼                  ▼              ▼                ▼                  ▼
Welcome    Filter by        Card preview   Full-page modal   LLM-processed    Return to
message    interest         + metadata     with animations   Chinese content   browsing
─────────────────────────────────────────────────────────
```

---

## 2. Enhanced Color Palette

### 2.1 Dark Mode (Primary Theme)

```
DARK MODE COLOR SYSTEM
═══════════════════════════════════════════════════════════

BACKGROUND LAYERS (Depth hierarchy)
├── --bg-deep          #0a0f1a      Page root (deepest)
├── --bg-page          #0f172a      Main viewport background
├──── --bg-gradient-1    linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)
├── --bg-elevated      #1e293b      Header, modals, dropdowns
├── --bg-card          rgba(255,255,255,0.04)   Card surfaces
├── --bg-card-hover    rgba(255,255,255,0.08)   Interactive hover
├── --bg-subtle        rgba(56,189,248,0.06)    Accent tinted areas
│
SURFACE TEXTURES (Optional enhancement)
├── --noise-overlay    url('data:image/svg+xml,...')   Subtle grain texture
├── --glass-blur       blur(12px)   Frosted glass effect
│
TEXT COLORS
├── --text-primary     #f8fafc      Headlines, article titles
├── --text-secondary   #e2e8f0      Body text, summaries
├──--text-muted        #94a3b8      Metadata, timestamps, tags
├── --text-accent      #38bdf8      Highlighted keywords
├── --text-inverse     #0f172a      Text on accent backgrounds
│
ACCENT SYSTEM (Brand identity)
├── --accent-primary   #38bdf8      Primary action color (cyan)
├── --accent-secondary #a78bfa      Secondary accent (purple gradient partner)
├── --accent-gradient  linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%)
├── --accent-glow      rgba(56,189,248,0.25)   Glow/shadow effect
├── --accent-pulse     rgba(56,189,248,0.4)   Active/pulsing state
│
CATEGORY COLORS (Semantic differentiation)
├── --cat-product      #f472b6      产品动态 - Pink/Rose
├── --cat-open-source  #22c55e      开源项目 - Green/Emerald
├── --cat-research     #8b5cf6      学术研究 - Purple/Violet
├── --cat-industry     #f59e0b      行业新闻 - Amber/Orange
│
STATUS COLORS
├── --status-success   #10b981      Success actions
├── --status-warning   #f59e0b      Warnings
├── --status-error     #ef4444      Errors
├── --status-loading   #38bdf8      Loading indicator
│
INTERACTIVE STATES
├── --border-default   rgba(255,255,255,0.08)   Default border
├── --border-subtle    rgba(255,255,255,0.04)   Minimal separation
├── --border-focus     rgba(56,189,248,0.5)    Focus ring
├── --border-active    rgba(56,189,248,0.3)    Active selection
```

### 2.2 Light Mode (Alternative Theme)

```
LIGHT MODE COLOR SYSTEM
═══════════════════════════════════════════════════════════

BACKGROUND LAYERS
├── --bg-deep          #f8fafc      Page root
├── --bg-page          #ffffff      Main viewport
├── --bg-gradient-1    linear-gradient(135deg, #ffffff 0%, #f1f5f9 50%, #ffffff 100%)
├── --bg-elevated      #ffffff      Header, modals
├── --bg-card          rgba(15,23,42,0.03)    Card surfaces
├── --bg-card-hover    rgba(15,23,42,0.06)    Interactive hover
│
TEXT COLORS
├── --text-primary     #0f172a      Headlines
├── --text-secondary   #334155      Body text
├── --text-muted       #64748b      Metadata
├── --text-accent      #0ea5e9      Highlighted keywords
│
ACCENT SYSTEM
├── --accent-primary   #0ea5e9      Primary action (darker cyan)
├── --accent-secondary #7c3aed      Secondary accent
├── --accent-gradient  linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)
├── --accent-glow      rgba(14,165,233,0.15)   Subtle glow
│
CATEGORY COLORS (Same semantic meaning, adjusted for light)
├── --cat-product      #ec4899      产品动态
├── --cat-open-source  #16a34a      开源项目
├── --cat-research     #7c3aed      学术研究
├── --cat-industry     #d97706      行业新闻
│
BORDERS
├── --border-default   rgba(15,23,42,0.1)
├── --border-subtle    rgba(15,23,42,0.05)
├── --border-focus     rgba(14,165,233,0.4)
```

### 2.3 Theme Transition

```css
/* Smooth theme switching */
:root {
    --theme-transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Apply to all theme-dependent properties */
.theme-dependent {
    transition: 
        background-color var(--theme-transition),
        color var(--theme-transition),
        border-color var(--theme-transition),
        box-shadow var(--theme-transition);
}

/* Theme toggle animation */
.theme-toggle-icon {
    transition: transform 0.5s ease;
}

[data-theme="light"] .theme-toggle-icon {
    transform: rotate(180deg);
}
```

---

## 3. Typography System

### 3.1 Font Stack

```
TYPOGRAPHY FOUNDATION
═══════════════════════════════════════════════════════════

PRIMARY FONT STACK (Chinese + English)
├── Chinese:  "PingFang SC", "Noto Sans SC", "Hiragino Sans GB"
├── English:  "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI"
├── Fallback: Roboto, "Helvetica Neue", Arial, sans-serif
│
MONOSPACE (Code, technical terms)
├── Primary:  "JetBrains Mono", "Fira Code"
├── Fallback: "SF Mono", Consolas, "Liberation Mono", monospace
│
DISPLAY (Optional: Hero headlines)
├── Primary:  "Space Grotesk"  (distinctive, tech-feel)
├── Fallback: "Inter", system fonts
```

### 3.2 Type Scale

```
TYPE SCALE (8-level hierarchy)
═══════════════════════════════════════════════════════════

Level    Size    Weight    Line Height    Usage
─────────────────────────────────────────────────────────────
Display  48px    700       1.1            Hero section title
H1       32px    600       1.2            Page titles
H2       24px    600       1.3            Section headers
H3       20px    500       1.4            Card titles, sub-sections
H4       18px    500       1.4            Small headings
Body-L   16px    400       1.6            Article body, large text
Body-M   14px    400       1.6            Default body text
Body-S   13px    400       1.5            Secondary text, descriptions
Caption  12px    400       1.4            Tags, timestamps, metadata
Micro    11px    500       1.3            Overlines, badges
```

### 3.3 Article Detail Typography

```
ARTICLE CONTENT TYPOGRAPHY
═══════════════════════════════════════════════════════════

Article Title (Chinese processed)
├── Font:      Display font or H1
├── Size:      28-32px responsive
├── Weight:    600-700
├── Color:     --text-primary
├── Spacing:   0.02em letter-spacing for Chinese
│
Section Headers (within article)
├── H2:        20px, 600, --accent-primary color
├── H3:        16px, 500, --text-primary
├── Margin:    24px top, 12px bottom
│
Body Paragraphs
├── Font:      Body-L (16px)
├── Weight:    400
├── Line-height: 1.75 (relaxed for reading)
├── Max-width: 720px (optimal reading width)
├── Margin:    16px between paragraphs
│
Key Points List (核心观点)
├── Style:     Custom bullet with accent color
├── Font:      Body-M (14px)
├── Indent:    20px left
├── Bullet:    Accent-colored dot or number badge
│
Technical Terms
├── Font:      Monospace
├── Size:      0.95em relative
├── Background: --bg-subtle
├── Padding:   2px 6px
├── Border-radius: 4px
│
Source Attribution
├── Font:      Caption (12px)
├── Color:     --text-muted
├── Style:     "原文链接" with arrow icon
```

---

## 4. Layout Wireframes

### 4.1 Homepage Layout (Desktop)

```
═══════════════════════════════════════════════════════════════════════════════
                              AI DAILY BRIEF - HOME PAGE (1280px+)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER (Fixed, 64px height)                                                │
│  ┌─────────┬──────────────────────────────────────────────────┬────────────┐│
│  │ LOGO    │          NAVIGATION                             │   ACTIONS  ││
│  │ AI Brief│  产品动态  开源项目  学术研究  行业新闻          │ 🔍  🌙/☀️  ││
│  │ + icon  │  (category pills, horizontal scroll on mobile)   │            ││
│  └─────┬───┴──────────────────────────────────────────────────┴────────────┘│
│        │ [gradient underline on active category]                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  HERO SECTION (Optional, collapsible)                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  "每日AI动态精选"                                                    │││
│  │  │  2026年5月19日 · 15篇文章 · 由AI整理                                 │││
│  │  │  ─────────────────────────────────────────────────────────────────  │││
│  │  │  [今日精选 TOP 3 cards - horizontal]                                 │││
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐                                       │││
│  │  │  │ #1   │  │ #2   │  │ #3   │  ← Featured/high-score articles       │││
│  │  │  │Card  │  │Card  │  │Card  │                                       │││
│  │  │  └──────┘  └──────┘  └──────┘                                       │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  FILTER BAR                                                             ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  [🔍 搜索框 placeholder="搜索AI动态..."]     [日期选择器] [排序:时间/热度]│││
│  │  │  ┌──────────────────────────────┐  ┌──────────┐  ┌────────────────┐ │││
│  │  │  │ 🔍 搜索AI动态...             │  │ 2026-05-19│  │ 时间 ↓ 最新   │ │││
│  │  │  └──────────────────────────────┘  └──────────┘  └────────────────┘ │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ARTICLE GRID (Main content area)                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                       │││
│  │  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │││
│  │  │   │ ARTICLE CARD    │  │ ARTICLE CARD    │  │ ARTICLE CARD    │     │││
│  │  │   │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │     │││
│  │  │   │ │ [CAT TAG]   │ │  │ │ [CAT TAG]   │ │  │ │ [CAT TAG]   │ │     │││
│  │  │   │ │ 产品动态    │ │  │ │ 开源项目    │ │  │ │ 学术研究    │ │     │││
│  │  │   │ ├─────────────┤ │  │ ├─────────────┤ │  │ ├─────────────┤ │     │││
│  │  │   │ │ TITLE       │ │  │ │ TITLE       │ │  │ │ TITLE       │ │     │││
│  │  │   │ │ Claude 4    │ │  │ │ Ollama 0.5  │ │  │ │ arXiv:新的  │ │     │││
│  │  │   │ │ 发布...     │ │  │ │ 发布...     │ │  │ │ 量化方法... │ │     │││
│  │  │   │ ├─────────────┤ │  │ ├─────────────┤ │  │ ├─────────────┤ │     │││
│  │  │   │ │ SUMMARY     │ │  │ │ SUMMARY     │ │  │ │ SUMMARY     │ │     │││
│  │  │   │ │ 中文摘要    │ │  │ │ 中文摘要    │ │  │ │ 中文摘要    │ │     │││
│  │  │   │ │ 截断2行...  │ │  │ │ 截断2行...  │ │  │ │ 截断2行...  │ │     │││
│  │  │   │ ├─────────────┤ │  │ ├─────────────┤ │  │ ├─────────────┤ │     │││
│  │  │   │ │ META        │ │  │ │ META        │ │  │ │ META        │ │     │││
│  │  │   │ │ 10:30 评分13│ │  │ │ 09:15 评分11│ │  │ │ 08:00 评分9 │ │     │││
│  │  │   │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │     │││
│  │  │   │                 │  │                 │  │                 │     │││
│  │  │   │   hover effect: │  │                 │  │                 │     │││
│  │  │   │   translateY(-4px)                   │  │                 │     │││
│  │  │   │   accent border                     │  │                 │     │││
│  │  │   │                                                                       │││
│  │  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │││
│  │  │   │ ARTICLE CARD    │  │ ARTICLE CARD    │  │ ARTICLE CARD    │     │││
│  │  │   │ ...             │  │ ...             │  │ ...             │     │││
│  │  │   └─────────────────┘  └─────────────────┘  └─────────────────┘     │││
│  │  │                                                                       │││
│  │  │   [Load more / Infinite scroll indicator]                             │││
│  │  │   ──────────────────────────────────────────────────────────────────│││
│  │  │                      ○ 加载更多...                                   │││
│  │  │                                                                       │││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FOOTER                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  AI Daily Brief v4 · Powered by GLM-4 + FastAPI · GitHub · RSS          ││
│  └─────────────────────────────────────────────────────────────────────────┐│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Article Detail Modal/Page

```
═══════════════════════════════════════════════════════════════════════════════
                        ARTICLE DETAIL VIEW (Modal Overlay)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKGROUND: Semi-transparent overlay (--bg-deep with 0.85 opacity)         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  MODAL CONTAINER                                                        ││
│  │  max-width: 800px, centered, glass-blur backdrop                       ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  HEADER                                                              │││
│  │  │  ┌─────────────────────────────────────────────────────────────────┐│││
│  │  │  │  [× 关闭]  [CAT TAG]                              [原文链接 →] ││││
│  │  │  └─────────────────────────────────────────────────────────────────┘│││
│  │  │                                                                       │││
│  │  │  ┌─────────────────────────────────────────────────────────────────┐│││
│  │  │  │  ARTICLE TITLE                                                   ││││
│  │  │  │  ─────────────────────────────────────────────────────────────  ││││
│  │  │  │  Claude 4.0 正式发布：多模态能力全面升级，性能超越GPT-4o          ││││
│  │  │  │  (Chinese title, 28-32px, semibold)                              ││││
│  │  │  │                                                                   ││││
│  │  │  │  2026-05-19 10:30 · Anthropic · 来源: 3个信源                    ││││
│  │  │  │  (metadata row, small, muted color)                              ││││
│  │  │  └─────────────────────────────────────────────────────────────────┘│││
│  │  │                                                                       │││
│  │  │  ┌─────────────────────────────────────────────────────────────────┐│││
│  │  │  │  CONTENT BODY                                                    ││││
│  │  │  │  ─────────────────────────────────────────────────────────────  ││││
│  │  │  │                                                                   ││││
│  │  │  │  ## 核心观点                                                      ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │  ┌─────────────────────────────────────────────────────────────┐││││
│  │  │  │  │  1. Claude 4.0在多项基准测试中超越GPT-4o，特别是在推理任务 │││││
│  │  │  │  │  2. 新增原生多模态能力，支持图像、音频、视频输入           │││││
│  │  │  │  │  3. API价格降低30%，推理速度提升2倍                         │││││
│  │  │  │  └─────────────────────────────────────────────────────────────┘││││
│  │  │  │                                                                   ││││
│  │  │  │  ## 技术要点                                                      ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │  采用新的混合架构，结合稠密检索和稀疏注意力机制...              ││││
│  │  │  │  [技术细节段落]                                                   ││││
│  │  │  │                                                                   ││││
│  │  │  │  ## 应用场景                                                      ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │  - 复杂文档分析                                                   ││││
│  │  │  │  - 多模态内容理解                                                 ││││
│  │  │  │  - 实时语音交互                                                   ││││
│  │  │  │                                                                   ││││
│  │  │  │  ## 行业影响                                                      ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │  Anthropic此举将加剧LLM市场竞争...                               ││││
│  │  │  │                                                                   ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │                                                                   ││││
│  │  │  │  [完整中文摘要段落, 300-500字]                                    ││││
│  │  │  │  Anthropic今日正式发布Claude 4.0...                              ││││
│  │  │  │                                                                   ││││
│  │  │  └─────────────────────────────────────────────────────────────────┘│││
│  │  │                                                                       │││
│  │  │  ┌─────────────────────────────────────────────────────────────────┐│││
│  │  │  │  FOOTER                                                          ││││
│  │  │  │  ───────────────────────────────────────────────────────────────││││
│  │  │  │  [分享] [收藏] [原文链接]                    评分: 13 · AI整理  ││││
│  │  │  └─────────────────────────────────────────────────────────────────┘│││
│  │  │                                                                       │││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Animation: Modal enters with scale(0.95) -> scale(1) + fade-in (300ms)
           Background dims gradually
           Exit: reverse animation
```

### 4.3 Mobile Layout (< 768px)

```
═══════════════════════════════════════════════════════════════════════════════
                        MOBILE VIEW (375px - iPhone baseline)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER (56px, sticky)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  [≡ 菜单]  AI Brief        [🔍]  [🌙]                                   ││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  CATEGORY TABS (Horizontal scroll, pill style)                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  <──scroll──>                                                        │││
│  │  │  [全部] [产品动态] [开源项目] [学术研究] [行业新闻]                  │││
│  │  │  ↑ active tab has accent underline                                  │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  SEARCH BAR (Collapsible, tap to expand)                                ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  [🔍 搜索...]                                                        │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ARTICLE LIST (Single column, card stack)                               ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │                                                                       │││
│  │  │   ┌─────────────────────────────────────────────────────────────────┐│││
│  │  │   │  ARTICLE CARD (Full width)                                       ││││
│  │  │   │  ┌─────────────────────────────────────────────────────────────┐││││
│  │  │   │  │  [产品动态]                              2026-05-19          │││││
│  │  │   │  │  ───────────────────────────────────────────────────────────│││││
│  │  │   │  │  Claude 4.0 正式发布：多模态能力全面升级...                  │││││
│  │  │   │  │  ───────────────────────────────────────────────────────────│││││
│  │  │   │  │  Anthropic今日正式发布Claude 4.0，在多项基准测试中...       │││││
│  │  │   │  │  (中文摘要，截断3行)                                          │││││
│  │  │   │  │  ───────────────────────────────────────────────────────────│││││
│  │  │   │  │  ↗ 查看全文                              评分 13 · 10:30    │││││
│  │  │   │  └─────────────────────────────────────────────────────────────┘││││
│  │  │   │                                                                   │││
│  │  │   │   ┌─────────────────────────────────────────────────────────────┐││││
│  │  │   │   │  ARTICLE CARD                                                ││││
│  │  │   │   │  ...                                                         ││││
│  │  │   │   └─────────────────────────────────────────────────────────────┘│││
│  │  │   │                                                                   │││
│  │  │   │   ┌─────────────────────────────────────────────────────────────┐│││
│  │  │   │   │  ARTICLE CARD                                                ││││
│  │  │   │   │  ...                                                         ││││
│  │  │   │   └─────────────────────────────────────────────────────────────┘│││
│  │  │   │                                                                   │││
│  │  │   │   [Load more button]                                             │││
│  │  │   │   ──────────────────────────────────────────────────────────────│││
│  │  │   │                        [加载更多 ↓]                              │││
│  │  │   │                                                                   │││
│  │  │   └─────────────────────────────────────────────────────────────────┐││
│  │  │                                                                       │││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  FOOTER (Minimal, 48px)                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  v4 · GLM-4 · GitHub                                                 │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Mobile Detail View (Full screen slide-in):

┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  HEADER (Sticky)                                                        ││
│  │  [← 返回]  文章详情                                                     ││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  [产品动态]                                                              ││
│  │  ───────────────────────────────────────────────────────────────────────││
│  │  Claude 4.0 正式发布...                                                  ││
│  │  2026-05-19 10:30                                                        ││
│  │                                                                          ││
│  │  ───────────────────────────────────────────────────────────────────────││
│  │                                                                          ││
│  │  ## 核心观点                                                              ││
│  │  1. ...                                                                  ││
│  │  2. ...                                                                  ││
│  │  3. ...                                                                  ││
│  │                                                                          ││
│  │  ## 技术要点                                                              ││
│  │  ...                                                                     ││
│  │                                                                          ││
│  │  [Full content scrollable]                                               ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  FIXED BOTTOM BAR                                                       ││
│  │  [分享] [收藏]                              [原文链接 →]                ││
│  └─────────────────────────────────────────────────────────────────────────┐│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Animation: Slide in from right (translateX 100% -> 0, 300ms ease-out)
```

---

## 5. Component Specifications

### 5.1 Article Card Component

```
ARTICLE CARD SPECIFICATION
═════════════════════════════════════════════════════════════

Structure:
┌─────────────────────────────────────────┐
│ [CATEGORY TAG]              [DATE TIME] │  Meta row
├─────────────────────────────────────────┤
│ Title (1-2 lines, truncate)             │  Title
├─────────────────────────────────────────┤
│ Summary (Chinese, 2-3 lines truncate)   │  Summary
├─────────────────────────────────────────┤
│ [View Full ↗]      [Score] · [Source]   │  Action row
└─────────────────────────────────────────┘

Dimensions (Desktop):
├── Width:      320-380px (grid responsive)
├── Height:     180-220px (auto based on content)
├── Padding:    16px internal
├── Border-radius: 12px
├── Border:     1px solid --border-default

Dimensions (Mobile):
├── Width:      100% - 32px margins
├── Padding:    16px
├── Border-radius: 8px

Interactive States:
├── Default:    Base card appearance
├── Hover:      
│   ├── translateY(-4px)
│   ├── border-color: --border-active
│   ├── box-shadow: --shadow-lg + --accent-glow
│   ├── cursor: pointer
│   └── transition: 200ms ease
│
├── Active/Click:
│   ├── scale(0.98) briefly
│   ├── then navigate to detail
│
├── Loading:
│   ├── Skeleton placeholders
│   ├── shimmer animation
│
├── Error:
│   ├── Dashed border
│   ├── Error icon + message
│   ├── Retry button

Category Tag Colors:
├── 产品动态:   background: rgba(244,114,182,0.15)  color: #f472b6
├── 开源项目:   background: rgba(34,197,94,0.15)    color: #22c55e
├── 学术研究:   background: rgba(139,92,246,0.15)   color: #8b5cf6
├── 行业新闻:   background: rgba(245,158,11,0.15)   color: #f59e0b
```

### 5.2 Category Navigation Component

```
CATEGORY NAVIGATION SPECIFICATION
═════════════════════════════════════════════════════════════

Desktop Layout (Horizontal pills):
┌─────────────────────────────────────────────────────────────────┐
│  [全部]  [产品动态]  [开源项目]  [学术研究]  [行业新闻]          │
│    ↑        ↑          ↑          ↑          ↑                  │
│  active   pill      pill       pill       pill                  │
│  accent   style     style      style      style                  │
│  underline                                                        │
└─────────────────────────────────────────────────────────────────┘

Pill Style:
├── Height:         36px
├── Padding:        8px 16px
├── Border-radius:  18px (rounded pill)
├── Font-size:      14px
├── Font-weight:    500
├── Gap:            12px between pills
│
States:
├── Default:
│   ├── background: transparent
│   ├── color: --text-secondary
│   ├── border: none
│
├── Hover:
│   ├── background: --bg-card
│   ├── color: --text-primary
│
├── Active:
│   ├── background: --accent-glow (category color tint)
│   ├── color: category-specific color
│   ├── border-bottom: 2px solid category-color (optional)
│   └── indicator dot: category color

Mobile Layout (Horizontal scroll):
┌─────────────────────────────────────────┐
│  <─scrollable container───────────────> │
│  [全部][产品][开源][学术][行业]          │
│   ↑ compact labels for mobile           │
└─────────────────────────────────────────┘

Mobile Pill Style:
├── Height:         32px
├── Padding:        6px 12px
├── Font-size:      13px
├── Scroll indicator: fade gradients on edges
```

### 5.3 Search Component

```
SEARCH COMPONENT SPECIFICATION
═════════════════════════════════════════════════════════════

Desktop (Inline in filter bar):
┌─────────────────────────────────────────────────────────────────┐
│  [🔍]  搜索AI动态...                                      [×] │
│        ↑ placeholder text         ↑ clear button (on input)    │
└─────────────────────────────────────────────────────────────────┘

Dimensions:
├── Width:      300-400px
├── Height:     40px
├── Padding:    12px 16px
├── Border-radius: 8px

Features:
├── Real-time filtering (debounced 300ms)
├── Clear button appears on input
├── Focus state: border-highlight + glow
├── Search icon: left-aligned, subtle
├── Placeholder: "搜索AI动态..."

Mobile (Collapsible):
├── Default: Compact icon button [🔍]
├── Tapped: Expands to full-width search bar
├── Animation: width 40px -> 100%, 200ms
├── backdrop: slight dim on expansion

Search Results Dropdown (Optional):
┌─────────────────────────────────────────┐
│  [🔍] Claude                             │
├─────────────────────────────────────────┤
│  Results:                                │
│  ┌─────────────────────────────────────┐│
│  │ Claude 4.0 发布...          产品    ││
│  │ Claude API 更新...          产品    ││
│  │ Claude vs GPT-4o 对比...    研究    ││
│  └─────────────────────────────────────┘│
│  [查看全部结果 →]                        │
└─────────────────────────────────────────┘
```

### 5.4 Date Picker Component

```
DATE PICKER SPECIFICATION
═════════════════════════════════════════════════════════════

Desktop (Dropdown calendar):
┌─────────────────────────────────────────┐
│  [📅]  2026-05-19              ↓        │
│        ↑ current date  ↑ dropdown arrow │
└─────────────────────────────────────────┘

On Click:
┌─────────────────────────────────────────┐
│  [📅]  2026-05-19              ↓        │
├─────────────────────────────────────────┤
│        2026年5月                        │
│  ┌─────────────────────────────────────┐│
│  │ 日 一 二 三 四 五 六                 ││
│  │                      1  2  3        ││
│  │  4  5  6  7  8  9 10                 ││
│  │ 11 12 13 14 15 16 17                 ││
│  │ 18 [19] 20 21 22 23                 ││ ← today highlighted
│  │ 24 25 26 27 28 29 30                 ││
│  │ 31                                   ││
│  └─────────────────────────────────────┘│
│  [今天]  [昨天]  [本周]                  │
└─────────────────────────────────────────┘

Features:
├── Visual indicator for dates with articles
├── Quick shortcuts: 今天, 昨天, 本周
├── Calendar popup with glass-blur backdrop
├── Dates with articles: accent-colored dot
├── Today: ring highlight
├── Selected: filled background

Mobile (Native date input or scroll picker):
├── Use native <input type="date"> for simplicity
├── Or custom scroll-wheel picker if needed
├── Quick date navigation: [<] [今天] [>]
```

### 5.5 Theme Toggle Component

```
 THEME TOGGLE SPECIFICATION
═════════════════════════════════════════════════════════════

Button Style:
┌─────────────────┐
│  [🌙] / [☀️]    │
│  ↑ icon only    │
└─────────────────┘

Dimensions:
├── Size:      40px × 40px (circle)
├── Padding:   8px
├── Position:  Header, right side

Icon Animation:
├── Dark -> Light:
│   ├── Moon icon rotates 180deg
│   ├── Fades to sun icon
│   ├── Transition: 500ms ease
│
├── Light -> Dark:
│   ├── Reverse animation

Interaction:
├── Hover: background glow (accent color)
├── Click: 
│   ├── Brief scale pulse
│   ├── Apply theme transition
│   ├── Store preference (localStorage)
│   ├── Announce to screen reader: "切换到浅色模式"

System Preference Detection:
├── On first visit: check prefers-color-scheme
├── If user toggles: override system preference
├── Remember in localStorage: 'ai-brief-theme'
```

### 5.6 Toast/Notification Component

```
TOAST NOTIFICATION SPECIFICATION
═════════════════════════════════════════════════════════════

Types:
├── Success:  Operation completed
├── Error:    Something failed
├── Warning:  Important notice
├── Info:     Neutral information

Appearance:
┌─────────────────────────────────────────┐
│  [✓]  操作成功                           │  Success
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  [!]  加载失败，请重试                   │  Error
└─────────────────────────────────────────┘

Dimensions:
├── Min-width:   280px
├── Max-width:   400px
├── Height:      auto (48px typical)
├── Padding:     16px
├── Border-radius: 8px

Position:
├── Desktop: bottom-center, 24px from bottom
├── Mobile:  bottom, full-width minus 32px margins

Animation:
├── Enter: translateY(20px) opacity 0 -> translateY(0) opacity 1
├── Exit:  reverse, after 3s auto-dismiss
├── Duration: 300ms ease-out

Color Mapping:
├── Success: background rgba(34,197,94,0.9)  border #22c55e
├── Error:   background rgba(239,68,68,0.9)  border #ef4444
├── Warning: background rgba(245,158,11,0.9) border #f59e0b
├── Info:    background --bg-elevated        border --border-default
```

---

## 6. Interaction Patterns

### 6.1 Scroll and Navigation

```
SCROLL BEHAVIOR SPECIFICATION
═════════════════════════════════════════════════════════════

Header Scroll Behavior:
├── Default: Fixed at top
├── On scroll down (> 100px):
│   ├── Header shrinks to 48px (mobile)
│   ├── Or slides up temporarily (desktop optional)
│   ├── Category tabs may collapse to icons
│
├── On scroll up:
│   ├── Header expands back
│   ├── Smooth reveal animation
│
├── Scroll threshold: 100px from top

Infinite Scroll / Pagination:
├── Trigger: 200px from bottom of article list
├── Action: Fetch next 10 articles
├── Loading indicator: Skeleton cards appear
├── Animation: Fade-in new cards

Pull-to-Refresh (Mobile):
├── Gesture: Pull down > 80px
├── Visual: Spinner appears
├── Release: Trigger refresh
├── Animation: Cards refresh with ripple effect
```

### 6.2 Article Card Interactions

```
CARD INTERACTION FLOW
═════════════════════════════════════════════════════════════

Hover Sequence (Desktop):
├── 0ms:    Mouse enters card area
├── 100ms:  Card begins lift (translateY)
├── 200ms:  Full hover state visible
│           ├── Border accent color
│           ├── Shadow enhancement
│           ├── "View Full" text accent
│
├── Exit:   Reverse sequence, 150ms

Click/Tap Sequence:
├── Desktop:
│   ├── Click: scale(0.98) for 100ms
│   ├── Then: Open modal overlay
│   ├── Modal animation: fade + scale
│   ├── Scroll position saved for return
│
├── Mobile:
│   ├── Tap: Brief highlight
│   ├── Then: Slide in full-screen detail
│   ├── Back button in header
│   ├── Swipe left/right to navigate articles
│   ├── Swipe down to close

Card Long-press (Mobile - Optional):
├── Trigger: Hold 500ms
├── Action: Show quick actions menu
│   ├── Share link
│   ├── Add to favorites
│   ├── Copy title
│   ├── Report issue
```

### 6.3 Category Filtering

```
CATEGORY FILTER INTERACTION
═════════════════════════════════════════════════════════════

Click on Category Tab:
├── Desktop:
│   ├── Click category pill
│   ├── Active state applies immediately
│   ├── Article list re-filters
│   ├── Animation: Cards fade out, new cards fade in
│   ├── Duration: 300ms staggered
│
├── Mobile:
│   ├── Tap category (horizontal scroll)
│   ├── Active indicator slides to new position
│   ├── Content refreshes below

Filter Combination:
├── Category + Date: Intersection filter
├── Category + Search: Search within category
├── All filters: Clear button appears

Filter State Persistence:
├── URL params: ?category=product&date=2026-05-19
├── Shareable link
├── Browser history: Back restores filters
```

### 6.4 Search Interaction

```
SEARCH INTERACTION FLOW
═════════════════════════════════════════════════════════════

Input Flow:
├── Focus: Search bar expands (mobile)
├── Type:  Real-time filtering begins
├── Debounce: 300ms delay before API call
├── Results: Cards update dynamically
│
├── Clear: X button or empty input
│   ├── Restores previous view
│   ├── Animation: smooth transition back

Keyboard Navigation:
├── Cmd/Ctrl + K: Focus search
├── Escape: Clear search, blur input
├── Arrow keys: Navigate results (if dropdown)
├── Enter: Select first result

Search Suggestions (Optional):
├── Recent searches (localStorage)
├── Popular topics
├── Trending keywords
├── Auto-complete from article titles
```

### 6.5 Theme Toggle Interaction

```
 THEME TOGGLE FLOW
═════════════════════════════════════════════════════════════

Toggle Click:
├── 0ms:    Click registered
├── 100ms:  Icon animation begins
├── 300ms:  CSS variables transition
│           ├── All theme-dependent elements
│           ├── Backgrounds, text, borders
│           ├── Smooth, not jarring
│
├── 500ms:  Icon settles to new state
├── Storage: Preference saved to localStorage
├── Toast:  Brief confirmation (optional)

System Preference Sync:
├── On load: Check prefers-color-scheme media query
├── Override: If user has manually toggled before
├── Re-sync: If user clears localStorage
```

---

## 7. Animation Specifications

### 7.1 Core Animations

```
CORE ANIMATION LIBRARY
═════════════════════════════════════════════════════════════

Entrance Animations:

├── fade-in
│   ├── from: opacity 0
│   ├── to:   opacity 1
│   ├── duration: 300ms
│   ├── easing: ease-out
│
├── slide-up
│   ├── from: translateY(20px) opacity 0
│   ├── to:   translateY(0) opacity 1
│   ├── duration: 400ms
│   ├── easing: cubic-bezier(0.16, 1, 0.3, 1)
│
├── scale-in
│   ├── from: scale(0.95) opacity 0
│   ├── to:   scale(1) opacity 1
│   ├── duration: 300ms
│   ├── easing: ease-out
│
├── stagger-fade
│   ├── Multiple elements fade in sequentially
│   ├── Delay: 50ms between each element
│   ├── Total: N * 50ms + base animation

Exit Animations:

├── fade-out
│   ├── Reverse of fade-in
│   ├── duration: 200ms (faster exit)
│
├── slide-down
│   ├── Reverse of slide-up
│   ├── duration: 200ms

State Animations:

├── pulse
│   ├── scale(1) -> scale(1.05) -> scale(1)
│   ├── duration: 600ms
│   ├── Used for: loading indicators, active states
│
├── shimmer
│   ├── background-position animation
│   ├── For skeleton loading screens
│   ├── duration: 1.5s infinite
│
├── bounce-subtle
│   ├── translateY(0) -> translateY(-4px) -> translateY(0)
│   ├── duration: 400ms
│   ├── Used for: hover feedback
```

### 7.2 Specific Animation Timings

```
COMPONENT ANIMATION TIMINGS
═════════════════════════════════════════════════════════════

| Component          | Animation         | Duration | Easing           |
|--------------------|-------------------|----------|------------------|
| Card hover         | lift + shadow     | 200ms    | ease             |
| Card click         | scale down        | 100ms    | ease-out         |
| Modal open         | scale + fade      | 300ms    | cubic-bezier     |
| Modal close        | reverse           | 200ms    | ease-in          |
| Category switch    | cards cross-fade  | 300ms    | ease             |
| Search expand      | width expand      | 200ms    | ease-out         |
| Theme toggle       | color transition  | 300ms    | ease             |
| Toast appear       | slide up          | 300ms    | ease-out         |
| Toast dismiss      | slide down        | 200ms    | ease-in          |
| Infinite scroll    | cards fade in     | 400ms    | staggered        |
| Skeleton shimmer   | shimmer           | 1.5s     | linear infinite  |
| Loading spinner    | rotate            | 800ms    | linear infinite  |
```

---

## 8. CSS Framework Recommendation

### 8.1 Recommended Approach: Minimal Custom CSS

```
CSS ARCHITECTURE RECOMMENDATION
═════════════════════════════════════════════════════════════

DO NOT USE:
├── Heavy frameworks (Bootstrap, Material UI)
├── Utility-only frameworks (Tailwind CSS - overkill for this scale)
├── Component libraries (Ant Design, Chakra)
│
WHY:
├── Design needs rich, custom aesthetics
├── Frameworks produce generic, template look
├── Total CSS will be < 2000 lines - manageable
├── Full control over animations and micro-interactions

RECOMMENDED STRUCTURE:
├── /static/css/
│   ├── variables.css      (~150 lines) - Color, typography, spacing
│   ├── base.css           (~100 lines) - Reset, root styles
│   ├── layout.css         (~200 lines) - Grid, containers
│   ├── components.css     (~400 lines) - Cards, buttons, inputs
│   ├── animations.css     (~150 lines) - Keyframes, transitions
│   ├── utilities.css      (~100 lines) - Helper classes
│   ├── responsive.css     (~200 lines) - Mobile/tablet adaptations
│   └── themes.css         (~100 lines) - Light/dark mode overrides
│   └────────────────────────────────────────────────────────────
│   Total:                  ~1200-1400 lines

BUILD STRATEGY:
├── Development: Individual files, linked separately
├── Production: Concatenate + minify
├── No build step required (vanilla CSS)
├── Optional: PostCSS for autoprefixer only
```

### 8.2 CSS Variable Architecture

```css
/* variables.css - Core design tokens */

:root[data-theme="dark"] {
    /* Backgrounds */
    --bg-deep: #0a0f1a;
    --bg-page: #0f172a;
    --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    --bg-elevated: #1e293b;
    --bg-card: rgba(255, 255, 255, 0.04);
    --bg-card-hover: rgba(255, 255, 255, 0.08);
    --bg-subtle-accent: rgba(56, 189, 248, 0.06);
    
    /* Text */
    --text-primary: #f8fafc;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;
    --text-accent: #38bdf8;
    --text-inverse: #0f172a;
    
    /* Accent */
    --accent: #38bdf8;
    --accent-hover: #0ea5e9;
    --accent-light: #7dd3fc;
    --accent-secondary: #a78bfa;
    --accent-gradient: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
    --accent-glow: rgba(56, 189, 248, 0.25);
    
    /* Category Colors */
    --cat-product: #f472b6;
    --cat-product-bg: rgba(244, 114, 182, 0.15);
    --cat-open-source: #22c55e;
    --cat-open-source-bg: rgba(34, 197, 94, 0.15);
    --cat-research: #8b5cf6;
    --cat-research-bg: rgba(139, 92, 246, 0.15);
    --cat-industry: #f59e0b;
    --cat-industry-bg: rgba(245, 158, 11, 0.15);
    
    /* Borders */
    --border: rgba(255, 255, 255, 0.08);
    --border-subtle: rgba(255, 255, 255, 0.04);
    --border-focus: rgba(56, 189, 248, 0.5);
    --border-active: rgba(56, 189, 248, 0.3);
    
    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.25);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.3);
    --shadow-glow: 0 0 20px rgba(56, 189, 248, 0.2);
    
    /* Typography */
    --font-sans: "PingFang SC", "Inter", -apple-system, sans-serif;
    --font-mono: "JetBrains Mono", "Fira Code", monospace;
    
    --fs-xs: 11px;
    --fs-sm: 12px;
    --fs-md: 13px;
    --fs-base: 14px;
    --fs-lg: 16px;
    --fs-xl: 18px;
    --fs-2xl: 20px;
    --fs-3xl: 24px;
    --fs-4xl: 32px;
    
    --fw-normal: 400;
    --fw-medium: 500;
    --fw-semibold: 600;
    --fw-bold: 700;
    
    --lh-tight: 1.25;
    --lh-normal: 1.5;
    --lh-relaxed: 1.75;
    
    /* Spacing */
    --sp-1: 4px;
    --sp-2: 8px;
    --sp-3: 12px;
    --sp-4: 16px;
    --sp-5: 20px;
    --sp-6: 24px;
    --sp-8: 32px;
    
    /* Radius */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-full: 9999px;
    
    /* Transitions */
    --tr-fast: 150ms ease;
    --tr-normal: 200ms ease;
    --tr-slow: 300ms ease;
    --tr-theme: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    
    /* Z-index */
    --z-dropdown: 100;
    --z-modal-bg: 400;
    --z-modal: 500;
    --z-toast: 600;
}

:root[data-theme="light"] {
    /* Override only what changes */
    --bg-deep: #f8fafc;
    --bg-page: #ffffff;
    --bg-gradient: linear-gradient(135deg, #ffffff 0%, #f1f5f9 50%, #ffffff 100%);
    --bg-elevated: #ffffff;
    --bg-card: rgba(15, 23, 42, 0.03);
    --bg-card-hover: rgba(15, 23, 42, 0.06);
    
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --text-accent: #0ea5e9;
    
    --accent: #0ea5e9;
    --accent-hover: #0284c7;
    --accent-glow: rgba(14, 165, 233, 0.15);
    
    --border: rgba(15, 23, 42, 0.1);
    --border-subtle: rgba(15, 23, 42, 0.05);
    --border-focus: rgba(14, 165, 233, 0.4);
    
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.1);
    --shadow-glow: 0 0 20px rgba(14, 165, 233, 0.1);
}
```

---

## 9. Accessibility Considerations

```
ACCESSIBILITY REQUIREMENTS
═════════════════════════════════════════════════════════════

Visual:
├── Color contrast: WCAG AA minimum (4.5:1 for text)
├── Focus indicators: Visible on all interactive elements
├── Don't rely solely on color for state indication
├── Font size: Minimum 12px, body text 14px+

Interaction:
├── Keyboard navigation: Full site navigable
│   ├── Tab: Move between elements
│   ├── Arrow keys: Navigate within components
│   ├── Escape: Close modals/dropdowns
│   ├── Enter/Space: Activate buttons
│
├── Touch targets: Minimum 44x44px (mobile)
├── Screen reader: Semantic HTML, ARIA labels
│   ├── aria-label for icon buttons
│   ├── aria-live for toast notifications
│   ├── aria-expanded for dropdowns
│
├── Motion: Respect prefers-reduced-motion
│   ├── Disable animations if user prefers
│   ├── Keep essential transitions only

Content:
├── Chinese content: Proper lang="zh-CN" attributes
├── Article structure: Semantic heading hierarchy
├── Links: Descriptive text, not just "点击这里"
├── Images: Alt text (if any decorative images)

Theme:
├── Both themes meet contrast requirements
├── Theme toggle announced to screen readers
├── System preference respected
```

---

## 10. Performance Considerations

```
PERFORMANCE TARGETS
═════════════════════════════════════════════════════════════

CSS:
├── Total CSS size: < 30KB (unminified ~15KB)
├── No runtime CSS-in-JS
├── Critical CSS inlined (optional)
├── Non-critical CSS loaded async

Animations:
├── Use transform/opacity only (GPU accelerated)
├── Avoid animating width/height directly
├── will-change: apply sparingly
├── Debounce scroll handlers

Images/Icons:
├── Icons: Inline SVG (no icon font loading)
├── No heavy images in cards
├── Lazy load article images in detail view
├── Use CSS gradients for visual effects

JavaScript:
├── Vanilla JS, no heavy libraries
├── Event delegation for card clicks
├── Debounced search/filter operations
├── IntersectionObserver for infinite scroll
├── requestAnimationFrame for animations

Initial Load:
├── HTML: < 10KB
├── CSS: < 30KB
├── JS: < 20KB
├── First paint: < 1s
├── Interactive: < 2s
```

---

## 11. Implementation Notes

```
IMPLEMENTATION PRIORITY
═════════════════════════════════════════════════════════════

Phase 1: Core Structure (MVP)
├── [1] CSS variables and base styles
├── [2] Header with logo and category pills
├── [3] Article card grid layout
├── [4] Basic card hover interactions
├── [5] Article list API integration

Phase 2: Interactions
├── [6] Category filtering
├── [7] Search functionality
├── [8] Date picker
├── [9] Article detail modal/page
├── [10] Infinite scroll

Phase 3: Enhancements
├── [11] Dark/Light theme toggle
├── [12] Skeleton loading
├── [13] Toast notifications
├── [14] Keyboard navigation
├── [15] Mobile optimizations

Phase 4: Polish
├── [16] Animation refinements
├── [17] Accessibility audit
├── [18] Performance optimization
├── [19] Edge case handling
├── [20] User testing feedback

File Structure:
/static/css/
├── variables.css    ← Create first
├── base.css         ← Reset + typography
├── layout.css       ← Grid + containers
├── components.css   ← Cards + buttons
├── animations.css   ← Keyframes
├── responsive.css   ← Mobile/tablet
├── themes.css       ← Light mode
└── main.css         ← Import all (or concatenate)
│
/static/js/
├── app.js           ← Existing, enhance
├── components.js    ← Card, modal logic (optional split)
├── animations.js    ← Animation utilities
├── theme.js         ← Theme toggle logic
│
/templates/
├── index.html       ← Main page
├── detail.html      ← Article detail (or modal)
├── partials/        ← Reusable HTML snippets (optional)
```

---

## 12. Design Inspiration References

```
DESIGN REFERENCES
═════════════════════════════════════════════════════════════

Visual Style:
├── Linear.app - Clean, modern, dark theme
├── Vercel Dashboard - Minimal, functional
├── GitHub Dark - Information density
├── Notion - Content-focused layout

Typography:
├── Inter font demo - Modern sans-serif usage
├── Chinese typography guides - PingFang SC best practices

Interaction:
├── Apple.com - Subtle hover effects
├── Stripe.com - Card interactions
├── Dropbox.com - Scroll behavior

Category Colors:
├── Semantic meaning preserved
├── Product = Pink (energy, innovation)
├── Open-source = Green (growth, community)
├── Research = Purple (depth, science)
├── Industry = Amber (news, attention)
```

---

*Document Version: 2.0.0*
*Created: 2026-05-19*
*Purpose: AI Daily Brief v4 Upgrade - UI Design Specification*