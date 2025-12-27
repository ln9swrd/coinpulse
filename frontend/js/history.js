/**
 * History Page Logic
 * 거래 내역 데이터 로드 및 표시
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
    return Number(amount).toLocaleString('ko-KR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' KRW';
}

// Format date
function formatDate(dateString) {
    if (!dateString || dateString === 'N/A') return '-';

    // Try parsing as ISO date
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
        // If parsing fails, return the string as-is (might be pre-formatted kr_time)
        return dateString;
    }

    // Format as KST
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Seoul'
    });
}

// Load orders with filters
async function loadOrders() {
    const token = getAuthToken();
    if (!token) {
        console.warn('[History] No auth token');
        showEmptyState('로그인이 필요합니다');
        return;
    }

    const container = $id('orders-container');
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
                <div class="skeleton-cell skeleton-shimmer"></div>
                <div class="skeleton-cell skeleton-shimmer"></div>
            </div>
        </div>
    `;

    try {
        // Get filter values
        const typeFilter = $id('filter-type')?.value || 'all';
        const stateFilter = $id('filter-state')?.value || 'all';
        const sortFilter = $id('filter-sort')?.value || 'recent';

        // Fetch orders from API using safeFetch
        const response = await safeFetch(`${API_BASE}/api/orders`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        let orders = data.orders || [];

        // Apply filters
        if (typeFilter !== 'all') {
            orders = orders.filter(o => o.side === typeFilter);
        }
        if (stateFilter !== 'all') {
            orders = orders.filter(o => o.state === stateFilter);
        }

        // Apply sorting
        orders.sort((a, b) => {
            const dateA = new Date(a.executed_at || a.created_at);
            const dateB = new Date(b.executed_at || b.created_at);
            return sortFilter === 'recent' ? dateB - dateA : dateA - dateB;
        });

        // Render orders
        if (orders.length === 0) {
            showEmptyState('거래 내역이 없습니다');
        } else {
            renderOrdersTable(orders);
        }

    } catch (error) {
        console.error('[History] Error loading orders:', error);
        showEmptyState('거래 내역을 불러오는데 실패했습니다');
    }
}

// Render orders table
function renderOrdersTable(orders) {
    const container = $id('orders-container');
    if (!container) return;

    const tableHTML = `
        <table class="orders-table">
            <thead>
                <tr>
                    <th>시각</th>
                    <th>마켓</th>
                    <th>유형</th>
                    <th>상태</th>
                    <th>주문 수량</th>
                    <th>체결 수량</th>
                    <th>주문 가격</th>
                    <th>체결 금액</th>
                </tr>
            </thead>
            <tbody>
                ${orders.map(order => `
                    <tr>
                        <td>${formatDate(order.kr_time || order.executed_at || order.created_at)}</td>
                        <td><strong>${order.market}</strong></td>
                        <td>
                            <span class="badge ${order.side === 'bid' ? 'badge-buy' : 'badge-sell'}">
                                ${order.side === 'bid' ? '매수' : '매도'}
                            </span>
                        </td>
                        <td>
                            <span class="badge ${order.state === 'done' ? 'badge-done' : 'badge-cancel'}">
                                ${order.state === 'done' ? '체결 완료' : order.state === 'cancel' ? '취소됨' : order.state}
                            </span>
                        </td>
                        <td>${parseFloat(order.volume || 0).toFixed(8)}</td>
                        <td>${parseFloat(order.executed_volume || 0).toFixed(8)}</td>
                        <td>${formatKRW(order.price)}</td>
                        <td>${formatKRW(order.paid_fee ? parseFloat(order.paid_fee) : 0)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

// Show empty state
function showEmptyState(message) {
    const container = $id('orders-container');
    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <p>${message}</p>
        </div>
    `;
}

// Load data on page load
window.addEventListener('DOMContentLoaded', () => {
    loadOrders();
});
