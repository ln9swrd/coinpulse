/**
 * ChartUtilities - Chart utility functions
 * Handles crosshair events, chart export, drawing mode, alerts
 */

class ChartUtilities {
    constructor(chartManager) {
        this.chartManager = chartManager;

        // Drawing mode variables
        this.drawingMode = null;
        this.isDrawing = false;
        this.startPoint = null;
        this.drawingLines = [];
        this.tempLine = null;
        this.tempFibonacci = [];
        this.fibonacciLines = [];
        this.patternDetections = [];

        // Undo/Redo functionality
        this.actionHistory = [];
        this.historyIndex = -1;
        this.MAX_HISTORY = 50;

        // Alert system
        this.alertSettings = {
            rsi: { overbought: 70, oversold: 30 },
            macd: { signal: 0 },
            ma: { cross: true },
            volume: { spike: 2.0 }
        };

        this.alerts = [];
        this.alertCallbacks = [];

        console.log('[ChartUtilities] Module initialized');
    }

    /**
     * Setup crosshair event listener
     * @param {Function} callback - Callback function for crosshair move
     */
    setupCrosshairListener(callback) {
        const chart = this.chartManager.getChart();
        if (!chart) {
            console.warn('[ChartUtilities] Chart not available for crosshair');
            return;
        }

        chart.subscribeCrosshairMove((param) => {
            if (callback && typeof callback === 'function') {
                callback(param);
            } else {
                this.handleCrosshairMove(param);
            }
        });

        console.log('[ChartUtilities] Crosshair listener setup');
    }

    /**
     * Default crosshair move handler
     * @param {Object} param - Crosshair event parameter
     */
    handleCrosshairMove(param) {
        const crosshairInfo = document.getElementById('crosshair-info');
        if (!crosshairInfo) return;

        const candleSeries = this.chartManager.getCandleSeries();
        if (!candleSeries) return;

        if (param.time && param.point) {
            const data = param.seriesData.get(candleSeries);
            if (data) {
                crosshairInfo.classList.add('visible');

                const timeEl = document.getElementById('crosshair-time');
                const openEl = document.getElementById('crosshair-open');
                const highEl = document.getElementById('crosshair-high');
                const lowEl = document.getElementById('crosshair-low');
                const closeEl = document.getElementById('crosshair-close');
                const volumeEl = document.getElementById('crosshair-volume');

                if (timeEl) timeEl.textContent = new Date(data.time * 1000).toLocaleString('ko-KR');
                if (openEl) openEl.textContent = this.formatPrice(data.open);
                if (highEl) highEl.textContent = this.formatPrice(data.high);
                if (lowEl) lowEl.textContent = this.formatPrice(data.low);
                if (closeEl) closeEl.textContent = this.formatPrice(data.close);
                if (volumeEl) volumeEl.textContent = this.formatNumber(data.volume || 0);
            }
        } else {
            crosshairInfo.classList.remove('visible');
        }
    }

    /**
     * Format price value
     * @param {number} price - Price value
     * @returns {string} Formatted price
     */
    formatPrice(price) {
        if (typeof price !== 'number' || isNaN(price)) return '0';
        return price.toLocaleString('ko-KR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    /**
     * Format number value
     * @param {number} num - Number value
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        if (typeof num !== 'number' || isNaN(num)) return '0';
        return num.toLocaleString('ko-KR');
    }

    /**
     * Set drawing mode
     * @param {string} mode - Drawing mode ('trendline', 'fibonacci', 'horizontal', etc.)
     */
    setDrawingMode(mode) {
        this.drawingMode = mode;
        this.isDrawing = false;
        this.startPoint = null;

        // Remove temp line
        if (this.tempLine) {
            const chart = this.chartManager.getChart();
            if (chart) {
                chart.removeSeries(this.tempLine);
            }
            this.tempLine = null;
        }

        console.log(`[ChartUtilities] Drawing mode set: ${mode}`);
    }

    /**
     * Get current drawing mode
     * @returns {string} Current drawing mode
     */
    getDrawingMode() {
        return this.drawingMode;
    }

    /**
     * Clear all drawings
     */
    clearDrawings() {
        const chart = this.chartManager.getChart();
        if (!chart) return;

        // Remove all drawing lines
        this.drawingLines.forEach(line => {
            try {
                chart.removeSeries(line);
            } catch (error) {
                console.warn('[ChartUtilities] Error removing drawing line:', error);
            }
        });

        this.drawingLines = [];
        this.fibonacciLines = [];
        this.patternDetections = [];

        console.log('[ChartUtilities] All drawings cleared');
    }

    /**
     * Export chart as image
     * @param {string} format - Image format ('png', 'jpeg')
     * @returns {string} Data URL of chart image
     */
    exportChart(format = 'png') {
        const chart = this.chartManager.getChart();
        if (!chart) {
            console.warn('[ChartUtilities] Chart not available for export');
            return null;
        }

        const container = this.chartManager.chartContainer;
        if (!container) {
            console.warn('[ChartUtilities] Container not available for export');
            return null;
        }

        const canvas = container.querySelector('canvas');
        if (canvas) {
            const dataUrl = canvas.toDataURL(`image/${format}`);
            console.log(`[ChartUtilities] Chart exported as ${format}`);
            return dataUrl;
        }

        console.warn('[ChartUtilities] Canvas not found for export');
        return null;
    }

    /**
     * Undo last action
     */
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const action = this.actionHistory[this.historyIndex];
            this.applyAction(action, true);
            console.log('[ChartUtilities] Undo action:', this.historyIndex);
        } else {
            console.log('[ChartUtilities] No actions to undo');
        }
    }

    /**
     * Redo last undone action
     */
    redo() {
        if (this.historyIndex < this.actionHistory.length - 1) {
            this.historyIndex++;
            const action = this.actionHistory[this.historyIndex];
            this.applyAction(action, false);
            console.log('[ChartUtilities] Redo action:', this.historyIndex);
        } else {
            console.log('[ChartUtilities] No actions to redo');
        }
    }

    /**
     * Apply action (for undo/redo)
     * @param {Object} action - Action to apply
     * @param {boolean} isUndo - Is this an undo operation
     */
    applyAction(action, isUndo) {
        // Placeholder for undo/redo implementation
        console.log(`[ChartUtilities] Applying action: ${action.type}, undo: ${isUndo}`);
    }

    /**
     * Add action to history
     * @param {Object} action - Action to add
     */
    addToHistory(action) {
        // Remove actions after current index
        this.actionHistory = this.actionHistory.slice(0, this.historyIndex + 1);

        // Add new action
        this.actionHistory.push(action);
        this.historyIndex++;

        // Limit history size
        if (this.actionHistory.length > this.MAX_HISTORY) {
            this.actionHistory.shift();
            this.historyIndex--;
        }

        console.log(`[ChartUtilities] Action added to history: ${action.type}, index: ${this.historyIndex}`);
    }

    /**
     * Setup alert for technical indicators
     * @param {string} indicator - Indicator name ('rsi', 'macd', 'ma', 'volume')
     * @param {Object} settings - Alert settings
     */
    setupAlert(indicator, settings) {
        if (!this.alertSettings[indicator]) {
            console.warn(`[ChartUtilities] Unknown indicator: ${indicator}`);
            return;
        }

        this.alertSettings[indicator] = { ...this.alertSettings[indicator], ...settings };
        console.log(`[ChartUtilities] Alert setup for ${indicator}:`, this.alertSettings[indicator]);
    }

    /**
     * Check alerts and trigger callbacks
     * @param {Object} data - Current market data
     */
    checkAlerts(data) {
        const newAlerts = [];

        // RSI alerts
        if (data.rsi) {
            if (data.rsi >= this.alertSettings.rsi.overbought) {
                newAlerts.push({
                    type: 'rsi',
                    level: 'warning',
                    message: `RSI overbought: ${data.rsi.toFixed(2)}`
                });
            } else if (data.rsi <= this.alertSettings.rsi.oversold) {
                newAlerts.push({
                    type: 'rsi',
                    level: 'warning',
                    message: `RSI oversold: ${data.rsi.toFixed(2)}`
                });
            }
        }

        // MACD alerts
        if (data.macd && data.macdSignal) {
            const macdCross = (data.macd > data.macdSignal) !== (data.prevMacd > data.prevMacdSignal);
            if (macdCross) {
                newAlerts.push({
                    type: 'macd',
                    level: 'info',
                    message: data.macd > data.macdSignal ? 'MACD bullish cross' : 'MACD bearish cross'
                });
            }
        }

        // Trigger alert callbacks
        if (newAlerts.length > 0) {
            this.alerts.push(...newAlerts);
            this.alertCallbacks.forEach(callback => {
                try {
                    callback(newAlerts);
                } catch (error) {
                    console.error('[ChartUtilities] Error in alert callback:', error);
                }
            });
        }
    }

    /**
     * Register alert callback
     * @param {Function} callback - Callback function
     */
    onAlert(callback) {
        if (typeof callback === 'function') {
            this.alertCallbacks.push(callback);
            console.log('[ChartUtilities] Alert callback registered');
        }
    }

    /**
     * Clear all alerts
     */
    clearAlerts() {
        this.alerts = [];
        console.log('[ChartUtilities] All alerts cleared');
    }

    /**
     * Get all alerts
     * @returns {Array} List of alerts
     */
    getAlerts() {
        return this.alerts;
    }
}

// Export to window
if (typeof window !== 'undefined') {
    window.ChartUtilities = ChartUtilities;
}
