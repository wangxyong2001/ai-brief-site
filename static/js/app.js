// AI Daily Brief Frontend App - Modern UI with working filters
const API_BASE = '/api/brief';

// State
let currentDate = new Date();
let articlesData = [];
let currentCategory = 'all';
let searchQuery = '';

// DOM Elements
const articlesGrid = document.getElementById('articles-grid');
const briefTitle = document.getElementById('brief-title');
const sourceCount = document.getElementById('source-count');
const datePicker = document.getElementById('date-picker');
const prevDayBtn = document.getElementById('prev-day');
const nextDayBtn = document.getElementById('next-day');
const todayBtn = document.getElementById('today-btn');
const searchInput = document.getElementById('search-input');
const categoryTabs = document.getElementById('category-tabs');
const articleModal = document.getElementById('article-modal');
const articleDetail = document.getElementById('article-detail');
const modalClose = document.getElementById('modal-close');
const toast = document.getElementById('toast');
const themeToggle = document.getElementById('theme-toggle');

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

// Utility Functions
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function formatDateDisplay(dateStr) {
    const d = new Date(dateStr);
    return `${d.getFullYear()}年${String(d.getMonth() + 1).padStart(2, '0')}月${String(d.getDate()).padStart(2, '0')}日`;
}

function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCategoryClass(category) {
    const cat = (category || '').toLowerCase();
    const map = {
        'product': 'product',
        'opensource': 'opensource',
        'research': 'research',
        'news': 'news',
        'anthropic': 'product',
        'openai': 'product',
        'deepmind': 'product',
        'huggingface': 'opensource',
        'arxiv': 'research',
        'github': 'opensource'
    };
    return map[cat] || 'news';
}

function getCategoryLabel(category) {
    const cat = (category || '').toLowerCase();
    const map = {
        'product': '产品动态',
        'opensource': '开源项目',
        'research': '学术研究',
        'news': '行业新闻',
        'anthropic': 'Anthropic',
        'openai': 'OpenAI',
        'deepmind': 'DeepMind',
        'arxiv': 'arXiv',
        'github': 'GitHub',
        'huggingface': 'Hugging Face',
        'other': '其他'
    };
    return map[cat] || cat;
}

// Render Functions
function renderLoading() {
    articlesGrid.innerHTML = `
        <div class="loading-state" style="grid-column: 1 / -1;">
            <div class="spinner"></div>
            <p>加载中...</p>
        </div>
    `;
}

function renderError(message) {
    articlesGrid.innerHTML = `
        <div class="error-state" style="grid-column: 1 / -1;">
            <div class="error-icon">!</div>
            <p class="error-message">${escapeHtml(message)}</p>
        </div>
    `;
}

function renderEmpty(message) {
    articlesGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <div class="empty-icon">-</div>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

function renderArticles(articles) {
    if (!articles || articles.length === 0) {
        renderEmpty('暂无文章，请稍后再试');
        return;
    }

    articlesGrid.innerHTML = articles.map((article, index) => `
        <article class="article-card"
                 data-index="${index}"
                 onclick="openArticleDetail(${index})">
            <span class="article-category ${getCategoryClass(article.source)}">${getCategoryLabel(article.source)}</span>
            <h3 class="article-title">${escapeHtml(article.title)}</h3>
            <div class="article-source">${escapeHtml(article.source)}</div>
            <p class="article-summary">${escapeHtml(article.summary || '点击查看详情')}</p>
            <div class="article-footer">
                <span class="article-date">${escapeHtml(article.published || '')}</span>
                <span class="read-more">查看详情 →</span>
            </div>
        </article>
    `).join('');

    sourceCount.textContent = articles.length;
}

function filterAndRender() {
    let filtered = articlesData;

    // Category filter - 实际过滤
    if (currentCategory !== 'all') {
        filtered = filtered.filter(a => {
            const source = (a.source || '').toLowerCase();
            return source.includes(currentCategory.toLowerCase());
        });
    }

    // Search filter
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(a =>
            (a.title || '').toLowerCase().includes(query) ||
            (a.summary || '').toLowerCase().includes(query)
        );
    }

    renderArticles(filtered);
}

// Modal Functions
function openModal() {
    articleModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    articleModal.classList.remove('active');
    document.body.style.overflow = '';
}

function openArticleDetail(index) {
    const article = articlesData[index];
    if (!article) return;

    // 构建详情内容
    const detailHtml = `
        <header class="detail-header">
            <span class="article-category ${getCategoryClass(article.source)}">${getCategoryLabel(article.source)}</span>
            <h2 class="detail-title">${escapeHtml(article.title)}</h2>
            <div class="detail-meta">
                <span>来源: ${escapeHtml(article.source)}</span>
                ${article.published ? `<span class="separator">·</span><span>${escapeHtml(article.published)}</span>` : ''}
            </div>
        </header>

        <section class="content-section">
            <h3 class="section-title">文章摘要</h3>
            <p>${escapeHtml(article.summary || '暂无摘要')}</p>
        </section>

        ${article['核心观点'] ? `
        <section class="content-section">
            <h3 class="section-title">核心观点</h3>
            <p>${escapeHtml(article['核心观点'])}</p>
        </section>
        ` : ''}

        ${article['技术要点'] ? `
        <section class="content-section">
            <h3 class="section-title">技术要点</h3>
            <p>${escapeHtml(article['技术要点'])}</p>
        </section>
        ` : ''}

        ${article['中文摘要'] ? `
        <section class="content-section">
            <h3 class="section-title">中文摘要</h3>
            <p>${escapeHtml(article['中文摘要'])}</p>
        </section>
        ` : `
        <section class="content-section">
            <h3 class="section-title">提示</h3>
            <p style="color: var(--text-secondary);">配置GLM API后，将自动生成中文摘要、核心观点、技术要点等内容。</p>
        </section>
        `}

        <div class="detail-actions">
            <a href="${escapeHtml(article.link)}" target="_blank" rel="noopener" class="btn-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                查看原文
            </a>
            <button class="btn-secondary" onclick="closeModal()">关闭</button>
        </div>
    `;

    articleDetail.innerHTML = detailHtml;
    openModal();
}

// API Functions
async function fetchBriefByDate(date) {
    renderLoading();

    try {
        const response = await fetch(`${API_BASE}/${date}`);
        if (!response.ok) {
            if (response.status === 404) {
                renderEmpty(`该日期 (${date}) 暂无简报`);
                briefTitle.textContent = `AI Daily Brief - ${date}`;
                return;
            }
            throw new Error('加载失败');
        }

        const data = await response.json();
        briefTitle.textContent = data.title || `AI Daily Brief - ${date}`;

        // Parse HTML content to get articles
        articlesData = parseBriefContent(data.content);
        filterAndRender();

    } catch (e) {
        renderError(e.message);
    }
}

async function fetchLatestBrief() {
    renderLoading();

    try {
        const response = await fetch(`${API_BASE}/latest`);
        if (!response.ok) {
            if (response.status === 404) {
                // Try to generate a brief
                const genResponse = await fetch(`${API_BASE}/generate`, { method: 'POST' });
                if (genResponse.ok) {
                    showToast('正在生成简报，请稍候...', 'info');
                    setTimeout(() => fetchLatestBrief(), 30000);
                    return;
                }
            }
            throw new Error('暂无简报，请稍后再试');
        }

        const data = await response.json();
        currentDate = new Date(data.date);
        updateDatePicker();
        briefTitle.textContent = data.title;

        articlesData = parseBriefContent(data.content);
        filterAndRender();

    } catch (e) {
        renderError(e.message);
    }
}

function parseBriefContent(content) {
    // Parse HTML content to extract articles
    const articles = [];
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;

    // Extract from h3 sections
    const sections = tempDiv.querySelectorAll('h3');
    sections.forEach(section => {
        const sourceName = section.textContent.trim();
        const ul = section.nextElementSibling;
        if (ul && ul.tagName === 'UL') {
            const items = ul.querySelectorAll('li');
            items.forEach(item => {
                const link = item.querySelector('a');
                const summaryP = item.querySelector('p');
                const summaryText = summaryP ? summaryP.textContent : '';

                // 尝试提取更多信息
                let summary = '';
                let keyPoints = '';

                if (summaryText.includes('摘要:')) {
                    const parts = summaryText.split('核心观点:');
                    summary = parts[0].replace('摘要:', '').trim();
                    if (parts.length > 1) {
                        keyPoints = parts[1].trim();
                    }
                } else {
                    summary = summaryText;
                }

                articles.push({
                    title: link ? link.textContent : item.textContent,
                    link: link ? link.href : '',
                    summary: summary,
                    '核心观点': keyPoints,
                    source: sourceName,
                    category: getCategoryClass(sourceName)
                });
            });
        }
    });

    return articles;
}

// Navigation Functions
function updateDatePicker() {
    const dateStr = formatDate(currentDate);
    datePicker.value = dateStr;
    nextDayBtn.disabled = dateStr >= formatDate(new Date());
}

function navigateDate(delta) {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + delta);

    if (newDate > new Date()) {
        showToast('不能查看未来的简报', 'warning');
        return;
    }

    currentDate = newDate;
    updateDatePicker();
    fetchBriefByDate(formatDate(currentDate));
}

function goToToday() {
    currentDate = new Date();
    updateDatePicker();
    fetchBriefByDate(formatDate(currentDate));
}

// Event Handlers
prevDayBtn.addEventListener('click', () => navigateDate(-1));
nextDayBtn.addEventListener('click', () => navigateDate(1));
todayBtn.addEventListener('click', goToToday);

datePicker.addEventListener('change', (e) => {
    const selectedDate = new Date(e.target.value);
    if (selectedDate > new Date()) {
        showToast('不能查看未来的简报', 'warning');
        datePicker.value = formatDate(currentDate);
        return;
    }
    currentDate = selectedDate;
    fetchBriefByDate(e.target.value);
});

searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    filterAndRender();
});

categoryTabs.addEventListener('click', (e) => {
    if (e.target.classList.contains('tab-btn')) {
        // 更新active状态
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');

        // 更新过滤条件并重新渲染
        currentCategory = e.target.dataset.category;
        filterAndRender();

        // 显示toast通知
        if (currentCategory !== 'all') {
            showToast(`筛选: ${getCategoryLabel(currentCategory)}`, 'info');
        }
    }
});

modalClose.addEventListener('click', closeModal);
articleModal.addEventListener('click', (e) => {
    if (e.target === articleModal) closeModal();
});

themeToggle.addEventListener('click', toggleTheme);

// Keyboard Navigation
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;

    if (e.key === 'ArrowLeft') navigateDate(-1);
    else if (e.key === 'ArrowRight') navigateDate(1);
    else if (e.key === 't' || e.key === 'T') goToToday();
    else if (e.key === 'Escape') closeModal();
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    updateDatePicker();
    fetchLatestBrief();
});