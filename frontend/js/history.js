/**
 * History Page Logic
 * 거래 내역 데이터 로드 및 표시
 */

// Get API base URL (use existing global if available)
if (typeof API_BASE === 'undefined') {
    var API_BASE = window.API_BASE || window.location.origin;
}

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
    // Handle null, undefined, or invalid values
    if (!dateString || dateString === 'N/A' || dateString === 'Invalid Date' || dateString === 'null' || dateString === 'undefined') {
        return '-';
    }

    // If it's already formatted (YYYY-MM-DD HH:MM:SS), return as-is
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(dateString)) {
        return dateString;
    }

    try {
        // Handle timestamp in milliseconds
        let date;
        if (typeof dateString === 'number') {
            date = new Date(dateString);
        } else if (typeof dateString === 'string') {
            // Try parsing as ISO date (handles 2025-12-27T06:14:00.831091 format)
            date = new Date(dateString);
        } else {
            console.warn('[History] Unexpected date type:', typeof dateString, dateString);
            return '-';
        }

        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.warn('[History] Invalid date:', dateString);
            return '-';
        }

        // Format as readable Korean time (YYYY-MM-DD HH:MM:SS)
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');

        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (e) {
        console.error('[History] Date parsing error:', e, dateString);
        return '-';
    }
}

// Load orders with filters
async function loadOrders() {
    console.log('[History] Loading orders...');
    const token = getAuthToken();
    if (!token) {
        console.warn('[History] No auth token');
        showEmptyState('로그인이 필요합니다');
        return;
    }

    const container = $id('orders-container');
    if (!container) {
        console.warn('[History] Container not found');
        return;
    }
    console.log('[History] Container found, loading data...');

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
            // Use kr_time first (if valid), then fallback to executed_at/created_at
            const dateStrA = (a.kr_time && a.kr_time !== 'N/A') ? a.kr_time : (a.executed_at || a.created_at);
            const dateStrB = (b.kr_time && b.kr_time !== 'N/A') ? b.kr_time : (b.executed_at || b.created_at);

            const dateA = new Date(dateStrA);
            const dateB = new Date(dateStrB);

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
                        <td>${formatDate((order.kr_time && order.kr_time !== 'N/A') ? order.kr_time : (order.executed_at || order.created_at))}</td>
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
function initHistoryPage() {
    console.log('[History] Initializing history page...');
    loadOrders();
}

// Handle both DOMContentLoaded and immediate execution (for dynamic loading)
if (document.readyState === 'loading') {
    // Still loading, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', initHistoryPage);
} else {
    // Already loaded (dynamic page loading), execute immediately
    initHistoryPage();
}
