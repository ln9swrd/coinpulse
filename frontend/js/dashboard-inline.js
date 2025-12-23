        (function() {
            'use strict';

            console.log('[Dashboard] Dashboard loaded');

            // ================================================================
            // Authentication Check
            // ================================================================

            // Redirect to login if not authenticated
            const isAuth = window.api.isAuthenticated();
            console.log('[Dashboard] Auth check:', {
                isAuthenticated: isAuth,
                accessToken: localStorage.getItem('access_token') ? 'EXISTS' : 'NULL',
                apiAccessToken: window.api.accessToken ? 'EXISTS' : 'NULL',
                currentURL: window.location.href
            });

            if (!isAuth) {
                console.log('[Dashboard] User not authenticated, redirecting to login...');
                setTimeout(() => {
                    window.location.href = '/login.html';
                }, 100);
                return;
            }

            console.log('[Dashboard] User authenticated, loading dashboard...');

            // ================================================================
            // DOM Elements
            // ================================================================

            const userNameEl = document.getElementById('user-name');
            const userEmailEl = document.getElementById('user-email');
            const userInitialEl = document.getElementById('user-initial');
            const logoutBtn = document.getElementById('logout-btn');
            const logoutDropdownBtn = document.getElementById('logout-dropdown');
            const contentContainer = document.getElementById('content-container');

            // ================================================================
            // API Key Status Check
            // ================================================================

            function checkApiKeyStatus(user) {
                const apiKeyNotice = document.getElementById('api-key-notice');
                const closeBtn = document.getElementById('close-api-notice');
                const showGuideBtn = document.getElementById('show-api-guide-btn');

                // Check if user dismissed the notice (stored in localStorage)
                const dismissed = localStorage.getItem('api-key-notice-dismissed');

                // Show notice if user doesn't have API keys and hasn't dismissed it
                if (!user.has_upbit_keys && !dismissed) {
                    console.log('[Dashboard] User has no Upbit API keys - showing notice');
                    apiKeyNotice.style.display = 'block';
                } else {
                    console.log('[Dashboard] API keys:', user.has_upbit_keys ? 'configured' : 'not configured (notice dismissed)');
                }

                // Close button handler
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => {
                        apiKeyNotice.style.display = 'none';
                        localStorage.setItem('api-key-notice-dismissed', 'true');
                        console.log('[Dashboard] API key notice dismissed');
                    });
                }

                // Show guide button handler
                if (showGuideBtn) {
                    showGuideBtn.addEventListener('click', () => {
                        showApiKeyGuide();
                    });
                }
            }

            function showApiKeyGuide() {
                alert(`
📖 업비트 API 키 발급 방법

1️⃣ 업비트 웹사이트 접속
   https://upbit.com

2️⃣ 로그인 후 우측 상단 '마이페이지' 클릭

3️⃣ 좌측 메뉴에서 'Open API 관리' 선택

4️⃣ 'Open API Key 발급' 버튼 클릭

5️⃣ 권한 설정:
   ✅ 자산 조회 (필수)
   ✅ 주문 조회 (필수)
   ⚠️ 주문하기 (자동거래 사용 시 필요)
   ⚠️ 출금하기 (권장하지 않음)

6️⃣ IP 주소 등록:
   - 특정 IP만 허용 (권장)
   - 또는 모든 IP 허용 (보안 위험)

7️⃣ 발급된 키 복사:
   - Access Key (공개 키)
   - Secret Key (비밀 키)
   ⚠️ Secret Key는 다시 볼 수 없으니 안전하게 보관하세요!

8️⃣ 코인펄스 설정에서 키 등록:
   대시보드 → 설정 → API 키 탭
                `);
            }

            // ================================================================
            // Load User Profile
            // ================================================================

            // Global variable to store current user
            let currentUser = null;

            async function loadUserProfile() {
                try {
                    console.log('[Dashboard] Loading user profile...');
                    const response = await window.api.getCurrentUser();

                    if (response.success && response.user) {
                        const user = response.user;
                        currentUser = user; // Store globally

                        // Update UI
                        if (userNameEl) {
                            userNameEl.textContent = user.username || user.email.split('@')[0];
                        }
                        if (userEmailEl) {
                            userEmailEl.textContent = user.email;
                        }
                        if (userInitialEl) {
                            const initial = (user.username || user.email)[0].toUpperCase();
                            userInitialEl.textContent = initial;
                        }

                        console.log('[Dashboard] User profile loaded:', user);
                        console.log('[Dashboard] is_admin:', user.is_admin, 'type:', typeof user.is_admin);

                        // Show admin menu if user is admin
                        if (user.is_admin) {
                            console.log('[Dashboard] User is admin - showing admin menu');

                            // Top bar dropdown admin menu
                            const adminMenuItem = document.getElementById('admin-menu-item');
                            if (adminMenuItem) {
                                adminMenuItem.style.display = 'flex';
                                console.log('[Dashboard] Admin dropdown menu shown');
                            } else {
                                console.warn('[Dashboard] Admin dropdown menu element not found!');
                            }

                            // Sidebar admin section
                            const adminSectionTitle = document.getElementById('admin-section-title');
                            const adminMenuLink = document.getElementById('admin-menu-link');
                            if (adminSectionTitle) {
                                adminSectionTitle.style.display = 'block';
                                console.log('[Dashboard] Admin section title shown');
                            } else {
                                console.warn('[Dashboard] Admin section title element not found!');
                            }
                            if (adminMenuLink) {
                                adminMenuLink.style.display = 'flex';
                                console.log('[Dashboard] Admin sidebar link shown');
                            } else {
                                console.warn('[Dashboard] Admin sidebar link element not found!');
                            }

                            console.log('[Dashboard] Admin menus enabled for:', user.email);
                        } else {
                            console.log('[Dashboard] User is NOT admin - hiding admin menu');
                            console.log('[Dashboard] Email:', user.email);
                        }

                        // Check if user has Upbit API keys
                        checkApiKeyStatus(user);

                        return user;
                    } else {
                        throw new Error('Invalid response format');
                    }
                } catch (error) {
                    console.error('[Dashboard] Failed to load user profile:', error);

                    // If unauthorized, logout
                    if (error.status === 401) {
                        console.warn('[Dashboard] 401 Unauthorized - redirecting to login');
                        window.api.clearTokens();
                        window.location.href = '/login.html';
                    }

                    // Show error in UI
                    if (userNameEl) userNameEl.textContent = '프로필 로딩 오류';
                    if (userEmailEl) userEmailEl.textContent = '페이지를 새로고침 해주세요';
                }
            }

            // ================================================================
            // Logout Functionality
            // ================================================================

            async function handleLogout() {
                try {
                    console.log('[Dashboard] Logging out...');

                    // Show loading state
                    if (contentContainer) {
                        contentContainer.innerHTML = `
                            <div class="loading-state">
                                <div class="spinner-large"></div>
                                <p>로그아웃 중...</p>
                            </div>
                        `;
                    }

                    // Call logout API
                    await window.api.logout();

                    // Redirect to home
                    window.location.href = '/index.html';
                } catch (error) {
                    console.error('[Dashboard] Logout error:', error);

                    // Clear tokens anyway
                    window.api.clearTokens();
                    window.location.href = '/index.html';
                }
            }

            // Attach logout handlers
            if (logoutBtn) {
                logoutBtn.addEventListener('click', handleLogout);
            }
            if (logoutDropdownBtn) {
                logoutDropdownBtn.addEventListener('click', handleLogout);
            }

            // ================================================================
            // Initialize Dashboard
            // ================================================================

            async function initDashboard() {
                try {
                    // Load user profile
                    await loadUserProfile();

                    // Show dashboard content
                    showDashboardContent();

                    // Load all dashboard data
                    await Promise.all([
                        loadPortfolio(),
                        loadOrders(),
                        loadAutoTradingStatus()
                    ]);

                    // Set up auto-refresh (every 30 seconds)
                    setInterval(async () => {
                        console.log('[Dashboard] Auto-refreshing data...');
                        await Promise.all([
                            loadPortfolio(),
                            loadOrders(),
                            loadAutoTradingStatus()
                        ]);
                    }, 30000); // 30 seconds

                    console.log('[Dashboard] Initialization complete');
                } catch (error) {
                    console.error('[Dashboard] Initialization error:', error);
                }
            }

            // ================================================================
            // Portfolio Display
            // ================================================================

            async function loadPortfolio() {
                const portfolioContainer = document.getElementById('portfolio-container');
                if (!portfolioContainer) return;

                // Check if user has API keys
                if (!currentUser || !currentUser.has_upbit_keys) {
                    console.log('[Dashboard] No API keys - showing empty state');
                    portfolioContainer.innerHTML = `
                        <div style="text-align: center; padding: 60px 20px;">
                            <div style="font-size: 64px; margin-bottom: 20px;">🔑</div>
                            <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                업비트 API 키가 등록되지 않았습니다
                            </h3>
                            <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                실제 보유 자산을 확인하려면<br>
                                업비트 API 키를 먼저 등록해주세요.
                            </p>
                            <button onclick="window.showPage('settings')" style="
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
                    return;
                }

                try {
                    console.log('[Dashboard] Loading portfolio...');
                    const response = await window.api.getHoldings();

                    if (response.success && response.coins) {
                        // Map new API format to legacy format for displayPortfolio
                        const holdings = response.coins.map(coin => ({
                            ...coin,
                            currency: coin.coin,  // Map coin → currency
                            avg_buy_price: coin.avg_price  // Map avg_price → avg_buy_price
                        }));
                        displayPortfolio(holdings);
                        return response;
                    } else if (response.success && response.holdings) {
                        // Fallback for legacy format
                        displayPortfolio(response.holdings);
                        return response.holdings;
                    } else {
                        throw new Error('Invalid holdings response');
                    }
                } catch (error) {
                    console.error('[Dashboard] Failed to load portfolio:', error);
                    showPortfolioError();
                    return null;
                }
            }

            function displayPortfolio(holdings) {
                const portfolioContainer = document.getElementById('portfolio-container');
                if (!portfolioContainer) return;

                if (!holdings || holdings.length === 0) {
                    portfolioContainer.innerHTML = `
                        <div style="text-align: center; padding: 40px; color: #666;">
                            <p>보유 자산이 없습니다. 거래를 시작하여 포트폴리오를 확인하세요.</p>
                        </div>
                    `;
                    return;
                }

                const holdingsHTML = holdings.map(holding => {
                    const value = parseFloat(holding.balance) * parseFloat(holding.avg_buy_price || 0);
                    const profitLoss = value - (parseFloat(holding.balance) * parseFloat(holding.avg_buy_price || 0));
                    const profitLossPercent = holding.avg_buy_price ?
                        ((parseFloat(holding.current_price || 0) - parseFloat(holding.avg_buy_price)) / parseFloat(holding.avg_buy_price) * 100).toFixed(2) :
                        0;

                    return `
                        <div class="holding-card">
                            <div class="holding-header">
                                <h3>${holding.currency}</h3>
                                <span class="holding-balance">${parseFloat(holding.balance).toFixed(8)}</span>
                            </div>
                            <div class="holding-details">
                                <div class="detail-row">
                                    <span>평균 매수가:</span>
                                    <span>${parseFloat(holding.avg_buy_price || 0).toLocaleString()} KRW</span>
                                </div>
                                <div class="detail-row">
                                    <span>현재가:</span>
                                    <span>${parseFloat(holding.current_price || 0).toLocaleString()} KRW</span>
                                </div>
                                <div class="detail-row">
                                    <span>총 평가액:</span>
                                    <span>${value.toLocaleString()} KRW</span>
                                </div>
                                <div class="detail-row ${profitLoss >= 0 ? 'profit' : 'loss'}">
                                    <span>손익:</span>
                                    <span>${profitLoss >= 0 ? '+' : ''}${profitLoss.toLocaleString()} KRW (${profitLossPercent}%)</span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');

                portfolioContainer.innerHTML = holdingsHTML;
            }

            function showPortfolioError() {
                const portfolioContainer = document.getElementById('portfolio-container');
                if (!portfolioContainer) return;

                portfolioContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #dc3545;">
                        <p>포트폴리오 로딩 실패. 페이지를 새로고침하거나 API 키를 확인하세요.</p>
                    </div>
                `;
            }

            // ================================================================
            // Orders History
            // ================================================================

            async function loadOrders() {
                const ordersContainer = document.getElementById('orders-container');
                if (!ordersContainer) return;

                // Check if user has API keys
                if (!currentUser || !currentUser.has_upbit_keys) {
                    console.log('[Dashboard] No API keys - showing empty state');
                    ordersContainer.innerHTML = `
                        <div style="text-align: center; padding: 60px 20px;">
                            <div style="font-size: 64px; margin-bottom: 20px;">📊</div>
                            <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                업비트 API 키가 등록되지 않았습니다
                            </h3>
                            <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                실제 거래 내역을 확인하려면<br>
                                업비트 API 키를 먼저 등록해주세요.
                            </p>
                            <button onclick="window.showPage('settings')" style="
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
                    return;
                }

                try {
                    console.log('[Dashboard] Loading orders...');
                    const response = await window.api.getOrders({ limit: 10, state: 'done' });

                    if (response.success && response.orders) {
                        displayOrders(response.orders);
                        return response.orders;
                    } else {
                        throw new Error('Invalid orders response');
                    }
                } catch (error) {
                    console.error('[Dashboard] Failed to load orders:', error);
                    showOrdersError();
                    return null;
                }
            }

            function displayOrders(orders) {
                const ordersContainer = document.getElementById('orders-container');
                if (!ordersContainer) return;

                if (!orders || orders.length === 0) {
                    ordersContainer.innerHTML = `
                        <div style="text-align: center; padding: 40px; color: #666;">
                            <p>최근 거래 내역이 없습니다.</p>
                        </div>
                    `;
                    return;
                }

                const ordersHTML = `
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>날짜</th>
                                <th>마켓</th>
                                <th>유형</th>
                                <th>가격</th>
                                <th>수량</th>
                                <th>총액</th>
                                <th>상세</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${orders.map((order, index) => `
                                <tr>
                                    <td>${new Date(order.created_at).toLocaleString()}</td>
                                    <td>${order.market}</td>
                                    <td class="${order.side === 'bid' ? 'buy' : 'sell'}">${order.side.toUpperCase()}</td>
                                    <td>${parseFloat(order.price || 0).toLocaleString()} KRW</td>
                                    <td>${parseFloat(order.volume || 0).toFixed(8)}</td>
                                    <td>${(parseFloat(order.price || 0) * parseFloat(order.volume || 0)).toLocaleString()} KRW</td>
                                    <td><button class="btn-small btn-primary" onclick='showOrderDetails(${JSON.stringify(order).replace(/'/g, "&#39;")})'>보기</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;

                ordersContainer.innerHTML = ordersHTML;
            }

            function showOrderDetails(order) {
                const modalHTML = `
                    <div class="modal-overlay" onclick="this.remove()">
                        <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 600px;">
                            <div class="modal-header">
                                <h3>거래 상세 정보</h3>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <div class="modal-body" style="max-height: 500px; overflow-y: auto;">
                                <div class="detail-grid" style="display: grid; grid-template-columns: 140px 1fr; gap: 12px; font-size: 14px;">
                                    <div style="font-weight: 600; color: #666;">주문 ID:</div>
                                    <div style="word-break: break-all;">${order.uuid || 'N/A'}</div>

                                    <div style="font-weight: 600; color: #666;">마켓:</div>
                                    <div>${order.market || 'N/A'}</div>

                                    <div style="font-weight: 600; color: #666;">거래 유형:</div>
                                    <div><span class="${order.side === 'bid' ? 'buy' : 'sell'}" style="padding: 4px 12px; border-radius: 4px; background: ${order.side === 'bid' ? '#d1fae5' : '#fee2e2'}; color: ${order.side === 'bid' ? '#065f46' : '#991b1b'}; font-weight: 600;">${order.side === 'bid' ? '매수 (BID)' : '매도 (ASK)'}</span></div>

                                    <div style="font-weight: 600; color: #666;">주문 타입:</div>
                                    <div>${order.ord_type || 'N/A'}</div>

                                    <div style="font-weight: 600; color: #666;">주문 상태:</div>
                                    <div><span style="padding: 4px 12px; border-radius: 4px; background: #d1fae5; color: #065f46; font-weight: 600;">${order.state || 'N/A'}</span></div>

                                    <div style="font-weight: 600; color: #666;">주문 가격:</div>
                                    <div>${parseFloat(order.price || 0).toLocaleString()} KRW</div>

                                    <div style="font-weight: 600; color: #666;">평균 체결가:</div>
                                    <div style="font-weight: 700; color: #667eea;">${parseFloat(order.avg_price || 0).toLocaleString()} KRW</div>

                                    <div style="font-weight: 600; color: #666;">주문 수량:</div>
                                    <div>${parseFloat(order.volume || 0).toFixed(8)}</div>

                                    <div style="font-weight: 600; color: #666;">체결 수량:</div>
                                    <div style="font-weight: 700; color: #10b981;">${parseFloat(order.executed_volume || 0).toFixed(8)}</div>

                                    <div style="font-weight: 600; color: #666;">미체결 수량:</div>
                                    <div>${parseFloat(order.remaining_volume || 0).toFixed(8)}</div>

                                    <div style="font-weight: 600; color: #666;">거래 총액:</div>
                                    <div style="font-weight: 700; font-size: 16px; color: #667eea;">${(parseFloat(order.price || 0) * parseFloat(order.volume || 0)).toLocaleString()} KRW</div>

                                    <div style="font-weight: 600; color: #666;">수수료:</div>
                                    <div>${parseFloat(order.paid_fee || 0).toLocaleString()} KRW</div>

                                    <div style="font-weight: 600; color: #666;">주문 생성 시각:</div>
                                    <div>${order.created_at ? new Date(order.created_at).toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'}) : 'N/A'}</div>

                                    ${order.executed_at ? `
                                        <div style="font-weight: 600; color: #666;">체결 완료 시각:</div>
                                        <div>${new Date(order.executed_at).toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'})}</div>
                                    ` : ''}

                                    ${order.locked ? `
                                        <div style="font-weight: 600; color: #666;">예약 금액:</div>
                                        <div>${parseFloat(order.locked).toLocaleString()} KRW</div>
                                    ` : ''}

                                    ${order.reserved_fee ? `
                                        <div style="font-weight: 600; color: #666;">예약 수수료:</div>
                                        <div>${parseFloat(order.reserved_fee).toLocaleString()} KRW</div>
                                    ` : ''}
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">닫기</button>
                            </div>
                        </div>
                    </div>
                `;

                document.body.insertAdjacentHTML('beforeend', modalHTML);
            }

            function showOrdersError() {
                const ordersContainer = document.getElementById('orders-container');
                if (!ordersContainer) return;

                ordersContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #dc3545;">
                        <p>거래 내역 로딩 실패. 페이지를 새로고침 해주세요.</p>
                    </div>
                `;
            }

            // ================================================================
            // Auto-Trading Status
            // ================================================================

            async function loadAutoTradingStatus() {
                const container = document.getElementById('auto-trading-container');
                if (!container) return;

                // Check subscription eligibility for auto-trading
                // Requirements: NOT free plan + active status + not expired
                try {
                    const subscriptionResponse = await window.api.getCurrentSubscription();
                    console.log('[Dashboard] Subscription API response:', subscriptionResponse);
                    const subscription = subscriptionResponse?.subscription;
                    console.log('[Dashboard] Subscription object:', subscription);
                    const plan = subscription?.plan || 'free';
                    const status = subscription?.status;
                    const endDate = subscription?.current_period_end;
                    console.log('[Dashboard] Parsed values:', {plan, status, endDate});

                    // Check 1: Free plan
                    if (plan === 'free' || !subscription) {
                        console.log('[Dashboard] Free plan or no subscription - auto-trading not available');
                        container.innerHTML = `
                            <div style="text-align: center; padding: 60px 20px;">
                                <div style="font-size: 64px; margin-bottom: 20px;">💎</div>
                                <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                    자동 거래는 유료 플랜 기능입니다
                                </h3>
                                <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                    자동 거래 기능을 사용하려면<br>
                                    Basic 또는 Pro 플랜으로 업그레이드하세요.
                                </p>
                                <button onclick="window.showPage('pricing')" style="
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
                                    요금제 업그레이드
                                </button>
                            </div>
                        `;
                        return;
                    }

                    // Check 2: Inactive subscription
                    if (status !== 'active') {
                        console.log('[Dashboard] Inactive subscription - auto-trading not available');
                        container.innerHTML = `
                            <div style="text-align: center; padding: 60px 20px;">
                                <div style="font-size: 64px; margin-bottom: 20px;">⏸️</div>
                                <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                    구독이 비활성화되었습니다
                                </h3>
                                <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                    자동 거래를 사용하려면<br>
                                    구독을 다시 활성화해주세요.
                                </p>
                                <button onclick="window.showPage('pricing')" style="
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
                                    구독 재개
                                </button>
                            </div>
                        `;
                        return;
                    }

                    // Check 3: Expired subscription
                    // NOTE: 만료일이 없으면 (null/undefined) 무제한 사용 가능
                    if (endDate && new Date(endDate) < new Date()) {
                        console.log('[Dashboard] Expired subscription - auto-trading not available');
                        const expiredDate = new Date(endDate).toLocaleDateString('ko-KR');
                        container.innerHTML = `
                            <div style="text-align: center; padding: 60px 20px;">
                                <div style="font-size: 64px; margin-bottom: 20px;">⏰</div>
                                <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                    구독이 만료되었습니다
                                </h3>
                                <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                    만료일: ${expiredDate}<br>
                                    자동 거래를 계속 사용하려면 구독을 갱신하세요.
                                </p>
                                <button onclick="window.showPage('pricing')" style="
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
                                    구독 갱신
                                </button>
                            </div>
                        `;
                        return;
                    }

                    // All checks passed - auto-trading available
                    if (endDate) {
                        console.log('[Dashboard] Subscription valid - auto-trading available', {plan, status, endDate});
                    } else {
                        console.log('[Dashboard] Subscription valid (unlimited - no expiry date) - auto-trading available', {plan, status, endDate: 'unlimited'});
                    }

                } catch (error) {
                    console.error('[Dashboard] Failed to check subscription:', error);
                    // Continue to show API key check if subscription check fails
                }

                // Check if user has API keys
                if (!currentUser || !currentUser.has_upbit_keys) {
                    console.log('[Dashboard] No API keys - showing empty state');
                    container.innerHTML = `
                        <div style="text-align: center; padding: 60px 20px;">
                            <div style="font-size: 64px; margin-bottom: 20px;">🤖</div>
                            <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px; font-weight: 600;">
                                업비트 API 키가 등록되지 않았습니다
                            </h3>
                            <p style="margin: 0 0 24px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                자동 거래를 시작하려면<br>
                                업비트 API 키를 먼저 등록해주세요.
                            </p>
                            <button onclick="window.showPage('settings')" style="
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
                    return;
                }

                try {
                    console.log('[Dashboard] Loading auto-trading status...');
                    const response = await window.api.getAutoTradingStatus();

                    if (response.success) {
                        displayAutoTradingStatus(response);
                        return response;
                    } else {
                        throw new Error(response.error || 'Invalid response');
                    }
                } catch (error) {
                    console.error('[Dashboard] Failed to load auto-trading status:', error);
                    showAutoTradingError(error);
                    return null;
                }
            }

            function displayAutoTradingStatus(data) {
                const container = document.getElementById('auto-trading-container');
                if (!container) return;

                const isEnabled = data.auto_trading_enabled || false;
                const positionsCount = data.open_positions_count || 0;
                const stats = data.statistics || {};

                const statusHTML = `
                    <div class="auto-trading-widget">
                        <!-- Status Header -->
                        <div class="status-header ${isEnabled ? 'enabled' : 'disabled'}">
                            <div class="status-indicator">
                                <div class="status-dot ${isEnabled ? 'active' : ''}"></div>
                                <span class="status-text">${isEnabled ? '활성' : '비활성'}</span>
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <button class="btn-toggle-trading" onclick="window.showPage('auto-trading-settings')" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;">
                                    ⚙️ 세부 설정
                                </button>
                                <button class="btn-toggle-trading" onclick="toggleAutoTrading(${!isEnabled})">
                                    ${isEnabled ? '중지' : '시작'}
                                </button>
                            </div>
                        </div>

                        <!-- Stats Grid -->
                        <div class="stats-grid">
                            <div class="stat-item">
                                <div class="stat-label">진행 중인 포지션</div>
                                <div class="stat-value">${positionsCount}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">총 거래 수</div>
                                <div class="stat-value">${stats.total_trades || 0}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">승률</div>
                                <div class="stat-value">${(stats.win_rate || 0).toFixed(1)}%</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">총 손익</div>
                                <div class="stat-value ${(stats.total_profit || 0) >= 0 ? 'profit' : 'loss'}">
                                    ${(stats.total_profit || 0) >= 0 ? '+' : ''}${(stats.total_profit || 0).toLocaleString()} KRW
                                </div>
                            </div>
                        </div>

                        <!-- Last Update -->
                        <div class="last-update">
                            마지막 업데이트: ${data.last_check ? new Date(data.last_check).toLocaleString() : '없음'}
                        </div>
                    </div>
                `;

                container.innerHTML = statusHTML;
            }

            function showAutoTradingError(error) {
                const container = document.getElementById('auto-trading-container');
                if (!container) return;

                const errorMessage = error?.message || '알 수 없는 오류';
                const errorDetails = error?.stack || '';

                container.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                        <h3 style="margin: 0 0 12px 0; color: #dc3545; font-size: 18px; font-weight: 600;">
                            자동 거래 상태 로딩 실패
                        </h3>
                        <p style="margin: 0 0 12px 0; color: #666; font-size: 14px;">
                            ${errorMessage}
                        </p>
                        <details style="margin-top: 20px; text-align: left; padding: 12px; background: #f8f9fa; border-radius: 4px; font-size: 12px; color: #666;">
                            <summary style="cursor: pointer; font-weight: 600; margin-bottom: 8px;">상세 오류 정보</summary>
                            <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${errorDetails}</pre>
                        </details>
                        <button onclick="loadAutoTradingStatus()" style="
                            margin-top: 20px;
                            background: #667eea;
                            color: white;
                            border: none;
                            padding: 10px 24px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: 600;
                            cursor: pointer;
                        ">
                            다시 시도
                        </button>
                    </div>
                `;
            }

            async function toggleAutoTrading(enable) {
                try {
                    console.log(`[Dashboard] ${enable ? 'Starting' : 'Stopping'} auto-trading...`);

                    // Show loading state
                    const container = document.getElementById('auto-trading-container');
                    if (container) {
                        container.innerHTML = `
                            <div class="loading-state">
                                <div class="spinner-small"></div>
                                <p>자동 거래 ${enable ? '시작' : '중지'} 중...</p>
                            </div>
                        `;
                    }

                    // Call API
                    const response = enable ?
                        await window.api.startAutoTrading({}) :
                        await window.api.stopAutoTrading();

                    if (response.success) {
                        console.log('[Dashboard] Auto-trading toggled successfully');
                        // Reload status after 1 second
                        setTimeout(() => loadAutoTradingStatus(), 1000);
                    } else {
                        throw new Error(response.error || 'Failed to toggle auto-trading');
                    }
                } catch (error) {
                    console.error('[Dashboard] Toggle auto-trading error:', error);
                    alert(`자동 거래 ${enable ? '시작' : '중지'} 실패: ${error.message}`);
                    // Reload current status
                    loadAutoTradingStatus();
                }
            }

            // ================================================================
            // Dashboard Content
            // ================================================================

            function showDashboardContent() {
                if (!contentContainer) return;

                contentContainer.innerHTML = `
                    <div class="dashboard-grid">
                        <!-- Portfolio Section -->
                        <div class="dashboard-card">
                            <div class="card-header">
                                <h2>포트폴리오 보유 자산</h2>
                                <button class="btn-refresh" onclick="loadPortfolio()">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                                    </svg>
                                    새로고침
                                </button>
                            </div>
                            <div class="card-content" id="portfolio-container">
                                <div id="portfolio-summary">
                                    <div class="loading-state">
                                        <div class="spinner-small"></div>
                                        <p>포트폴리오 로딩 중...</p>
                                    </div>
                                </div>
                                <div id="portfolio-holdings-table" style="margin-top: 24px;">
                                    <div class="loading-state">
                                        <div class="spinner-small"></div>
                                        <p>보유 자산 로딩 중...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Recent Orders Section -->
                        <div class="dashboard-card">
                            <div class="card-header">
                                <h2>최근 거래 내역</h2>
                                <button class="btn-refresh" onclick="loadOrders()">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                                    </svg>
                                    새로고침
                                </button>
                            </div>
                            <div class="card-content" id="orders-container">
                                <div class="loading-state">
                                    <div class="spinner-small"></div>
                                    <p>거래 내역 로딩 중...</p>
                                </div>
                            </div>
                        </div>

                        <!-- Auto-Trading Status Section -->
                        <div class="dashboard-card">
                            <div class="card-header">
                                <h2>자동 거래 상태</h2>
                                <button class="btn-refresh" onclick="loadAutoTradingStatus()">
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

                        <!-- Quick Links Section -->
                        <div class="dashboard-card">
                            <div class="card-header">
                                <h2>빠른 링크</h2>
                            </div>
                            <div class="card-content">
                                <div class="quick-links">
                                    <a href="/trading_chart.html" class="quick-link">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                                        </svg>
                                        <span>거래 차트</span>
                                    </a>
                                    <a href="/swing_trading_settings.html" class="quick-link">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <circle cx="12" cy="12" r="3"></circle>
                                            <path d="M12 1v6m0 6v6m-9-9h6m6 0h6"></path>
                                        </svg>
                                        <span>거래 설정</span>
                                    </a>
                                    <a href="/policy_manager.html" class="quick-link">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                            <polyline points="14 2 14 8 20 8"></polyline>
                                        </svg>
                                        <span>정책 관리자</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            // ================================================================
            // Start Dashboard
            // ================================================================

            // Expose functions to window for external access
            window.loadAutoTradingStatus = loadAutoTradingStatus;
            window.toggleAutoTrading = toggleAutoTrading;
            window.showDashboardContent = showDashboardContent;
            window.showPage = function(pageName) {
                if (window.dashboardApp) {
                    window.dashboardApp.loadPage(pageName);
                }
            };

            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initDashboard);
            } else {
                initDashboard();
            }

            console.log('[Dashboard] API integration loaded');
        })();
