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
                // Check if user is authenticated
                if (!window.authManager || !window.authManager.isAuthenticated()) {
                    console.warn('[Dashboard] User not authenticated, redirecting to login');
                    window.location.href = 'login.html';
                    return;
                }

                // Get user data
                this.user = window.authManager.getUser();

                if (!this.user) {
                    // Try to verify token with backend
                    const token = localStorage.getItem('auth_token');
                    if (!token) {
                        window.location.href = 'login.html';
                        return;
                    }

                    // For now, use stored user data
                    const userData = localStorage.getItem('user_data');
                    if (userData) {
                        this.user = JSON.parse(userData);
                    } else {
                        window.location.href = 'login.html';
                        return;
                    }
                }

                // Update UI with user info
                this.updateUserInfo();

                console.log('[Dashboard] User authenticated:', this.user.email);
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
                'overview': 'Overview',
                'trading': 'Trading Chart',
                'portfolio': 'Portfolio',
                'auto-trading': 'Auto Trading',
                'history': 'Trading History',
                'settings': 'Settings'
            };

            if (pageTitle) {
                pageTitle.textContent = titles[pageName] || 'Dashboard';
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
                        <h1>Welcome back, ${this.user.username || 'Trader'}!</h1>
                        <p>Here's your portfolio overview</p>
                    </div>

                    <!-- Stats Grid -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Portfolio Value</h3>
                            <p class="stat-value" id="portfolio-value">Loading...</p>
                            <div class="stat-change" id="portfolio-change">
                                <span>--</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Total Profit/Loss</h3>
                            <p class="stat-value" id="total-profit">Loading...</p>
                            <div class="stat-change" id="profit-change">
                                <span>--</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Holdings</h3>
                            <p class="stat-value" id="holdings-count">Loading...</p>
                            <div class="stat-change neutral">
                                <span id="holdings-label">Active positions</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Win Rate</h3>
                            <p class="stat-value" id="win-rate">Loading...</p>
                            <div class="stat-change" id="win-rate-change">
                                <span id="trades-count">-- trades</span>
                            </div>
                        </div>
                    </div>

                    <!-- Portfolio Chart -->
                    <div class="portfolio-chart-container">
                        <h2>Portfolio Performance</h2>
                        <div class="chart-placeholder">
                            Chart coming soon - Historical portfolio value
                        </div>
                    </div>

                    <!-- Current Holdings -->
                    <div class="holdings-section">
                        <h2>Current Holdings</h2>
                        <div id="holdings-table-container">
                            <div class="loading-state">
                                <div class="spinner-large"></div>
                                <p>Loading holdings...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="recent-activity">
                        <h2>Recent Trading Activity</h2>
                        <div id="recent-activity-container">
                            <div class="loading-state">
                                <div class="spinner-large"></div>
                                <p>Loading activity...</p>
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
                    <h2>Portfolio</h2>
                    <p>Your portfolio details will be displayed here.</p>
                </div>
            `;
        }

        async loadAutoTradingPage() {
            return `
                <div class="auto-trading-page">
                    <h2>Auto Trading</h2>
                    <p>Configure and monitor your automated trading strategies.</p>
                </div>
            `;
        }

        async loadHistoryPage() {
            return `
                <div class="history-page">
                    <h2>Trading History</h2>
                    <p>Your complete trading history will be displayed here.</p>
                </div>
            `;
        }

        async loadSettingsPage() {
            return `
                <div class="settings-page">
                    <div class="settings-header">
                        <h1>Settings</h1>
                        <p>Manage your account and trading preferences</p>
                    </div>

                    <!-- Settings Tabs -->
                    <div class="settings-tabs">
                        <button class="settings-tab active" data-tab="account">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            <span>Account</span>
                        </button>
                        <button class="settings-tab" data-tab="api-keys">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <span>API Keys</span>
                        </button>
                        <button class="settings-tab" data-tab="trading">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                            </svg>
                            <span>Trading</span>
                        </button>
                        <button class="settings-tab" data-tab="notifications">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            <span>Notifications</span>
                        </button>
                    </div>

                    <!-- Settings Content -->
                    <div class="settings-content">
                        <!-- Account Settings Tab -->
                        <div class="settings-tab-content active" data-tab-content="account">
                            <div class="settings-section">
                                <h2>Profile Information</h2>
                                <form id="profile-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="settings-username">Username</label>
                                        <input type="text" id="settings-username" value="${this.user.username || ''}" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="settings-email">Email</label>
                                        <input type="email" id="settings-email" value="${this.user.email || ''}" required>
                                    </div>
                                    <button type="submit" class="btn-primary">Save Changes</button>
                                </form>
                            </div>

                            <div class="settings-section">
                                <h2>Change Password</h2>
                                <form id="password-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="current-password">Current Password</label>
                                        <input type="password" id="current-password" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="new-password">New Password</label>
                                        <input type="password" id="new-password" required minlength="8">
                                    </div>
                                    <div class="form-group">
                                        <label for="confirm-password">Confirm New Password</label>
                                        <input type="password" id="confirm-password" required minlength="8">
                                    </div>
                                    <button type="submit" class="btn-primary">Change Password</button>
                                </form>
                            </div>

                            <div class="settings-section danger-zone">
                                <h2>Danger Zone</h2>
                                <p>Once you delete your account, there is no going back. Please be certain.</p>
                                <button class="btn-danger" id="delete-account-btn">Delete Account</button>
                            </div>
                        </div>

                        <!-- API Keys Tab -->
                        <div class="settings-tab-content" data-tab-content="api-keys">
                            <div class="settings-section">
                                <h2>Upbit API Keys</h2>
                                <p>Connect your Upbit account to enable live trading and portfolio tracking.</p>

                                <form id="api-keys-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="api-access-key">Access Key</label>
                                        <input type="text" id="api-access-key" placeholder="Enter your Upbit access key" required>
                                    </div>
                                    <div class="form-group">
                                        <label for="api-secret-key">Secret Key</label>
                                        <input type="password" id="api-secret-key" placeholder="Enter your Upbit secret key" required>
                                    </div>
                                    <div class="form-actions">
                                        <button type="button" class="btn-secondary" id="test-api-btn">Test Connection</button>
                                        <button type="submit" class="btn-primary">Save API Keys</button>
                                    </div>
                                </form>

                                <div id="api-test-result" class="api-test-result" style="display: none;"></div>
                            </div>
                        </div>

                        <!-- Trading Preferences Tab -->
                        <div class="settings-tab-content" data-tab-content="trading">
                            <div class="settings-section">
                                <h2>Trading Preferences</h2>
                                <form id="trading-prefs-form" class="settings-form">
                                    <div class="form-group">
                                        <label for="default-market">Default Trading Pair</label>
                                        <select id="default-market">
                                            <option value="KRW-BTC">KRW-BTC</option>
                                            <option value="KRW-ETH">KRW-ETH</option>
                                            <option value="KRW-XRP">KRW-XRP</option>
                                            <option value="KRW-ADA">KRW-ADA</option>
                                            <option value="KRW-SOL">KRW-SOL</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label for="risk-tolerance">Risk Tolerance</label>
                                        <select id="risk-tolerance">
                                            <option value="conservative">Conservative</option>
                                            <option value="moderate">Moderate</option>
                                            <option value="aggressive">Aggressive</option>
                                        </select>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="auto-trading-enabled">
                                            <span>Enable Auto Trading</span>
                                        </label>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="stop-loss-enabled">
                                            <span>Enable Stop Loss</span>
                                        </label>
                                    </div>
                                    <button type="submit" class="btn-primary">Save Preferences</button>
                                </form>
                            </div>
                        </div>

                        <!-- Notifications Tab -->
                        <div class="settings-tab-content" data-tab-content="notifications">
                            <div class="settings-section">
                                <h2>Email Notifications</h2>
                                <form id="notifications-form" class="settings-form">
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-trades" checked>
                                            <span>Trade Confirmations</span>
                                        </label>
                                        <p class="help-text">Receive email when trades are executed</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-price-alerts" checked>
                                            <span>Price Alerts</span>
                                        </label>
                                        <p class="help-text">Receive email when price targets are hit</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-portfolio">
                                            <span>Daily Portfolio Summary</span>
                                        </label>
                                        <p class="help-text">Receive daily email with portfolio performance</p>
                                    </div>
                                    <div class="form-group checkbox-group">
                                        <label>
                                            <input type="checkbox" id="notify-marketing">
                                            <span>Marketing Emails</span>
                                        </label>
                                        <p class="help-text">Receive updates about new features and promotions</p>
                                    </div>
                                    <button type="submit" class="btn-primary">Save Preferences</button>
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
                const [holdingsData, ordersData] = await Promise.all([
                    this.fetchHoldings(),
                    this.fetchOrders()
                ]);

                // Calculate and update stats
                this.updatePortfolioStats(holdingsData, ordersData);

                // Display holdings table
                this.displayHoldingsTable(holdingsData);

                // Display recent activity
                this.displayRecentActivity(ordersData);

                console.log('[Dashboard] Overview page loaded successfully');
            } catch (error) {
                console.error('[Dashboard] Error loading overview data:', error);
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
                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                return data.holdings || [];
            } catch (error) {
                console.error('[Dashboard] Error fetching holdings:', error);
                return [];
            }
        }

        async fetchOrders() {
            try {
                const config = await this.loadConfig();
                const apiUrl = config?.api?.tradingServerUrl || 'http://localhost:8081';

                const response = await fetch(`${apiUrl}/api/orders?limit=50`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
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
                return await response.json();
            } catch (error) {
                console.error('[Dashboard] Error loading config:', error);
                return null;
            }
        }

        updatePortfolioStats(holdings, orders) {
            // Calculate portfolio value
            let totalValue = 0;
            let totalCost = 0;

            holdings.forEach(holding => {
                const value = parseFloat(holding.balance || 0) * parseFloat(holding.avg_buy_price || 0);
                const cost = parseFloat(holding.balance || 0) * parseFloat(holding.avg_buy_price || 0);
                totalValue += value;
                totalCost += cost;
            });

            // Add KRW balance
            const krwHolding = holdings.find(h => h.currency === 'KRW');
            if (krwHolding) {
                totalValue += parseFloat(krwHolding.balance || 0);
            }

            // Calculate profit/loss
            const totalProfit = totalValue - totalCost;
            const profitPercent = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

            // Calculate win rate
            const completedTrades = orders.filter(o => o.state === 'done');
            const winningTrades = completedTrades.filter(o => {
                // Simple heuristic: buy at lower price than current
                return parseFloat(o.profit || 0) > 0;
            });
            const winRate = completedTrades.length > 0
                ? (winningTrades.length / completedTrades.length) * 100
                : 0;

            // Update DOM
            document.getElementById('portfolio-value').textContent =
                `₩${this.formatNumber(totalValue)}`;

            const portfolioChange = document.getElementById('portfolio-change');
            portfolioChange.innerHTML = `<span>${profitPercent >= 0 ? '▲' : '▼'} ${Math.abs(profitPercent).toFixed(2)}%</span>`;
            portfolioChange.className = `stat-change ${profitPercent >= 0 ? 'positive' : 'negative'}`;

            document.getElementById('total-profit').textContent =
                `₩${this.formatNumber(Math.abs(totalProfit))}`;

            const profitChange = document.getElementById('profit-change');
            profitChange.innerHTML = `<span>${totalProfit >= 0 ? 'Profit' : 'Loss'}</span>`;
            profitChange.className = `stat-change ${totalProfit >= 0 ? 'positive' : 'negative'}`;

            document.getElementById('holdings-count').textContent =
                holdings.filter(h => h.currency !== 'KRW').length;

            document.getElementById('win-rate').textContent = `${winRate.toFixed(1)}%`;
            document.getElementById('trades-count').textContent =
                `${completedTrades.length} trades`;
        }

        displayHoldingsTable(holdings) {
            const container = document.getElementById('holdings-table-container');

            const cryptoHoldings = holdings.filter(h => h.currency !== 'KRW' && parseFloat(h.balance) > 0);

            if (cryptoHoldings.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <h3>No Holdings Yet</h3>
                        <p>Start trading to see your portfolio here</p>
                    </div>
                `;
                return;
            }

            let tableHTML = `
                <table class="holdings-table">
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Balance</th>
                            <th>Avg Buy Price</th>
                            <th>Current Value</th>
                            <th>Profit/Loss</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            cryptoHoldings.forEach(holding => {
                const balance = parseFloat(holding.balance || 0);
                const avgPrice = parseFloat(holding.avg_buy_price || 0);
                const currentValue = balance * avgPrice;
                const profitLoss = currentValue - (balance * avgPrice);
                const profitPercent = avgPrice > 0 ? (profitLoss / (balance * avgPrice)) * 100 : 0;
                const market = `KRW-${holding.currency}`;

                tableHTML += `
                    <tr class="holding-row" data-market="${market}" style="cursor: pointer;">
                        <td>
                            <div class="coin-info">
                                <div class="coin-icon">${holding.currency.substring(0, 2).toUpperCase()}</div>
                                <div>
                                    <div class="coin-name">${holding.currency}</div>
                                    <div class="coin-symbol">${market}</div>
                                </div>
                            </div>
                        </td>
                        <td>${balance.toFixed(8)}</td>
                        <td>₩${this.formatNumber(avgPrice)}</td>
                        <td>₩${this.formatNumber(currentValue)}</td>
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

            container.innerHTML = tableHTML;

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

            if (!orders || orders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v6l4 2"></path>
                        </svg>
                        <h3>No Recent Activity</h3>
                        <p>Your trading history will appear here</p>
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
                                ${isBuy ? 'Bought' : 'Sold'} ${order.market}
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

        formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(2) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(2) + 'K';
            } else {
                return num.toFixed(0);
            }
        }

        getTimeAgo(date) {
            const seconds = Math.floor((new Date() - date) / 1000);

            if (seconds < 60) return 'Just now';
            if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
            if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
            if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
            return date.toLocaleDateString();
        }

        showOverviewError() {
            const statsCards = ['portfolio-value', 'total-profit', 'holdings-count', 'win-rate'];
            statsCards.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = 'Error';
            });

            document.getElementById('holdings-table-container').innerHTML = `
                <div class="empty-state">
                    <h3>Error Loading Data</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;

            document.getElementById('recent-activity-container').innerHTML = `
                <div class="empty-state">
                    <h3>Error Loading Activity</h3>
                    <p>Please try refreshing the page</p>
                </div>
            `;
        }

        initPortfolioPage() {
            // Fetch and display portfolio data
            console.log('[Dashboard] Portfolio page initialized');
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

                    this.showSuccess(form, 'Profile updated successfully!');

                    // Update user data
                    this.user.username = username;
                    this.user.email = email;
                    localStorage.setItem('user_data', JSON.stringify(this.user));
                    this.updateUserInfo();

                } catch (error) {
                    console.error('[Settings] Profile update error:', error);
                    this.showError(form, 'Failed to update profile. Please try again.');
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
                    this.showError(form, 'New passwords do not match');
                    return;
                }

                // Validate password strength
                if (newPassword.length < 8) {
                    this.showError(form, 'Password must be at least 8 characters');
                    return;
                }

                try {
                    // TODO: Call API to change password
                    console.log('[Settings] Changing password');

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, 'Password changed successfully!');

                    // Clear form
                    form.reset();

                } catch (error) {
                    console.error('[Settings] Password change error:', error);
                    this.showError(form, 'Failed to change password. Please check your current password.');
                }
            });
        }

        initAPIKeysForm() {
            const form = document.getElementById('api-keys-form');
            const testBtn = document.getElementById('test-api-btn');
            const resultDiv = document.getElementById('api-test-result');

            if (!form || !testBtn) return;

            // Test API connection
            testBtn.addEventListener('click', async () => {
                const accessKey = document.getElementById('api-access-key').value.trim();
                const secretKey = document.getElementById('api-secret-key').value.trim();

                if (!accessKey || !secretKey) {
                    this.showAPITestResult('error', 'Please enter both access key and secret key');
                    return;
                }

                testBtn.disabled = true;
                testBtn.textContent = 'Testing...';

                try {
                    // TODO: Call API to test Upbit connection
                    console.log('[Settings] Testing API connection');

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 2000));

                    this.showAPITestResult('success', '✓ API connection successful! Your keys are valid.');

                } catch (error) {
                    console.error('[Settings] API test error:', error);
                    this.showAPITestResult('error', '✗ API connection failed. Please check your keys.');
                } finally {
                    testBtn.disabled = false;
                    testBtn.textContent = 'Test Connection';
                }
            });

            // Save API keys
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const accessKey = document.getElementById('api-access-key').value.trim();
                const secretKey = document.getElementById('api-secret-key').value.trim();

                try {
                    // TODO: Call API to save keys
                    console.log('[Settings] Saving API keys');

                    // Mock response
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    this.showSuccess(form, 'API keys saved successfully!');

                } catch (error) {
                    console.error('[Settings] API keys save error:', error);
                    this.showError(form, 'Failed to save API keys. Please try again.');
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

                    this.showSuccess(form, 'Trading preferences saved successfully!');

                } catch (error) {
                    console.error('[Settings] Trading prefs save error:', error);
                    this.showError(form, 'Failed to save preferences. Please try again.');
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

                    this.showSuccess(form, 'Notification preferences saved successfully!');

                } catch (error) {
                    console.error('[Settings] Notification prefs save error:', error);
                    this.showError(form, 'Failed to save preferences. Please try again.');
                }
            });
        }

        initDeleteAccount() {
            const deleteBtn = document.getElementById('delete-account-btn');
            if (!deleteBtn) return;

            deleteBtn.addEventListener('click', () => {
                const confirmed = confirm(
                    'Are you sure you want to delete your account? This action cannot be undone.\n\n' +
                    'All your data, including trading history and settings, will be permanently deleted.'
                );

                if (confirmed) {
                    const doubleCheck = confirm(
                        'This is your last chance. Are you absolutely sure you want to delete your account?'
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
                        <h1>Choose Your Plan</h1>
                        <p>Simple, transparent pricing that grows with you</p>
                    </div>

                    <!-- Billing Toggle -->
                    <div class="billing-toggle">
                        <span class="billing-option active" data-billing="monthly">Monthly</span>
                        <div class="toggle-switch" id="billing-toggle">
                            <div class="toggle-slider"></div>
                        </div>
                        <span class="billing-option" data-billing="annual">
                            Annual
                            <span class="billing-badge">Save 20%</span>
                        </span>
                    </div>

                    <!-- Pricing Cards -->
                    <div class="pricing-grid">
                        <!-- Free Plan -->
                        <div class="pricing-card">
                            <div class="plan-header">
                                <h3 class="plan-name">Free</h3>
                                <p class="plan-description">Perfect for getting started</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount">0</span>
                                <span class="price-period">/month</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>1 Trading Bot</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Basic Technical Indicators</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Portfolio Tracking</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Email Notifications</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>Advanced Strategies</span>
                                </li>
                                <li class="feature-excluded">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span>API Access</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-secondary" data-plan="free">
                                Current Plan
                            </button>
                        </div>

                        <!-- Premium Plan (Highlighted) -->
                        <div class="pricing-card pricing-card-featured">
                            <div class="featured-badge">Most Popular</div>
                            <div class="plan-header">
                                <h3 class="plan-name">Premium</h3>
                                <p class="plan-description">For professional traders</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-currency">₩</span>
                                <span class="price-amount" data-monthly="49000" data-annual="39200">49,000</span>
                                <span class="price-period">/month</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Unlimited Trading Bots</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>All Technical Indicators</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Advanced Chart Tools</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>AI-Powered Strategies</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Real-time Alerts</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Priority Support</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-primary" data-plan="premium">
                                Upgrade to Premium
                            </button>
                        </div>

                        <!-- Enterprise Plan -->
                        <div class="pricing-card">
                            <div class="plan-header">
                                <h3 class="plan-name">Enterprise</h3>
                                <p class="plan-description">For institutional investors</p>
                            </div>
                            <div class="plan-price">
                                <span class="price-custom">Custom</span>
                            </div>
                            <ul class="plan-features">
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Everything in Premium</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Dedicated Account Manager</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>Custom Strategy Development</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>White-label Solution</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>API & Webhook Access</span>
                                </li>
                                <li class="feature-included">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <span>SLA Guarantee</span>
                                </li>
                            </ul>
                            <button class="plan-cta plan-cta-secondary" data-plan="enterprise">
                                Contact Sales
                            </button>
                        </div>
                    </div>

                    <!-- FAQ Section -->
                    <div class="pricing-faq">
                        <h2>Frequently Asked Questions</h2>
                        <div class="faq-grid">
                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>Can I change plans later?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>Yes! You can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>What payment methods do you accept?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>We accept credit cards, Kakao Pay, Toss, and bank transfers for Enterprise plans.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>Is there a free trial?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>Premium plans come with a 14-day free trial. No credit card required to start.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>What happens if I cancel?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>You can cancel anytime. Your account will remain active until the end of your billing period, then revert to the Free plan.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>Do you offer refunds?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>We offer a 30-day money-back guarantee for annual plans. No questions asked.</p>
                                </div>
                            </div>

                            <div class="faq-item">
                                <h3 class="faq-question">
                                    <span>Is my data secure?</span>
                                    <svg class="faq-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                </h3>
                                <div class="faq-answer">
                                    <p>Yes! We use bank-level encryption (AES-256) and never store your exchange API secret keys in plain text.</p>
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
                        alert('You are already on the Free plan.');
                    } else if (plan === 'premium') {
                        // TODO: Redirect to checkout page
                        console.log('[Pricing] Upgrading to Premium');
                        alert('Premium upgrade coming soon! This will redirect to the payment page.');
                    } else if (plan === 'enterprise') {
                        // TODO: Open contact form or redirect to contact page
                        console.log('[Pricing] Contacting sales for Enterprise');
                        alert('Enterprise inquiries coming soon! We will contact you within 24 hours.');
                    }
                });
            });
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
                    localStorage.removeItem('auth_token');
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
        window.dashboardManager = new DashboardManager();
    });

})();
