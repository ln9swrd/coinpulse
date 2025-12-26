/**
 * CoinPulse Dashboard JavaScript
 * Handles dashboard navigation, content loading, and user session
 */

(function() {
    'use strict';

    // ============================================
    // 1. Dashboard Manager Class
    // ============================================
    class DashboardManager {
        constructor() {
            this.currentPage = 'overview';
            this.user = null;
            this.init();
        }

        async init() {
            // Check authentication
            await this.checkAuth();

            // Initialize UI components
            this.initSidebar();
            this.initNavigation();
            this.initNotificationsButton();
            this.initUserMenu();
            this.initLogout();

            // Load initial page
            this.loadPage('overview');

            console.log('[Dashboard] Initialized successfully');
        }

        // ============================================
        // Authentication
        // ============================================
        async checkAuth() {
            try {
                // Check if user is authenticated using window.api
                if (!window.api || !window.api.isAuthenticated()) {
                    console.warn('[Dashboard] User not authenticated, redirecting to login');
                    window.location.href = 'login.html';
                    return;
                }

                // Get user data from API
                try {
                    const response = await window.api.getCurrentUser();
                    if (response.success && response.user) {
                        this.user = response.user;
                    }
                } catch (error) {
                    console.error('[Dashboard] Failed to get user profile:', error);
                    return;
                }

                // Update UI with user info
                this.updateUserInfo();

                console.log('[Dashboard] User authenticated:', this.user?.email || 'unknown');
            } catch (error) {
                console.error('[Dashboard] Auth check failed:', error);
                window.location.href = 'login.html';
            }
        }

        updateUserInfo() {
            if (!this.user) return;

            // Update user name and email
            const userNameEl = document.getElementById('user-name');
            const userEmailEl = document.getElementById('user-email');
            const userInitialEl = document.getElementById('user-initial');
            const userInitialSmallEl = document.getElementById('user-initial-small');

            if (userNameEl) userNameEl.textContent = this.user.username || 'User';
            if (userEmailEl) userEmailEl.textContent = this.user.email || '';

            // Set user initial (first letter of name)
            const initial = (this.user.username || this.user.email || 'U')[0].toUpperCase();
            if (userInitialEl) userInitialEl.textContent = initial;
            if (userInitialSmallEl) userInitialSmallEl.textContent = initial;
        }

        // ============================================
        // Sidebar
        // ============================================
        initSidebar() {
            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.getElementById('sidebar-toggle');
            const mobileMenuToggle = document.getElementById('mobile-menu-toggle');

            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', () => {
                    sidebar.classList.toggle('collapsed');
                    localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
                });
            }

            if (mobileMenuToggle) {
                mobileMenuToggle.addEventListener('click', () => {
                    sidebar.classList.toggle('mobile-open');
                });
            }

            // Close sidebar on mobile when clicking outside
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768) {
                    if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                        sidebar.classList.remove('mobile-open');
                    }
                }
            });

            // Restore sidebar state
            const sidebarCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
            }
        }

        // ============================================
        // Navigation
        // ============================================
        initNavigation() {
            const navItems = document.querySelectorAll('.nav-item[data-page]');

            navItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();

                    const page = item.getAttribute('data-page');
                    this.loadPage(page);

                    // Update active state
                    navItems.forEach(nav => nav.classList.remove('active'));
                    item.classList.add('active');

                    // Close mobile sidebar
                    if (window.innerWidth <= 768) {
                        document.getElementById('sidebar').classList.remove('mobile-open');
                    }
                });
            });

            // Handle hash changes (browser back/forward)
            window.addEventListener('hashchange', () => {
                const hash = window.location.hash.substring(1);
                if (hash) {
                    this.loadPage(hash);
                }
            });
        }

        // ============================================
        // Load Page Content
        // ============================================
        async loadPage(pageName) {
            this.currentPage = pageName;

            // Update page title
            const pageTitle = document.getElementById('page-title');
            const titles = {
                'overview': '개요',
                'trading': '거래 차트',
                'portfolio': '포트폴리오',
                'auto-trading': '자동 거래',
                'history': '거래 내역',
                'settings': '설정'
            };

            if (pageTitle) {
                pageTitle.textContent = titles[pageName] || '대시보드';
            }

            // Update URL hash
            window.location.hash = pageName;

            // Load page content
            const contentContainer = document.getElementById('content-container');

            try {
                // Check if this is an external page (handled by page-loader in dashboard.html)
                // External pages: trading, signals, telegram, realtime, surge, auto-trading, referral, admin, surge-history, my-feedback
                const externalPages = ['trading', 'signals', 'telegram', 'realtime', 'surge', 'auto-trading', 'referral', 'admin', 'surge-history', 'my-feedback'];
                if (externalPages.includes(pageName)) {
                    console.log('[Dashboard] External page detected, skipping dashboard-fixed.js loader:', pageName);
                    return; // Let dashboard.html handle it
                }

                contentContainer.innerHTML = '<div class="loading-state"><div class="spinner-large"></div><p>Loading...</p></div>';

                // Load page-specific content
                let content = '';

                switch (pageName) {
                    case 'overview':
                        content = await this.loadOverviewPage();
                        break;
                    case 'portfolio':
                        content = await this.loadPortfolioPage();
                        break;
                    // NOTE: auto-trading now handled by dashboard-page-loader.js (loads surge_auto_trading.html via iframe)
                    case 'history':
                        content = await this.loadHistoryPage();
                        break;
                    case 'settings':
                        content = await this.loadSettingsPage();
                        break;
                    case 'pricing':
                        content = await this.loadPricingPage();
                        break;
                    default:
                        content = '<div class="text-center mt-lg"><h2>Page not found</h2></div>';
                }

                contentContainer.innerHTML = content;

                // Wait for DOM to update before initializing scripts
                await new Promise(resolve => setTimeout(resolve, 100));

                // Initialize page-specific scripts
                await this.initPageScripts(pageName);

            } catch (error) {
                console.error(`[Dashboard] Error loading ${pageName}:`, error);
                contentContainer.innerHTML = '<div class="text-center mt-lg"><h2>Error loading page</h2><p>Please try again</p></div>';
            }
        }

        // ============================================
        // Page Content Loaders
        // ============================================
        async loadOverviewPage() {
            return `
                <div class="overview-page">
                    <!-- Welcome Section -->
                    <div class="welcome-section">
                        <h1>환영합니다, ${this.user.username || '트레이더'}님!</h1>
                        <p>포트폴리오 개요입니다</p>
                    </div>

                    <!-- Stats Grid -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>포트폴리오 가치</h3>
                            <p class="stat-value" id="portfolio-value">불러오는 중...</p>
                            <div class="stat-change" id="portfolio-change">
                                <span>--</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>총 손익</h3>
                            <p class="stat-value" id="total-profit">불러오는 중...</p>
                            <div class="stat-change" id="profit-change">
                                <span>--</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>보유 자산</h3>
                            <p class="stat-value" id="holdings-count">불러오는 중...</p>
                            <div class="stat-change neutral">
                                <span id="holdings-label">활성 포지션</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>승률</h3>
                            <p class="stat-value" id="win-rate">불러오는 중...</p>
                            <div class="stat-change" id="win-rate-change">
                                <span id="trades-count">-- 거래</span>
                            </div>
                        </div>
                    </div>

                    <!-- Portfolio Chart -->
                    <div class="portfolio-chart-container">
                        <h2>포트폴리오 성과</h2>
                        <div id="portfolio-performance-container" style="padding: 40px; background: white; border: 1px solid #e0e0e0; border-radius: 12px;">
                            <div class="loading-state">
                                <div class="spinner-small"></div>
                                <p>포트폴리오 성과 데이터 로딩 중...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Current Holdings -->
                    <div class="holdings-section">
                        <h2>현재 보유 자산</h2>
                        <div id="holdings-table-container">
                            <div class="loading-state">
                                <div class="spinner-large"></div>
                                <p>보유 자산 불러오는 중...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="recent-activity">
                        <h2>최근 거래 활동</h2>
                        <div id="recent-activity-container">
                            <div class="loading-state">
                                <div class="spinner-large"></div>
                                <p>거래 활동 불러오는 중...</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }


        async loadPortfolioPage() {
            return `
                <div class="portfolio-page">
                    <div class="page-header">
                        <h2>포트폴리오 성과</h2>
                        <button class="btn-refresh" onclick="window.dashboardApp.refreshPortfolioData()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                            </svg>
                            새로고침
                        </button>
                    </div>

                    <!-- Summary Cards -->
                    <div id="portfolio-summary" class="portfolio-summary">
                        <div class="loading-state">
                            <div class="spinner-small"></div>
                            <p>포트폴리오 데이터 로딩 중...</p>
                        </div>
                    </div>

                    <!-- Holdings Table -->
                    <div class="dashboard-card" style="margin-top: 24px;">
                        <div class="card-header">
                            <h3>보유 자산 상세</h3>
                        </div>
                        <div class="card-content" id="portfolio-holdings-table">
                            <div class="loading-state">
                                <div class="spinner-small"></div>
                                <p>보유 자산 로딩 중...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <style>
                    .portfolio-page {
                        padding: 24px;
                    }

                    .page-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 24px;
                    }

                    .page-header h2 {
                        margin: 0;
                        font-size: 28px;
                        font-weight: 700;
                        color: #1a1a1a;
                    }

                    .btn-refresh {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 10px 20px;
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: 500;
                        color: #333;
                        transition: all 0.2s;
                    }

                    .btn-refresh:hover {
                        background: #f5f5f5;
                        border-color: #d0d0d0;
                    }

                    .portfolio-summary {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin-bottom: 24px;
                    }

                    .summary-card {
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        padding: 24px;
                        transition: all 0.2s;
                    }

                    .summary-card:hover {
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                        transform: translateY(-2px);
                    }

                    .summary-card-label {
                        font-size: 14px;
                        color: #666;
                        margin-bottom: 8px;
                    }

                    .summary-card-value {
                        font-size: 32px;
                        font-weight: 700;
                        color: #1a1a1a;
                        margin-bottom: 8px;
                    }

                    .summary-card-value.profit {
                        color: #10b981;
                    }

                    .summary-card-value.loss {
                        color: #ef4444;
                    }

                    .summary-card-change {
                        font-size: 14px;
                        font-weight: 600;
                    }

                    .summary-card-change.profit {
                        color: #10b981;
                    }

                    .summary-card-change.loss {
                        color: #ef4444;
                    }

                    .holdings-table {
                        width: 100%;
                        border-collapse: collapse;
                    }

                    .holdings-table th {
                        text-align: left;
                        padding: 12px;
                        background: #f8f9fa;
                        font-weight: 600;
                        font-size: 14px;
                        color: #333;
                        border-bottom: 2px solid #e0e0e0;
                    }

                    .holdings-table td {
                        padding: 16px 12px;
                        border-bottom: 1px solid #f0f0f0;
                        font-size: 14px;
                    }

                    .holdings-table tr:hover {
                        background: #f8f9fa;
                    }

                    .coin-name {
                        font-weight: 600;
                        color: #1a1a1a;
                    }

                    .profit-cell {
                        font-weight: 600;
                        color: #10b981;
                    }

                    .loss-cell {
                        font-weight: 600;
                        color: #ef4444;
                    }

                    .loading-state {
                        text-align: center;
                        padding: 60px 20px;
                        color: #666;
                    }

                    .spinner-small {
                        border: 3px solid #f3f3f3;
                        border-top: 3px solid #667eea;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 16px;
                    }

                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            `;
        }

        async loadAutoTradingPage() {
            return `
                <div class="auto-trading-page">
                    <div style="max-width: 1200px; margin: 0 auto;">
                        <div class="dashboard-card">
                            <div class="card-header">
                                <h2>자동 거래 상태</h2>
                                <button class="btn-refresh" onclick="if(window.loadAutoTradingStatus) window.loadAutoTradingStatus()">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                                    </svg>
                                    새로고침
                                </button>
                            </div>
                            <div class="card-content" id="auto-trading-container">
                                <div class="loading-state">
                                    <div class="spinner-small"></div>
                                    <p>자동 거래 상태 로딩 중...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }


        async loadHistoryPage() {
            const html = `
                <div class="history-page">
                    <div class="history-controls">
                        <div class="filter-buttons">
                            <button class="filter-btn active" data-filter="all">전체</button>
                            <button class="filter-btn" data-filter="bid">매수</button>
                            <button class="filter-btn" data-filter="ask">매도</button>
                        </div>
                    </div>

                    <div id="history-table-container">
                        <div class="loading-spinner">
                            <div class="spinner"></div>
                            <p>거래 내역을 불러오는 중...</p>
                        </div>
                    </div>
                </div>
            `;

            // Load orders after rendering
            setTimeout(() => this.loadOrderHistory(), 100);

            return html;
        }

        async loadOrderHistory(filter = 'all') {
            try {
                const container = document.getElementById('history-table-container');
                if (!container) return;

                // Show loading
                container.innerHTML = `
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>거래 내역을 불러오는 중...</p>
                    </div>
                `;

                // Use defensive API_BASE (avoid global variable conflicts)
                const API_BASE = window.API_BASE || window.location.origin;
                const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
                const response = await fetch(`${API_BASE}/api/orders`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to load orders');
                }

                const data = await response.json();
                let orders = data.orders || [];

                // Apply filter
                if (filter !== 'all') {
                    orders = orders.filter(order => order.side === filter);
                }

                if (orders.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"></circle>
                                <path d="M12 6v6l4 2"></path>
                            </svg>
                            <h3>거래 내역 없음</h3>
                            <p>아직 거래 내역이 없습니다</p>
                        </div>
                    `;
                    return;
                }

                // Build table
                let tableHTML = `
                    <div class="history-table-wrapper">
                        <table class="history-table">
                            <thead>
                                <tr>
                                    <th>시간</th>
                                    <th>코인</th>
                                    <th>타입</th>
                                    <th>가격</th>
                                    <th>수량</th>
                                    <th>총액</th>
                                    <th>상태</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                orders.forEach(order => {
                    const date = new Date(order.created_at || order.executed_at);
                    const dateStr = date.toLocaleDateString('ko-KR', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    const market = order.market || 'N/A';
                    const coin = market.replace('KRW-', '');
                    const side = order.side === 'bid' ? '매수' : '매도';
                    const sideClass = order.side === 'bid' ? 'buy' : 'sell';
                    const price = parseFloat(order.price || 0).toLocaleString('ko-KR');
                    const volume = parseFloat(order.volume || 0).toFixed(8);
                    const total = (parseFloat(order.price || 0) * parseFloat(order.volume || 0)).toLocaleString('ko-KR');
                    const state = order.state === 'done' ? '완료' : order.state === 'cancel' ? '취소' : '대기';

                    tableHTML += `
                        <tr>
                            <td>${dateStr}</td>
                            <td><strong>${coin}</strong></td>
                            <td><span class="side-badge ${sideClass}">${side}</span></td>
                            <td>₩${price}</td>
                            <td>${volume}</td>
                            <td>₩${total}</td>
                            <td><span class="state-badge">${state}</span></td>
                        </tr>
                    `;
                });

                tableHTML += `
                            </tbody>
                        </table>
                    </div>
                `;

                container.innerHTML = tableHTML;

                // Setup filter buttons
                this.setupHistoryFilters();

            } catch (error) {
                console.error('Error loading order history:', error);
                const container = document.getElementById('history-table-container');
                if (container) {
                    container.innerHTML = `
                        <div class="error-state">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                            <h3>오류 발생</h3>
                            <p>거래 내역을 불러올 수 없습니다</p>
                        </div>
                    `;
                }
            }
        }

        setupHistoryFilters() {
            const filterBtns = document.querySelectorAll('.filter-btn');
            filterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    // Update active state
                    filterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    // Load with filter
                    const filter = btn.dataset.filter;
                    this.loadOrderHistory(filter);
                });
            });
        }

        async loadSettingsPage() {
            return `
                <style>
                    .coin-search-container {
                        position: relative;
                        margin-bottom: 16px;
                    }
                    .coin-search-wrapper {
                        position: relative;
                    }
                    .coin-dropdown {
                        position: absolute;
                        top: 100%;
                        left: 0;
                        right: 0;
                        margin-top: 4px;
                        background: var(--card-bg, white);
                        border: 1px solid var(--border-color, #e5e7eb);
                        border-radius: 8px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        max-height: 300px;
                        overflow-y: auto;
                        z-index: 1000;
                    }
                    .coin-dropdown-loading {
                        padding: 16px;
                        text-align: center;
                        color: var(--text-muted, #666);
                    }
                    .coin-dropdown-list {
                        padding: 4px 0;
                    }
                    .coin-dropdown-item {
                        padding: 12px 16px;
                        cursor: pointer;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        transition: background 0.2s;
                    }
                    .coin-dropdown-item:hover {
                        background: var(--hover-bg, #f3f4f6);
                    }
                    .coin-dropdown-item.disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }
                    .coin-dropdown-item.disabled:hover {
                        background: transparent;
                    }
                    .coin-dropdown-item-info {
                        display: flex;
                        flex-direction: column;
                    }
                    .coin-dropdown-item-name {
                        font-weight: 600;
                        margin-bottom: 2px;
                    }
                    .coin-dropdown-item-symbol {
                        font-size: 12px;
                        color: var(--text-muted, #666);
                    }
                    .coin-dropdown-no-results {
                        padding: 16px;
                        text-align: center;
                        color: var(--text-muted, #666);
                    }
                    .selected-coins-tags {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-bottom: 12px;
                        min-height: 40px;
                    }
                    .coin-tag {
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 12px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border-radius: 20px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                    .coin-tag-remove {
                        cursor: pointer;
                        width: 16px;
                        height: 16px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        transition: background 0.2s;
                    }
                    .coin-tag-remove:hover {
                        background: rgba(255, 255, 255, 0.5);
                    }
                </style>
                <div class="settings-page">
                    <!-- Settings Tabs -->
                    <div class="settings-tabs">
                        <button class="settings-tab active" data-tab="account">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            <span>계정</span>
                        </button>
                        <button class="settings-tab" data-tab="api-keys">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <span>API 키</span>
                        </button>
                        <button class="settings-tab" data-tab="trading">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                            </svg>
                            <span>관심 코인</span>
                        </button>
                        <button class="settings-tab" data-tab="notifications">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            <span>알림</span>
                        </button>
                    </div>

                    <!-- Settings Content -->
                    <div class="settings-content">
                        <!-- Account Settings Tab -->
                        <div class="settings-tab-content active" data-tab-content="account">
                            <div class="settings-section">
                                <h2>프로필 정보</h2>
                                <form id="profile-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="settings-username">사용자 이름</label>
                                        <input type="text" id="settings-username" value="${this.user.username || ''}" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="settings-email">이메일</label>
                                        <input type="email" id="settings-email" value="${this.user.email || ''}" required>
                                    </div>
                                    <button type="submit" class="btn-primary">변경사항 저장</button>
                                </form>
                            </div>

                            <div class="settings-section">
                                <h2>비밀번호 변경</h2>
                                <form id="password-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="current-password">현재 비밀번호</label>
                                        <input type="password" id="current-password" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="new-password">새 비밀번호</label>
                                        <input type="password" id="new-password" required minlength="8">
                                    </div>
                                    <div class="form-group">
                                        <label for="confirm-password">새 비밀번호 확인</label>
                                        <input type="password" id="confirm-password" required minlength="8">
                                    </div>
                                    <button type="submit" class="btn-primary">비밀번호 변경</button>
                                </form>
                            </div>

                            <div class="settings-section danger-zone">
                                <h2>위험 구역</h2>
                                <p>계정을 삭제하면 되돌릴 수 없습니다. 신중하게 결정하세요.</p>
                                <button class="btn-danger" id="delete-account-btn">계정 삭제</button>
                            </div>
                        </div>

                        <!-- API Keys Tab -->
                        <div class="settings-tab-content" data-tab-content="api-keys">
                            <div class="settings-section">
                                <h2>업비트 API 키</h2>
                                <p>업비트 계정을 연결하여 실시간 거래 및 포트폴리오 추적을 활성화하세요.</p>

                                <!-- API Key Guide (shown when no keys) -->
                                <div id="api-key-guide" style="display: none; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                                    <h3 style="margin: 0 0 16px 0; font-size: 18px; display: flex; align-items: center; gap: 8px;">
                                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="12" cy="12" r="10"></circle>
                                            <line x1="12" y1="16" x2="12" y2="12"></line>
                                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                                        </svg>
                                        업비트 API 키가 등록되지 않았습니다
                                    </h3>
                                    <p style="margin: 0 0 20px 0; opacity: 0.95; line-height: 1.6;">
                                        코인펄스를 사용하려면 업비트 API 키가 필요합니다. 아래 가이드를 따라 API 키를 발급받고 등록하세요.
                                    </p>

                                    <details style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px; margin-bottom: 12px;">
                                        <summary style="cursor: pointer; font-weight: 600; font-size: 15px; list-style: none; display: flex; align-items: center; gap: 8px;">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <polyline points="6 9 12 15 18 9"></polyline>
                                            </svg>
                                            📝 1단계: 업비트에서 API 키 발급하기
                                        </summary>
                                        <div style="margin-top: 16px; padding-left: 28px; line-height: 1.8; font-size: 14px;">
                                            <ol style="margin: 0; padding-left: 20px;">
                                                <li><strong>업비트 웹사이트 접속</strong><br>
                                                    <a href="https://upbit.com" target="_blank" style="color: #fff; text-decoration: underline;">https://upbit.com</a></li>
                                                <li><strong>로그인</strong> 후 우측 상단 <strong>'마이페이지'</strong> 클릭</li>
                                                <li>좌측 메뉴에서 <strong>'Open API 관리'</strong> 선택</li>
                                                <li><strong>'Open API Key 발급'</strong> 버튼 클릭</li>
                                                <li><strong>권한 설정</strong> (필수):
                                                    <ul style="margin-top: 8px;">
                                                        <li>✅ <strong>자산 조회</strong> (필수)</li>
                                                        <li>✅ <strong>주문 조회</strong> (필수)</li>
                                                        <li>⚠️ <strong>주문하기</strong> (자동거래 사용 시 필요)</li>
                                                        <li>❌ <strong>출금하기</strong> (절대 선택 금지)</li>
                                                    </ul>
                                                </li>
                                                <li><strong>IP 주소 등록</strong>:
                                                    <ul style="margin-top: 8px;">
                                                        <li>특정 IP만 허용 (권장)</li>
                                                        <li>또는 모든 IP 허용 (보안 위험)</li>
                                                    </ul>
                                                </li>
                                                <li><strong>발급된 키 복사</strong>:
                                                    <ul style="margin-top: 8px;">
                                                        <li>Access Key (공개 키)</li>
                                                        <li>Secret Key (비밀 키)</li>
                                                        <li style="color: #ffeb3b;">⚠️ Secret Key는 다시 볼 수 없으니 안전하게 보관하세요!</li>
                                                    </ul>
                                                </li>
                                            </ol>
                                        </div>
                                    </details>

                                    <details style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                                        <summary style="cursor: pointer; font-weight: 600; font-size: 15px; list-style: none; display: flex; align-items: center; gap: 8px;">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <polyline points="6 9 12 15 18 9"></polyline>
                                            </svg>
                                            🔑 2단계: 코인펄스에 API 키 등록하기
                                        </summary>
                                        <div style="margin-top: 16px; padding-left: 28px; line-height: 1.8; font-size: 14px;">
                                            <ol style="margin: 0; padding-left: 20px;">
                                                <li>아래 <strong>'액세스 키'</strong> 입력 필드에 복사한 Access Key 붙여넣기</li>
                                                <li><strong>'시크릿 키'</strong> 입력 필드에 복사한 Secret Key 붙여넣기</li>
                                                <li><strong>'연결 테스트'</strong> 버튼 클릭하여 키 유효성 확인</li>
                                                <li>테스트 성공 시 <strong>'API 키 저장'</strong> 버튼 클릭</li>
                                                <li>✅ 완료! 이제 코인펄스의 모든 기능을 사용할 수 있습니다</li>
                                            </ol>
                                        </div>
                                    </details>

                                    <div style="margin-top: 16px; padding: 12px; background: rgba(255,235,59,0.2); border-left: 4px solid #ffeb3b; border-radius: 4px;">
                                        <strong>🔒 보안 안내</strong>
                                        <ul style="margin: 8px 0 0 20px; line-height: 1.6; font-size: 13px;">
                                            <li>API 키는 암호화되어 저장되며, 절대 제3자와 공유하지 마세요</li>
                                            <li>Secret Key는 마스킹 처리되어 표시됩니다</li>
                                            <li>의심스러운 활동 발견 시 즉시 업비트에서 키를 삭제하세요</li>
                                        </ul>
                                    </div>
                                </div>

                                <form id="api-keys-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="api-access-key">
                                            액세스 키
                                            <button type="button" id="edit-access-key-btn" class="btn-link" style="display: none; margin-left: 10px; font-size: 12px;">변경</button>
                                        </label>
                                        <input type="text" id="api-access-key" placeholder="업비트 액세스 키를 입력하세요" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="api-secret-key">시크릿 키</label>
                                        <input type="password" id="api-secret-key" placeholder="업비트 시크릿 키를 입력하세요" required>
                                        <small style="color: var(--text-muted); font-size: 12px; margin-top: 5px; display: block;">
                                            보안상 시크릿 키는 마스킹 처리되어 표시됩니다
                                        </small>
                                    </div>
                                    <div class="form-actions">
                                        <button type="button" class="btn-secondary" id="test-api-btn">연결 테스트</button>
                                        <button type="submit" class="btn-primary">API 키 저장</button>
                                    </div>
                                </form>

                                <div id="api-test-result" class="api-test-result" style="display: none;"></div>
                            </div>
                        </div>

                        <!-- Favorite Coins Tab -->
                        <div class="settings-tab-content" data-tab-content="trading">
                            <div class="settings-section">
                                <h2>투자조언 알림 설정 <span style="background: #fbbf24; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 8px;">준비 중</span></h2>
                                <p style="color: var(--text-muted); margin-bottom: 20px;">
                                    선택한 코인에 대한 AI 투자 조언을 받을 수 있는 기능입니다. 매수/매도 타이밍, 목표가, 손절가 등을 분석하여 텔레그램으로 알림을 보내드립니다.
                                </p>

                                <!-- Coming Soon Alert -->
                                <div class="info-alert" style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                                    <div style="display: flex; align-items: start; gap: 12px;">
                                        <span style="font-size: 32px;">🚧</span>
                                        <div>
                                            <strong style="color: #92400e; font-size: 16px; display: block; margin-bottom: 8px;">투자조언 알림 기능 개발 중</strong>
                                            <p style="color: #92400e; font-size: 14px; line-height: 1.6; margin: 0;">
                                                현재 투자조언 알림 시스템은 개발 중입니다. AI 기반 투자 조언 엔진과 알림 시스템을 구축하고 있으며,
                                                곧 베타 테스트를 시작할 예정입니다.
                                            </p>
                                            <p style="color: #92400e; font-size: 14px; line-height: 1.6; margin: 12px 0 0 0;">
                                                <strong>출시 예정 기능:</strong><br>
                                                • 매수/매도 타이밍 추천 (신뢰도 점수 포함)<br>
                                                • 목표가 및 손절가 계산<br>
                                                • 기술적 지표 분석 및 근거 제공<br>
                                                • 텔레그램 실시간 알림
                                            </p>
                                            <p style="color: #92400e; font-size: 13px; margin-top: 12px;">
                                                💡 현재는 <strong>급등 자동매매</strong> 기능을 이용해주세요. (사이드바 > 자동매매 설정)
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <!-- Disabled Coin Selection Section -->
                                <div class="coin-selector-section" style="opacity: 0.5; pointer-events: none; user-select: none;">
                                    <h3>코인 선택 (최대 5개)</h3>

                                    <!-- Search Input with Dropdown -->
                                    <div class="coin-search-container">
                                        <div class="coin-search-wrapper">
                                            <input
                                                type="text"
                                                id="coin-search-input"
                                                placeholder="코인 이름 또는 심볼을 검색하세요 (예: 비트코인, BTC)"
                                                autocomplete="off"
                                                style="width: 100%; padding: 12px 40px 12px 12px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 14px;"
                                            >
                                            <svg style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; pointer-events: none;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                            </svg>
                                        </div>
                                        <div id="coin-dropdown" class="coin-dropdown" style="display: none;">
                                            <div id="coin-dropdown-loading" class="coin-dropdown-loading">
                                                코인 목록을 불러오는 중...
                                            </div>
                                            <div id="coin-dropdown-list" class="coin-dropdown-list"></div>
                                        </div>
                                    </div>

                                    <!-- Selected Coins Tags -->
                                    <div class="selected-coins-tags" id="selected-coins-tags"></div>

                                    <div class="selected-coins-count">
                                        선택됨: <span id="selected-count">0</span>/5
                                    </div>
                                </div>

                                <!-- Individual Coin Settings -->
                                <div class="coin-settings-section" id="coin-settings-container">
                                    <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                                        관심 코인을 선택하면 각 코인별 설정이 여기에 표시됩니다.
                                    </p>
                                </div>

                                <button type="button" class="btn-primary" id="save-trading-settings">전체 설정 저장</button>
                            </div>
                        </div>

                        <!-- Notifications Tab -->
                        <div class="settings-tab-content" data-tab-content="notifications">
                            <div class="settings-section">
                                <h2>이메일 알림</h2>
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 24px;">
                                    <h3 style="margin: 0 0 8px 0; font-size: 16px; display: flex; align-items: center; gap: 8px;">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="12" cy="12" r="10"></circle>
                                            <line x1="12" y1="8" x2="12" y2="12"></line>
                                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                        </svg>
                                        추후 구현 예정
                                    </h3>
                                    <p style="margin: 0; opacity: 0.9; font-size: 14px; line-height: 1.5;">
                                        이메일 알림 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려 주세요.
                                    </p>
                                </div>
                                <form id="notifications-form" class="settings-form">
                                    <div class="form-group checkbox-group">
                                        <label style="opacity: 0.5; cursor: not-allowed;">
                                            <input type="checkbox" id="notify-trades" disabled>
                                            <span>거래 확인</span>
                                        </label>
                                        <p class="help-text">거래가 실행될 때 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label style="opacity: 0.5; cursor: not-allowed;">
                                            <input type="checkbox" id="notify-price-alerts" disabled>
                                            <span>가격 알림</span>
                                        </label>
                                        <p class="help-text">목표 가격에 도달할 때 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label style="opacity: 0.5; cursor: not-allowed;">
                                            <input type="checkbox" id="notify-portfolio" disabled>
                                            <span>일일 포트폴리오 요약</span>
                                        </label>
                                        <p class="help-text">포트폴리오 성과를 담은 일일 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label style="opacity: 0.5; cursor: not-allowed;">
                                            <input type="checkbox" id="notify-marketing" disabled>
                                            <span>마케팅 이메일</span>
                                        </label>
                                        <p class="help-text">새로운 기능 및 프로모션 업데이트 수신</p>
                                    </div>
                                    <button type="submit" class="btn-primary" disabled style="opacity: 0.5; cursor: not-allowed;">설정 저장</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // ============================================
        // Initialize Page-Specific Scripts
        // ============================================
        async initPageScripts(pageName) {
            switch (pageName) {
                case 'overview':
                    await this.initOverviewPage();
                    break;
                case 'trading':
                    // Trading chart has its own scripts
                    break;
                case 'portfolio':
                    await this.initPortfolioPage();
                    break;
                case 'auto-trading':
                    await this.initAutoTradingPage();
                    break;
                case 'swing-trading':
                    // Swing trading iframe has its own scripts
                    break;
                case 'settings':
                    await this.initSettingsPage();
                    break;
                case 'pricing':
                    await this.initPricingPage();
                    break;
                // Add more page initializers as needed
            }
        }

        async initOverviewPage() {
            console.log('[Dashboard] Initializing overview page');

            try {
                // Fetch all required data in parallel
                console.log('[DEBUG] Fetching holdings and orders...');
                const [holdingsData, ordersData] = await Promise.all([
                    this.fetchHoldings(),
                    this.fetchOrders()
                ]);

                console.log('[DEBUG] Data fetched successfully');
                console.log('[DEBUG] holdingsData:', holdingsData);
                console.log('[DEBUG] ordersData:', ordersData);

                // Calculate and update stats
                console.log('[DEBUG] Updating portfolio stats...');
                this.updatePortfolioStats(holdingsData, ordersData);

                // Display holdings table
                console.log('[DEBUG] Calling displayHoldingsTable...');
                await this.displayHoldingsTable(holdingsData);

                // Display portfolio performance
                console.log('[DEBUG] Displaying portfolio performance...');
                this.displayPortfolioPerformance(holdingsData, ordersData);

                // Display recent activity
                console.log('[DEBUG] Displaying recent activity...');
                this.displayRecentActivity(ordersData);

                console.log('[Dashboard] Overview page loaded successfully');
            } catch (error) {
                console.error('[Dashboard] Error loading overview data:', error);
                console.error('[DEBUG] Error stack:', error.stack);
                this.showOverviewError();
            }
        }

        async fetchHoldings() {
            try {
                // Load config to get API URL
                const config = await this.loadConfig();
                const apiUrl = config?.api?.tradingServerUrl || 'http://localhost:8081';

                const response = await fetch(`${apiUrl}/api/holdings`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                // API 응답 형식: { coins: [...], krw: {...}, summary: {...} }
                // API 필드명을 JavaScript 필드명으로 매핑
                const summary = data.summary || {};
                return {
                    coins: data.coins || [],
                    krw: data.krw || { balance: 0, locked: 0, total: 0 },
                    summary: {
                        total_value: summary.total_value_krw || 0,
                        total_profit: summary.total_profit_loss_krw || 0,
                        coin_count: summary.coin_count || 0,
                        profit_rate: summary.total_profit_rate || 0
                    }
                };
            } catch (error) {
                console.error('[Dashboard] Error fetching holdings:', error);
                return { coins: [], krw: { balance: 0, locked: 0, total: 0 }, summary: { total_value: 0, total_profit: 0, coin_count: 0, profit_rate: 0 } };
            }
        }

        async fetchOrders() {
            try {
                const config = await this.loadConfig();
                const apiUrl = config?.api?.tradingServerUrl || 'http://localhost:8081';

                const response = await fetch(`${apiUrl}/api/orders?limit=50`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                return data.orders || [];
            } catch (error) {
                console.error('[Dashboard] Error fetching orders:', error);
                return [];
            }
        }

        async loadConfig() {
            try {
                const response = await fetch('config.json');
                const config = await response.json();

                // "auto" 값을 현재 origin으로 변환 (환경 자동 감지)
                if (config?.api?.chartServerUrl === 'auto') {
                    config.api.chartServerUrl = window.location.origin;
                }
                if (config?.api?.tradingServerUrl === 'auto') {
                    config.api.tradingServerUrl = window.location.origin;
                }

                return config;
            } catch (error) {
                console.error('[Dashboard] Error loading config:', error);
                return null;
            }
        }

        updatePortfolioStats(holdingsData, orders) {
            // holdingsData는 { coins: [...], krw: {...}, summary: {...} } 형식
            const { coins, krw, summary } = holdingsData;

            // summary에서 계산된 값 사용
            const totalValue = summary.total_value || 0;
            const totalProfit = summary.total_profit || 0;
            const profitRate = summary.profit_rate || 0;
            const coinCount = summary.coin_count || 0;

            // Calculate win rate
            const completedTrades = orders.filter(o => o.state === 'done');
            const winningTrades = completedTrades.filter(o => {
                // Simple heuristic: buy at lower price than current
                return parseFloat(o.profit || 0) > 0;
            });
            const winRate = completedTrades.length > 0
                ? (winningTrades.length / completedTrades.length) * 100
                : 0;

            // Update DOM with null checks
            const portfolioValueEl = document.getElementById('portfolio-value');
            if (portfolioValueEl) {
                portfolioValueEl.textContent = `₩${this.formatNumber(totalValue)}`;
            }

            const portfolioChange = document.getElementById('portfolio-change');
            if (portfolioChange) {
                portfolioChange.innerHTML = `<span>${profitRate >= 0 ? '▲' : '▼'} ${Math.abs(profitRate).toFixed(2)}%</span>`;
                portfolioChange.className = `stat-change ${profitRate >= 0 ? 'positive' : 'negative'}`;
            }

            const totalProfitEl = document.getElementById('total-profit');
            if (totalProfitEl) {
                totalProfitEl.textContent = `₩${this.formatNumber(Math.abs(totalProfit))}`;
            }

            const profitChange = document.getElementById('profit-change');
            if (profitChange) {
                profitChange.innerHTML = `<span>${totalProfit >= 0 ? '수익' : '손실'}</span>`;
                profitChange.className = `stat-change ${totalProfit >= 0 ? 'positive' : 'negative'}`;
            }

            const holdingsCountEl = document.getElementById('holdings-count');
            if (holdingsCountEl) {
                holdingsCountEl.textContent = coinCount;
            }

            const winRateEl = document.getElementById('win-rate');
            if (winRateEl) {
                winRateEl.textContent = `${winRate.toFixed(1)}%`;
            }

            const tradesCountEl = document.getElementById('trades-count');
            if (tradesCountEl) {
                tradesCountEl.textContent = `${completedTrades.length}건`;
            }
        }

        async displayHoldingsTable(holdingsData) {
            console.log('[DEBUG] displayHoldingsTable called');
            console.log('[DEBUG] holdingsData:', holdingsData);
            console.log('[DEBUG] holdingsData.coins:', holdingsData?.coins);
            console.log('[DEBUG] holdingsData.coins length:', holdingsData?.coins?.length);

            // Try to find container with retry logic
            let container = null;
            let attempts = 0;
            const maxAttempts = 10;

            while (!container && attempts < maxAttempts) {
                // Try both container IDs (overview page and portfolio page)
                container = document.getElementById('holdings-table-container');
                if (!container) {
                    container = document.getElementById('portfolio-holdings-table');
                }

                if (!container) {
                    attempts++;
                    console.log(`[DEBUG] Container not found, retry ${attempts}/${maxAttempts}`);
                    await new Promise(resolve => setTimeout(resolve, 50));
                }
            }

            console.log('[DEBUG] container found:', !!container);
            console.log('[DEBUG] container element:', container);

            if (!container) {
                console.warn('[Dashboard] No holdings table container found after retries');
                return;
            }

            // holdingsData는 { coins: [...], krw: {...}, summary: {...} } 형식
            const coins = holdingsData.coins || [];
            console.log('[DEBUG] coins after extraction:', coins);
            console.log('[DEBUG] coins.length:', coins.length);

            if (coins.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <h3>아직 보유 자산이 없습니다</h3>
                        <p>거래를 시작하여 포트폴리오를 확인하세요</p>
                    </div>
                `;
                return;
            }

            let tableHTML = `
                <table class="holdings-table">
                    <thead>
                        <tr>
                            <th>자산</th>
                            <th>수량</th>
                            <th>평균 매수가</th>
                            <th>현재가</th>
                            <th>손익</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            coins.forEach(coin => {
                const balance = parseFloat(coin.balance || 0);
                const avgPrice = parseFloat(coin.avg_price || 0);
                const currentPrice = parseFloat(coin.current_price || 0);
                const currentValue = parseFloat(coin.total_value || 0);
                const profitLoss = parseFloat(coin.profit_loss || 0);
                const profitPercent = parseFloat(coin.profit_rate || 0);
                const market = coin.market || `KRW-${coin.coin}`;
                const coinName = coin.name || coin.coin;

                const coinSymbol = coin.coin.toUpperCase();
                const logoUrl = `https://static.upbit.com/logos/${coinSymbol}.png`;

                tableHTML += `
                    <tr class="holding-row" data-market="${market}" style="cursor: pointer;">
                        <td>
                            <div class="coin-info">
                                <img src="${logoUrl}"
                                     alt="${coinSymbol}"
                                     class="coin-logo"
                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                     style="width: 32px; height: 32px; border-radius: 50%; margin-right: 12px;">
                                <div class="coin-icon" style="display: none;">${coin.coin.substring(0, 2).toUpperCase()}</div>
                                <div>
                                    <div class="coin-name">${coinName}</div>
                                    <div class="coin-symbol">${market}</div>
                                </div>
                            </div>
                        </td>
                        <td>${balance.toFixed(8)}</td>
                        <td>₩${this.formatNumber(avgPrice)}</td>
                        <td>₩${this.formatNumber(currentPrice)}</td>
                        <td>
                            <div class="stat-change ${profitLoss >= 0 ? 'positive' : 'negative'}">
                                ${profitLoss >= 0 ? '▲' : '▼'} ₩${this.formatNumber(Math.abs(profitLoss))}
                                (${Math.abs(profitPercent).toFixed(2)}%)
                            </div>
                        </td>
                    </tr>
                `;
            });

            tableHTML += `
                    </tbody>
                </table>
            `;

            console.log('[DEBUG] About to set container.innerHTML');
            console.log('[DEBUG] tableHTML length:', tableHTML.length);
            console.log('[DEBUG] tableHTML preview:', tableHTML.substring(0, 200));

            container.innerHTML = tableHTML;

            console.log('[DEBUG] container.innerHTML updated successfully');

            // Add click handlers to navigate to trading chart
            setTimeout(() => {
                const holdingRows = document.querySelectorAll('.holding-row');
                holdingRows.forEach(row => {
                    row.addEventListener('click', () => {
                        const market = row.getAttribute('data-market');
                        console.log(`[Dashboard] Navigating to trading chart: ${market}`);
                        this.navigateToTrading(market);
                    });
                });
            }, 100);
        }

        navigateToTrading(market) {
            // Update hash to include market parameter
            window.location.hash = `trading&market=${market}`;

            // Load trading page
            this.loadPage('trading');

            // Update active nav item
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            document.querySelector('.nav-item[data-page="trading"]')?.classList.add('active');
        }

        displayRecentActivity(orders) {
            const container = document.getElementById('recent-activity-container');
            if (!container) {
                console.warn('[Dashboard] recent-activity-container not found');
                return;
            }

            if (!orders || orders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v6l4 2"></path>
                        </svg>
                        <h3>최근 활동 없음</h3>
                        <p>거래 내역이 여기에 표시됩니다</p>
                    </div>
                `;
                return;
            }

            // Show only last 10 orders
            const recentOrders = orders.slice(0, 10);

            let activityHTML = '<div class="activity-list">';

            recentOrders.forEach(order => {
                const isBuy = order.side === 'bid';
                const date = new Date(order.created_at);
                const timeAgo = this.getTimeAgo(date);

                activityHTML += `
                    <div class="activity-item" data-market="${order.market}" style="cursor: pointer;">
                        <div class="activity-icon ${isBuy ? 'buy' : 'sell'}">
                            ${isBuy ? '📈' : '📉'}
                        </div>
                        <div class="activity-details">
                            <div class="activity-title">
                                ${isBuy ? '매수' : '매도'} ${order.market}
                            </div>
                            <div class="activity-subtitle">
                                ${parseFloat(order.volume || 0).toFixed(8)} @ ₩${this.formatNumber(parseFloat(order.price || 0))}
                            </div>
                        </div>
                        <div>
                            <div class="activity-amount ${isBuy ? 'negative' : 'positive'}">
                                ${isBuy ? '-' : '+'}₩${this.formatNumber(parseFloat(order.price || 0) * parseFloat(order.volume || 0))}
                            </div>
                            <div class="activity-time">${timeAgo}</div>
                        </div>
                    </div>
                `;
            });

            activityHTML += '</div>';
            container.innerHTML = activityHTML;

            // Add click handlers to navigate to trading chart
            setTimeout(() => {
                const activityItems = document.querySelectorAll('.activity-item[data-market]');
                activityItems.forEach(item => {
                    item.addEventListener('click', () => {
                        const market = item.getAttribute('data-market');
                        console.log(`[Dashboard] Navigating to trading chart from activity: ${market}`);
                        this.navigateToTrading(market);
                    });
                });
            }, 100);
        }

        displayPortfolioPerformance(holdingsData, orders) {
            const container = document.getElementById('portfolio-performance-container');
            if (!container) return;

            const { summary, coins } = holdingsData;
            const totalValue = summary.total_value || 0;
            const totalProfit = summary.total_profit || 0;
            const profitRate = summary.profit_rate || 0;

            // Calculate win rate
            const completedTrades = orders.filter(o => o.state === 'done');
            const winningTrades = completedTrades.filter(o => {
                const isSell = o.side === 'ask';
                if (!isSell) return false;
                const profit = (parseFloat(o.avg_price || 0) - parseFloat(o.price || 0)) * parseFloat(o.executed_volume || 0);
                return profit > 0;
            });
            const winRate = completedTrades.length > 0 ? (winningTrades.length / completedTrades.length * 100) : 0;

            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px;">
                    <div style="text-align: center;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">총 자산 가치</div>
                        <div style="font-size: 32px; font-weight: 700; color: #1a1a1a;">₩${this.formatNumber(totalValue)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">총 손익</div>
                        <div style="font-size: 32px; font-weight: 700; color: ${totalProfit >= 0 ? '#10b981' : '#ef4444'};">
                            ${totalProfit >= 0 ? '+' : ''}₩${this.formatNumber(totalProfit)}
                        </div>
                        <div style="font-size: 14px; color: ${totalProfit >= 0 ? '#10b981' : '#ef4444'};">
                            ${totalProfit >= 0 ? '▲' : '▼'} ${Math.abs(profitRate).toFixed(2)}%
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">승률</div>
                        <div style="font-size: 32px; font-weight: 700; color: #1a1a1a;">${winRate.toFixed(1)}%</div>
                        <div style="font-size: 14px; color: #666;">${completedTrades.length}건 완료</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">보유 코인</div>
                        <div style="font-size: 32px; font-weight: 700; color: #1a1a1a;">${coins.length}</div>
                        <div style="font-size: 14px; color: #666;">활성 포지션</div>
                    </div>
                </div>
                <div style="margin-top: 24px; text-align: center;">
                    <button onclick="window.dashboardApp.loadPage('portfolio')" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 12px 32px;
                        border-radius: 8px;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s;
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.5)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';">
                        상세 포트폴리오 보기
                    </button>
                </div>
            `;
        }

        formatNumber(num) {
            // Format as full Korean Won with comma separators, no decimals
            return Math.round(num).toLocaleString('ko-KR');
        }

        getTimeAgo(date) {
            const seconds = Math.floor((new Date() - date) / 1000);

            if (seconds < 60) return '방금';
            if (seconds < 3600) return `${Math.floor(seconds / 60)}분 전`;
            if (seconds < 86400) return `${Math.floor(seconds / 3600)}시간 전`;
            if (seconds < 604800) return `${Math.floor(seconds / 86400)}일 전`;
            return date.toLocaleDateString();
        }

        showOverviewError() {
            const statsCards = ['portfolio-value', 'total-profit', 'holdings-count', 'win-rate'];
            statsCards.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = '오류';
            });

            const holdingsContainer = document.getElementById('holdings-table-container');
            if (holdingsContainer) {
                holdingsContainer.innerHTML = `
                    <div class="empty-state">
                        <h3>데이터 불러오기 실패</h3>
                        <p>페이지를 새로고침해주세요</p>
                    </div>
                `;
            }

            const activityContainer = document.getElementById('recent-activity-container');
            if (activityContainer) {
                activityContainer.innerHTML = `
                    <div class="empty-state">
                        <h3>활동 내역 불러오기 실패</h3>
                        <p>페이지를 새로고침해주세요</p>
                    </div>
                `;
            }
        }

        async initPortfolioPage() {
            console.log('[Dashboard] Portfolio page initialized');
            await this.loadPortfolioData();
        }

        async initAutoTradingPage() {
            console.log('[Dashboard] Auto-trading page initialized');
            // Call the loadAutoTradingStatus function from dashboard.html
            if (window.loadAutoTradingStatus) {
                await window.loadAutoTradingStatus();
            } else {
                console.warn('[Dashboard] loadAutoTradingStatus function not found');
            }
        }

        async loadPortfolioData() {
            const summaryContainer = document.getElementById('portfolio-summary');
            const tableContainer = document.getElementById('portfolio-holdings-table');

            if (!summaryContainer || !tableContainer) return;

            // Check if user has API keys
            const currentUser = await this.getCurrentUser();
            if (!currentUser || !currentUser.has_upbit_keys) {
                const emptyStateHTML = `
                    <div style="text-align: center; padding: 60px 20px; grid-column: 1 / -1;">
                        <div style="font-size: 64px; margin-bottom: 20px;">🔑</div>
                        <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                            업비트 API 키가 등록되지 않았습니다
                        </h3>
                        <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                            포트폴리오 성과를 확인하려면<br>
                            업비트 API 키를 먼저 등록해주세요.
                        </p>
                        <button onclick="window.dashboardApp.loadPage('settings')" style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 12px 32px;
                            border-radius: 8px;
                            font-size: 15px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.2s;
                            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.5)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';">
                            API 키 등록하기
                        </button>
                    </div>
                `;
                summaryContainer.innerHTML = emptyStateHTML;
                tableContainer.innerHTML = emptyStateHTML;
                return;
            }

            try {
                // Fetch holdings data
                const response = await window.api.getHoldings();

                if (!response.success) {
                    throw new Error(response.error || 'Failed to fetch holdings');
                }

                const coins = response.coins || [];

                // Calculate summary statistics
                let totalValue = 0;
                let totalInvested = 0;

                coins.forEach(coin => {
                    const value = parseFloat(coin.total_value || 0);
                    const invested = parseFloat(coin.balance || 0) * parseFloat(coin.avg_price || 0);
                    totalValue += value;
                    totalInvested += invested;
                });

                const totalProfit = totalValue - totalInvested;
                const totalProfitRate = totalInvested > 0 ? (totalProfit / totalInvested * 100) : 0;

                // Display summary cards
                this.displayPortfolioSummary({
                    totalValue,
                    totalInvested,
                    totalProfit,
                    totalProfitRate,
                    coinsCount: coins.length
                });

                // Display holdings table
                await this.displayHoldingsTable({ coins: coins, krw: {}, summary: {} });

            } catch (error) {
                console.error('[Dashboard] Failed to load portfolio:', error);
                summaryContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #dc3545; grid-column: 1 / -1;">
                        <p>포트폴리오 로딩 실패. 페이지를 새로고침하거나 API 키를 확인하세요.</p>
                    </div>
                `;
                tableContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #dc3545;">
                        <p>데이터를 불러올 수 없습니다.</p>
                    </div>
                `;
            }
        }

        displayPortfolioSummary(data) {
            const container = document.getElementById('portfolio-summary');
            if (!container) return;

            const { totalValue, totalInvested, totalProfit, totalProfitRate, coinsCount } = data;

            container.innerHTML = `
                <div class="summary-card">
                    <div class="summary-card-label">총 자산 가치</div>
                    <div class="summary-card-value">
                        ₩${totalValue.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}
                    </div>
                    <div class="summary-card-change">
                        보유 코인: ${coinsCount}개
                    </div>
                </div>

                <div class="summary-card">
                    <div class="summary-card-label">총 투자금</div>
                    <div class="summary-card-value">
                        ₩${totalInvested.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}
                    </div>
                </div>

                <div class="summary-card">
                    <div class="summary-card-label">총 손익</div>
                    <div class="summary-card-value ${totalProfit >= 0 ? 'profit' : 'loss'}">
                        ${totalProfit >= 0 ? '+' : ''}₩${totalProfit.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}
                    </div>
                    <div class="summary-card-change ${totalProfitRate >= 0 ? 'profit' : 'loss'}">
                        ${totalProfitRate >= 0 ? '+' : ''}${totalProfitRate.toFixed(2)}%
                    </div>
                </div>
            `;
        }


        async refreshPortfolioData() {
            console.log('[Dashboard] Refreshing portfolio data...');
            await this.loadPortfolioData();
        }

        async getCurrentUser() {
            try {
                const response = await window.api.getCurrentUser();
                return response.success ? response.user : null;
            } catch (error) {
                console.error('[Dashboard] Failed to get current user:', error);
                return null;
            }
        }

        initSettingsPage() {
            console.log('[Dashboard] Settings page initialized');

            // Initialize tab switching
            this.initSettingsTabs();

            // Initialize forms
            this.initProfileForm();
            this.initPasswordForm();
            this.initAPIKeysForm();
            this.initTradingPrefsForm();
            this.initNotificationsForm();
            this.initDeleteAccount();
        }

        initSettingsTabs() {
            const tabs = document.querySelectorAll('.settings-tab');
            const tabContents = document.querySelectorAll('.settings-tab-content');

            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabName = tab.getAttribute('data-tab');

                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');

                    // Update active content
                    tabContents.forEach(content => {
                        if (content.getAttribute('data-tab-content') === tabName) {
                            content.classList.add('active');
                        } else {
                            content.classList.remove('active');
                        }
                    });
                });
            });
        }

        initProfileForm() {
            const form = document.getElementById('profile-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const username = document.getElementById('settings-username').value.trim();
                const email = document.getElementById('settings-email').value.trim();

                try {
                    // TODO: Call API to update profile
                    console.log('[Settings] Updating profile:', { username, email });

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, '프로필이 성공적으로 업데이트되었습니다!');

                    // Update user data
                    this.user.username = username;
                    this.user.email = email;
                    localStorage.setItem('user_data', JSON.stringify(this.user));
                    this.updateUserInfo();

                } catch (error) {
                    console.error('[Settings] Profile update error:', error);
                    this.showError(form, '프로필 업데이트 실패. 다시 시도해주세요.');
                }
            });
        }

        initPasswordForm() {
            const form = document.getElementById('password-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const currentPassword = document.getElementById('current-password').value;
                const newPassword = document.getElementById('new-password').value;
                const confirmPassword = document.getElementById('confirm-password').value;

                // Validate passwords match
                if (newPassword !== confirmPassword) {
                    this.showError(form, '새 비밀번호가 일치하지 않습니다');
                    return;
                }

                // Validate password strength
                if (newPassword.length < 8) {
                    this.showError(form, '비밀번호는 최소 8자 이상이어야 합니다');
                    return;
                }

                try {
                    // TODO: Call API to change password
                    console.log('[Settings] Changing password');

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, '비밀번호가 성공적으로 변경되었습니다!');

                    // Clear form
                    form.reset();

                } catch (error) {
                    console.error('[Settings] Password change error:', error);
                    this.showError(form, '비밀번호 변경 실패. 현재 비밀번호를 확인해주세요.');
                }
            });
        }

        async initAPIKeysForm() {
            const form = document.getElementById('api-keys-form');
            const testBtn = document.getElementById('test-api-btn');
            const resultDiv = document.getElementById('api-test-result');
            const accessKeyInput = document.getElementById('api-access-key');
            const secretKeyInput = document.getElementById('api-secret-key');

            if (!form || !testBtn) return;

            // Load existing API keys
            try {
                console.log('[Settings] Loading API keys...');
                const token = localStorage.getItem('access_token');
                if (!token) {
                    console.error('[Settings] No access token found');
                    return;
                }

                const response = await fetch('/api/user/api-keys', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        const editBtn = document.getElementById('edit-access-key-btn');
                        const guideDiv = document.getElementById('api-key-guide');
                        const hasApiKeys = data.access_key && data.secret_key_masked;

                        // Show guide if no API keys
                        if (!hasApiKeys && guideDiv) {
                            guideDiv.style.display = 'block';
                            console.log('[Settings] API key guide displayed (no keys found)');
                        }

                        // Display access key (if exists)
                        if (data.access_key) {
                            accessKeyInput.value = data.access_key;
                            accessKeyInput.setAttribute('readonly', 'readonly');
                            accessKeyInput.style.backgroundColor = 'var(--input-disabled-bg, #f5f5f5)';
                            accessKeyInput.style.color = '#2563eb';
                            accessKeyInput.style.fontWeight = '600';

                            // Add visual indicator
                            const accessKeyLabel = accessKeyInput.previousElementSibling;
                            if (accessKeyLabel && accessKeyLabel.tagName === 'LABEL') {
                                const existingBadge = accessKeyLabel.querySelector('.key-loaded-badge');
                                if (!existingBadge) {
                                    const badge = document.createElement('span');
                                    badge.className = 'key-loaded-badge';
                                    badge.textContent = '✓ 등록됨';
                                    badge.style.cssText = 'color: #22c55e; font-size: 12px; font-weight: 600; margin-left: 8px;';
                                    accessKeyLabel.appendChild(badge);
                                }
                            }

                            // Show edit button
                            if (editBtn) {
                                editBtn.style.display = 'inline-block';
                                editBtn.addEventListener('click', () => {
                                    accessKeyInput.removeAttribute('readonly');
                                    accessKeyInput.style.backgroundColor = '';
                                    accessKeyInput.style.color = '';
                                    accessKeyInput.style.fontWeight = '';
                                    accessKeyInput.focus();
                                    editBtn.style.display = 'none';
                                    console.log('[Settings] Access key edit mode enabled');
                                });
                            }

                            console.log('[Settings] Access key loaded and displayed');
                        }

                        // Display masked secret key as placeholder
                        if (data.secret_key_masked) {
                            secretKeyInput.placeholder = `저장된 키: ${data.secret_key_masked} (변경하려면 새 키 입력)`;
                            secretKeyInput.style.backgroundColor = 'var(--input-disabled-bg, #f5f5f5)';

                            // Add visual indicator
                            const secretKeyLabel = secretKeyInput.previousElementSibling;
                            if (secretKeyLabel && secretKeyLabel.tagName === 'LABEL') {
                                const existingBadge = secretKeyLabel.querySelector('.key-loaded-badge');
                                if (!existingBadge) {
                                    const badge = document.createElement('span');
                                    badge.className = 'key-loaded-badge';
                                    badge.textContent = '✓ 등록됨';
                                    badge.style.cssText = 'color: #22c55e; font-size: 12px; font-weight: 600; margin-left: 8px;';
                                    secretKeyLabel.appendChild(badge);
                                }
                            }

                            console.log('[Settings] Secret key masked displayed');
                        }

                        // Show success message if both keys are loaded
                        if (data.access_key && data.secret_key_masked) {
                            // Create success notification
                            const successMsg = document.createElement('div');
                            successMsg.style.cssText = `
                                background: #dcfce7;
                                border: 1px solid #86efac;
                                border-radius: 8px;
                                padding: 12px 16px;
                                margin-bottom: 16px;
                                color: #166534;
                                font-size: 14px;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                            `;
                            successMsg.innerHTML = `
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                                </svg>
                                <span><strong>API 키가 등록되어 있습니다.</strong> 변경하려면 "변경" 버튼을 클릭하세요.</span>
                            `;

                            // Insert before form
                            form.parentElement.insertBefore(successMsg, form);
                        }
                    }
                }
            } catch (error) {
                console.error('[Settings] Failed to load API keys:', error);
                // Show guide on error (assume no keys)
                const guideDiv = document.getElementById('api-key-guide');
                if (guideDiv) {
                    guideDiv.style.display = 'block';
                }
            }

            // Test API connection
            testBtn.addEventListener('click', async () => {
                const accessKey = document.getElementById('api-access-key').value.trim();
                const secretKey = document.getElementById('api-secret-key').value.trim();

                if (!accessKey || !secretKey) {
                    this.showAPITestResult('error', '액세스 키와 시크릿 키를 모두 입력해주세요');
                    return;
                }

                testBtn.disabled = true;
                testBtn.textContent = '테스트 중...';

                try {
                    // TODO: Call API to test Upbit connection
                    console.log('[Settings] Testing API connection');

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 2000));

                    this.showAPITestResult('success', '✓ API 연결 성공! 키가 유효합니다.');

                } catch (error) {
                    console.error('[Settings] API test error:', error);
                    this.showAPITestResult('error', '✗ API 연결 실패. 키를 확인해주세요.');
                } finally {
                    testBtn.disabled = false;
                    testBtn.textContent = '연결 테스트';
                }
            });

            // Save API keys
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const accessKey = document.getElementById('api-access-key').value.trim();
                const secretKey = document.getElementById('api-secret-key').value.trim();

                if (!accessKey || !secretKey) {
                    this.showError(form, '액세스 키와 시크릿 키를 모두 입력하세요');
                    return;
                }

                try {
                    console.log('[Settings] Saving API keys');

                    // Call API to save keys
                    const response = await window.api.updateProfile({
                        upbit_access_key: accessKey,
                        upbit_secret_key: secretKey
                    });

                    if (response.success) {
                        this.showSuccess(form, 'API 키가 안전하게 저장되었습니다');

                        // Hide guide after successful save
                        const guideDiv = document.getElementById('api-key-guide');
                        if (guideDiv) {
                            guideDiv.style.display = 'none';
                        }

                        // Reload API keys to show saved values
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);

                        console.log('[Settings] API keys saved successfully');
                    } else {
                        throw new Error(response.error || 'Unknown error');
                    }
                } catch (error) {
                    console.error('[Settings] API keys save error:', error);
                    this.showError(form, 'API 키 저장 실패: ' + error.message);
                }
            });
        }

        initTradingPrefsForm() {
            const form = document.getElementById('trading-prefs-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const defaultMarket = document.getElementById('default-market').value;
                const riskTolerance = document.getElementById('risk-tolerance').value;
                const autoTradingEnabled = document.getElementById('auto-trading-enabled').checked;
                const stopLossEnabled = document.getElementById('stop-loss-enabled').checked;

                try {
                    // TODO: Call API to save preferences
                    console.log('[Settings] Saving trading preferences:', {
                        defaultMarket,
                        riskTolerance,
                        autoTradingEnabled,
                        stopLossEnabled
                    });

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, '거래 설정이 성공적으로 저장되었습니다!');

                } catch (error) {
                    console.error('[Settings] Trading prefs save error:', error);
                    this.showError(form, '설정 저장 실패. 다시 시도해주세요.');
                }
            });
        }

        initNotificationsForm() {
            const form = document.getElementById('notifications-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const notifyTrades = document.getElementById('notify-trades').checked;
                const notifyPriceAlerts = document.getElementById('notify-price-alerts').checked;
                const notifyPortfolio = document.getElementById('notify-portfolio').checked;
                const notifyMarketing = document.getElementById('notify-marketing').checked;

                try {
                    // TODO: Call API to save notification preferences
                    console.log('[Settings] Saving notification preferences:', {
                        notifyTrades,
                        notifyPriceAlerts,
                        notifyPortfolio,
                        notifyMarketing
                    });

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, '알림 설정이 성공적으로 저장되었습니다!');

                } catch (error) {
                    console.error('[Settings] Notification prefs save error:', error);
                    this.showError(form, '설정 저장 실패. 다시 시도해주세요.');
                }
            });
        }

        initDeleteAccount() {
            const deleteBtn = document.getElementById('delete-account-btn');
            if (!deleteBtn) return;

            deleteBtn.addEventListener('click', () => {
                const confirmed = confirm(
                    '정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.\n\n' +
                    '거래 내역 및 설정을 포함한 모든 데이터가 영구적으로 삭제됩니다.'
                );

                if (confirmed) {
                    const doubleCheck = confirm(
                        '마지막 확인입니다. 정말로 계정을 삭제하시겠습니까?'
                    );

                    if (doubleCheck) {
                        this.deleteAccount();
                    }
                }
            });
        }

        async deleteAccount() {
            try {
                // TODO: Call API to delete account
                console.log('[Settings] Deleting account');

                // Mock response
                await new Promise(resolve => setTimeout(resolve, 1000));

                alert('Your account has been deleted. You will be logged out.');

                // Logout
                await this.logout();

            } catch (error) {
                console.error('[Settings] Account deletion error:', error);
                alert('Failed to delete account. Please contact support.');
            }
        }

        showSuccess(form, message) {
            // Remove existing messages
            const existingMsg = form.querySelector('.success-message, .error-message');
            if (existingMsg) existingMsg.remove();

            // Add success message
            const msgDiv = document.createElement('div');
            msgDiv.className = 'success-message';
            msgDiv.textContent = message;
            form.insertBefore(msgDiv, form.firstChild);

            // Remove after 5 seconds
            setTimeout(() => msgDiv.remove(), 5000);
        }

        showError(form, message) {
            // Remove existing messages
            const existingMsg = form.querySelector('.success-message, .error-message');
            if (existingMsg) existingMsg.remove();

            // Add error message
            const msgDiv = document.createElement('div');
            msgDiv.className = 'error-message';
            msgDiv.textContent = message;
            form.insertBefore(msgDiv, form.firstChild);

            // Remove after 5 seconds
            setTimeout(() => msgDiv.remove(), 5000);
        }

        showAPITestResult(type, message) {
            const resultDiv = document.getElementById('api-test-result');
            if (!resultDiv) return;

            resultDiv.className = `api-test-result ${type}`;
            resultDiv.textContent = message;
            resultDiv.style.display = 'block';

            // Remove after 10 seconds
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 10000);
        }

        // ============================================
        // Pricing Page
        // ============================================
        async loadPricingPage() {
            return `
                <div class="pricing-page">
                    <!-- Pricing Header -->
                    <div class="pricing-header">
                        <h1>요금제 선택</h1>
                        <p>투명하고 합리적인 가격으로 성장하세요</p>
                    </div>

                    <!-- Billing Toggle -->
                    <div class="billing-toggle">
                        <span class="billing-option active" data-billing="monthly">월간</span>
                        <div class="toggle-switch" id="billing-toggle">
                            <div class="toggle-slider"></div>
                        </div>
                        <span class="billing-option" data-billing="annual">
                            연간
                            <span class="billing-badge">20% 절약</span>
                        </span>
                    </div>

                    <!-- Pricing Cards -->
                    <div class="pricing-grid">
                        <!-- Free Plan -->
                        <div class="pricing-card">
                            <div class="plan-header">
                                <h3 class="plan-name">Free</h3>
                                <p class="plan-description">무료로 시작하기</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount">0</span>
                                <span class="price-period" data-fixed="true">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>대시보드 조회</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>포트폴리오 조회</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>거래 내역 조회</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>거래 차트 조회만</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>거래 주문 불가</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>급등 신호 알림 불가</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>자동 매매 불가</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-secondary" data-plan="free">
                                현재 플랜
                            </button>
                        </div>

                        <!-- Basic Plan -->
                        <div class="pricing-card">
                            <div class="plan-header">
                                <h3 class="plan-name">Basic</h3>
                                <p class="plan-description">입문 트레이더용</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount" data-monthly="29000" data-annual="278400">29,000</span>
                                <span class="price-period">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Free 플랜 모든 기능</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>수동 거래 주문 (매수/매도/취소)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>기본 기술적 지표 (MA, RSI, MACD)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>포트폴리오 추적 (5개 코인)</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-secondary" data-plan="basic">
                                베이직으로 시작하기
                            </button>
                        </div>

                        <!-- Pro Plan (Highlighted) -->
                        <div class="pricing-card pricing-card-featured">
                            <div class="featured-badge">인기</div>
                            <div class="plan-header">
                                <h3 class="plan-name">Pro</h3>
                                <p class="plan-description">전문 트레이더용</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount" data-monthly="59000" data-annual="566400">59,000</span>
                                <span class="price-period">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Basic 플랜 모든 기능</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>고급 기술적 지표 (Ichimoku, SuperTrend)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>고급 차트 분석 도구 (그리기, 패턴)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>포트폴리오 추적 (10개 코인)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>데이터 내보내기 (CSV)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>우선 고객 지원</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-primary" data-plan="pro">
                                프로로 업그레이드
                            </button>
                        </div>

                        <!-- Enterprise Plan -->
                        <div class="pricing-card featured">
                            <div class="plan-badge">프리미엄</div>
                            <div class="plan-header">
                                <h3 class="plan-name">Enterprise</h3>
                                <p class="plan-description">기관 투자자 및 전문가를 위한 맞춤형 솔루션</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-amount" style="font-size: 1.5rem;">영업문의</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Pro 플랜 모든 기능</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>급등 예측 무제한 조회</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>자동매매 무제한 전략 (AI 최적화)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>텔레그램 실시간 알림 (모든 신호)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>포트폴리오 추적 (무제한 코인)</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>백테스트 및 성과 분석</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>우선 고객 지원</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-primary" data-plan="enterprise">
                                엔터프라이즈로 업그레이드
                            </button>
                        </div>
                    </div>

                    <!-- FAQ Section -->
                    <div class="pricing-faq">
                        <h2>자주 묻는 질문</h2>
                        <div class="faq-grid">
                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>요금제를 변경할 수 있나요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>네! 언제든지 요금제를 업그레이드하거나 다운그레이드할 수 있습니다. 변경사항은 다음 결제 주기부터 적용됩니다.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>어떤 결제 수단을 지원하나요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>현재 계좌 이체만 지원합니다. 입금 확인 후 관리자가 수동으로 플랜을 활성화합니다. 신용카드 결제는 추후 도입 예정입니다.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>무료 체험이 있나요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>Free 플랜은 영구 무료로 사용 가능합니다. 유료 플랜은 계좌 이체 결제 후 즉시 활성화되며, 별도의 무료 체험 기간은 없습니다.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>해지하면 어떻게 되나요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>언제든지 해지할 수 있습니다. 계정은 결제 기간 종료까지 활성 상태로 유지되며, 이후 Free 요금제로 전환됩니다.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>환불이 가능한가요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>연간 요금제의 경우 30일 환불 보장 정책을 제공합니다. 질문 없이 전액 환불해드립니다.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>데이터는 안전한가요?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>네! 은행급 암호화(AES-256)를 사용하며, API 시크릿 키는 평문으로 저장하지 않습니다.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        async initPricingPage() {
            console.log('[Dashboard] Pricing page initialized');

            // Initialize billing toggle
            this.initBillingToggle();

            // Initialize FAQ accordions
            this.initFAQ();

            // Fetch user's current plan and update UI
            await this.updateCurrentPlan();

            // Initialize plan CTAs
            this.initPlanCTAs();
        }

        async updateCurrentPlan() {
            try {
                const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
                const apiUrl = window.location.origin;

                const response = await fetch(`${apiUrl}/api/user/plan`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                const data = await response.json();
                console.log('[Pricing] User plan data:', data);

                if (data.success && data.plan) {
                    const currentPlan = (data.plan.plan_code || 'free').toLowerCase();
                    console.log('[Pricing] Current plan:', currentPlan);

                    // Update all plan buttons
                    const ctaButtons = document.querySelectorAll('.plan-cta');
                    ctaButtons.forEach(button => {
                        const planType = button.getAttribute('data-plan');

                        if (planType === currentPlan) {
                            // This is the current plan
                            button.textContent = '현재 플랜';
                            button.classList.remove('plan-cta-primary');
                            button.classList.add('plan-cta-secondary');
                            button.disabled = false; // Keep clickable for info
                        } else {
                            // Different plan - show upgrade/start button
                            if (planType === 'free') {
                                button.textContent = '무료 플랜으로 변경';
                            } else if (planType === 'basic') {
                                button.textContent = currentPlan === 'free' ? '베이직으로 시작하기' : '베이직으로 변경';
                            } else if (planType === 'pro') {
                                button.textContent = currentPlan === 'free' ? '프로로 업그레이드' : '프로로 변경';
                            }
                            button.disabled = false;
                        }
                    });
                }
            } catch (error) {
                console.error('[Pricing] Error fetching user plan:', error);
                // If error, keep default state (free plan)
            }
        }

        initBillingToggle() {
            const billingToggle = document.getElementById('billing-toggle');
            const billingOptions = document.querySelectorAll('.billing-option');
            const priceAmounts = document.querySelectorAll('.price-amount');

            if (!billingToggle) return;

            let isAnnual = false;

            billingToggle.addEventListener('click', () => {
                isAnnual = !isAnnual;
                billingToggle.classList.toggle('active');

                // Update active state on labels
                billingOptions.forEach(option => {
                    const billing = option.getAttribute('data-billing');
                    if ((billing === 'annual' && isAnnual) || (billing === 'monthly' && !isAnnual)) {
                        option.classList.add('active');
                    } else {
                        option.classList.remove('active');
                    }
                });

                // Update prices and periods
                priceAmounts.forEach(amount => {
                    const monthlyPrice = amount.getAttribute('data-monthly');
                    const annualPrice = amount.getAttribute('data-annual');

                    if (monthlyPrice && annualPrice) {
                        amount.textContent = isAnnual ?
                            parseInt(annualPrice).toLocaleString() :
                            parseInt(monthlyPrice).toLocaleString();
                    }
                });

                // Update price periods (/월 or /년) - skip fixed periods
                const pricePeriods = document.querySelectorAll('.price-period');
                pricePeriods.forEach(period => {
                    if (!period.getAttribute('data-fixed')) {
                        period.textContent = isAnnual ? '/년' : '/월';
                    }
                });
            });

            // Also allow clicking on labels
            billingOptions.forEach(option => {
                option.addEventListener('click', () => {
                    const billing = option.getAttribute('data-billing');
                    const shouldBeAnnual = billing === 'annual';

                    if (shouldBeAnnual !== isAnnual) {
                        billingToggle.click();
                    }
                });
            });
        }

        initFAQ() {
            const faqItems = document.querySelectorAll('.faq-item');

            faqItems.forEach(item => {
                const question = item.querySelector('.faq-question');
                const answer = item.querySelector('.faq-answer');

                question.addEventListener('click', () => {
                    const isOpen = item.classList.contains('open');

                    // Close all other items
                    faqItems.forEach(otherItem => {
                        otherItem.classList.remove('open');
                    });

                    // Toggle current item
                    if (!isOpen) {
                        item.classList.add('open');
                    }
                });
            });
        }

        initPlanCTAs() {
            const ctaButtons = document.querySelectorAll('.plan-cta');

            ctaButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const plan = button.getAttribute('data-plan');
                    const buttonText = button.textContent.trim();

                    // Check if this is the current plan
                    if (buttonText === '현재 플랜') {
                        alert(`현재 ${plan === 'free' ? 'Free' : plan === 'basic' ? 'Basic' : 'Pro'} 플랜을 사용 중입니다.`);
                        return;
                    }

                    // Handle plan changes
                    if (plan === 'free') {
                        alert('무료 플랜으로 변경하시겠습니까? 유료 기능이 제한됩니다.');
                        // TODO: Implement downgrade logic
                    } else if (plan === 'basic') {
                        // Redirect to payment guide page
                        console.log('[Pricing] Upgrading to Basic');
                        window.location.href = `/payment_guide.html?plan=basic&billing=monthly`;
                    } else if (plan === 'pro') {
                        // Redirect to payment guide page
                        console.log('[Pricing] Upgrading to Pro');
                        window.location.href = `/payment_guide.html?plan=pro&billing=monthly`;
                    }
                });
            });
        }

        // ============================================
        // Notifications
        // ============================================
        initNotificationsButton() {
            const notificationsBtn = document.getElementById('notifications-btn');

            if (notificationsBtn) {
                notificationsBtn.addEventListener('click', () => {
                    // 알림 패널 토글 (향후 구현 예정)
                    alert('알림 기능은 곧 제공될 예정입니다.\n\n주요 업데이트:\n• 거래 체결 알림\n• 가격 알림\n• 시스템 공지사항');
                });
            }
        }

        // ============================================
        // User Menu
        // ============================================
        initUserMenu() {
            const userMenuBtn = document.getElementById('user-menu-btn');
            const userMenuDropdown = document.getElementById('user-menu-dropdown');

            if (userMenuBtn && userMenuDropdown) {
                userMenuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    userMenuDropdown.classList.toggle('show');
                });

                // Close dropdown when clicking outside
                document.addEventListener('click', (e) => {
                    if (!userMenuDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
                        userMenuDropdown.classList.remove('show');
                    }
                });

                // Handle dropdown items
                const dropdownItems = userMenuDropdown.querySelectorAll('.dropdown-item:not(.logout-item)');
                dropdownItems.forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        const href = item.getAttribute('href');
                        if (href && href.startsWith('#')) {
                            this.loadPage(href.substring(1));
                        }
                        userMenuDropdown.classList.remove('show');
                    });
                });
            }
        }

        // ============================================
        // Logout
        // ============================================
        initLogout() {
            const logoutBtns = document.querySelectorAll('.logout-btn, #logout-dropdown');

            logoutBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.logout();
                });
            });
        }

        // ============================================
        // Settings Page Initialization
        // ============================================
        async initSettingsPage() {
            console.log('[Dashboard] Initializing settings page');

            // Setup settings tabs
            this.setupSettingsTabs();

            // Setup trading settings (coin selection) - async
            await this.setupTradingSettings();

            // Setup other form handlers
            this.setupProfileForm();
            this.setupPasswordForm();
            this.setupAPIKeysForm();
            this.setupNotificationsForm();
        }

        setupSettingsTabs() {
            const tabs = document.querySelectorAll('.settings-tab');
            const tabContents = document.querySelectorAll('.settings-tab-content');

            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabName = tab.dataset.tab;

                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');

                    // Update active content
                    tabContents.forEach(content => {
                        if (content.dataset.tabContent === tabName) {
                            content.classList.add('active');
                        } else {
                            content.classList.remove('active');
                        }
                    });
                });
            });
        }

        async setupTradingSettings() {
            const searchInput = document.getElementById('coin-search-input');
            const dropdown = document.getElementById('coin-dropdown');
            const dropdownList = document.getElementById('coin-dropdown-list');
            const dropdownLoading = document.getElementById('coin-dropdown-loading');
            const selectedTagsContainer = document.getElementById('selected-coins-tags');
            const selectedCountSpan = document.getElementById('selected-count');
            const settingsContainer = document.getElementById('coin-settings-container');
            const saveButton = document.getElementById('save-trading-settings');

            let selectedCoins = [];
            let allCoins = [];
            const MAX_COINS = 5;

            // Korean coin names mapping
            const coinNamesKo = {
                'BTC': '비트코인', 'ETH': '이더리움', 'XRP': '리플', 'ADA': '에이다',
                'SOL': '솔라나', 'DOGE': '도지코인', 'DOT': '폴카닷', 'MATIC': '폴리곤',
                'LTC': '라이트코인', 'LINK': '체인링크', 'BCH': '비트코인캐시',
                'AVAX': '아발란체', 'ATOM': '코스모스', 'ETC': '이더리움클래식',
                'NEAR': '니어프로토콜', 'UNI': '유니스왑', 'ALGO': '알고랜드',
                'HBAR': '헤데라', 'FIL': '파일코인', 'AAVE': '에이브', 'APT': '앱토스',
                'OP': '옵티미즘', 'ARB': '아비트럼', 'SUI': '수이', 'STX': '스택스',
                'IMX': '이뮤터블엑스', 'INJ': '인젝티브', 'TIA': '셀레스티아'
            };

            // Load saved settings from localStorage
            const savedSettings = JSON.parse(localStorage.getItem('trading_settings') || '{}');
            if (savedSettings.selectedCoins) {
                selectedCoins = savedSettings.selectedCoins;
                this.renderSelectedTags(selectedCoins, coinNamesKo);
                this.updateCoinSettings(selectedCoins, savedSettings);
                selectedCountSpan.textContent = selectedCoins.length;
            }

            // Fetch all KRW markets
            try {
                dropdownLoading.style.display = 'block';
                // Use origin directly for Upbit public endpoint (not /api/admin)
                const response = await fetch(`${window.location.origin}/api/upbit/market/all`);
                const data = await response.json();
                const markets = data.markets || data || [];

                // Filter KRW markets and sort by symbol
                allCoins = markets
                    .filter(m => m.market.startsWith('KRW-'))
                    .map(m => {
                        const symbol = m.market.replace('KRW-', '');
                        return {
                            symbol: symbol,
                            nameKo: m.korean_name || coinNamesKo[symbol] || symbol,
                            nameEn: m.english_name || symbol
                        };
                    })
                    .sort((a, b) => a.symbol.localeCompare(b.symbol));

                dropdownLoading.style.display = 'none';
                console.log(`[Settings] Loaded ${allCoins.length} KRW markets`);
            } catch (error) {
                console.error('[Settings] Failed to fetch markets:', error);
                dropdownLoading.textContent = '코인 목록을 불러오지 못했습니다';
            }

            // Search input focus - show dropdown
            searchInput.addEventListener('focus', () => {
                if (allCoins.length > 0) {
                    this.renderCoinDropdown(allCoins, selectedCoins);
                    dropdown.style.display = 'block';
                }
            });

            // Search input - filter coins
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();

                if (!query) {
                    this.renderCoinDropdown(allCoins, selectedCoins);
                } else {
                    const filtered = allCoins.filter(coin =>
                        coin.symbol.toLowerCase().includes(query) ||
                        coin.nameKo.includes(query) ||
                        coin.nameEn.toLowerCase().includes(query)
                    );
                    this.renderCoinDropdown(filtered, selectedCoins);
                }

                dropdown.style.display = 'block';
            });

            // Click outside to close dropdown
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });

            // Save selected coins property for access in other methods
            this._selectedCoins = selectedCoins;
            this._coinNamesKo = coinNamesKo;
            this._savedSettings = savedSettings;

            // Save button handler
            if (saveButton) {
                saveButton.addEventListener('click', () => {
                    this.saveTradingSettings(this._selectedCoins);
                });
            }
        }

        renderCoinDropdown(coins, selectedCoins) {
            const dropdownList = document.getElementById('coin-dropdown-list');
            const MAX_COINS = 5;

            if (coins.length === 0) {
                dropdownList.innerHTML = '<div class="coin-dropdown-no-results">검색 결과가 없습니다</div>';
                return;
            }

            let html = '';
            coins.forEach(coin => {
                const isSelected = selectedCoins.includes(coin.symbol);
                const isDisabled = !isSelected && selectedCoins.length >= MAX_COINS;

                html += `
                    <div class="coin-dropdown-item ${isDisabled ? 'disabled' : ''}" data-symbol="${coin.symbol}">
                        <div class="coin-dropdown-item-info">
                            <div class="coin-dropdown-item-name">${coin.nameKo}</div>
                            <div class="coin-dropdown-item-symbol">${coin.symbol}</div>
                        </div>
                        ${isSelected ? '<span style="color: #22c55e; font-weight: 600;">✓</span>' : ''}
                    </div>
                `;
            });

            dropdownList.innerHTML = html;

            // Add click handlers
            dropdownList.querySelectorAll('.coin-dropdown-item').forEach(item => {
                item.addEventListener('click', () => {
                    if (item.classList.contains('disabled')) {
                        alert(`최대 ${MAX_COINS}개 코인까지만 선택할 수 있습니다.`);
                        return;
                    }

                    const symbol = item.dataset.symbol;
                    this.toggleCoinSelection(symbol);
                });
            });
        }

        toggleCoinSelection(symbol) {
            const selectedCoins = this._selectedCoins;
            const coinNamesKo = this._coinNamesKo;
            const savedSettings = this._savedSettings;
            const MAX_COINS = 5;
            const dropdown = document.getElementById('coin-dropdown');
            const searchInput = document.getElementById('coin-search-input');

            const index = selectedCoins.indexOf(symbol);

            if (index > -1) {
                // Remove coin
                selectedCoins.splice(index, 1);
            } else {
                // Add coin
                if (selectedCoins.length >= MAX_COINS) {
                    alert(`최대 ${MAX_COINS}개 코인까지만 선택할 수 있습니다.`);
                    return;
                }
                selectedCoins.push(symbol);
            }

            // Update UI
            this.renderSelectedTags(selectedCoins, coinNamesKo);
            document.getElementById('selected-count').textContent = selectedCoins.length;
            this.updateCoinSettings(selectedCoins, savedSettings);

            // Close dropdown and clear search
            dropdown.style.display = 'none';
            searchInput.value = '';
        }

        renderSelectedTags(selectedCoins, coinNamesKo) {
            const container = document.getElementById('selected-coins-tags');

            if (selectedCoins.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted); font-size: 14px; margin: 12px 0;">선택된 코인이 없습니다. 위 검색창에서 코인을 검색하여 선택하세요.</p>';
                return;
            }

            let html = '';
            selectedCoins.forEach(symbol => {
                const name = coinNamesKo[symbol] || symbol;
                html += `
                    <div class="coin-tag" data-symbol="${symbol}">
                        <span>${name} (${symbol})</span>
                        <div class="coin-tag-remove" data-symbol="${symbol}">
                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M2 2L10 10M10 2L2 10"/>
                            </svg>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            // Add remove handlers
            container.querySelectorAll('.coin-tag-remove').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const symbol = btn.dataset.symbol;
                    this.toggleCoinSelection(symbol);
                });
            });
        }

        updateCoinSettings(selectedCoins, savedSettings = {}) {
            const container = document.getElementById('coin-settings-container');

            if (selectedCoins.length === 0) {
                container.innerHTML = `
                    <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                        관심 코인을 선택하면 각 코인별 설정이 여기에 표시됩니다.
                    </p>
                `;
                return;
            }

            // Use instance coin names or fallback to symbol
            const coinNames = this._coinNamesKo || {};

            let html = '';
            selectedCoins.forEach(coin => {
                const settings = savedSettings[coin] || {
                    risk: 'moderate',
                    alertEnabled: true,
                    stopLoss: false
                };

                const coinName = coinNames[coin] || coin;

                html += `
                    <div class="coin-settings-card" data-coin="${coin}">
                        <div class="coin-settings-header">
                            <h4>${coinName} (${coin})</h4>
                        </div>
                        <div class="coin-settings-body">
                            <div class="coin-setting-group">
                                <label>위험 허용도</label>
                                <select class="risk-select" data-coin="${coin}">
                                    <option value="conservative" ${settings.risk === 'conservative' ? 'selected' : ''}>보수적</option>
                                    <option value="moderate" ${settings.risk === 'moderate' ? 'selected' : ''}>중립</option>
                                    <option value="aggressive" ${settings.risk === 'aggressive' ? 'selected' : ''}>공격적</option>
                                </select>
                            </div>
                            <div class="coin-setting-group">
                                <div class="coin-setting-toggle">
                                    <input type="checkbox" id="alert-${coin}" ${settings.alertEnabled !== false ? 'checked' : ''}>
                                    <label for="alert-${coin}">급등 알림 받기</label>
                                </div>
                            </div>
                            <div class="coin-setting-group">
                                <div class="coin-setting-toggle">
                                    <input type="checkbox" id="stop-${coin}" ${settings.stopLoss ? 'checked' : ''}>
                                    <label for="stop-${coin}">손절매 활성화</label>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        saveTradingSettings(selectedCoins) {
            const settings = {
                selectedCoins: selectedCoins
            };

            // Collect settings for each coin
            selectedCoins.forEach(coin => {
                const riskSelect = document.querySelector(`.risk-select[data-coin="${coin}"]`);
                const alertCheckbox = document.getElementById(`alert-${coin}`);
                const stopCheckbox = document.getElementById(`stop-${coin}`);

                settings[coin] = {
                    risk: riskSelect?.value || 'moderate',
                    alertEnabled: alertCheckbox?.checked !== false,
                    stopLoss: stopCheckbox?.checked || false
                };
            });

            // Save to localStorage
            localStorage.setItem('trading_settings', JSON.stringify(settings));

            // Show success message
            alert('거래 설정이 저장되었습니다.');
            console.log('[Dashboard] Trading settings saved:', settings);
        }

        setupProfileForm() {
            const form = document.getElementById('profile-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                // TODO: Implement profile update
                alert('프로필 업데이트 기능은 준비 중입니다.');
            });
        }

        setupPasswordForm() {
            const form = document.getElementById('password-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                // TODO: Implement password change
                alert('비밀번호 변경 기능은 준비 중입니다.');
            });
        }

        setupAPIKeysForm() {
            const form = document.getElementById('api-keys-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                // TODO: Implement API keys save
                alert('API 키 저장 기능은 준비 중입니다.');
            });
        }

        setupNotificationsForm() {
            const form = document.getElementById('notifications-form');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                // TODO: Implement notifications save
                alert('알림 설정 저장 기능은 준비 중입니다.');
            });
        }

        async logout() {
            try {
                // Call logout API
                if (window.authManager) {
                    await window.authManager.logout();
                } else {
                    // Fallback: clear local storage
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_data');
                    localStorage.removeItem('remember_me');
                }

                // Redirect to login
                window.location.href = 'login.html';
            } catch (error) {
                console.error('[Dashboard] Logout error:', error);
                // Force logout on error
                localStorage.clear();
                window.location.href = 'login.html';
            }
        }
    }

    // ============================================
    // 2. Initialize Dashboard
    // ============================================
    document.addEventListener('DOMContentLoaded', () => {
        window.dashboardApp = new DashboardManager();
    });

})();
