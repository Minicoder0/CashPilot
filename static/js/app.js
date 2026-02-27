/* ===============================================
   CashPilot — Main App Controller
   =============================================== */

// Global state
let transactions = [];
let currentSort = { field: 'date', direction: 'desc' };
let cashflowChart = null;
let expenseChart = null;

// ---- Formatting Utilities ----

function formatCurrency(amount) {
    const abs = Math.abs(amount);
    const formatted = abs.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return amount < 0 ? `-$${formatted}` : `$${formatted}`;
}

function formatDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ---- Loading / Toast Helpers ----

function showLoading(text = 'Analyzing transactions...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showToast(message, type = 'info') {
    const icons = { error: '❌', success: '✅', info: 'ℹ️' };
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ---- Load Demo Data ----

async function loadDemoData() {
    const btn = document.getElementById('loadDemoBtn');
    btn.disabled = true;
    showLoading('Loading demo data & categorizing with AI...');

    try {
        const res = await fetch('/api/demo-data');
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || 'Failed to load demo data');

        transactions = data.transactions;
        updateAIBadge(data.ai_available);
        renderDashboard();
        showToast('Demo data loaded successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        hideLoading();
        btn.disabled = false;
    }
}

// ---- CSV Upload ----

async function handleCSVUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showLoading('Uploading & analyzing your transactions...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || 'Upload failed');

        transactions = data.transactions;
        updateAIBadge(data.ai_available);
        renderDashboard();
        showToast(`${data.count} transactions loaded!`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        hideLoading();
        event.target.value = '';
    }
}

// ---- Dashboard Rendering ----

function renderDashboard() {
    // Hide empty state, show dashboard + chat
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('chatContainer').style.display = 'block';

    updateSummaryCards();
    renderTransactionTable();
    renderCharts();
    renderEntities();
    fetchInsights();
}

function updateSummaryCards() {
    const income = transactions.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
    const expenses = transactions.filter(t => t.type === 'expense').reduce((s, t) => s + Math.abs(t.amount), 0);
    const net = income - expenses;

    animateValue('totalIncome', income);
    animateValue('totalExpenses', expenses);
    animateValue('netCashflow', net, true);
    document.getElementById('txnCount').textContent = transactions.length;

    // Update net card color
    const netCard = document.getElementById('cardNet');
    if (net >= 0) {
        netCard.querySelector('.card-value').style.color = 'var(--green)';
    } else {
        netCard.querySelector('.card-value').style.color = 'var(--red)';
    }
}

function animateValue(elementId, target, showSign = false) {
    const el = document.getElementById(elementId);
    const duration = 800;
    const start = performance.now();
    const startVal = 0;

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = startVal + (target - startVal) * eased;

        const prefix = showSign && current >= 0 ? '+' : '';
        el.textContent = prefix + formatCurrency(current);

        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ---- Transaction Table ----

function renderTransactionTable() {
    const sorted = [...transactions].sort((a, b) => {
        let valA = a[currentSort.field];
        let valB = b[currentSort.field];
        if (currentSort.field === 'amount') {
            valA = Math.abs(valA);
            valB = Math.abs(valB);
        }
        if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
        if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const tbody = document.getElementById('txnBody');
    tbody.innerHTML = sorted.map(t => `
        <tr>
            <td>${formatDate(t.date)}</td>
            <td>${t.description}</td>
            <td><span class="category-badge badge-${t.category}">${t.category}</span></td>
            <td class="${t.amount >= 0 ? 'amount-positive' : 'amount-negative'}">${formatCurrency(t.amount)}</td>
        </tr>
    `).join('');

    document.getElementById('txnSubtitle').textContent = `${transactions.length} transactions`;
}

function sortTable(field) {
    if (currentSort.field === field) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.direction = 'asc';
    }
    renderTransactionTable();
}

// ---- AI Insights ----

async function fetchInsights() {
    const grid = document.getElementById('insightsGrid');
    grid.innerHTML = `
        <div class="insight-skeleton"></div>
        <div class="insight-skeleton"></div>
        <div class="insight-skeleton"></div>
    `;

    try {
        const res = await fetch('/api/insights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transactions }),
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || 'Failed to get insights');

        renderInsights(data.insights);

        // Render new creativity features
        if (data.health_score) renderHealthScore(data.health_score);
        if (data.runway) renderRunway(data.runway);
        if (data.anomalies) renderAnomalies(data.anomalies);

    } catch (err) {
        grid.innerHTML = `<div class="insight-card info"><span class="insight-icon">ℹ️</span><span class="insight-text">Could not load AI insights. ${err.message}</span></div>`;
    }
}

function renderInsights(insights) {
    const grid = document.getElementById('insightsGrid');
    grid.innerHTML = insights.map(i => `
        <div class="insight-card ${i.type || 'info'}">
            <span class="insight-icon">${i.icon || '💡'}</span>
            <span class="insight-text">${i.text}</span>
        </div>
    `).join('');
}

function refreshInsights() {
    fetchInsights();
    showToast('Refreshing insights...', 'info');
}

// ---- Health Score Gauge ----

function renderHealthScore(health) {
    const section = document.getElementById('healthScoreSection');
    section.style.display = 'block';

    const colorMap = { green: 'var(--green)', blue: 'var(--blue)', amber: 'var(--amber)', red: 'var(--red)' };
    const color = colorMap[health.color] || 'var(--blue)';
    const deg = (health.score / 100) * 360;

    // Animate the gauge ring
    const ring = document.getElementById('gaugeRing');
    ring.style.background = `conic-gradient(${color} 0deg, ${color} ${deg}deg, var(--border-color) ${deg}deg)`;

    // Animate the number
    const valueEl = document.getElementById('gaugeValue');
    const duration = 1200;
    const start = performance.now();
    function animate(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        valueEl.textContent = Math.round(health.score * eased);
        if (progress < 1) requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);

    // Set tier
    const tierEl = document.getElementById('gaugeTier');
    tierEl.textContent = health.tier;
    tierEl.style.color = color;
}

// ---- Cash Runway ----

function renderRunway(runway) {
    const el = document.getElementById('runwayValue');
    const card = document.getElementById('cardRunway');
    el.textContent = runway.label;

    const colorMap = { green: 'var(--green)', amber: 'var(--amber)', red: 'var(--red)', gray: 'var(--text-muted)' };
    el.style.color = colorMap[runway.color] || 'var(--text-secondary)';
}

// ---- Anomaly Detection ----

function renderAnomalies(anomalies) {
    const container = document.getElementById('anomaliesContainer');
    const grid = document.getElementById('anomaliesGrid');

    if (!anomalies || anomalies.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    grid.innerHTML = anomalies.map(a => `
        <div class="anomaly-card">
            <div class="anomaly-header">
                <span class="anomaly-amount">${formatCurrency(a.amount)}</span>
                <span class="anomaly-badge">${a.multiplier}x above avg</span>
            </div>
            <div class="anomaly-desc">${a.description}</div>
            <div class="anomaly-reason">${a.reason}</div>
            <div class="anomaly-meta">${a.date} · ${a.category}</div>
        </div>
    `).join('');
}

// ---- Entities: Customers & Suppliers ----

const ENTITY_PREFIXES = [
    'TRANSFER FROM ', 'CLIENT PAYMENT - ', 'FREELANCE PAYMENT - ',
    'PAYMENT FROM ', 'INVOICE - ', 'PAYMENT TO ', 'TRANSFER TO ',
    'DIRECT DEPOSIT - ', 'WIRE FROM ', 'WIRE TO ',
];

const MONTH_NAMES = 'JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC';
// Matches trailing patterns like "- SEPT", "- OCT 2025", "- SEP 4", "- Q3 2025"
const TRAILING_DATE_RE = new RegExp(
    `\\s*[-–]\\s*(?:${MONTH_NAMES})(?:\\s+\\d{1,4})?\\s*$`, 'i'
);
// Matches trailing person names after PAYROLL like "- JOHN SMITH"
const PAYROLL_SUFFIX_RE = /\s*[-–]\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*$/;

function cleanEntityName(desc, category) {
    let name = desc.trim();

    // Strip common prefixes
    for (const prefix of ENTITY_PREFIXES) {
        if (name.toUpperCase().startsWith(prefix)) {
            name = name.slice(prefix.length).trim();
            break;
        }
    }

    // Group all payroll entries under one name
    if ((category || '').toLowerCase() === 'payroll' || name.toUpperCase().startsWith('PAYROLL')) {
        return 'Payroll';
    }

    // Strip trailing month / date suffixes
    name = name.replace(TRAILING_DATE_RE, '').trim();

    return name || desc.trim();
}

function buildEntityData(txns, type) {
    const filtered = txns.filter(t => t.type === type);
    const totalRevenue = type === 'income'
        ? filtered.reduce((s, t) => s + t.amount, 0)
        : filtered.reduce((s, t) => s + Math.abs(t.amount), 0);

    const grouped = {};
    for (const t of filtered) {
        const cleaned = cleanEntityName(t.description, t.category);
        const key = cleaned.toUpperCase();
        if (!grouped[key]) {
            grouped[key] = { name: cleaned, total: 0, count: 0, lastDate: t.date };
        }
        grouped[key].total += type === 'income' ? t.amount : Math.abs(t.amount);
        grouped[key].count += 1;
        if (t.date > grouped[key].lastDate) grouped[key].lastDate = t.date;
    }

    return Object.values(grouped)
        .map(e => ({ ...e, pct: totalRevenue > 0 ? ((e.total / totalRevenue) * 100) : 0 }))
        .sort((a, b) => b.total - a.total);
}

const ENTITY_MAX_ROWS = 6;

function renderEntityList(entities, gridId, label) {
    const grid = document.getElementById(gridId);
    if (!entities.length) {
        grid.innerHTML = `<div class="entity-empty">No ${label.toLowerCase()} found.</div>`;
        return;
    }

    const visible = entities.slice(0, ENTITY_MAX_ROWS);
    const remaining = entities.length - ENTITY_MAX_ROWS;

    let html = visible.map((e, i) => `
        <div class="entity-row">
            <span class="entity-rank">${i + 1}</span>
            <span class="entity-name">${e.name}</span>
            <span class="entity-count">${e.count} txn${e.count !== 1 ? 's' : ''}</span>
            <span class="entity-total">${formatCurrency(e.total)}</span>
        </div>
    `).join('');

    if (remaining > 0) {
        html += `<div class="entity-more">+ ${remaining} more</div>`;
    }

    grid.innerHTML = html;
}

function renderEntities() {
    const container = document.getElementById('entitiesContainer');
    const customers = buildEntityData(transactions, 'income');
    const suppliers = buildEntityData(transactions, 'expense');

    if (customers.length === 0 && suppliers.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    renderEntityList(customers, 'customersGrid', 'Customers');
    renderEntityList(suppliers, 'suppliersGrid', 'Suppliers');
}

function switchEntityTab(tab) {
    document.querySelectorAll('.entity-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.entity-tab[data-entity="${tab}"]`).classList.add('active');
    document.getElementById('customersGrid').style.display = tab === 'customers' ? '' : 'none';
    document.getElementById('suppliersGrid').style.display = tab === 'suppliers' ? '' : 'none';
}

// ---- AI Badge ----

function updateAIBadge(available) {
    const badge = document.getElementById('aiBadge');
    if (available) {
        badge.classList.add('active');
        badge.title = 'AI Connected (OpenAI)';
    } else {
        badge.classList.remove('active');
        badge.title = 'AI Offline — using fallback mode';
    }
}

