/**
 * Portfolio Page Logic
 * 포트폴리오 데이터 로드 및 표시
 */

// Get API base URL
const API_BASE = window.API_BASE || window.location.origin;

// Get auth token
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Format number as KRW
function formatKRW(amount) {
    if (!amount && amount !== 0) return '-';
    return Number(amount).toLocaleString('ko-KR') + ' KRW';
}

// Format percentage
function formatPercent(value) {
    if (!value && value !== 0) return '-';
    const sign = value >= 0 ? '+' : '';
    return sign + Number(value).toFixed(2) + '%';
}

// Load portfolio data
async function loadPortfolio() {
    const token = getAuthToken();
    if (!token) {
        console.warn('[Portfolio] No auth token');
        showEmptyState('로그인이 필요합니다');
        return;
    }

    const container = $id('holdings-container');
    if (!container) return;

    // Show skeleton loader
    container.innerHTML = `
        <div class="skeleton-table">
            <div class="skeleton-row">
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
            </div>
            <div class="skeleton-row">
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
            </div>
            <div class="skeleton-row">
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
            </div>
        </div>
    `;

    try {
        // Fetch holdings from API using safeFetch
        const response = await safeFetch(`${API_BASE}/api/holdings`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        const holdings = data.holdings || [];

        // Update summary cards
        updateSummary(holdings);

        // Render holdings table
        if (holdings.length === 0) {
            showEmptyState('보유 중인 자산이 없습니다');
        } else {
            renderHoldingsTable(holdings);
        }

    } catch (error) {
        console.error('[Portfolio] Error loading data:', error);
        showEmptyState('데이터를 불러오는데 실패했습니다');
    }
}

// Update summary cards
function updateSummary(holdings) {
    const totalValue = holdings.reduce((sum, h) => sum + (parseFloat(h.balance) * parseFloat(h.avg_buy_price || 0)), 0);
    const totalInvestment = holdings.reduce((sum, h) => sum + (parseFloat(h.balance) * parseFloat(h.avg_buy_price || 0)), 0);
    const totalProfit = 0; // Calculate based on current prices
    const profitRate = totalInvestment > 0 ? (totalProfit / totalInvestment * 100) : 0;

    const totalValueEl = $id('total-value');
    const totalInvestmentEl = $id('total-investment');
    const totalProfitEl = $id('total-profit');
    const profitRateEl = $id('profit-rate');
    const holdingsCountEl = $id('holdings-count');

    if (totalValueEl) totalValueEl.textContent = formatKRW(totalValue);
    if (totalInvestmentEl) totalInvestmentEl.textContent = formatKRW(totalInvestment);
    if (totalProfitEl) totalProfitEl.textContent = formatKRW(totalProfit);
    if (profitRateEl) profitRateEl.textContent = formatPercent(profitRate);
    if (holdingsCountEl) holdingsCountEl.textContent = holdings.length + '개';

    // Update change colors
    if (profitRateEl) {
        if (profitRate >= 0) {
            profitRateEl.classList.add('positive');
            profitRateEl.classList.remove('negative');
        } else {
            profitRateEl.classList.add('negative');
            profitRateEl.classList.remove('positive');
        }
    }
}

// Render holdings table
function renderHoldingsTable(holdings) {
    const container = $id('holdings-container');
    if (!container) return;

    const tableHTML = `
        <table class="holdings-table">
            <thead>
                <tr>
                    <th>자산</th>
                    <th>보유 수량</th>
                    <th>평균 매수가</th>
                    <th>현재가</th>
                    <th>평가 금액</th>
                    <th>수익/손실</th>
                </tr>
            </thead>
            <tbody>
                ${holdings.map(holding => {
                    const balance = parseFloat(holding.balance) || 0;
                    const avgPrice = parseFloat(holding.avg_buy_price) || 0;
                    const currentPrice = parseFloat(holding.current_price) || avgPrice;
                    const value = balance * currentPrice;
                    const profit = balance * (currentPrice - avgPrice);
                    const profitRate = avgPrice > 0 ? ((currentPrice - avgPrice) / avgPrice * 100) : 0;

                    return `
                        <tr>
                            <td>
                                <div class="coin-info">
                                    <div class="coin-icon">${holding.currency.substring(0, 2).toUpperCase()}</div>
                                    <div>
                                        <div class="coin-name">${holding.currency}</div>
                                        <div class="coin-symbol">${holding.unit_currency}</div>
                                    </div>
                                </div>
                            </td>
                            <td>${balance.toLocaleString('ko-KR', {minimumFractionDigits: 2, maximumFractionDigits: 8})}</td>
                            <td>${formatKRW(avgPrice)}</td>
                            <td>${formatKRW(currentPrice)}</td>
                            <td>${formatKRW(value)}</td>
                            <td>
                                <div class="${profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                                    ${formatKRW(profit)}
                                    <br>
                                    <small>${formatPercent(profitRate)}</small>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// Show empty state
function showEmptyState(message) {
    const container = $id('holdings-container');
    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <p>${message}</p>
        </div>
    `;
}

// Load data on page load
window.addEventListener('DOMContentLoaded', () => {
    loadPortfolio();
});
