        import pageLoader from './pages/page-loader.js';

        // Page mapping: route -> file path
        const PAGE_ROUTES = {
            'signals': 'my_signals.html',
            'telegram': 'telegram_settings.html',
            'trading': 'trading_chart.html',
            'realtime': 'realtime_dashboard.html',
            'surge': 'surge_monitoring.html',
            'auto-trading': 'surge_auto_trading.html',  // Surge-based auto-trading settings
            'referral': 'referral.html',
            'admin': 'admin.html'
            // Note: trading chart, surge, and auto-trading pages loaded via iframe
        };

        // Get content container
        const contentContainer = document.getElementById('content-container');

        /**
         * Load external page into dashboard
         */
        async function loadExternalPage(pageName) {
            const filePath = PAGE_ROUTES[pageName];

            if (!filePath) {
                console.warn('[Dashboard] Unknown page:', pageName);
                return false;
            }

            console.log('[Dashboard] Loading external page:', pageName, '→', filePath);

            try {
                // Special handling for pages that need iframe (to prevent CSS conflicts and enable JS execution)
                if (pageName === 'trading' || pageName === 'surge' || pageName === 'auto-trading') {
                    const pageUrl = `${window.location.origin}/${filePath}`;
                    const iframeId = pageName === 'trading' ? 'trading-chart-iframe' :
                                     pageName === 'surge' ? 'surge-monitoring-iframe' :
                                     'auto-trading-iframe';
                    console.log(`[Dashboard] Loading ${pageName} page via iframe:`, pageUrl);

                    contentContainer.innerHTML = `
                        <div style="width: 100%; height: calc(100vh - 80px); overflow: hidden; background: white;">
                            <iframe
                                src="${pageUrl}"
                                style="width: 100%; height: 100%; border: none; display: block;"
                                frameborder="0"
                                id="${iframeId}"
                                allow="clipboard-read; clipboard-write"
                                onload="console.log('[Dashboard] ${pageName} iframe loaded successfully')"
                                onerror="console.error('[Dashboard] ${pageName} iframe load error')"
                            ></iframe>
                        </div>
                    `;

                    // Verify iframe loaded
                    setTimeout(() => {
                        const iframe = document.getElementById(iframeId);
                        if (iframe) {
                            console.log(`[Dashboard] Iframe element exists for ${pageName}:`, iframe.src);
                            try {
                                console.log('[Dashboard] Iframe contentWindow:', iframe.contentWindow ? 'accessible' : 'blocked');
                            } catch (e) {
                                console.error('[Dashboard] Cannot access iframe content:', e.message);
                            }
                        }
                    }, 1000);

                    return true;
                }

                // Load page content for other pages
                await pageLoader.loadPage(filePath, contentContainer, {
                    useCache: true,
                    showLoading: true,
                    extractBody: true,
                    executeScripts: true
                });

                // Update page title
                updatePageTitle(pageName);

                return true;
            } catch (error) {
                console.error('[Dashboard] Failed to load page:', error);
                return false;
            }
        }

        /**
         * Update page title based on route
         */
        function updatePageTitle(pageName) {
            const pageTitleEl = document.getElementById('page-title');

            const titles = {
                'overview': '대시보드 홈',
                'trading': '거래 차트',
                'portfolio': '포트폴리오',
                'history': '거래 내역',
                'auto-trading': '자동매매 설정',
                'realtime': '실시간 모니터링',
                'surge': '급등 예측',
                'signals': '내 시그널',
                'telegram': '텔레그램 연동',
                'referral': '친구 초대하기',
                'pricing': '요금제',
                'settings': '설정',
                'admin': '관리자'
            };

            if (pageTitleEl && titles[pageName]) {
                pageTitleEl.textContent = titles[pageName];
            }
        }

        /**
         * Handle navigation click
         */
        async function handleNavigation(event) {
            // Get clicked nav item
            let navItem = event.target.closest('.nav-item');
            if (!navItem) return;

            // Allow external links (target="_blank") to open normally
            if (navItem.getAttribute('target') === '_blank') {
                return; // Don't prevent default, let the link open in new tab
            }

            // Prevent default link behavior
            event.preventDefault();

            // Get page name
            const href = navItem.getAttribute('href') || '';
            const pageName = navItem.dataset.page || (href.startsWith('#') ? href.substring(1) : href);
            if (!pageName) return;

            console.log('[Dashboard] Navigation clicked:', pageName);

            // Update active state
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            navItem.classList.add('active');

            // Update URL hash (without triggering hashchange)
            if (window.history.replaceState) {
                window.history.replaceState(null, null, `#${pageName}`);
            } else {
                window.location.hash = pageName;
            }

            // Load page
            const isExternal = PAGE_ROUTES[pageName];

            if (isExternal) {
                // Load external page
                await loadExternalPage(pageName);
            } else {
                // Internal page - use existing dashboard logic
                updatePageTitle(pageName);

                // Show dashboard content if returning to overview
                if (pageName === 'overview') {
                    window.showDashboardContent();
                }
            }
        }

        /**
         * Handle hash change (browser back/forward)
         */
        function handleHashChange() {
            const hash = window.location.hash.substring(1) || 'overview';
            console.log('[Dashboard] Hash changed:', hash);

            // Find and click the corresponding nav item
            const navItem = document.querySelector(`.nav-item[data-page="${hash}"]`);
            if (navItem) {
                navItem.click();
            }
        }

        /**
         * Initialize page router
         */
        function initPageRouter() {
            // Attach click listeners to all nav items
            document.querySelectorAll('.nav-item').forEach(navItem => {
                navItem.addEventListener('click', handleNavigation);
            });

            // Handle browser back/forward
            window.addEventListener('hashchange', handleHashChange);

            // Load initial page based on hash
            const initialHash = window.location.hash.substring(1);
            if (initialHash && initialHash !== 'overview') {
                handleHashChange();
            }

            console.log('[Dashboard] Page router initialized');
        }

        // Expose loadExternalPage to window
        window.loadExternalPage = loadExternalPage;

        // Initialize router when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initPageRouter);
        } else {
            initPageRouter();
        }

        console.log('[Dashboard] Page loader integrated');
