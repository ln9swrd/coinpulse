/**
 * ChartManager - Chart initialization, data management, and lifecycle
 * Handles chart creation, data setting, theme changes, and cleanup
 */

class ChartManager {
    constructor() {
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.chartContainer = null;
        this.chartData = [];

        console.log('[ChartManager] Module initialized');
    }

    /**
     * Initialize chart with TradingView style
     * @param {string} containerId - DOM container ID
     * @returns {Object} LightweightCharts instance
     */
    initChart(containerId) {
        console.log('[ChartManager] Initializing chart with container:', containerId);

        this.chartContainer = document.getElementById(containerId);
        if (!this.chartContainer) {
            throw new Error(`Chart container with id '${containerId}' not found`);
        }

        // Remove existing chart
        if (this.chart) {
            console.log('[ChartManager] Removing existing chart');
            try {
                this.chart.remove();
            } catch (error) {
                console.warn('[ChartManager] Error removing existing chart:', error);
            }
            this.chart = null;
        }

        // Get container dimensions with defaults
        let width = this.chartContainer.clientWidth;
        let height = this.chartContainer.clientHeight;

        if (!width || width <= 0) {
            width = 800;
            console.warn('[ChartManager] Container width is 0, using default:', width);
        }
        if (!height || height <= 0) {
            height = 500;
            console.warn('[ChartManager] Container height is 0, using default:', height);
        }

        // Ensure minimum size
        width = Math.max(width, 300);
        height = Math.max(height, 400);

        // Force container size
        this.chartContainer.style.width = width + 'px';
        this.chartContainer.style.height = height + 'px';

        console.log(`[ChartManager] Creating chart: ${width}x${height}`);

        try {
            // Validate LightweightCharts library
            if (typeof LightweightCharts === 'undefined') {
                throw new Error('LightweightCharts library not loaded');
            }

            if (typeof LightweightCharts.createChart !== 'function') {
                throw new Error('LightweightCharts.createChart function not available');
            }

            if (typeof LightweightCharts.CrosshairMode === 'undefined') {
                throw new Error('LightweightCharts.CrosshairMode not available');
            }

            // Create chart with TradingView style options
            this.chart = LightweightCharts.createChart(this.chartContainer, {
                width: width,
                height: height,
                layout: {
                    background: { color: '#131722' },
                    textColor: '#d1d4dc',
                    fontSize: 12,
                    fontFamily: 'Trebuchet MS, Arial, sans-serif',
                },
                localeOptions: {
                    locale: 'ko-KR',
                    dateFormat: 'yyyy-MM-dd',
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { visible: false },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        width: 1,
                        color: 'rgba(224, 227, 235, 0.1)',
                        style: 0,
                        labelBackgroundColor: '#363c4e',
                    },
                    horzLine: {
                        width: 1,
                        color: 'rgba(224, 227, 235, 0.1)',
                        style: 0,
                        labelBackgroundColor: '#363c4e',
                    },
                },
                rightPriceScale: {
                    borderColor: '#2a2e39',
                    borderVisible: true,
                    scaleMargins: {
                        top: 0.05,
                        bottom: 0.35,
                    },
                    mode: 1, // Log mode
                },
                timeScale: {
                    borderColor: '#2a2e39',
                    borderVisible: true,
                    timeVisible: true,
                    secondsVisible: false,
                    rightOffset: 12,
                    barSpacing: 8,
                    minBarSpacing: 0.5,
                    fixLeftEdge: false,
                    fixRightEdge: false,
                    lockVisibleTimeRangeOnResize: true,
                    rightBarStaysOnScroll: true,
                    shiftVisibleRangeOnNewBar: true,
                },
                handleScroll: {
                    mouseWheel: true,
                    pressedMouseMove: true,
                    horzTouchDrag: true,
                    vertTouchDrag: true,
                },
                handleScale: {
                    axisPressedMouseMove: true,
                    mouseWheel: true,
                    pinch: true,
                },
            });
            console.log('[ChartManager] Chart created successfully');
        } catch (error) {
            console.error('[ChartManager] Failed to create chart:', error);
            throw error;
        }

        // Add candlestick series
        try {
            if (this.chart && typeof this.chart.addCandlestickSeries === 'function') {
                this.candleSeries = this.chart.addCandlestickSeries({
                    upColor: '#089981',
                    downColor: '#f23645',
                    borderUpColor: '#089981',
                    borderDownColor: '#f23645',
                    wickUpColor: '#089981',
                    wickDownColor: '#f23645',
                    priceFormat: {
                        type: 'price',
                        precision: 0,
                        minMove: 1,
                    },
                });
                console.log('[ChartManager] Candlestick series added');
            } else {
                throw new Error('addCandlestickSeries function not available');
            }
        } catch (error) {
            console.error('[ChartManager] Failed to add candlestick series:', error);
            throw error;
        }

        // Add volume series
        try {
            if (this.chart && typeof this.chart.addHistogramSeries === 'function') {
                this.volumeSeries = this.chart.addHistogramSeries({
                    color: '#26a69a',
                    priceFormat: { type: 'volume' },
                    priceScaleId: 'volume_scale',
                    scaleMargins: {
                        top: 0.65,
                        bottom: 0,
                    },
                });

                this.chart.priceScale('volume_scale').applyOptions({
                    scaleMargins: {
                        top: 0.65,
                        bottom: 0,
                    },
                });

                console.log('[ChartManager] Volume series added');
            } else {
                throw new Error('addHistogramSeries function not available');
            }
        } catch (error) {
            console.error('[ChartManager] Failed to add volume series:', error);
        }

        // Setup resize listener
        window.addEventListener('resize', () => {
            if (this.chart && this.chartContainer) {
                this.chart.applyOptions({
                    width: this.chartContainer.clientWidth,
                    height: this.chartContainer.clientHeight,
                });
            }
        });

        return this.chart;
    }

    /**
     * Set candle and volume data
     * @param {Array} candles - Candle data array
     * @param {Array} volume - Volume data array
     */
    setData(candles, volume = null) {
        console.log('[ChartManager] setData called');
        console.log('[ChartManager] Chart exists:', !!this.chart);
        console.log('[ChartManager] Candle series exists:', !!this.candleSeries);
        console.log('[ChartManager] Volume series exists:', !!this.volumeSeries);

        // Validate input
        if (!candles || !Array.isArray(candles)) {
            console.warn('[ChartManager] Invalid candles data');
            candles = [];
        }

        if (!volume || !Array.isArray(volume)) {
            console.warn('[ChartManager] Invalid volume data');
            volume = [];
        }

        // Filter and validate candle data
        const safeCandles = candles.filter(candle => {
            if (!candle || candle === null || candle === undefined) return false;

            if (candle.time === null || candle.time === undefined) return false;
            if (candle.open === null || candle.open === undefined) return false;
            if (candle.high === null || candle.high === undefined) return false;
            if (candle.low === null || candle.low === undefined) return false;
            if (candle.close === null || candle.close === undefined) return false;

            if (isNaN(candle.time) || isNaN(candle.open) || isNaN(candle.high) || isNaN(candle.low) || isNaN(candle.close)) return false;

            if (!Number.isFinite(candle.time) || !Number.isFinite(candle.open) || !Number.isFinite(candle.high) || !Number.isFinite(candle.low) || !Number.isFinite(candle.close)) return false;

            if (candle.time <= 0 || candle.open <= 0 || candle.high <= 0 || candle.low <= 0 || candle.close <= 0) return false;

            if (candle.high < Math.max(candle.open, candle.close) || candle.low > Math.min(candle.open, candle.close)) return false;

            return true;
        });

        // Filter and validate volume data
        const safeVolume = volume.filter(vol => {
            if (!vol || vol === null || vol === undefined) return false;

            if (vol.time === null || vol.time === undefined) return false;
            if (vol.value === null || vol.value === undefined) return false;

            if (isNaN(vol.time) || isNaN(vol.value)) return false;

            if (!Number.isFinite(vol.time) || !Number.isFinite(vol.value)) return false;

            if (vol.time <= 0 || vol.value < 0) return false;

            return true;
        });

        console.log(`[ChartManager] Safe data: ${safeCandles.length} candles, ${safeVolume.length} volume`);

        if (safeCandles.length === 0) {
            console.warn('[ChartManager] No safe candles data available');
            if (this.candleSeries) {
                try {
                    this.candleSeries.setData([]);
                } catch (error) {
                    console.error('[ChartManager] Failed to set empty candles:', error);
                }
            }
            return;
        }

        // Set candle data
        if (this.candleSeries && safeCandles.length > 0) {
            try {
                const sortedCandles = safeCandles.sort((a, b) => a.time - b.time);
                console.log('[ChartManager] Setting candles:', sortedCandles.length);

                this.candleSeries.setData(sortedCandles);
                this.chartData = sortedCandles;
                console.log('[ChartManager] Candles set successfully');
            } catch (error) {
                console.error('[ChartManager] Error setting candles:', error);
                try {
                    this.candleSeries.setData([]);
                } catch (fallbackError) {
                    console.error('[ChartManager] Failed to set empty candles:', fallbackError);
                }
            }
        }

        // Set volume data
        if (this.volumeSeries && safeVolume.length > 0) {
            try {
                const sortedVolume = safeVolume.sort((a, b) => a.time - b.time);
                console.log('[ChartManager] Setting volume:', sortedVolume.length);

                this.volumeSeries.setData(sortedVolume);
                console.log('[ChartManager] Volume set successfully');
            } catch (error) {
                console.error('[ChartManager] Error setting volume:', error);
                try {
                    this.volumeSeries.setData([]);
                } catch (fallbackError) {
                    console.error('[ChartManager] Failed to set empty volume:', fallbackError);
                }
            }
        }
    }

    /**
     * Change chart theme (light/dark)
     * @param {string} theme - 'light' or 'dark'
     */
    setTheme(theme) {
        if (!this.chart) {
            console.warn('[ChartManager] Chart not available for theme change');
            return;
        }

        const isLight = theme === 'light';

        this.chart.applyOptions({
            layout: {
                background: { color: isLight ? '#ffffff' : '#131722' },
                textColor: isLight ? '#1e293b' : '#d1d4dc',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            rightPriceScale: {
                borderColor: isLight ? '#e2e8f0' : '#2a2e39',
            },
            timeScale: {
                borderColor: isLight ? '#e2e8f0' : '#2a2e39',
            },
        });

        console.log(`[ChartManager] Theme changed to: ${theme}`);
    }

    /**
     * Clean up chart instance
     */
    destroy() {
        if (this.chart) {
            try {
                this.chart.remove();
                console.log('[ChartManager] Chart removed');
            } catch (error) {
                console.error('[ChartManager] Error removing chart:', error);
            }
            this.chart = null;
        }

        this.candleSeries = null;
        this.volumeSeries = null;
        this.chartContainer = null;
        this.chartData = [];
    }

    /**
     * Get current chart data
     * @returns {Array} Chart data
     */
    getChartData() {
        return this.chartData;
    }

    /**
     * Get chart instance
     * @returns {Object} LightweightCharts instance
     */
    getChart() {
        return this.chart;
    }

    /**
     * Get candlestick series
     * @returns {Object} Candlestick series
     */
    getCandleSeries() {
        return this.candleSeries;
    }

    /**
     * Get volume series
     * @returns {Object} Volume series
     */
    getVolumeSeries() {
        return this.volumeSeries;
    }
}

// Export to window
if (typeof window !== 'undefined') {
    window.ChartManager = ChartManager;
}
