// Working Trading Chart Implementation
// Based on test_null_fix.html which works correctly

class WorkingTradingChart {
    constructor() {
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.maSeries = {};
        this.rsiSeries = null;
        this.macdSeries = {
            macd: null,
            signal: null,
            histogram: null
        };
        this.chartData = [];
        this.currentMarket = 'KRW-BTC';

        // Unsupported coins list (no trading available on Upbit)
        this.unsupportedCoins = [
            'ETHW', 'ETHF', 'LUNA', 'LUNC', 'USTC',
            'BTG', 'BTT', 'BORA', 'MED', 'MVL'
        ];

        // TradingView 방식 로딩을 위한 속성들
        this.isLoading = false;
        this.hasMoreData = true;
        this.oldestTimestamp = null;
        this.newestTimestamp = null;
        this.loadedCandles = [];
        this.loadedVolume = [];
        this.currentTimeframe = 'days'; // Upbit API timeframe: minutes, days, weeks, months
        this.currentUnit = null; // For minutes: 1, 3, 5, 10, 15, 30, 60, 240
        this.autoUpdateInterval = null;

        // 코인 목록 저장
        this.allMarkets = [];

        // MA 설정 상태 (localStorage에서 로드 또는 기본값)
        this.maSettings = this.loadMASettings();
        // 초기 로드시 이평선은 표시하지 않음 (사용자 요청 시에만 표시)
        this.movingAveragesVisible = false;
        
        // 매매 이력 마커 표시 여부
        this.showTradeMarkers = true;

        // 테마 상태 (dark/light)
        this.currentTheme = localStorage.getItem('theme') || 'dark';

        // 평균단가 및 미체결 주문 수평선
        this.avgPriceLine = null;
        this.pendingOrderLines = [];
        this.avgPriceLineEnabled = true;  // 항상 표시
        this.pendingOrderLinesEnabled = true;  // 항상 표시

        // 지지저항선
        this.supportResistanceLines = [];
        this.supportResistanceEnabled = false;

        // Chart Actions Module (theme, volume, trade markers)
        this.chartActions = null; // Will be initialized after chart is ready

        // Moving Averages Module
        this.movingAverages = null; // Will be initialized after chart is ready

        // Technical Indicators Module (RSI, MACD, BB, SuperTrend)
        this.technicalIndicators = null; // Will be initialized after chart is ready

        // Chart Settings Module (timeframe, coin selection)
        this.chartSettings = null; // Will be initialized after chart is ready

        // Drawing Tools Module (trendlines, fibonacci, etc.)
        this.drawingTools = null; // Will be initialized after chart is ready

        console.log('[Working] Chart class initialized');

        // Initialize delegated modules
        this.dataLoader = null; // Will be initialized after chart is ready
        this.realtimeUpdates = null; // Will be initialized after chart is ready
    }

    // MA 설정 로드 (localStorage)
    loadMASettings() {
        try {
            const saved = localStorage.getItem('maSettings');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('[Working] Failed to load MA settings:', error);
        }

        // 기본값 - 모두 표시 안 함
        return {
            20: false,
            50: false,
            100: false,
            200: false,
            300: false,
            500: false,
            1000: false
        };
    }

    // MA 설정 저장 (localStorage)
    saveMASettings() {
        try {
            localStorage.setItem('maSettings', JSON.stringify(this.maSettings));
            console.log('[Working] MA settings saved:', this.maSettings);
        } catch (error) {
            console.error('[Working] Failed to save MA settings:', error);
        }
    }

    async init() {
        try {
            console.log('[Working] Initialization started');

            // MA 설정 불러오기 (저장된 설정이 있으면 유지)
            this.maSettings = this.loadMASettings();
            console.log('[Working] MA settings loaded:', this.maSettings);

            // Initialize chart
            await this.initChart();

            // Initialize DataLoader module
            this.dataLoader = new DataLoader(this);
            console.log('[Working] DataLoader module initialized');

            // Initialize RealtimeUpdates module
            this.realtimeUpdates = new RealtimeUpdates(this);
            console.log('[Working] RealtimeUpdates module initialized');

            // Load data
            await this.dataLoader.loadData();

            // Setup event handlers
            this.setupEventHandlers();

            // Initialize ChartActions module
            if (typeof ChartActions !== 'undefined') {
                this.chartActions = new ChartActions(this);
                this.chartActions.initializeTheme();
                console.log('[Working] ChartActions module initialized');
            } else {
                // Fallback to old method if module not loaded
                this.applyTheme(this.currentTheme);
                console.warn('[Working] ChartActions module not available, using fallback');
            }

            // Initialize MovingAverages module
            if (typeof MovingAverages !== 'undefined') {
                this.movingAverages = new MovingAverages(this);
                console.log('[Working] MovingAverages module initialized');
            } else {
                console.warn('[Working] MovingAverages module not available, using fallback');
            }

            // Initialize TechnicalIndicators module
            if (typeof TechnicalIndicators !== 'undefined') {
                this.technicalIndicators = new TechnicalIndicators(this);
                console.log('[Working] TechnicalIndicators module initialized');
            } else {
                console.warn('[Working] TechnicalIndicators module not available, using fallback');
            }

            // Initialize ChartSettings module
            if (typeof ChartSettings !== 'undefined') {
                this.chartSettings = new ChartSettings(this);
                console.log('[Working] ChartSettings module initialized');
                // Load coin list using module
                await this.chartSettings.loadCoinList();
            } else {
                console.warn('[Working] ChartSettings module not available, using fallback');
                // Fallback: load coin list directly
                await this.dataLoader.loadCoinList();
            }

            // Initialize DrawingTools module
            if (typeof DrawingTools !== 'undefined') {
                this.drawingTools = new DrawingTools(this);
                this.drawingTools.setupEventHandlers();
                console.log('[Working] DrawingTools module initialized');

                // Setup chart click handler for drawing
                this.chartContainer = document.getElementById('chart-container');
                if (this.chartContainer) {
                    this.chartContainer.addEventListener('click', (event) => {
                        this.handleChartClickForDrawing(event);
                    });
                    console.log('[Working] Chart click handler setup for drawing tools');
                }

                // Load saved drawings
                this.drawingTools.loadDrawings();
            } else {
                console.warn('[Working] DrawingTools module not available');
            }

            console.log('[Working] Main initialization completed');

            // Load holdings and trading history in background (non-blocking)
            this.dataLoader.loadBackgroundData();

        } catch (error) {
            console.error('[Working] Initialization failed:', error);
        }
    }

    // 백그라운드에서 보유 코인 및 거래내역 로딩 (병렬 처리)

    async initChart() {
        console.log('[Working] Creating chart...');

        const chartContainer = document.getElementById('chart-container');
        if (!chartContainer) {
            throw new Error('Chart container not found');
        }

        // Use ChartUtils for initialization
        if (!window.chartUtils) {
            console.error('[Working] ChartUtils not available, creating new instance');
            window.chartUtils = new ChartUtils();
        }

        this.chart = window.chartUtils.initChart('chart-container');
        this.candleSeries = window.chartUtils.candleSeries;
        this.volumeSeries = window.chartUtils.volumeSeries;

        // 거래량을 기본적으로 표시
        if (this.volumeSeries) {
            this.volumeSeries.applyOptions({
                visible: true
            });
            console.log('[Working] Volume series set to visible by default');
        }

        console.log('[Working] Chart created successfully');
    }


    // TradingView 방식: 초기 캔들 로드 (200개)

    // TradingView 방식: 스크롤 시 과거 데이터 로딩 설정

    // TradingView 방식: 과거 데이터 로딩

    // TradingView 방식: 최신 데이터 업데이트

    // TradingView 방식: 자동 업데이트 시작

    // TradingView 방식: 자동 업데이트 중지

    // TradingView 방식: 코인 변경
    async changeCoin(market) {
        if (this.currentMarket === market) return;

        console.log(`[Working] Changing coin from ${this.currentMarket} to ${market}`);
        
        // 자동 업데이트 중지
        this.realtimeUpdates.stopAutoUpdate();
        
        // SuperTrend 활성화 상태 저장
        const superTrendBtn = document.getElementById('supertrend-toggle');
        const isSuperTrendActive = superTrendBtn && superTrendBtn.classList.contains('active');
        
        // 상태 초기화
        this.currentMarket = market;
        this.isLoading = false;
        this.hasMoreData = true;
        this.oldestTimestamp = null;
        this.newestTimestamp = null;
        this.loadedCandles = [];
        this.loadedVolume = [];
        
        // 새로운 코인 데이터 로드
        await this.dataLoader.loadInitialCandles();
        this.dataLoader.setupTradingViewStyleLoading();
        this.realtimeUpdates.startAutoUpdate();
        
        // SuperTrend가 활성화되어 있었다면 새 데이터로 다시 그리기
        if (isSuperTrendActive && this.chartData && this.chartData.length > 0 && window.chartUtils) {
            console.log('[Working] Re-applying SuperTrend for new coin');
            window.chartUtils.removeSuperTrend();
            const result = window.chartUtils.addSuperTrend(this.chartData, 10, 3.0);
            if (result) {
                console.log('[Working] SuperTrend re-applied successfully');
            }
        }

        // 지지저항선이 활성화되어 있었다면 새 데이터로 다시 그리기
        if (this.supportResistanceEnabled && this.chartData && this.chartData.length > 0) {
            console.log('[Working] Re-applying support/resistance for new coin');
            this.drawSupportResistance();
        }

        // 매매 이력도 새로운 코인으로 업데이트 (캐시 무시하고 강제 로드)
        await this.dataLoader.loadTradingHistory(true);

        // 평균단가와 미체결 주문 수평선 표시
        await this.updateAvgPriceAndPendingOrders();

        // 코인별 그리기 도구 로드
        if (this.drawingTools) {
            console.log('[Working] Loading drawings for new coin');
            this.drawingTools.loadDrawings();
        }

        // 수동 주문 패널 업데이트
        if (this.updateOrderPanelCoin) {
            console.log('[Working] Updating manual order panel for new coin');
            this.updateOrderPanelCoin();
        }
        if (this.updateAvailableBalances) {
            console.log('[Working] Updating available balances for new coin');
            this.updateAvailableBalances();
        }

        console.log(`[Working] Coin changed to ${market}`);
    }

    // Clear all MA series from chart
    clearMAs() {
        // Use MovingAverages module if available
        if (this.movingAverages) {
            this.movingAverages.clearMAs();
            this.maSeries = this.movingAverages.maSeries;
            return;
        }

        // Fallback
        console.log('[Working] Clearing all MA series...');
        const maKeys = ['ma20', 'ma50', 'ma100', 'ma200', 'ma300', 'ma500', 'ma1000'];
        maKeys.forEach(key => {
            if (this.maSeries[key]) {
                try {
                    window.chartUtils.chart.removeSeries(this.maSeries[key]);
                    this.maSeries[key] = null;
                    console.log(`[Working] ${key.toUpperCase()} series removed`);
                } catch (error) {
                    console.error(`[Working] Failed to remove ${key}:`, error);
                }
            }
        });
        console.log('[Working] All MA series cleared');
    }

    drawMAs() {
        // Use MovingAverages module if available
        if (this.movingAverages) {
            this.movingAverages.drawMAs();
            this.maSeries = this.movingAverages.maSeries;
            return;
        }

        // Fallback
        console.log('[Working] Drawing MA lines based on saved settings...');
        if (!this.chartData || this.chartData.length === 0) {
            console.warn('[Working] No data for MA calculation');
            return;
        }
        this.clearMAs();

        const maConfigs = [
            { period: 20, color: '#ff6b6b' },
            { period: 50, color: '#4ecdc4' },
            { period: 100, color: '#45b7d1' },
            { period: 200, color: '#96ceb4' },
            { period: 300, color: '#feca57' },
            { period: 500, color: '#ff9ff3' },
            { period: 1000, color: '#54a0ff' }
        ];

        maConfigs.forEach(({ period, color }) => {
            // 저장된 설정 확인
            if (!this.maSettings[period]) {
                console.log(`[Working] MA${period} is disabled, skipping...`);
                return;
            }

            try {
                const maData = window.chartUtils.calculateMovingAverage(this.chartData, period);
                console.log(`[Working] MA${period}: ${maData.length} values`);

                if (maData.length > 0) {
                    const maSeries = window.chartUtils.addMovingAverage(period, color);
                    maSeries.setData(maData);
                    this.maSeries[`ma${period}`] = maSeries;
                    console.log(`[Working] MA${period} added successfully (enabled in settings)`);
                }
            } catch (error) {
                console.error(`[Working] MA${period} failed:`, error);
            }
        });

        console.log('[Working] MA drawing completed');
    }



    /**
     * Update real-time analysis panel
     * Updates RSI, trend, volatility, support/resistance, and trading signals
     */

    /**
     * Update trend direction indicator
     */

    /**
     * Update volatility indicator (based on ATR)
     */

    /**
     * Update support and resistance levels in analysis panel
     */


    // 코인별 아이콘 이미지 URL 반환 (cryptocurrency-icons GitHub CDN 사용)



    
    // 매매 이력을 차트에 마커로 표시
    
    // 매매 마커 토글
    toggleTradeMarkers() {
        // Use ChartActions module if available
        if (this.chartActions) {
            this.chartActions.toggleTradeMarkers();
            // Sync showTradeMarkers state
            this.showTradeMarkers = this.chartActions.showTradeMarkers;
        } else {
            // Fallback to original implementation
            this.showTradeMarkers = !this.showTradeMarkers;

            const toggleBtn = document.getElementById('trade-markers-toggle');
            if (toggleBtn) {
                if (this.showTradeMarkers) {
                    toggleBtn.classList.add('active');
                } else {
                    toggleBtn.classList.remove('active');
                }
            }

            console.log(`[Working] Trade markers ${this.showTradeMarkers ? 'enabled' : 'disabled'}`);
            this.dataLoader.loadTradingHistory(true);
        }
    }

    // Load trading history (delegation method)
    async loadTradingHistory(forceRefresh = false) {
        if (this.dataLoader && typeof this.dataLoader.loadTradingHistory === 'function') {
            await this.dataLoader.loadTradingHistory(forceRefresh);
        } else {
            console.warn('[Working] DataLoader not available for loadTradingHistory');
        }
    }

    // Timeframe 문자열 파싱 (HTML select value -> API parameters)
    parseTimeframe(timeframeValue) {
        const map = {
            '1m': { timeframe: 'minutes', unit: 1 },
            '5m': { timeframe: 'minutes', unit: 5 },
            '15m': { timeframe: 'minutes', unit: 15 },
            '1h': { timeframe: 'minutes', unit: 60 },
            '4h': { timeframe: 'minutes', unit: 240 },
            '1d': { timeframe: 'days', unit: null },
            '1w': { timeframe: 'weeks', unit: null }
        };
        return map[timeframeValue] || { timeframe: 'days', unit: null };
    }

    // Timeframe 변경
    async changeTimeframe(timeframeValue) {
        const { timeframe, unit } = this.parseTimeframe(timeframeValue);

        if (this.currentTimeframe === timeframe && this.currentUnit === unit) {
            console.log('[Working] Timeframe already set, skipping');
            return;
        }

        console.log(`[Working] Changing timeframe to: ${timeframeValue} (${timeframe}, unit: ${unit})`);

        // 자동 업데이트 중지
        this.realtimeUpdates.stopAutoUpdate();

        // 상태 초기화
        this.currentTimeframe = timeframe;
        this.currentUnit = unit;
        this.isLoading = false;
        this.hasMoreData = true;
        this.oldestTimestamp = null;
        this.newestTimestamp = null;
        this.loadedCandles = [];
        this.loadedVolume = [];

        // 새로운 데이터 로드
        await this.dataLoader.loadInitialCandles();
        this.dataLoader.setupTradingViewStyleLoading();
        this.realtimeUpdates.startAutoUpdate();

        // 지지저항선이 활성화되어 있었다면 새 데이터로 다시 그리기
        if (this.supportResistanceEnabled && this.chartData && this.chartData.length > 0) {
            console.log('[Working] Re-applying support/resistance for new timeframe');
            this.drawSupportResistance();
        }

        console.log(`[Working] Timeframe changed to ${timeframeValue}`);
    }

    setupEventHandlers() {
        console.log('[Working] Setting up event handlers...');

        // Use ChartSettings module for settings-related event handlers
        if (this.chartSettings) {
            this.chartSettings.setupEventHandlers();
        } else {
            // Fallback: setup event handlers manually
            // Coin search input
            const coinSearch = document.getElementById('coin-search');
            if (coinSearch) {
                coinSearch.addEventListener('input', (e) => {
                    const searchTerm = e.target.value;
                    this.dataLoader.searchCoins(searchTerm);
                });

                coinSearch.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        const coinSelect = document.getElementById('coin-select');
                        if (coinSelect && coinSelect.options.length > 0) {
                            coinSelect.options[0].selected = true;
                            const selectedMarket = coinSelect.value;
                            console.log(`[Working] Search Enter: Selecting first result ${selectedMarket}`);
                            this.changeCoin(selectedMarket);
                            coinSearch.value = '';
                            this.dataLoader.searchCoins('');
                        }
                    }
                });

                coinSearch.addEventListener('focus', (e) => {
                    e.target.select();
                });
            }

            // Timeframe select change
            const timeframeSelect = document.getElementById('timeframe');
            if (timeframeSelect) {
                timeframeSelect.addEventListener('change', async (e) => {
                    const selectedTimeframe = e.target.value;
                    console.log(`[Working] Timeframe changed to: ${selectedTimeframe}`);
                    await this.changeTimeframe(selectedTimeframe);
                });
            }

            // Coin select change
            const coinSelect = document.getElementById('coin-select');
            if (coinSelect) {
                coinSelect.addEventListener('change', async (e) => {
                    const selectedMarket = e.target.value;
                    console.log(`[Working] Coin changed to: ${selectedMarket}`);
                    await this.changeCoin(selectedMarket);

                    // Update policy modal and header status
                    if (window.policyModalController) {
                        window.policyModalController.currentCoin = selectedMarket;
                        window.policyModalController.updateHeaderPolicyStatus(selectedMarket);
                    }
                });
            }

            // Refresh coins button
            const refreshCoinsBtn = document.getElementById('refresh-coins');
            if (refreshCoinsBtn) {
                refreshCoinsBtn.addEventListener('click', async () => {
                    console.log('[Working] Refreshing coin list...');
                    await this.dataLoader.loadCoinList();
                });
            }
        }

        // Refresh holdings button
        const refreshHoldingsBtn = document.getElementById('refresh-holdings');
        if (refreshHoldingsBtn) {
            refreshHoldingsBtn.addEventListener('click', async () => {
                console.log('[Working] Refreshing holdings...');
                await this.dataLoader.loadHoldings();
            });
        }

        // Hide unsupported coins toggle
        const hideUnsupportedToggle = document.getElementById('hide-unsupported');
        if (hideUnsupportedToggle) {
            // Load saved state from localStorage
            const savedState = localStorage.getItem('hideUnsupportedCoins');
            if (savedState !== null) {
                hideUnsupportedToggle.checked = savedState === 'true';
            }

            hideUnsupportedToggle.addEventListener('change', async (e) => {
                const isChecked = e.target.checked;
                console.log(`[Working] Hide unsupported coins: ${isChecked}`);

                // Save state to localStorage
                localStorage.setItem('hideUnsupportedCoins', isChecked);

                // Reload holdings with new filter
                await this.dataLoader.loadHoldings();
            });
        }

        // Manual order functionality
        this.initializeManualOrders();

        // Refresh trading history button
        const refreshHistoryBtn = document.getElementById('refresh-history');
        if (refreshHistoryBtn) {
            refreshHistoryBtn.addEventListener('click', async () => {
                console.log('[Working] Refreshing trading history...');
                await this.dataLoader.loadTradingHistory();
            });
        }

        // Technical Indicator Toggles
        const rsiToggle = document.getElementById('rsi-toggle');
        const macdToggle = document.getElementById('macd-toggle');
        const bollingerToggle = document.getElementById('bollinger-toggle');
        const superTrendToggle = document.getElementById('supertrend-toggle');

        if (rsiToggle) {
            rsiToggle.addEventListener('click', () => {
                console.log('[Working] RSI toggle clicked');
                if (this.technicalIndicators) {
                    this.technicalIndicators.toggleRSI();
                } else {
                    this.toggleRSI(); // Fallback
                }
            });
        }

        if (macdToggle) {
            macdToggle.addEventListener('click', () => {
                console.log('[Working] MACD toggle clicked');
                if (this.technicalIndicators) {
                    this.technicalIndicators.toggleMACD();
                } else {
                    this.toggleMACD(); // Fallback
                }
            });
        }

        if (bollingerToggle) {
            bollingerToggle.addEventListener('click', () => {
                console.log('[Working] Bollinger Bands toggle clicked');
                if (this.technicalIndicators) {
                    this.technicalIndicators.toggleBollingerBands();
                } else {
                    this.toggleBollingerBands(); // Fallback
                }
            });
        }

        if (superTrendToggle) {
            superTrendToggle.addEventListener('click', () => {
                console.log('[Working] SuperTrend toggle clicked');
                if (this.technicalIndicators) {
                    this.technicalIndicators.toggleSuperTrend();
                } else {
                    this.toggleSuperTrend(); // Fallback
                }
            });
        }

        // MA Toggle Button (Show/Hide all MAs)
        const maToggleBtn = document.getElementById('ma-toggle');
        if (maToggleBtn) {
            maToggleBtn.addEventListener('click', () => {
                console.log('[Working] MA toggle button clicked');
                this.toggleAllMAs();
            });
        }

        // Volume Toggle Button (Show/Hide volume)
        const volumeToggleBtn = document.getElementById('volume-toggle');
        if (volumeToggleBtn) {
            volumeToggleBtn.addEventListener('click', () => {
                console.log('[Working] Volume toggle button clicked');
                this.toggleVolume();
            });
            // 기본적으로 active 상태로 설정 (거래량 표시)
            volumeToggleBtn.classList.add('active');
        }

        // Support/Resistance Toggle Button
        const supportResistanceToggleBtn = document.getElementById('support-resistance-toggle');
        if (supportResistanceToggleBtn) {
            supportResistanceToggleBtn.addEventListener('click', () => {
                console.log('[Working] Support/Resistance toggle button clicked');
                this.toggleSupportResistance();
            });
        }

        // Theme Toggle Button (Dark/Light mode)
        const themeToggleBtn = document.getElementById('theme-toggle');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => {
                console.log('[Working] Theme toggle button clicked');
                this.toggleTheme();
            });
        }

        // MA Settings Modal
        const maSettingsBtn = document.getElementById('ma-settings-btn');
        const maSettingsModal = document.getElementById('ma-settings-modal');
        const closeMaSettings = document.getElementById('close-ma-settings');
        const applyMaSettings = document.getElementById('apply-ma-settings');
        const cancelMaSettings = document.getElementById('cancel-ma-settings');

        if (maSettingsBtn) {
            maSettingsBtn.addEventListener('click', () => {
                console.log('[Working] MA settings button clicked');
                this.openMASettingsModal();
            });
        }

        if (closeMaSettings) {
            closeMaSettings.addEventListener('click', () => {
                console.log('[Working] Close MA settings clicked');
                this.closeMASettingsModal();
            });
        }

        if (applyMaSettings) {
            applyMaSettings.addEventListener('click', () => {
                console.log('[Working] Apply MA settings clicked');
                this.applyMASettings();
            });
        }

        if (cancelMaSettings) {
            cancelMaSettings.addEventListener('click', () => {
                console.log('[Working] Cancel MA settings clicked');
                this.closeMASettingsModal();
            });
        }

        // Close modal when clicking outside
        if (maSettingsModal) {
            maSettingsModal.addEventListener('click', (e) => {
                if (e.target === maSettingsModal) {
                    this.closeMASettingsModal();
                }
            });
        }

        console.log('[Working] Event handlers set up successfully');
    }

    // Technical Indicator Toggle Functions
    toggleRSI() {
        const btn = document.getElementById('rsi-toggle');
        const isActive = btn.classList.contains('active');

        if (isActive) {
            // Hide RSI
            btn.classList.remove('active');
            console.log('[Working] Hiding RSI');

            // Remove RSI series from chart
            if (this.rsiSeries) {
                window.chartUtils.chart.removeSeries(this.rsiSeries);
                this.rsiSeries = null;
                console.log('[Working] RSI series removed');
            }

            // Hide RSI info panel
            const rsiInfo = document.getElementById('rsi-status');
            const rsiValue = document.getElementById('rsi-value');
            if (rsiInfo && rsiValue) {
                rsiInfo.textContent = '-';
                rsiValue.textContent = '-';
            }
        } else {
            // Show RSI
            btn.classList.add('active');
            console.log('[Working] Showing RSI');

            if (this.chartData && this.chartData.length > 0) {
                const rsiData = window.chartUtils.calculateRSI(this.chartData, 14);
                console.log('[Working] RSI calculated:', rsiData.length, 'values');

                if (rsiData.length > 0) {
                    // Create RSI line series (scaled to price chart)
                    // Note: This shows RSI on main chart - not ideal but simple
                    // For production, you'd want a separate pane

                    // Scale RSI (0-100) to price range for visibility
                    const priceRange = this.chartData.reduce((acc, candle) => {
                        return {
                            min: Math.min(acc.min, candle.low),
                            max: Math.max(acc.max, candle.high)
                        };
                    }, { min: Infinity, max: -Infinity });

                    const priceSpan = priceRange.max - priceRange.min;
                    const scaledRsiData = rsiData.map(item => ({
                        time: item.time,
                        value: priceRange.min + (item.value / 100) * priceSpan * 0.2 // Scale to 20% of price range
                    }));

                    this.rsiSeries = window.chartUtils.chart.addLineSeries({
                        color: '#9C27B0',
                        lineWidth: 2,
                        title: 'RSI(14)',
                        priceLineVisible: false,
                        lastValueVisible: false,
                        priceScaleId: 'right'
                    });

                    this.rsiSeries.setData(scaledRsiData);
                    console.log('[Working] RSI series added to chart');

                    // Update RSI info display
                    this.updateRSIInfo(rsiData);
                }
            }
        }
    }

    updateRSIInfo(rsiData) {
        if (!rsiData || rsiData.length === 0) return;

        const latestRSI = rsiData[rsiData.length - 1];
        const rsiValue = document.getElementById('rsi-value');
        const rsiStatus = document.getElementById('rsi-status');
        const tradingSignal = document.getElementById('trading-signal');

        if (rsiValue && latestRSI) {
            rsiValue.textContent = latestRSI.value.toFixed(1);

            let statusText = '';
            let signalText = '';
            let statusClass = '';
            let backgroundColor = '';
            let textColor = '';

            if (rsiStatus) {
                if (latestRSI.value >= 80) {
                    // 극심한 과매수 (매우 위험)
                    statusText = '⚠️ 극심한 과매수';
                    statusClass = 'indicator-status extreme-overbought';
                    signalText = '🔴 강한 매도 신호 (조정 임박)';
                    backgroundColor = '#ff1744';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 70) {
                    // 과매수 (주의)
                    statusText = '⚠️ 과매수';
                    statusClass = 'indicator-status overbought';
                    signalText = '🟠 매도 고려 (고점 근처)';
                    backgroundColor = '#ff9800';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 60) {
                    // 강세 (상승 중)
                    statusText = '📈 강세';
                    statusClass = 'indicator-status bullish';
                    signalText = '✅ 상승 추세 유지';
                    backgroundColor = '#4caf50';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 40) {
                    // 중립 (횡보)
                    statusText = '➡️ 중립';
                    statusClass = 'indicator-status neutral';
                    signalText = '⏸️ 관망 (방향성 불명확)';
                    backgroundColor = '#9e9e9e';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 30) {
                    // 약세 (하락 중)
                    statusText = '📉 약세';
                    statusClass = 'indicator-status bearish';
                    signalText = '⚠️ 하락 추세 지속';
                    backgroundColor = '#f44336';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 20) {
                    // 과매도 (매수 기회)
                    statusText = '💡 과매도';
                    statusClass = 'indicator-status oversold';
                    signalText = '🟡 매수 고려 (저점 근처)';
                    backgroundColor = '#ff9800';
                    textColor = '#ffffff';
                } else {
                    // 극심한 과매도 (강한 매수 기회)
                    statusText = '⭐ 극심한 과매도';
                    statusClass = 'indicator-status extreme-oversold';
                    signalText = '🟢 강한 매수 신호 (반등 가능)';
                    backgroundColor = '#00e676';
                    textColor = '#000000';
                }

                rsiStatus.textContent = statusText;
                rsiStatus.className = statusClass;

                // 배경색과 텍스트 색상 적용 (더 눈에 띄게)
                rsiStatus.style.backgroundColor = backgroundColor;
                rsiStatus.style.color = textColor;
                rsiStatus.style.padding = '6px 16px';
                rsiStatus.style.borderRadius = '8px';
                rsiStatus.style.fontWeight = 'bold';
                rsiStatus.style.fontSize = '16px';
                rsiStatus.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
                rsiStatus.style.transition = 'all 0.3s ease';
                rsiStatus.style.border = `2px solid ${backgroundColor}`;
                rsiStatus.style.textTransform = 'uppercase';

                // 극단 구간에서 펄스 애니메이션 추가
                if (latestRSI.value >= 80 || latestRSI.value <= 20) {
                    rsiStatus.style.animation = 'pulse 1.5s infinite';
                } else {
                    rsiStatus.style.animation = 'none';
                }

                // RSI 값에도 스타일 적용 (더 크게)
                rsiValue.style.fontSize = '22px';
                rsiValue.style.fontWeight = 'bold';
                rsiValue.style.color = backgroundColor;
                rsiValue.style.textShadow = `0 2px 4px ${backgroundColor}40`;

                // 신호 업데이트 (더 눈에 띄게)
                if (tradingSignal) {
                    tradingSignal.textContent = signalText;
                    tradingSignal.style.fontSize = '15px';
                    tradingSignal.style.padding = '4px 12px';
                    tradingSignal.style.borderRadius = '6px';
                    tradingSignal.style.transition = 'all 0.3s ease';
                    tradingSignal.style.display = 'inline-block';
                    tradingSignal.style.marginTop = '4px';

                    // 신호에 따른 색상 및 배경 적용
                    if (signalText.includes('🔴')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#ef5350';
                        tradingSignal.style.fontWeight = 'bold';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(239, 83, 80, 0.4)';
                    } else if (signalText.includes('🟢')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#26a69a';
                        tradingSignal.style.fontWeight = 'bold';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(38, 166, 154, 0.4)';
                    } else if (signalText.includes('🟡')) {
                        tradingSignal.style.color = '#000000';
                        tradingSignal.style.backgroundColor = '#ffc107';
                        tradingSignal.style.fontWeight = 'bold';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(255, 193, 7, 0.4)';
                    } else if (signalText.includes('🟠')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#ff9800';
                        tradingSignal.style.fontWeight = '600';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(255, 152, 0, 0.4)';
                    } else if (signalText.includes('⚠️')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#ffa726';
                        tradingSignal.style.fontWeight = '600';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(255, 167, 38, 0.4)';
                    } else if (signalText.includes('📈') || signalText.includes('✅')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#66bb6a';
                        tradingSignal.style.fontWeight = '500';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(102, 187, 106, 0.4)';
                    } else if (signalText.includes('📉')) {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#ef5350';
                        tradingSignal.style.fontWeight = '500';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(239, 83, 80, 0.4)';
                    } else {
                        tradingSignal.style.color = '#ffffff';
                        tradingSignal.style.backgroundColor = '#9e9e9e';
                        tradingSignal.style.fontWeight = '400';
                        tradingSignal.style.boxShadow = '0 2px 8px rgba(158, 158, 158, 0.4)';
                    }
                }

                // 콘솔에 상세 정보 출력
                console.log(`[RSI Signal] RSI: ${latestRSI.value.toFixed(1)} | ${statusText} | ${signalText}`);
            }
        }
    }

    toggleMACD() {
        const btn = document.getElementById('macd-toggle');
        const isActive = btn.classList.contains('active');

        if (isActive) {
            // Hide MACD
            btn.classList.remove('active');
            console.log('[Working] MACD hidden');

            // Remove MACD series from chart
            if (this.macdSeries.macd) {
                window.chartUtils.chart.removeSeries(this.macdSeries.macd);
                this.macdSeries.macd = null;
            }
            if (this.macdSeries.signal) {
                window.chartUtils.chart.removeSeries(this.macdSeries.signal);
                this.macdSeries.signal = null;
            }
            if (this.macdSeries.histogram) {
                window.chartUtils.chart.removeSeries(this.macdSeries.histogram);
                this.macdSeries.histogram = null;
            }
        } else {
            // Show MACD
            btn.classList.add('active');
            console.log('[Working] MACD shown');

            if (this.chartData && this.chartData.length > 0) {
                const macdData = window.chartUtils.calculateMACD(this.chartData, 12, 26, 9);
                console.log('[Working] MACD calculated:', macdData.macd.length, 'values');

                // MACD를 가격 범위에 스케일링 (RSI와 동일한 방식)
                const priceRange = this.chartData.reduce((acc, candle) => {
                    return {
                        min: Math.min(acc.min, candle.low),
                        max: Math.max(acc.max, candle.high)
                    };
                }, { min: Infinity, max: -Infinity });

                const priceSpan = priceRange.max - priceRange.min;

                // MACD 값의 범위 계산
                const macdValues = macdData.macd.map(item => item.value);
                const signalValues = macdData.signal.map(item => item.value);
                const histogramValues = macdData.histogram.map(item => item.value);

                const allValues = [...macdValues, ...signalValues, ...histogramValues];
                const macdMin = Math.min(...allValues);
                const macdMax = Math.max(...allValues);
                const macdSpan = macdMax - macdMin;

                // MACD를 차트 하단 20%에 표시
                const scaledMacdData = macdData.macd.map(item => ({
                    time: item.time,
                    value: priceRange.min + ((item.value - macdMin) / macdSpan) * priceSpan * 0.2
                }));

                const scaledSignalData = macdData.signal.map(item => ({
                    time: item.time,
                    value: priceRange.min + ((item.value - macdMin) / macdSpan) * priceSpan * 0.2
                }));

                const scaledHistogramData = macdData.histogram.map(item => ({
                    time: item.time,
                    value: priceRange.min + ((item.value - macdMin) / macdSpan) * priceSpan * 0.2,
                    color: item.color
                }));

                // MACD Line (파란색)
                this.macdSeries.macd = window.chartUtils.chart.addLineSeries({
                    color: '#2196F3',
                    lineWidth: 2,
                    title: 'MACD',
                    priceLineVisible: false,
                    lastValueVisible: false
                });
                this.macdSeries.macd.setData(scaledMacdData);

                // Signal Line (주황색)
                this.macdSeries.signal = window.chartUtils.chart.addLineSeries({
                    color: '#FF9800',
                    lineWidth: 2,
                    title: 'Signal',
                    priceLineVisible: false,
                    lastValueVisible: false
                });
                this.macdSeries.signal.setData(scaledSignalData);

                // Histogram (막대)
                this.macdSeries.histogram = window.chartUtils.chart.addHistogramSeries({
                    priceFormat: {
                        type: 'price',
                    },
                    priceLineVisible: false,
                    lastValueVisible: false
                });
                this.macdSeries.histogram.setData(scaledHistogramData);

                console.log('[Working] MACD series added to chart');
            }
        }
    }

    toggleBollingerBands() {
        const btn = document.getElementById('bollinger-toggle');
        const isActive = btn.classList.contains('active');

        if (isActive) {
            // Hide Bollinger Bands
            btn.classList.remove('active');
            console.log('[Working] Bollinger Bands hidden');
            // TODO: Remove Bollinger Bands series from chart
        } else {
            // Show Bollinger Bands
            btn.classList.add('active');
            console.log('[Working] Bollinger Bands shown');

            if (this.chartData && this.chartData.length > 0) {
                const bbData = window.chartUtils.calculateBollingerBands(this.chartData, 20, 2);
                console.log('[Working] Bollinger Bands calculated:', bbData.upper.length, 'values');
                // TODO: Add Bollinger Bands series to chart
            }
        }
    }
    
    // Toggle SuperTrend (TradingView Style)
    toggleSuperTrend() {
        const btn = document.getElementById('supertrend-toggle');
        const isActive = btn.classList.contains('active');

        if (isActive) {
            // Hide SuperTrend
            btn.classList.remove('active');
            console.log('[Working] SuperTrend hidden');
            
            if (window.chartUtils) {
                window.chartUtils.removeSuperTrend();
            }
        } else {
            // Show SuperTrend
            btn.classList.add('active');
            console.log('[Working] SuperTrend shown');

            if (this.chartData && this.chartData.length > 0 && window.chartUtils) {
                // TradingView 기본 설정: period=10, multiplier=3.0
                const result = window.chartUtils.addSuperTrend(this.chartData, 10, 3.0);
                
                if (result) {
                    console.log('[Working] SuperTrend added successfully');
                    
                    // 현재 신호 가져오기
                    const signal = window.chartUtils.getCurrentSuperTrendSignal();
                    if (signal) {
                        console.log(`[Working] SuperTrend Signal: ${signal.signal} (${signal.trend})`);
                        // 알림 표시 (선택사항)
                        this.showNotification(`SuperTrend: ${signal.signal}`, signal.color);
                    }
                } else {
                    console.error('[Working] Failed to add SuperTrend');
                    btn.classList.remove('active');
                }
            } else {
                console.error('[Working] No chart data available for SuperTrend');
                btn.classList.remove('active');
            }
        }
    }
    
    // Update SuperTrend (자동 업데이트 시 호출)
    updateSuperTrend() {
        const superTrendBtn = document.getElementById('supertrend-toggle');
        const isSuperTrendActive = superTrendBtn && superTrendBtn.classList.contains('active');
        
        if (isSuperTrendActive && this.chartData && this.chartData.length > 0 && window.chartUtils) {
            console.log('[Working] Updating SuperTrend with new data');
            window.chartUtils.removeSuperTrend();
            const result = window.chartUtils.addSuperTrend(this.chartData, 10, 3.0);
            if (result) {
                console.log('[Working] SuperTrend updated successfully');
            } else {
                console.error('[Working] Failed to update SuperTrend');
            }
        }
    }

    // Toggle Volume Display
    toggleVolume() {
        // Use ChartActions module if available
        if (this.chartActions) {
            this.chartActions.toggleVolume();
        } else {
            // Fallback to original implementation
            const btn = document.getElementById('volume-toggle');
            const isActive = btn.classList.contains('active');

            if (isActive) {
                btn.classList.remove('active');
                console.log('[Working] Volume hidden');
                if (this.volumeSeries) {
                    this.volumeSeries.applyOptions({ visible: false });
                }
            } else {
                btn.classList.add('active');
                console.log('[Working] Volume shown');
                if (this.volumeSeries) {
                    this.volumeSeries.applyOptions({ visible: true });
                }
            }
        }
    }

    // Toggle Theme (Dark/Light mode)
    toggleTheme() {
        // Use ChartActions module if available
        if (this.chartActions) {
            this.chartActions.toggleTheme();
            // Sync currentTheme state
            this.currentTheme = this.chartActions.currentTheme;
        } else {
            // Fallback to original implementation
            const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
            console.log(`[Working] Switching theme from ${this.currentTheme} to ${newTheme}`);

            this.currentTheme = newTheme;
            localStorage.setItem('theme', newTheme);

            this.applyTheme(newTheme);

            const btn = document.getElementById('theme-toggle');
            if (btn) {
                btn.innerHTML = newTheme === 'dark' ? 'Dark' : 'Light';
            }

            this.showNotification(`Switched to ${newTheme} mode`, '#4CAF50');
        }
    }

    // Apply Theme to entire page and chart
    applyTheme(theme) {
        console.log(`[Working] Applying ${theme} theme`);
        
        // HTML에 테마 클래스 추가/제거
        const html = document.documentElement;
        if (theme === 'dark') {
            html.classList.remove('light-theme');
            html.classList.add('dark-theme');
        } else {
            html.classList.remove('dark-theme');
            html.classList.add('light-theme');
        }
        
        // 차트 테마 적용
        if (this.chart) {
            const chartOptions = theme === 'dark' ? this.getDarkChartOptions() : this.getLightChartOptions();
            this.chart.applyOptions(chartOptions);
            console.log(`[Working] Chart theme applied: ${theme}`);
        }
        
        // 버튼 아이콘 업데이트
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '🌙 테마' : '☀️ 테마';
        }
    }

    // Dark theme options for chart
    getDarkChartOptions() {
        return {
            layout: {
                background: { color: '#1a1a1a' },
                textColor: '#d1d4dc'
            },
            grid: {
                vertLines: { color: '#2B2B43' },
                horzLines: { color: '#2B2B43' }
            },
            crosshair: {
                mode: 0,
                vertLine: {
                    color: '#758696',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#363c4e'
                },
                horzLine: {
                    color: '#758696',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#363c4e'
                }
            }
        };
    }

    // Light theme options for chart
    getLightChartOptions() {
        return {
            layout: {
                background: { color: '#ffffff' },
                textColor: '#191919'
            },
            grid: {
                vertLines: { color: '#e1e3eb' },
                horzLines: { color: '#e1e3eb' }
            },
            crosshair: {
                mode: 0,
                vertLine: {
                    color: '#9598a1',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#f0f3fa'
                },
                horzLine: {
                    color: '#9598a1',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#f0f3fa'
                }
            }
        };
    }

    // Toggle all MAs on/off
    toggleAllMAs() {
        // Use MovingAverages module if available
        if (this.movingAverages) {
            this.movingAverages.toggleAllMAs();
            // Sync state
            this.movingAveragesVisible = this.movingAverages.movingAveragesVisible;
            this.maSeries = this.movingAverages.maSeries;
        } else {
            // Fallback to original implementation
            const btn = document.getElementById('ma-toggle');
            const isActive = btn.classList.contains('active');

            if (isActive) {
                btn.classList.remove('active');
                console.log('[Working] Hiding all MAs');

                const periods = [20, 50, 100, 200, 300, 500, 1000];
                periods.forEach(period => {
                    const key = `ma${period}`;
                    if (this.maSeries[key]) {
                        window.chartUtils.chart.removeSeries(this.maSeries[key]);
                        this.maSeries[key] = null;
                    }
                });
                console.log('[Working] All MAs hidden');
            } else {
                btn.classList.add('active');
                console.log('[Working] Showing MAs based on settings');
                this.realtimeUpdates.updateMAs();
                console.log('[Working] MAs shown based on settings');
            }
        }
    }

    // MA Settings Modal Functions
    openMASettingsModal() {
        // Use MovingAverages module if available
        if (this.movingAverages) {
            this.movingAverages.openMASettingsModal();
            return;
        }

        // Fallback
        const modal = document.getElementById('ma-settings-modal');
        if (!modal) {
            console.error('[Working] MA settings modal not found');
            return;
        }

        const periods = [20, 50, 100, 200, 300, 500, 1000];
        periods.forEach(period => {
            const checkbox = document.getElementById(`ma${period}-toggle`);
            if (checkbox) {
                checkbox.checked = this.maSettings[period];
            }
        });

        modal.style.display = 'flex';
        console.log('[Working] MA settings modal opened');
    }

    closeMASettingsModal() {
        const modal = document.getElementById('ma-settings-modal');
        if (modal) {
            modal.style.display = 'none';
            console.log('[Working] MA settings modal closed');
        }
    }

    updateDrawingsList() {
        console.log('[Working] updateDrawingsList() called - delegating to drawingTools module');

        // Delegate to drawingTools module
        if (this.drawingTools) {
            this.drawingTools.updateDrawingsList();
        } else {
            console.warn('[Working] drawingTools module not available');
        }
    }

    deleteDrawing(index) {
        console.log('[Drawings] Deleting drawing at index', index);
        
        if (this.drawings && this.drawings[index]) {
            // 차트에서 그리기 제거
            const drawing = this.drawings[index];
            if (drawing.series) {
                this.chart.removeSeries(drawing.series);
            }
            if (drawing.lines) {
                drawing.lines.forEach(line => {
                    if (line && line.series) {
                        this.chart.removeSeries(line.series);
                    }
                });
            }

            // 배열에서 제거
            this.drawings.splice(index, 1);

            // 저장
            this.saveDrawings();

            // 목록 업데이트
            this.updateDrawingsList();

            console.log('[Drawings] Drawing deleted successfully');
        }
    }

    applyMASettings() {
        // Use MovingAverages module if available
        if (this.movingAverages) {
            this.movingAverages.applyMASettings();
            // Sync state
            this.maSettings = this.movingAverages.maSettings;
            this.maSeries = this.movingAverages.maSeries;
            return;
        }

        // Fallback
        console.log('[Working] Applying MA settings...');
        const periods = [20, 50, 100, 200, 300, 500, 1000];
        periods.forEach(period => {
            const checkbox = document.getElementById(`ma${period}-toggle`);
            if (checkbox) {
                this.maSettings[period] = checkbox.checked;
            }
        });

        this.saveMASettings();
        this.realtimeUpdates.updateMAs();
        this.closeMASettingsModal();
        console.log('[Working] MA settings applied:', this.maSettings);
    }
}

// 모달 관리 함수들
function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
        modal.style.display = 'flex';
        
        // 타이틀 업데이트 (현재 선택된 코인으로)
        const titleElement = document.getElementById('trading-history-title');
        if (titleElement && window.workingChart) {
            const coinSymbol = window.workingChart.currentMarket.split('-')[1]; // KRW-BTC → BTC
            titleElement.textContent = `${coinSymbol} 거래내역`;
        }
        
        // 거래내역 새로고침
        if (window.workingChart) {
            window.workingChart.loadTradingHistory();
        }
    }
}

function hideHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showDrawingsModal() {
    console.log('[Working] showDrawingsModal() called - delegating to drawingTools');

    // Delegate to drawingTools module
    if (window.workingChart && window.workingChart.drawingTools) {
        window.workingChart.drawingTools.showDrawingsList();
    } else {
        console.warn('[Working] drawingTools module not available');

        // Fallback: just open modal
        const modal = document.getElementById('drawings-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }
}

function hideDrawingsModal() {
    const modal = document.getElementById('drawings-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[Working] DOM loaded, initializing chart...');

    try {
        // Wait for APIHandler to be ready
        let retries = 0;
        while (!window.apiHandler && retries < 50) {
            console.log('[Working] Waiting for APIHandler...');
            await new Promise(resolve => setTimeout(resolve, 100));
            retries++;
        }

        if (!window.apiHandler) {
            console.error('[Working] APIHandler not available after waiting');
            return;
        }

        console.log('[Working] APIHandler ready, starting chart initialization');
        window.workingChart = new WorkingTradingChart();
        await window.workingChart.init();

        // Initialize analytics dashboard (DB statistics)
        if (window.AnalyticsDashboard) {
            console.log('[Working] Initializing analytics dashboard...');
            window.analyticsDashboard = new AnalyticsDashboard(window.apiHandler);
            await window.analyticsDashboard.init();
            console.log('[Working] Analytics dashboard initialized');
        } else {
            console.warn('[Working] AnalyticsDashboard class not available');
        }

        // Setup modal event listeners
        setupModalEventListeners();

    } catch (error) {
        console.error('[Working] Failed to initialize:', error);
    }
});

// 모달 이벤트 리스너 설정
function setupModalEventListeners() {
    // 거래내역 모달
    const showHistoryBtn = document.getElementById('show-history');
    const closeHistoryModal = document.getElementById('close-history-modal');
    const closeHistoryBtn = document.getElementById('close-history-btn');
    const refreshHistoryBtn = document.getElementById('refresh-history');

    if (showHistoryBtn) {
        showHistoryBtn.addEventListener('click', showHistoryModal);
    }
    if (closeHistoryModal) {
        closeHistoryModal.addEventListener('click', hideHistoryModal);
    }
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', hideHistoryModal);
    }
    if (refreshHistoryBtn) {
        refreshHistoryBtn.addEventListener('click', () => {
            if (window.workingChart) {
                window.workingChart.loadTradingHistory(true);
            }
        });
    }

    // 그리기 목록 모달
    const showDrawingsBtn = document.getElementById('show-drawings');
    const closeDrawingsModal = document.getElementById('close-drawings-modal');
    const closeDrawingsBtn = document.getElementById('close-drawings-btn');
    const refreshDrawingsBtn = document.getElementById('refresh-drawings');

    if (showDrawingsBtn) {
        showDrawingsBtn.addEventListener('click', showDrawingsModal);
    }
    if (closeDrawingsModal) {
        closeDrawingsModal.addEventListener('click', hideDrawingsModal);
    }
    if (closeDrawingsBtn) {
        closeDrawingsBtn.addEventListener('click', hideDrawingsModal);
    }
    if (refreshDrawingsBtn) {
        refreshDrawingsBtn.addEventListener('click', () => {
            if (window.workingChart) {
                window.workingChart.updateDrawingsList();
            }
        });
    }
    
    // 매매 마커 토글 버튼
    const tradeMarkersToggle = document.getElementById('trade-markers-toggle');
    if (tradeMarkersToggle) {
        tradeMarkersToggle.addEventListener('click', () => {
            if (window.workingChart) {
                window.workingChart.toggleTradeMarkers();
            }
        });
    }

    // 모달 외부 클릭 시 닫기
    const historyModal = document.getElementById('history-modal');
    const drawingsModal = document.getElementById('drawings-modal');

    if (historyModal) {
        historyModal.addEventListener('click', (e) => {
            if (e.target === historyModal) {
                hideHistoryModal();
            }
        });
    }

    if (drawingsModal) {
        drawingsModal.addEventListener('click', (e) => {
            if (e.target === drawingsModal) {
                hideDrawingsModal();
            }
        });
    }

    console.log('[Modal] Event listeners setup completed');
}

// ========================================
// 평균단가 & 미체결 주문 수평선 표시 기능
// ========================================

/**
 * 평균단가와 미체결 주문을 수평선으로 항상 표시
 */
WorkingTradingChart.prototype.updateAvgPriceAndPendingOrders = async function() {
    console.log('[Working] Updating average price and pending orders lines...');

    // 기존 라인 제거
    this.removeAvgPriceAndPendingOrderLines();

    try {
        // 평균단가 표시
        await this.drawAvgPriceLine();

        // 미체결 주문 표시
        await this.drawPendingOrderLines();

        console.log('[Working] Average price and pending orders updated');
    } catch (error) {
        console.error('[Working] Failed to update avg price and pending orders:', error);
    }
};

/**
 * 평균단가 수평선 그리기
 */
WorkingTradingChart.prototype.drawAvgPriceLine = async function() {
    console.log('[Working] === drawAvgPriceLine START ===');
    console.log('[Working] avgPriceLineEnabled:', this.avgPriceLineEnabled);

    if (!this.avgPriceLineEnabled) {
        console.log('[Working] Avg price line is disabled, skipping');
        return;
    }

    try {
        // API로 현재 코인의 보유 정보 가져오기
        if (!window.apiHandler || !window.apiHandler.getHoldings) {
            console.warn('[Working] API Handler not available');
            return;
        }

        console.log('[Working] Calling getHoldings API...');
        const result = await window.apiHandler.getHoldings();
        console.log('[Working] getHoldings result:', result);

        if (!result || !result.success) {
            console.log('[Working] No holdings data');
            return;
        }

        // 현재 코인의 평균단가 찾기 (API는 result.coins에 데이터 반환)
        const holdings = result.coins || result.data || [];
        console.log('[Working] Holdings array length:', holdings.length);
        console.log('[Working] Current market:', this.currentMarket);

        // Extract coin symbol from market (KRW-XRP -> XRP)
        const coinSymbol = this.currentMarket.replace('KRW-', '');
        const currentHolding = holdings.find(h => h.coin === coinSymbol);
        console.log('[Working] Current holding:', currentHolding);

        if (!currentHolding || !currentHolding.avg_price) {
            console.log('[Working] No avg price for current coin:', this.currentMarket);
            console.log('[Working] Available coins:', holdings.map(h => h.coin).join(', '));
            return;
        }

        const avgPrice = parseFloat(currentHolding.avg_price);
        const balance = parseFloat(currentHolding.balance) || 0;

        console.log('[Working] Avg price:', avgPrice, 'Balance:', balance);

        // 유효성 검사: avgPrice가 숫자가 아니거나 0 이하면 종료
        if (!avgPrice || isNaN(avgPrice) || avgPrice <= 0) {
            console.log('[Working] Invalid avg price:', avgPrice);
            return;
        }

        // ✅ FIXED: Allow avg price line display even when balance is 0
        // Users may have sold all coins but still want to see historical avg price
        console.log(`[Working] Drawing avg price line: ${avgPrice.toLocaleString()} KRW (Balance: ${balance})`);

        // 수평선 그리기 - this.chart 사용 (chartUtils보다 안정적)
        const chart = this.chart || window.chartUtils?.chart;
        console.log('[Working] Chart available (this.chart):', !!this.chart);
        console.log('[Working] Chart available (chartUtils):', !!window.chartUtils?.chart);
        console.log('[Working] Using chart:', !!chart);
        console.log('[Working] chartData length:', this.chartData ? this.chartData.length : 0);

        if (!chart) {
            console.error('[Working] ❌ Chart not available - CANNOT DRAW LINE');
            console.error('[Working] this.chart:', this.chart);
            console.error('[Working] window.chartUtils:', window.chartUtils);
            return;
        }

        const priceLine = chart.addLineSeries({
            color: '#FFD700',  // 금색
            lineWidth: 2,
            lineStyle: 2,  // Dashed
            title: `평균단가: ${avgPrice.toLocaleString()}`,
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true
        });
        console.log('[Working] Price line series created');

        // 차트 전체 시간 범위에 걸쳐 수평선 그리기
        if (this.chartData && this.chartData.length > 0) {
            const lineData = this.chartData
                .filter(candle => {
                    // Validate candle data
                    if (!candle) return false;
                    if (candle.time == null || candle.time === undefined) return false;
                    return true;
                })
                .map(candle => {
                    // Create data point with strict validation
                    const dataPoint = {
                        time: candle.time,
                        value: avgPrice
                    };

                    // Double-check that value is not null/undefined
                    if (dataPoint.value == null || isNaN(dataPoint.value)) {
                        console.error('[Working] Invalid value in lineData:', dataPoint);
                        return null;
                    }

                    return dataPoint;
                })
                .filter(point => point !== null);  // Remove any null points

            console.log('[Working] Line data points:', lineData.length);

            if (lineData.length > 0) {
                priceLine.setData(lineData);
                this.avgPriceLine = { series: priceLine, price: avgPrice };
                console.log('[Working] ✅ Average price line drawn successfully!');
            } else {
                console.warn('[Working] No line data points generated');
            }
        } else {
            console.warn('[Working] No chartData available for line drawing');
        }

        console.log('[Working] === drawAvgPriceLine END ===');

    } catch (error) {
        console.error('[Working] Failed to draw avg price line:', error);
        console.error('[Working] Error stack:', error.stack);
    }
};

/**
 * 미체결 주문 수평선들 그리기
 */
WorkingTradingChart.prototype.drawPendingOrderLines = async function() {
    if (!this.pendingOrderLinesEnabled) return;

    try {
        // API로 미체결 주문 가져오기
        if (!window.apiHandler || !window.apiHandler.getOrders) {
            console.warn('[Working] API Handler not available');
            return;
        }

        const result = await window.apiHandler.getOrders(this.currentMarket, 'wait', 50, false);

        if (!result || !result.success) {
            console.log('[Working] No pending orders');
            return;
        }

        const orders = result.orders || result.data || [];

        if (orders.length === 0) {
            console.log('[Working] No pending orders for current coin');
            return;
        }

        console.log(`[Working] Drawing ${orders.length} pending order lines`);

        const chart = this.chart || window.chartUtils?.chart;
        console.log('[Working] Chart available for pending orders:', !!chart);
        if (!chart) {
            console.error('[Working] ❌ Chart not available - CANNOT DRAW PENDING ORDER LINES');
            return;
        }

        // 각 미체결 주문에 대해 수평선 그리기
        orders.forEach((order) => {
            const price = parseFloat(order.price);
            const volume = parseFloat(order.volume) || parseFloat(order.remaining_volume) || 0;

            // 유효성 검사: price가 유효하지 않으면 스킵
            if (!price || isNaN(price) || price <= 0) {
                console.warn('[Working] Invalid order price, skipping:', order);
                return;
            }

            const isBid = order.side === 'bid';

            // 매수: 초록색, 매도: 빨간색
            const color = isBid ? '#26a69a' : '#ef5350';
            const side = isBid ? '매수' : '매도';

            const priceLine = chart.addLineSeries({
                color: color,
                lineWidth: 1,
                lineStyle: 2,  // Dashed
                title: `${side} ${volume.toFixed(4)} @ ${price.toLocaleString()}`,
                priceLineVisible: false,
                lastValueVisible: true,
                crosshairMarkerVisible: true
            });

            // 차트 전체 시간 범위에 걸쳐 수평선 그리기
            if (this.chartData && this.chartData.length > 0) {
                const lineData = this.chartData
                    .filter(candle => {
                        // Validate candle data
                        if (!candle) return false;
                        if (candle.time == null || candle.time === undefined) return false;
                        return true;
                    })
                    .map(candle => {
                        // Create data point with strict validation
                        const dataPoint = {
                            time: candle.time,
                            value: price
                        };

                        // Double-check that value is not null/undefined
                        if (dataPoint.value == null || isNaN(dataPoint.value)) {
                            console.error('[Working] Invalid value in pending order lineData:', dataPoint);
                            return null;
                        }

                        return dataPoint;
                    })
                    .filter(point => point !== null);  // Remove any null points

                if (lineData.length > 0) {
                    priceLine.setData(lineData);
                    this.pendingOrderLines.push({
                        series: priceLine,
                        price: price,
                        side: order.side,
                        volume: volume
                    });
                }
            }
        });

        console.log(`[Working] ${this.pendingOrderLines.length} pending order lines drawn`);

    } catch (error) {
        console.error('[Working] Failed to draw pending order lines:', error);
    }
};

/**
 * 평균단가 및 미체결 주문 수평선 제거
 */
WorkingTradingChart.prototype.removeAvgPriceAndPendingOrderLines = function() {
    const chart = this.chart || window.chartUtils?.chart;
    if (!chart) {
        console.warn('[Working] Chart not available for removing lines');
        return;
    }

    // 평균단가 라인 제거
    if (this.avgPriceLine && this.avgPriceLine.series) {
        try {
            chart.removeSeries(this.avgPriceLine.series);
            console.log('[Working] Average price line removed');
        } catch (error) {
            console.error('[Working] Failed to remove avg price line:', error);
        }
        this.avgPriceLine = null;
    }

    // 미체결 주문 라인들 제거
    this.pendingOrderLines.forEach((line) => {
        if (line && line.series) {
            try {
                chart.removeSeries(line.series);
            } catch (error) {
                console.error('[Working] Failed to remove pending order line:', error);
            }
        }
    });
    this.pendingOrderLines = [];

    console.log('[Working] All avg price and pending order lines removed');
};

/**
 * 지지저항선 토글
 */
WorkingTradingChart.prototype.toggleSupportResistance = function() {
    this.supportResistanceEnabled = !this.supportResistanceEnabled;
    this.updateSupportResistanceToggleButton();

    if (this.supportResistanceEnabled) {
        this.drawSupportResistance();
    } else {
        this.removeSupportResistance();
    }
};

/**
 * 지지저항선 그리기
 */
WorkingTradingChart.prototype.drawSupportResistance = function() {
    const chart = window.chartUtils?.chart;
    if (!chart || !this.chartData || this.chartData.length === 0) {
        console.warn('[SR] Cannot draw support/resistance: missing data or chart');
        return;
    }

    try {
        this.removeSupportResistance();

        const levels = this.calculateSupportResistance();
        console.log('[SR] Calculated support/resistance levels:', levels.length);

        levels.forEach((level) => {
            this.drawHorizontalLine(level.price, level.type, level.strength);
        });

        console.log('[SR] Support/resistance lines drawn successfully');
    } catch (error) {
        console.error('[SR] Failed to draw support/resistance:', error);
    }
};

/**
 * 지지저항 레벨 계산 (개선된 피벗 포인트 방식)
 */
WorkingTradingChart.prototype.calculateSupportResistance = function() {
    if (!this.chartData || this.chartData.length < 50) {
        console.warn('[SR] Insufficient data for calculation (need at least 50 candles)');
        return [];
    }

    const lookback = 5; // 5 candles lookback/forward for better significance
    const levels = [];
    const currentPrice = this.chartData[this.chartData.length - 1].close;

    // Calculate ATR for dynamic tolerance
    const atr = this.calculateATR(14);
    const dynamicTolerance = atr > 0 ? (atr / currentPrice) : 0.015; // Use ATR or fallback to 1.5%

    console.log('[SR] Using dynamic tolerance:', (dynamicTolerance * 100).toFixed(2) + '%', 'ATR:', atr.toFixed(2));

    // Find pivot points with larger lookback
    for (let i = lookback; i < this.chartData.length - lookback; i++) {
        const candle = this.chartData[i];
        let isResistance = true;
        let isSupport = true;

        // Check if this is a pivot high (resistance)
        for (let j = 1; j <= lookback; j++) {
            if (candle.high <= this.chartData[i - j].high || candle.high <= this.chartData[i + j].high) {
                isResistance = false;
                break;
            }
        }

        // Check if this is a pivot low (support)
        for (let j = 1; j <= lookback; j++) {
            if (candle.low >= this.chartData[i - j].low || candle.low >= this.chartData[i + j].low) {
                isSupport = false;
                break;
            }
        }

        if (isResistance) {
            levels.push({
                price: candle.high,
                type: 'resistance',
                index: i,
                time: candle.time
            });
        }

        if (isSupport) {
            levels.push({
                price: candle.low,
                type: 'support',
                index: i,
                time: candle.time
            });
        }
    }

    console.log('[SR] Found', levels.length, 'initial pivot points');

    // Merge nearby levels (clustering)
    const mergedLevels = this.mergeSimilarLevels(levels, dynamicTolerance);
    console.log('[SR] After merging:', mergedLevels.length, 'levels');

    // Calculate strength with time decay
    const allPrices = this.chartData.map(c => [c.high, c.low]).flat();
    mergedLevels.forEach(level => {
        level.strength = this.calculateLevelStrengthImproved(level.price, allPrices, dynamicTolerance, level.index);
        level.distanceFromCurrent = Math.abs(level.price - currentPrice) / currentPrice;
    });

    // Filter levels that are too close together (minimum 3% apart)
    const filteredLevels = this.filterClusteredLevels(mergedLevels, 0.03);
    console.log('[SR] After distance filter:', filteredLevels.length, 'levels');

    // Sort by combination of strength and proximity to current price
    const scoredLevels = filteredLevels.map(level => ({
        ...level,
        score: level.strength * (1 + (1 - Math.min(level.distanceFromCurrent * 2, 1))) // Boost nearby levels
    }));

    // Sort by score and take top levels, ensuring balance between support/resistance
    const sortedLevels = scoredLevels.sort((a, b) => b.score - a.score);

    // Try to get balanced support/resistance
    const supports = sortedLevels.filter(l => l.type === 'support').slice(0, 3);
    const resistances = sortedLevels.filter(l => l.type === 'resistance').slice(0, 3);
    const balancedLevels = [...supports, ...resistances].sort((a, b) => b.score - a.score).slice(0, 6);

    console.log('[SR] Final levels:', balancedLevels.map(l => ({
        type: l.type,
        price: l.price.toFixed(0),
        strength: l.strength,
        distance: (l.distanceFromCurrent * 100).toFixed(1) + '%',
        score: l.score.toFixed(1)
    })));

    return balancedLevels;
};

/**
 * ATR (Average True Range) 계산
 */
WorkingTradingChart.prototype.calculateATR = function(period) {
    if (!this.chartData || this.chartData.length < period + 1) {
        return 0;
    }

    const trueRanges = [];
    for (let i = 1; i < this.chartData.length; i++) {
        const current = this.chartData[i];
        const previous = this.chartData[i - 1];

        const tr = Math.max(
            current.high - current.low,
            Math.abs(current.high - previous.close),
            Math.abs(current.low - previous.close)
        );
        trueRanges.push(tr);
    }

    // Simple moving average of TR
    const recentTR = trueRanges.slice(-period);
    const atr = recentTR.reduce((sum, tr) => sum + tr, 0) / period;

    return atr;
};

/**
 * 유사한 레벨 병합 (클러스터링)
 */
WorkingTradingChart.prototype.mergeSimilarLevels = function(levels, tolerance) {
    if (levels.length === 0) return [];

    const merged = [];
    const used = new Set();

    levels.forEach((level, i) => {
        if (used.has(i)) return;

        const cluster = [level];
        used.add(i);

        // Find similar levels
        for (let j = i + 1; j < levels.length; j++) {
            if (used.has(j)) continue;

            const other = levels[j];
            if (level.type === other.type &&
                Math.abs(level.price - other.price) / level.price <= tolerance) {
                cluster.push(other);
                used.add(j);
            }
        }

        // Average the cluster
        const avgPrice = cluster.reduce((sum, l) => sum + l.price, 0) / cluster.length;
        const mostRecentIndex = Math.max(...cluster.map(l => l.index));

        merged.push({
            price: avgPrice,
            type: level.type,
            index: mostRecentIndex,
            clusterSize: cluster.length
        });
    });

    return merged;
};

/**
 * 거리 기반 레벨 필터링
 */
WorkingTradingChart.prototype.filterClusteredLevels = function(levels, minDistance) {
    if (levels.length === 0) return [];

    const sorted = [...levels].sort((a, b) => a.price - b.price);
    const filtered = [sorted[0]];

    for (let i = 1; i < sorted.length; i++) {
        const lastPrice = filtered[filtered.length - 1].price;
        const currentPrice = sorted[i].price;
        const distance = Math.abs(currentPrice - lastPrice) / lastPrice;

        if (distance >= minDistance) {
            filtered.push(sorted[i]);
        }
    }

    return filtered;
};

/**
 * 개선된 레벨 강도 계산 (시간 가중치 적용)
 */
WorkingTradingChart.prototype.calculateLevelStrengthImproved = function(price, prices, tolerance, levelIndex) {
    const priceWithTolerance = price * tolerance;
    let strength = 0;
    const dataLength = this.chartData.length;

    // Count touches with time decay
    prices.forEach((p, idx) => {
        if (Math.abs(p - price) <= priceWithTolerance) {
            // Calculate candle index (each candle has 2 prices: high and low)
            const candleIndex = Math.floor(idx / 2);

            // Time decay: recent touches are more important
            const age = dataLength - candleIndex;
            const timeWeight = Math.exp(-age / (dataLength * 0.3)); // Exponential decay

            strength += (0.5 + timeWeight * 0.5); // Base 0.5 + time-weighted 0.5
        }
    });

    // Bonus for cluster size if available
    const level = { price };
    if (level.clusterSize && level.clusterSize > 1) {
        strength *= (1 + Math.log(level.clusterSize) * 0.2);
    }

    return strength;
};

/**
 * 레벨 강도 계산 (가격 근처에서 터치한 횟수) - Legacy
 */
WorkingTradingChart.prototype.calculateLevelStrength = function(price, prices) {
    const tolerance = price * 0.015; // 1.5% 허용 오차
    const touches = prices.filter(p => Math.abs(p - price) <= tolerance).length;
    return touches;
};

/**
 * 수평선 그리기
 */
WorkingTradingChart.prototype.drawHorizontalLine = function(price, type, strength) {
    const chart = window.chartUtils?.chart;
    if (!chart) return;

    try {
        const color = type === 'support' ? '#26a69a' : '#ef5350'; // 초록색: 지지, 빨간색: 저항
        const lineWidth = Math.min(Math.max(strength / 5, 1), 3); // 강도에 따라 1~3 픽셀

        const lineSeries = chart.addLineSeries({
            color: color,
            lineWidth: lineWidth,
            lineStyle: 2, // Dashed line
            crosshairMarkerVisible: false,
            lastValueVisible: true,
            priceLineVisible: false,
            title: `${type === 'support' ? '지지' : '저항'}: ${price.toFixed(0)}`
        });

        // 차트 전체 시간 범위에 수평선 그리기
        const timeRange = chart.timeScale().getVisibleRange();
        if (timeRange && this.chartData.length > 0) {
            const startTime = this.chartData[0].time;
            const endTime = this.chartData[this.chartData.length - 1].time;

            lineSeries.setData([
                { time: startTime, value: price },
                { time: endTime, value: price }
            ]);
        }

        this.supportResistanceLines.push({
            lineSeries,
            price,
            type,
            strength
        });

        console.log(`[SR] Drew ${type} line at ${price.toFixed(0)} (strength: ${strength})`);
    } catch (error) {
        console.error('[SR] Failed to draw horizontal line:', error);
    }
};

/**
 * 지지저항선 제거
 */
WorkingTradingChart.prototype.removeSupportResistance = function() {
    const chart = window.chartUtils?.chart;
    if (!chart) return;

    this.supportResistanceLines.forEach(({ lineSeries }) => {
        try {
            if (lineSeries) {
                chart.removeSeries(lineSeries);
            }
        } catch (error) {
            console.error('[SR] Failed to remove line:', error);
        }
    });

    this.supportResistanceLines = [];
    console.log('[SR] All support/resistance lines removed');
};

/**
 * 지지저항선 토글 버튼 업데이트
 */
WorkingTradingChart.prototype.updateSupportResistanceToggleButton = function() {
    const btn = document.getElementById('support-resistance-toggle');
    if (btn) {
        if (this.supportResistanceEnabled) {
            btn.textContent = '지지저항선';
            btn.classList.add('active');
        } else {
            btn.textContent = '지지저항선';
            btn.classList.remove('active');
        }
    }
};

/**
 * Handle chart click for drawing tools
 * Converts pixel coordinates to time/price and passes to DrawingTools module
 */
WorkingTradingChart.prototype.handleChartClickForDrawing = function(event) {
    try {
        // Only process if drawing tools module is active
        if (!this.drawingTools || !this.drawingTools.drawingMode) {
            return;
        }

        // Get chart container bounding box
        const rect = this.chartContainer.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Convert pixel coordinates to time/price
        // Note: Lightweight Charts doesn't provide direct coordinate conversion
        // We'll use approximate conversion based on chart dimensions

        if (!this.chart || !this.candleSeries || !this.chartData || this.chartData.length === 0) {
            console.warn('[Working] Chart not ready for coordinate conversion');
            return;
        }

        // Get time from x coordinate
        const timeScale = this.chart.timeScale();
        const time = timeScale.coordinateToTime(x);

        if (!time) {
            console.warn('[Working] Could not convert x coordinate to time');
            return;
        }

        // Get price from y coordinate
        const price = this.candleSeries.coordinateToPrice(y);

        if (!price) {
            console.warn('[Working] Could not convert y coordinate to price');
            return;
        }

        console.log(`[Working] Chart clicked: time=${time}, price=${price}`);

        // Pass to DrawingTools module
        this.drawingTools.handleChartClick(time, price);

    } catch (error) {
        console.error('[Working] Error handling chart click for drawing:', error);
    }
};

/**
 * ========================================
 * AUTO TRADING CONTROLLER
 * ========================================
 * Manages frontend auto-trading controls and API communication
 */

