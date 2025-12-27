/**
 * Chart Settings Module
 * Handles timeframe selection, coin selection, and coin search
 *
 * Features:
 * - Timeframe parsing and changing (1m, 5m, 15m, 1h, 4h, 1d, 1w)
 * - Coin list loading from API
 * - Coin search (Korean name, English name, symbol)
 * - Coin selection and switching
 * - Select box updates
 */

class ChartSettings {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.allMarkets = [];

        console.log('[ChartSettings] Module initialized');
    }

    /**
     * Load coin list from API
     */
    async loadCoinList() {
        try {
            console.log('[ChartSettings] Loading coin list...');

            if (!window.apiHandler) {
                console.error('[ChartSettings] APIHandler not available');
                return;
            }

            const response = await window.apiHandler.getMarketList();
            console.log('[ChartSettings] Market list response:', response);

            // API returns array directly
            const marketList = Array.isArray(response) ? response : (response.data || []);

            if (!marketList || marketList.length === 0) {
                console.error('[ChartSettings] Failed to load market list or empty list');
                return;
            }

            // Filter KRW markets only
            this.allMarkets = marketList.filter(market => market.market.startsWith('KRW-'));
            this.chart.allMarkets = this.allMarkets; // Sync with main chart
            console.log(`[ChartSettings] Found ${this.allMarkets.length} KRW markets`);

            // Update coin select box
            this.updateCoinSelectBox(this.allMarkets);

            console.log('[ChartSettings] Coin list loaded successfully');
        } catch (error) {
            console.error('[ChartSettings] Failed to load coin list:', error);
        }
    }

    /**
     * Update coin select box with market list
     */
    updateCoinSelectBox(markets, keepSelection = false) {
        try {
            const coinSelect = document.getElementById('coin-select');
            if (!coinSelect) {
                console.error('[ChartSettings] Coin select element not found');
                return;
            }

            // Save current selection
            const currentValue = keepSelection ? coinSelect.value : this.chart.currentMarket;

            // Clear existing options
            coinSelect.innerHTML = '';

            // Add options
            markets.forEach(market => {
                const option = document.createElement('option');
                option.value = market.market;
                option.textContent = `${market.korean_name} (${market.market})`;

                // Add data attributes for search and matching
                option.dataset.koreanName = market.korean_name;
                option.dataset.englishName = market.english_name;

                // Restore previous selection or set default
                if (market.market === currentValue) {
                    option.selected = true;
                }

                coinSelect.appendChild(option);
            });

            // Select first item if no selection
            if (coinSelect.options.length > 0 && !coinSelect.value) {
                coinSelect.options[0].selected = true;
            }

            console.log('[ChartSettings] Coin select box updated with', markets.length, 'markets');
        } catch (error) {
            console.error('[ChartSettings] Error in updateCoinSelectBox:', error);
        }
    }

    /**
     * Search coins by Korean/English name or symbol
     */
    searchCoins(searchTerm) {
        try {
            if (!searchTerm || searchTerm.trim() === '') {
                // Show all if no search term
                this.updateCoinSelectBox(this.allMarkets, true);
                return;
            }

            const term = searchTerm.toLowerCase().trim();

            // Search by Korean name, English name, code
            const filtered = this.allMarkets.filter(market => {
                const koreanName = market.korean_name.toLowerCase();
                const englishName = market.english_name.toLowerCase();
                const marketCode = market.market.toLowerCase();
                const symbol = market.market.split('-')[1].toLowerCase(); // KRW-BTC -> btc

                return koreanName.includes(term) ||
                       englishName.includes(term) ||
                       marketCode.includes(term) ||
                       symbol.includes(term);
            });

            console.log(`[ChartSettings] Search "${searchTerm}": found ${filtered.length} results`);

            // Update with filtered list
            this.updateCoinSelectBox(filtered, true);
        } catch (error) {
            console.error('[ChartSettings] Error in searchCoins:', error);
        }
    }

    /**
     * Parse timeframe value to API parameters
     */
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

    /**
     * Change timeframe
     */
    async changeTimeframe(timeframeValue) {
        try {
            const { timeframe, unit } = this.parseTimeframe(timeframeValue);

            // Allow re-selection of same timeframe (for refresh/retry)
            // if (this.chart.currentTimeframe === timeframe && this.chart.currentUnit === unit) {
            //     console.log('[ChartSettings] Timeframe already set, skipping');
            //     return;
            // }

            console.log(`[ChartSettings] Changing timeframe to: ${timeframeValue} (${timeframe}, unit: ${unit})`);

            // Stop auto-update
            this.chart.stopAutoUpdate();

            // Reset state
            this.chart.currentTimeframe = timeframe;
            this.chart.currentUnit = unit;
            this.chart.isLoading = false;
            this.chart.hasMoreData = true;
            this.chart.oldestTimestamp = null;
            this.chart.newestTimestamp = null;
            this.chart.loadedCandles = [];
            this.chart.loadedVolume = [];

            // Load new data
            await this.chart.loadInitialCandles();
            this.chart.setupTradingViewStyleLoading();
            this.chart.startAutoUpdate();

            // Re-apply support/resistance if enabled
            if (this.chart.supportResistanceEnabled && this.chart.chartData && this.chart.chartData.length > 0) {
                console.log('[ChartSettings] Re-applying support/resistance for new timeframe');
                if (this.chart.drawSupportResistance) {
                    this.chart.drawSupportResistance();
                }
            }

            // Update technical indicators if active
            if (this.chart.technicalIndicators) {
                this.chart.technicalIndicators.updateAll();
            }

            // Update candle type display
            this.updateCandleTypeDisplay(timeframeValue);

            console.log(`[ChartSettings] Timeframe changed to ${timeframeValue}`);
        } catch (error) {
            console.error('[ChartSettings] Error in changeTimeframe:', error);
        }
    }

    /**
     * Update candle type display text
     */
    updateCandleTypeDisplay(timeframeValue) {
        const candleTypeEl = document.getElementById('candle-type');
        if (!candleTypeEl) return;

        const displayMap = {
            '1m': '1분봉',
            '5m': '5분봉',
            '15m': '15분봉',
            '1h': '1시간봉',
            '4h': '4시간봉',
            '1d': '일봉',
            '1w': '주봉'
        };

        const displayText = displayMap[timeframeValue] || '일봉';
        candleTypeEl.textContent = displayText;
        console.log(`[ChartSettings] Updated candle type display to: ${displayText}`);
    }

    /**
     * Change coin/market
     */
    async changeCoin(market) {
        try {
            if (this.chart.currentMarket === market) {
                console.log('[ChartSettings] Coin already selected, skipping');
                return;
            }

            console.log(`[ChartSettings] Changing coin from ${this.chart.currentMarket} to ${market}`);

            // Stop auto-update
            this.chart.stopAutoUpdate();

            // Save SuperTrend state
            const superTrendBtn = document.getElementById('supertrend-toggle');
            const isSuperTrendActive = superTrendBtn && superTrendBtn.classList.contains('active');

            // Reset state
            this.chart.currentMarket = market;
            this.chart.isLoading = false;
            this.chart.hasMoreData = true;
            this.chart.oldestTimestamp = null;
            this.chart.newestTimestamp = null;
            this.chart.loadedCandles = [];
            this.chart.loadedVolume = [];

            // Load new coin data
            await this.chart.loadInitialCandles();
            this.chart.setupTradingViewStyleLoading();
            this.chart.startAutoUpdate();

            // Re-apply SuperTrend if it was active
            if (isSuperTrendActive && this.chart.chartData && this.chart.chartData.length > 0 && window.chartUtils) {
                console.log('[ChartSettings] Re-applying SuperTrend for new coin');
                window.chartUtils.removeSuperTrend();
                const result = window.chartUtils.addSuperTrend(this.chart.chartData, 10, 3.0);
                if (result) {
                    console.log('[ChartSettings] SuperTrend re-applied successfully');
                }
            }

            // Re-apply support/resistance if enabled
            if (this.chart.supportResistanceEnabled && this.chart.chartData && this.chart.chartData.length > 0) {
                console.log('[ChartSettings] Re-applying support/resistance for new coin');
                if (this.chart.drawSupportResistance) {
                    this.chart.drawSupportResistance();
                }
            }

            // Clear all drawings (trendlines, fibonacci, etc.) when coin changes
            if (this.chart.drawingTools && this.chart.drawingTools.clearAllDrawings) {
                this.chart.drawingTools.clearAllDrawings();
                console.log('[ChartSettings] Drawings cleared for new coin');
            }

            // Update trading history for new coin (force reload, ignore cache)
            if (this.chart.loadTradingHistory) {
                await this.chart.loadTradingHistory(true);
            }

            // Update average price and pending orders
            if (this.chart.updateAvgPriceAndPendingOrders) {
                await this.chart.updateAvgPriceAndPendingOrders();
            }

            // Update technical indicators if active
            if (this.chart.technicalIndicators) {
                this.chart.technicalIndicators.updateAll();
            }

            console.log(`[ChartSettings] Coin changed to ${market}`);
        } catch (error) {
            console.error('[ChartSettings] Error in changeCoin:', error);
        }
    }

    /**
     * Setup event handlers for settings controls
     */
    setupEventHandlers() {
        try {
            // Timeframe selector
            const timeframeSelect = document.getElementById('timeframe');
            if (timeframeSelect) {
                timeframeSelect.addEventListener('change', async (e) => {
                    const selectedTimeframe = e.target.value;
                    console.log('[ChartSettings] Timeframe selected:', selectedTimeframe);
                    await this.changeTimeframe(selectedTimeframe);
                });
                console.log('[ChartSettings] Timeframe selector event handler set');
            }

            // Coin selector
            const coinSelect = document.getElementById('coin-select');
            if (coinSelect) {
                coinSelect.addEventListener('change', async (e) => {
                    const selectedMarket = e.target.value;
                    console.log('[ChartSettings] Coin selected:', selectedMarket);
                    await this.changeCoin(selectedMarket);
                });
                console.log('[ChartSettings] Coin selector event handler set');
            }

            // Coin search input
            const coinSearch = document.getElementById('coin-search');
            if (coinSearch) {
                coinSearch.addEventListener('input', (e) => {
                    const searchTerm = e.target.value;
                    this.searchCoins(searchTerm);
                });

                coinSearch.addEventListener('keydown', async (e) => {
                    if (e.key === 'Enter') {
                        const coinSelect = document.getElementById('coin-select');
                        if (coinSelect && coinSelect.options.length > 0) {
                            const firstMarket = coinSelect.options[0].value;
                            const marketCode = firstMarket.split(' ')[0];
                            console.log('[ChartSettings] Enter pressed, selecting first result:', marketCode);
                            await this.changeCoin(marketCode);
                            // Clear search
                            coinSearch.value = '';
                            this.searchCoins('');
                        }
                    }
                });
                console.log('[ChartSettings] Coin search event handlers set');
            }

            // Refresh coins button
            const refreshCoinsBtn = document.getElementById('refresh-coins');
            if (refreshCoinsBtn) {
                refreshCoinsBtn.addEventListener('click', async () => {
                    console.log('[ChartSettings] Refreshing coin list');
                    await this.loadCoinList();
                });
                console.log('[ChartSettings] Refresh coins button event handler set');
            }

            console.log('[ChartSettings] All event handlers set up');
        } catch (error) {
            console.error('[ChartSettings] Error in setupEventHandlers:', error);
        }
    }

    /**
     * Get current timeframe display text
     */
    getTimeframeDisplayText(timeframeValue) {
        const map = {
            '1m': '1 Minute',
            '5m': '5 Minutes',
            '15m': '15 Minutes',
            '1h': '1 Hour',
            '4h': '4 Hours',
            '1d': 'Daily',
            '1w': 'Weekly'
        };
        return map[timeframeValue] || 'Daily';
    }

    /**
     * Update candle type display in UI
     */
    updateCandleTypeDisplay() {
        try {
            const candleTypeElement = document.getElementById('candle-type');
            if (!candleTypeElement) return;

            const timeframeSelect = document.getElementById('timeframe');
            if (!timeframeSelect) return;

            const currentTimeframe = timeframeSelect.value;
            const displayText = this.getTimeframeDisplayText(currentTimeframe);

            candleTypeElement.textContent = displayText;
            console.log('[ChartSettings] Candle type display updated:', displayText);
        } catch (error) {
            console.error('[ChartSettings] Error in updateCandleTypeDisplay:', error);
        }
    }

    /**
     * Update coin name display in UI
     */
    updateCoinNameDisplay() {
        try {
            const coinNameElement = document.getElementById('coin-name');
            if (!coinNameElement) return;

            const coinSelect = document.getElementById('coin-select');
            if (!coinSelect) return;

            const selectedOption = coinSelect.options[coinSelect.selectedIndex];
            if (!selectedOption) return;

            const koreanName = selectedOption.dataset.koreanName || selectedOption.textContent.split('(')[0].trim();
            coinNameElement.textContent = koreanName;

            console.log('[ChartSettings] Coin name display updated:', koreanName);
        } catch (error) {
            console.error('[ChartSettings] Error in updateCoinNameDisplay:', error);
        }
    }
}

// Export to window for global access
if (typeof window !== 'undefined') {
    window.ChartSettings = ChartSettings;
}
