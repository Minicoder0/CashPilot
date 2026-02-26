/* ===============================================
   CashPilot — Chart.js Setup
   =============================================== */

const CHART_COLORS = {
    green: '#22c55e',
    greenAlpha: 'rgba(34, 197, 94, 0.6)',
    red: '#ef4444',
    redAlpha: 'rgba(239, 68, 68, 0.6)',
    blue: '#3b82f6',
    blueAlpha: 'rgba(59, 130, 246, 0.6)',
};

const PIE_COLORS = [
    'rgba(239, 68, 68, 0.75)',    // rent - red
    'rgba(245, 158, 11, 0.75)',   // utilities - amber
    'rgba(168, 85, 247, 0.75)',   // payroll - purple
    'rgba(236, 72, 153, 0.75)',   // marketing - pink
    'rgba(59, 130, 246, 0.75)',   // software - blue
    'rgba(6, 182, 212, 0.75)',    // travel - cyan
    'rgba(234, 179, 8, 0.75)',    // supplies - yellow
    'rgba(148, 163, 184, 0.5)',   // other - gray
];

const PIE_BORDERS = [
    'rgba(239, 68, 68, 1)',
    'rgba(245, 158, 11, 1)',
    'rgba(168, 85, 247, 1)',
    'rgba(236, 72, 153, 1)',
    'rgba(59, 130, 246, 1)',
    'rgba(6, 182, 212, 1)',
    'rgba(234, 179, 8, 1)',
    'rgba(148, 163, 184, 0.7)',
];

// Shared Chart.js defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;


function renderCharts() {
    renderCashflowChart();
    renderExpenseChart();
}


/* ---- Monthly Cashflow Bar Chart ---- */

function renderCashflowChart() {
    const ctx = document.getElementById('cashflowChart').getContext('2d');

    // Group by month
    const monthly = {};
    transactions.forEach(t => {
        const month = t.date.substring(0, 7); // YYYY-MM
        if (!monthly[month]) monthly[month] = { income: 0, expenses: 0 };
        if (t.type === 'income') {
            monthly[month].income += t.amount;
        } else {
            monthly[month].expenses += Math.abs(t.amount);
        }
    });

    const sortedMonths = Object.keys(monthly).sort();
    const labels = sortedMonths.map(m => {
        const [y, mo] = m.split('-');
        const date = new Date(parseInt(y), parseInt(mo) - 1);
        return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    });

    const incomeData = sortedMonths.map(m => monthly[m].income);
    const expenseData = sortedMonths.map(m => monthly[m].expenses);
    const netData = sortedMonths.map(m => monthly[m].income - monthly[m].expenses);

    // Destroy previous chart if exists
    if (cashflowChart) cashflowChart.destroy();

    cashflowChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: CHART_COLORS.greenAlpha,
                    borderColor: CHART_COLORS.green,
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false,
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: CHART_COLORS.redAlpha,
                    borderColor: CHART_COLORS.red,
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false,
                },
                {
                    label: 'Net',
                    data: netData,
                    type: 'line',
                    borderColor: CHART_COLORS.blue,
                    borderWidth: 2,
                    pointBackgroundColor: CHART_COLORS.blue,
                    pointBorderColor: '#111827',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    tension: 0.3,
                    fill: false,
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { weight: '600' },
                    callbacks: {
                        label: function (ctx) {
                            return ` ${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                        }
                    }
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { padding: 8 },
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: {
                        padding: 8,
                        callback: val => '$' + (val / 1000).toFixed(0) + 'k'
                    },
                },
            },
        },
    });
}


/* ---- Expense Breakdown Donut Chart ---- */

function renderExpenseChart() {
    const ctx = document.getElementById('expenseChart').getContext('2d');

    // Aggregate expense categories
    const catTotals = {};
    transactions.forEach(t => {
        if (t.type === 'expense') {
            const cat = t.category || 'other';
            catTotals[cat] = (catTotals[cat] || 0) + Math.abs(t.amount);
        }
    });

    // Sort and take top 5 + other
    const sorted = Object.entries(catTotals).sort((a, b) => b[1] - a[1]);
    let labels = [];
    let data = [];
    let otherTotal = 0;

    sorted.forEach((entry, i) => {
        if (i < 5) {
            labels.push(entry[0].charAt(0).toUpperCase() + entry[0].slice(1));
            data.push(entry[1]);
        } else {
            otherTotal += entry[1];
        }
    });

    if (otherTotal > 0) {
        labels.push('Other');
        data.push(otherTotal);
    }

    // Destroy previous chart if exists
    if (expenseChart) expenseChart.destroy();

    expenseChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: PIE_COLORS.slice(0, labels.length),
                borderColor: PIE_BORDERS.slice(0, labels.length),
                borderWidth: 1,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 11 },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function (ctx) {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return ` ${ctx.label}: $${ctx.parsed.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${pct}%)`;
                        }
                    }
                },
            },
        },
    });
}
