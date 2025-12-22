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
                contentContainer.innerHTML = '<div class="loading-state"><div class="spinner-large"></div><p>Loading...</p></div>';

                // Load page-specific content
                let content = '';

                switch (pageName) {
                    case 'overview':
                        content = await this.loadOverviewPage();
                        break;
                    case 'trading':
                        content = await this.loadTradingPage();
                        break;
                    case 'portfolio':
                        content = await this.loadPortfolioPage();
                        break;
                    case 'auto-trading':
                        content = await this.loadAutoTradingPage();
                        break;
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
                this.initPageScripts(pageName);

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

        async loadTradingPage() {
            // Get selected market from URL hash or default
            const hash = window.location.hash;
            const marketMatch = hash.match(/market=([^&]+)/);
            const market = marketMatch ? marketMatch[1] : 'KRW-BTC';

            // Build iframe URL with market parameter
            const iframeUrl = `trading_chart.html?market=${market}`;

            return `
                <div class="trading-page">
                    <iframe id="trading-chart-iframe"
                            src="${iframeUrl}"
                            style="width: 100%; height: calc(100vh - 140px); border: none;"
                            title="Trading Chart"></iframe>
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

        async loadSwingTradingPage() {
            return `
                <div class="swing-trading-page">
                    <iframe id="swing-trading-iframe"
                            src="swing_trading.html"
                            style="width: 100%; height: calc(100vh - 140px); border: none;"
                            title="Swing Trading"></iframe>
                </div>
            `;
        }

        async loadHistoryPage() {
            return `
                <div class="history-page">
                    <h2>거래 내역</h2>
                    <p>전체 거래 내역이 여기에 표시됩니다.</p>
                </div>
            `;
        }

        async loadSettingsPage() {
            return `
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
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                            </svg>
                            <span>거래</span>
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

                        <!-- Trading Preferences Tab -->
                        <div class="settings-tab-content" data-tab-content="trading">
                            <div class="settings-section">
                                <h2>거래 설정</h2>
                                <form id="trading-prefs-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="default-market">기본 거래 쌍</label>
                                        <select id="default-market">
                                            <option value="KRW-BTC">KRW-BTC</option>
                                            <option value="KRW-ETH">KRW-ETH</option>
                                            <option value="KRW-XRP">KRW-XRP</option>
                                            <option value="KRW-ADA">KRW-ADA</option>
                                            <option value="KRW-SOL">KRW-SOL</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label for="risk-tolerance">위험 허용도</label>
                                        <select id="risk-tolerance">
                                            <option value="conservative">보수적</option>
                                            <option value="moderate">중립</option>
                                            <option value="aggressive">공격적</option>
                                        </select>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="auto-trading-enabled">
                                            <span>자동 거래 활성화</span>
                                        </label>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="stop-loss-enabled">
                                            <span>손절매 활성화</span>
                                        </label>
                                    </div>
                                    <button type="submit" class="btn-primary">설정 저장</button>
                                </form>
                            </div>
                        </div>

                        <!-- Notifications Tab -->
                        <div class="settings-tab-content" data-tab-content="notifications">
                            <div class="settings-section">
                                <h2>이메일 알림</h2>
                                <form id="notifications-form" class="settings-form">
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-trades" checked>
                                            <span>거래 확인</span>
                                        </label>
                                        <p class="help-text">거래가 실행될 때 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-price-alerts" checked>
                                            <span>가격 알림</span>
                                        </label>
                                        <p class="help-text">목표 가격에 도달할 때 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-portfolio">
                                            <span>일일 포트폴리오 요약</span>
                                        </label>
                                        <p class="help-text">포트폴리오 성과를 담은 일일 이메일 수신</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-marketing">
                                            <span>마케팅 이메일</span>
                                        </label>
                                        <p class="help-text">새로운 기능 및 프로모션 업데이트 수신</p>
                                    </div>
                                    <button type="submit" class="btn-primary">설정 저장</button>
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
        initPageScripts(pageName) {
            switch (pageName) {
                case 'overview':
                    this.initOverviewPage();
                    break;
                case 'trading':
                    // Trading chart has its own scripts
                    break;
                case 'portfolio':
                    this.initPortfolioPage();
                    break;
                case 'auto-trading':
                    this.initAutoTradingPage();
                    break;
                case 'swing-trading':
                    // Swing trading iframe has its own scripts
                    break;
                case 'settings':
                    this.initSettingsPage();
                    break;
                case 'pricing':
                    this.initPricingPage();
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
                const response = await fetch('/api/auth/me?include_api_keys=true', {
                    headers: {
                        'Authorization': `Bearer ${window.api.accessToken}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.user) {
                        const editBtn = document.getElementById('edit-access-key-btn');
                        const guideDiv = document.getElementById('api-key-guide');
                        const hasApiKeys = data.user.upbit_access_key && data.user.upbit_secret_key_masked;

                        // Show guide if no API keys
                        if (!hasApiKeys && guideDiv) {
                            guideDiv.style.display = 'block';
                            console.log('[Settings] API key guide displayed (no keys found)');
                        }

                        // Display access key (if exists)
                        if (data.user.upbit_access_key) {
                            accessKeyInput.value = data.user.upbit_access_key;
                            accessKeyInput.setAttribute('readonly', 'readonly');
                            accessKeyInput.style.backgroundColor = 'var(--input-disabled-bg, #f5f5f5)';

                            // Show edit button
                            if (editBtn) {
                                editBtn.style.display = 'inline-block';
                                editBtn.addEventListener('click', () => {
                                    accessKeyInput.removeAttribute('readonly');
                                    accessKeyInput.style.backgroundColor = '';
                                    accessKeyInput.focus();
                                    editBtn.style.display = 'none';
                                    console.log('[Settings] Access key edit mode enabled');
                                });
                            }

                            console.log('[Settings] Access key loaded');
                        }

                        // Display masked secret key as placeholder
                        if (data.user.upbit_secret_key_masked) {
                            secretKeyInput.placeholder = `저장된 키: ${data.user.upbit_secret_key_masked} (변경하려면 새 키 입력)`;
                            console.log('[Settings] Secret key masked displayed');
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
                                <p class="plan-description">시작하기에 완벽</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount">0</span>
                                <span class="price-period">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>포트폴리오 추적</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>급등 모니터링 (참고용)</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>수동 매매</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>자동매매 알림</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>텔레그램 메시지</span>
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
                                <span class="price-amount" data-monthly="49000" data-annual="39200">49,000</span>
                                <span class="price-period">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>수동 매매</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>급등 모니터링</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>자동매매 알림 1개</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>텔레그램 메시지</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>고급 지표</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>백테스팅</span>
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
                                <span class="price-amount" data-monthly="99000" data-annual="79200">99,000</span>
                                <span class="price-period">/월</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>수동 매매</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>급등 모니터링</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>무제한 자동매매 알림</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>텔레그램 메시지</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>고급 기술적 지표</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>백테스팅 기능</span>
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
                                    <p>신용카드, 카카오페이, 토스를 지원합니다. Pro 요금제는 계좌이체도 가능합니다.</p>
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
                                    <p>Premium 요금제는 14일 무료 체험을 제공합니다. 신용카드 등록 없이 시작할 수 있습니다.</p>
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

        initPricingPage() {
            console.log('[Dashboard] Pricing page initialized');

            // Initialize billing toggle
            this.initBillingToggle();

            // Initialize FAQ accordions
            this.initFAQ();

            // Initialize plan CTAs
            this.initPlanCTAs();
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

                // Update prices
                priceAmounts.forEach(amount => {
                    const monthlyPrice = amount.getAttribute('data-monthly');
                    const annualPrice = amount.getAttribute('data-annual');

                    if (monthlyPrice && annualPrice) {
                        amount.textContent = isAnnual ?
                            parseInt(annualPrice).toLocaleString() :
                            parseInt(monthlyPrice).toLocaleString();
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

                    if (plan === 'free') {
                        alert('이미 무료 플랜을 사용 중입니다.');
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
