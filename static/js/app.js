// AI Daily Brief Frontend App
const API_BASE = '/api/brief';

// State
let currentDate = new Date();
let briefsList = [];
let isLoading = false;

// DOM Elements
const briefContent = document.getElementById('brief-content');
const listContainer = document.getElementById('list-container');
const datePicker = document.getElementById('date-picker');
const currentDateDisplay = document.getElementById('current-date-display');
const prevDayBtn = document.getElementById('prev-day');
const nextDayBtn = document.getElementById('next-day');
const todayBtn = document.getElementById('today-btn');
const toast = document.getElementById('toast');

// Utility: Format date as YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Utility: Format date for display (YYYY年MM月DD日)
function formatDateDisplay(date) {
    const d = new Date(date);
    return `${d.getFullYear()}年${String(d.getMonth() + 1).padStart(2, '0')}月${String(d.getDate()).padStart(2, '0')}日`;
}

// Utility: Show toast notification
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Render loading state
function renderLoading(container) {
    container.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
        </div>
    `;
}

// Render error state
function renderError(container, message, retryFn) {
    container.innerHTML = `
        <div class="error-state">
            <div class="error-icon">!</div>
            <p class="error-message">${message}</p>
            ${retryFn ? '<button class="retry-btn" onclick="(' + retryFn.toString() + ')()">重试</button>' : ''}
        </div>
    `;
}

// Render empty state
function renderEmpty(container, message) {
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">-</div>
            <p>${message}</p>
        </div>
    `;
}

// Render brief content with HTML support
function renderBriefContent(data) {
    if (!data) {
        renderEmpty(briefContent, '该日期暂无简报');
        return;
    }

    briefContent.innerHTML = `
        <h2 class="brief-title">${escapeHtml(data.title)}</h2>
        <div class="brief-date">${formatDateDisplay(data.date)}</div>
        <div class="brief-body">${sanitizeHtml(data.content)}</div>
    `;
}

// Escape HTML for title
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Sanitize HTML content (basic XSS protection)
function sanitizeHtml(html) {
    // Allow specific tags only
    const allowedTags = ['p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                         'ul', 'ol', 'li', 'a', 'strong', 'em', 'b', 'i',
                         'code', 'pre', 'blockquote', 'hr'];

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    // Remove script tags
    const scripts = tempDiv.querySelectorAll('script');
    scripts.forEach(s => s.remove());

    // Remove event handlers
    const allElements = tempDiv.querySelectorAll('*');
    allElements.forEach(el => {
        // Remove event handlers
        Array.from(el.attributes).forEach(attr => {
            if (attr.name.startsWith('on')) {
                el.removeAttribute(attr.name);
            }
        });

        // Sanitize href for links
        if (el.tagName === 'A') {
            const href = el.getAttribute('href');
            if (href && !href.startsWith('http') && !href.startsWith('/') && !href.startsWith('#')) {
                el.removeAttribute('href');
            } else {
                el.setAttribute('target', '_blank');
                el.setAttribute('rel', 'noopener noreferrer');
            }
        }
    });

    return tempDiv.innerHTML;
}

// Render brief list
function renderBriefList(data) {
    briefsList = data || [];

    if (briefsList.length === 0) {
        renderEmpty(listContainer, '暂无历史简报');
        return;
    }

    const currentDateStr = formatDate(currentDate);
    listContainer.innerHTML = `
        <ul class="brief-list">
            ${briefsList.map(brief => `
                <li class="brief-item ${brief.date === currentDateStr ? 'active' : ''}"
                    data-date="${brief.date}">
                    <span class="brief-item-title">${escapeHtml(brief.title)}</span>
                    <span class="brief-item-date">${brief.date}</span>
                </li>
            `).join('')}
        </ul>
    `;

    // Add click handlers
    document.querySelectorAll('.brief-item').forEach(item => {
        item.addEventListener('click', () => {
            const date = item.dataset.date;
            currentDate = new Date(date);
            updateDatePicker();
            fetchBriefByDate(date);
        });
    });
}

// Update date picker and navigation buttons
function updateDatePicker() {
    const dateStr = formatDate(currentDate);
    datePicker.value = dateStr;
    currentDateDisplay.textContent = formatDateDisplay(dateStr);

    const today = formatDate(new Date());
    nextDayBtn.disabled = dateStr >= today;
}

// Fetch brief by date
async function fetchBriefByDate(date) {
    renderLoading(briefContent);

    try {
        const response = await fetch(`${API_BASE}/${date}`);
        if (!response.ok) {
            if (response.status === 404) {
                renderEmpty(briefContent, '该日期暂无简报');
                return;
            }
            throw new Error('加载失败');
        }

        const data = await response.json();
        renderBriefContent(data);

        // Update active state in list
        document.querySelectorAll('.brief-item').forEach(item => {
            item.classList.toggle('active', item.dataset.date === date);
        });
    } catch (e) {
        renderError(briefContent, e.message, () => fetchBriefByDate(date));
    }
}

// Fetch latest brief
async function fetchLatestBrief() {
    renderLoading(briefContent);

    try {
        const response = await fetch(`${API_BASE}/latest`);
        if (!response.ok) {
            throw new Error('暂无简报');
        }

        const data = await response.json();
        currentDate = new Date(data.date);
        updateDatePicker();
        renderBriefContent(data);

        // Update active state in list
        document.querySelectorAll('.brief-item').forEach(item => {
            item.classList.toggle('active', item.dataset.date === data.date);
        });
    } catch (e) {
        renderError(briefContent, e.message, fetchLatestBrief);
    }
}

// Fetch brief list
async function fetchBriefList() {
    renderLoading(listContainer);

    try {
        const response = await fetch(`${API_BASE}/list`);
        if (!response.ok) {
            throw new Error('加载失败');
        }

        const data = await response.json();
        renderBriefList(data);
    } catch (e) {
        renderError(listContainer, e.message, fetchBriefList);
    }
}

// Navigate date
function navigateDate(delta) {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + delta);

    const today = new Date();
    if (newDate > today) {
        showToast('不能查看未来的简报', 'warning');
        return;
    }

    currentDate = newDate;
    updateDatePicker();
    fetchBriefByDate(formatDate(currentDate));
}

// Go to today
function goToToday() {
    currentDate = new Date();
    updateDatePicker();
    fetchBriefByDate(formatDate(currentDate));
}

// Event Listeners
prevDayBtn.addEventListener('click', () => navigateDate(-1));
nextDayBtn.addEventListener('click', () => navigateDate(1));
todayBtn.addEventListener('click', goToToday);

datePicker.addEventListener('change', (e) => {
    const selectedDate = new Date(e.target.value);
    const today = new Date();

    if (selectedDate > today) {
        showToast('不能查看未来的简报', 'warning');
        datePicker.value = formatDate(currentDate);
        return;
    }

    currentDate = selectedDate;
    fetchBriefByDate(e.target.value);
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;

    if (e.key === 'ArrowLeft') {
        navigateDate(-1);
    } else if (e.key === 'ArrowRight') {
        navigateDate(1);
    } else if (e.key === 't' || e.key === 'T') {
        goToToday();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateDatePicker();
    fetchLatestBrief();
    fetchBriefList();
});