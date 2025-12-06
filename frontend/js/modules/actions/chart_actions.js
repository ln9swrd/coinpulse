/**
 * Chart Actions Module
 * Handles chart control actions: theme toggle, volume toggle, trade markers
 *
 * Features:
 * - Dark/Light theme switching with localStorage persistence
 * - Volume series visibility toggle
 * - Trade markers display toggle
 * - Trading history loading and display
 */

class ChartActions {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.showTradeMarkers = true;

        console.log('[ChartActions] Module initialized with theme:', this.currentTheme);
    }

    /**
     * Toggle between dark and light theme
     */
    toggleTheme() {
        try {
            const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
            console.log(`[ChartActions] Switching theme from ${this.currentTheme} to ${newTheme}`);

            this.currentTheme = newTheme;
            localStorage.setItem('theme', newTheme);

            this.applyTheme(newTheme);
            this.updateThemeButton(newTheme);

            // Show notification
            if (this.chart.showNotification) {
                this.chart.showNotification(
                    `Switched to ${newTheme} mode`,
                    '#4CAF50'
                );
            }
        } catch (error) {
            console.error('[ChartActions] Error in toggleTheme:', error);
        }
    }

    /**
     * Apply theme to entire page and chart
     */
    applyTheme(theme) {
        try {
            console.log(`[ChartActions] Applying ${theme} theme`);

            // Apply theme class to HTML element
            const html = document.documentElement;
            if (theme === 'dark') {
                html.classList.remove('light-theme');
                html.classList.add('dark-theme');
            } else {
                html.classList.remove('dark-theme');
                html.classList.add('light-theme');
            }

            // Apply theme to chart
            if (this.chart.chart) {
                const chartOptions = theme === 'dark'
                    ? this.getDarkChartOptions()
                    : this.getLightChartOptions();
                this.chart.chart.applyOptions(chartOptions);
                console.log(`[ChartActions] Chart theme applied: ${theme}`);
            }
        } catch (error) {
            console.error('[ChartActions] Error in applyTheme:', error);
        }
    }

    /**
     * Get dark theme chart options
     */
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

    /**
     * Get light theme chart options
     */
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

    /**
     * Update theme toggle button appearance
     */
    updateThemeButton(theme) {
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? 'Dark' : 'Light';
        }
    }

    /**
     * Toggle volume series visibility
     */
    toggleVolume() {
        try {
            const btn = document.getElementById('volume-toggle');
            if (!btn) {
                console.warn('[ChartActions] Volume toggle button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                // Hide volume
                btn.classList.remove('active');
                console.log('[ChartActions] Volume hidden - expanding chart area');

                if (this.chart.volumeSeries) {
                    this.chart.volumeSeries.applyOptions({
                        visible: false,
                        priceScaleId: ''
                    });
                }

                // Adjust layout to use full height for price chart
                if (this.chart.chart) {
                    this.chart.chart.priceScale('right').applyOptions({
                        scaleMargins: {
                            top: 0.05,
                            bottom: 0.05  // Reduced from default ~0.2 when volume is hidden
                        }
                    });
                }
            } else {
                // Show volume
                btn.classList.add('active');
                console.log('[ChartActions] Volume shown - reserving space for volume');

                if (this.chart.volumeSeries) {
                    this.chart.volumeSeries.applyOptions({
                        visible: true,
                        priceScaleId: ''
                    });
                }

                // Restore layout to reserve space for volume
                if (this.chart.chart) {
                    this.chart.chart.priceScale('right').applyOptions({
                        scaleMargins: {
                            top: 0.05,
                            bottom: 0.2  // Reserve 20% for volume
                        }
                    });
                }
            }
        } catch (error) {
            console.error('[ChartActions] Error in toggleVolume:', error);
        }
    }

    /**
     * Toggle trade markers display
     */
    toggleTradeMarkers() {
        try {
            this.showTradeMarkers = !this.showTradeMarkers;

            const toggleBtn = document.getElementById('trade-markers-toggle');
            if (toggleBtn) {
                if (this.showTradeMarkers) {
                    toggleBtn.classList.add('active');
                } else {
                    toggleBtn.classList.remove('active');
                }
            }

            console.log(`[ChartActions] Trade markers ${this.showTradeMarkers ? 'enabled' : 'disabled'}`);

            // Reload trading history to reflect marker state
            this.loadTradingHistory(true);
        } catch (error) {
            console.error('[ChartActions] Error in toggleTradeMarkers:', error);
        }
    }

    /**
     * Load trading history for current market
     */
    async loadTradingHistory(forceRefresh = false) {
        try {
            console.log(`[ChartActions] Loading trading history for ${this.chart.currentMarket}... (forceRefresh: ${forceRefresh})`);

            if (!window.apiHandler) {
                console.error('[ChartActions] APIHandler not available');
                return;
            }

            const historyList = document.getElementById('history-list');
            if (!historyList) {
                console.error('[ChartActions] History list element not found');
                return;
            }

            // Show loading state
            historyList.innerHTML = '<div class="loading-state">Loading trading history...</div>';

            // Fetch trading history (limit 100)
            const response = await window.apiHandler.getOrders(
                this.chart.currentMarket,
                'done',
                100,
                !forceRefresh
            );
            console.log(`[ChartActions] Trading history response for ${this.chart.currentMarket}:`, response);

            // Extract orders from response
            const orders = response.orders || (response.data && response.data.orders) || [];

            if (!response.success || orders.length === 0) {
                historyList.innerHTML = `<div class="empty-state">No trading history for ${this.chart.currentMarket}</div>`;
                return;
            }

            // Clear loading state
            historyList.innerHTML = '';

            // Get visible time range from chart
            const visibleRange = this.getVisibleTimeRange();

            // Filter orders to only show those in visible time range
            let visibleOrders = orders;
            if (visibleRange) {
                visibleOrders = orders.filter(order => {
                    try {
                        const orderTime = new Date(order.executed_at || order.created_at).getTime();
                        return orderTime >= visibleRange.from && orderTime <= visibleRange.to;
                    } catch (e) {
                        return false;
                    }
                });
                console.log(`[ChartActions] Filtered ${orders.length} orders to ${visibleOrders.length} visible orders`);
            }

            // Display each order (max 50 visible orders)
            console.log(`[ChartActions] Displaying ${visibleOrders.length} visible orders for ${this.chart.currentMarket}`);

            visibleOrders.slice(0, 50).forEach((order, index) => {
                const orderItem = document.createElement('div');
                orderItem.className = 'history-item';

                const side = order.side || 'unknown';
                const sideClass = side === 'bid' ? 'buy' : 'sell';
                const sideText = side === 'bid' ? 'BUY' : 'SELL';

                const price = parseFloat(order.avg_price || order.price || 0);
                const volume = parseFloat(order.volume || 0);
                const executedVolume = parseFloat(order.executed_volume || volume);
                const totalPrice = price * executedVolume;

                // Use kr_time (already formatted), or executed_at, or created_at as fallback
                let displayTime = 'Unknown';
                if (order.kr_time) {
                    displayTime = order.kr_time;
                } else if (order.executed_at && order.executed_at !== 'N/A') {
                    try {
                        displayTime = new Date(order.executed_at).toLocaleString('ko-KR');
                    } catch (e) {
                        displayTime = order.executed_at;
                    }
                } else if (order.created_at && order.created_at !== 'N/A') {
                    try {
                        displayTime = new Date(order.created_at).toLocaleString('ko-KR');
                    } catch (e) {
                        displayTime = order.created_at;
                    }
                }

                orderItem.innerHTML = `
                    <div class="order-header">
                        <span class="order-side ${sideClass}">${sideText}</span>
                        <span class="order-time">${displayTime}</span>
                    </div>
                    <div class="order-details">
                        <div>가격: ${price.toLocaleString()} 원</div>
                        <div>수량: ${executedVolume.toFixed(8)}</div>
                        <div>총액: ${totalPrice.toLocaleString()} 원</div>
                    </div>
                `;

                historyList.appendChild(orderItem);
            });

            console.log('[ChartActions] Trading history displayed successfully');

            // Add markers to chart via DataLoader
            if (this.chart && this.chart.dataLoader && typeof this.chart.dataLoader.addTradingHistoryMarkers === 'function') {
                this.chart.dataLoader.addTradingHistoryMarkers(orders);
                console.log('[ChartActions] Called addTradingHistoryMarkers with', orders.length, 'orders');
            } else {
                console.warn('[ChartActions] DataLoader.addTradingHistoryMarkers method not available');
            }

        } catch (error) {
            console.error('[ChartActions] Error loading trading history:', error);

            const historyList = document.getElementById('history-list');
            if (historyList) {
                historyList.innerHTML = `<div class="error-state">Failed to load trading history</div>`;
            }
        }
    }

    /**
     * Get visible time range from chart
     */
    getVisibleTimeRange() {
        try {
            if (!this.chart || !this.chart.chartData || this.chart.chartData.length === 0) {
                return null;
            }

            const chartData = this.chart.chartData;

            // Get the full time range
            const fromTime = chartData[0].time * 1000; // Convert to milliseconds
            const toTime = chartData[chartData.length - 1].time * 1000;

            // Get the visible range from the chart's time scale
            const timeScale = window.chartUtils?.chart?.timeScale();
            if (timeScale) {
                try {
                    const visibleLogicalRange = timeScale.getVisibleLogicalRange();
                    if (visibleLogicalRange) {
                        // Calculate actual time range based on visible logical range
                        const visibleFrom = Math.floor(visibleLogicalRange.from);
                        const visibleTo = Math.ceil(visibleLogicalRange.to);

                        // Ensure indices are within bounds
                        const fromIndex = Math.max(0, Math.min(visibleFrom, chartData.length - 1));
                        const toIndex = Math.max(0, Math.min(visibleTo, chartData.length - 1));

                        return {
                            from: chartData[fromIndex].time * 1000,
                            to: chartData[toIndex].time * 1000
                        };
                    }
                } catch (e) {
                    console.warn('[ChartActions] Could not get visible logical range:', e);
                }
            }

            // Fallback: return full time range
            return {
                from: fromTime,
                to: toTime
            };
        } catch (error) {
            console.error('[ChartActions] Error getting visible time range:', error);
            return null;
        }
    }

    /**
     * Initialize theme on page load
     */
    initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            this.currentTheme = savedTheme;
            this.applyTheme(savedTheme);
            this.updateThemeButton(savedTheme);
            console.log('[ChartActions] Theme initialized:', savedTheme);
        } catch (error) {
            console.error('[ChartActions] Error initializing theme:', error);
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ChartActions = ChartActions;
}
