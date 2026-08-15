const API_BASE = 'https://nutrition-reflections-caps-millennium.trycloudflare.com';
const API_URL = `${API_BASE}/api/data`;
// DOM Elements
const valRecords = document.getElementById('valRecords');
const valAmount = document.getElementById('valAmount');
const valDistricts = document.getElementById('valDistricts');
const dataTableBody = document.querySelector('#dataTable tbody');
const connectionStatus = document.getElementById('connectionStatus');
const statusDot = document.querySelector('.dot');
const autoRefreshCheckbox = document.getElementById('autoRefresh');
const refreshRateSlider = document.getElementById('refreshRate');
const rateValueDisplay = document.getElementById('rateValue');

const statusAction = document.getElementById('statusAction');
const statusProgress = document.getElementById('statusProgress');
const searchInput = document.getElementById('searchInput');
const btnPrev = document.getElementById('btnPrev');
const btnNext = document.getElementById('btnNext');
const pageIndicator = document.getElementById('pageIndicator');

// Charts
let countChartInstance = null;
let amountChartInstance = null;

// Settings & State
let refreshIntervalId = null;
let currentPage = 1;
let currentSearch = '';
let searchTimeout = null;
let currentSortBy = '';
let currentSortOrder = 'asc';

const btnExport = document.getElementById('btnExport');
const sortableHeaders = document.querySelectorAll('.sortable');

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-GH', { style: 'currency', currency: 'GHS' }).format(amount);
}

function updateStatus(message, state) {
    connectionStatus.textContent = message;
    statusDot.className = `dot ${state}`;
}

function initCharts() {
    const ctxCount = document.getElementById('countChart').getContext('2d');
    const ctxAmount = document.getElementById('amountChart').getContext('2d');

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: { beginAtZero: true }
        }
    };

    countChartInstance = new Chart(ctxCount, {
        type: 'bar',
        data: { labels: [], datasets: [{ data: [], backgroundColor: '#2563eb', borderRadius: 4 }] },
        options: commonOptions
    });

    amountChartInstance = new Chart(ctxAmount, {
        type: 'bar',
        data: { labels: [], datasets: [{ data: [], backgroundColor: '#10b981', borderRadius: 4 }] },
        options: commonOptions
    });
}

function updateCharts(chartsData) {
    // Update Count Chart
    const countLabels = Object.keys(chartsData.top_districts_count);
    const countData = Object.values(chartsData.top_districts_count);
    
    countChartInstance.data.labels = countLabels;
    countChartInstance.data.datasets[0].data = countData;
    countChartInstance.update();

    // Update Amount Chart
    const amountLabels = Object.keys(chartsData.top_districts_amount);
    const amountData = Object.values(chartsData.top_districts_amount);
    
    amountChartInstance.data.labels = amountLabels;
    amountChartInstance.data.datasets[0].data = amountData;
    amountChartInstance.update();
}

function updateTable(entries) {
    dataTableBody.innerHTML = '';
    
    if (entries.length === 0) {
        dataTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No data available yet.</td></tr>';
        return;
    }

    entries.forEach(entry => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: var(--text-muted); font-weight: 600;">${entry['_index']}</td>
            <td>${entry['Facility Name'] || '-'}</td>
            <td>${entry['District'] || '-'}</td>
            <td>${entry['Amount Paid'] || '-'}</td>
            <td>${entry['Claim Month'] || '-'}</td>
            <td>${entry['Payment Date'] || '-'}</td>
        `;
        dataTableBody.appendChild(tr);
    });
}

async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (response.ok) {
            const status = await response.json();
            statusAction.textContent = status.action;
            statusProgress.textContent = `${status.progress} - ${status.detail}`;
        }
    } catch (e) {}
}

async function fetchData() {
    try {
        updateStatus('Fetching...', 'pulsing');
        fetchStatus();
        
        let url = `${API_URL}?page=${currentPage}`;
        if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
        if (currentSortBy) url += `&sort_by=${encodeURIComponent(currentSortBy)}&order=${currentSortOrder}`;
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        
        if (data.error) {
            updateStatus(`Error: ${data.error}`, 'error');
            return;
        }

        // Update Metrics
        valRecords.textContent = data.metrics.total_records.toLocaleString();
        valAmount.textContent = formatCurrency(data.metrics.total_amount);
        valDistricts.textContent = data.metrics.unique_districts;

        // Update UI Components
        updateCharts(data.charts);
        updateTable(data.entries);
        
        // Update Pagination
        const p = data.pagination;
        currentPage = p.page;
        pageIndicator.textContent = `Page ${p.page} of ${p.total_pages} (${p.total_filtered} records)`;
        btnPrev.disabled = (p.page <= 1);
        btnNext.disabled = (p.page >= p.total_pages);
        
        updateStatus('Live', 'success');

    } catch (error) {
        console.error('Fetch error:', error);
        updateStatus('Connection Failed', 'error');
    }
}

function setupAutoRefresh() {
    if (refreshIntervalId) clearInterval(refreshIntervalId);
    
    if (autoRefreshCheckbox.checked) {
        const rateMs = parseInt(refreshRateSlider.value) * 1000;
        refreshIntervalId = setInterval(fetchData, rateMs);
    }
}

// Event Listeners
refreshRateSlider.addEventListener('input', (e) => {
    rateValueDisplay.textContent = e.target.value;
});

refreshRateSlider.addEventListener('change', setupAutoRefresh);
autoRefreshCheckbox.addEventListener('change', setupAutoRefresh);

btnPrev.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        fetchData();
    }
});

btnNext.addEventListener('click', () => {
    currentPage++;
    fetchData();
});

searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentSearch = e.target.value.trim();
        currentPage = 1; // reset to page 1 on new search
        fetchData();
    }, 500); // 500ms debounce
});

btnExport.addEventListener('click', () => {
    let url = `${API_BASE}/api/export?search=${encodeURIComponent(currentSearch)}`;
    if (currentSortBy) url += `&sort_by=${encodeURIComponent(currentSortBy)}&order=${currentSortOrder}`;
    window.location.href = url;
});

sortableHeaders.forEach(header => {
    header.addEventListener('click', () => {
        const sortBy = header.dataset.sort;
        
        if (currentSortBy === sortBy) {
            currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortBy = sortBy;
            currentSortOrder = 'asc';
        }
        
        sortableHeaders.forEach(h => h.removeAttribute('data-order'));
        header.setAttribute('data-order', currentSortOrder);
        
        currentPage = 1;
        fetchData();
    });
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchData();
    setupAutoRefresh();
});
