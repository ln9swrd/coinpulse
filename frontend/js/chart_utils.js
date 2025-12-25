/**
 * ChartUtils - Main chart utilities wrapper
 * Integrates ChartManager, IndicatorCalculator, IndicatorRenderer, ChartUtilities
 * Provides backward compatibility with previous monolithic ChartUtils class
 *
 * Phase 3: Modularized into 4 focused modules (2025-11-13)
 */

class ChartUtils {
    constructor() {
        // Initialize sub-modules
        this.chartManager = new ChartManager();
        this.calculator = new IndicatorCalculator();
        this.renderer = new IndicatorRenderer(this.chartManager, this.calculator);
        this.utilities = new ChartUtilities(this.chartManager);

        // Backward compatibility: expose internal properties
        this.chart = null;
        this.rsiChart = null;
        this.macdChart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.maSeries = { 20: null, 50: null, 100: null, 200: null };
        this.upperBandSeries = null;
        this.middleBandSeries = null;
        this.lowerBandSeries = null;
        this.rsiSeries = null;
        this.macdLineSeries = null;
        this.macdSignalSeries = null;
        this.macdHistogramSeries = null;
        this.superTrendUpSeries = null;
        this.superTrendDownSeries = null;
        this.superTrendData = null;
        this.chartContainer = null;
        this.chartData = [];

        // Drawing mode variables
        this.drawingMode = null;
        this.isDrawing = false;
        this.startPoint = null;
        this.drawingLines = [];
        this.tempLine = null;
        this.tempFibonacci = [];
        this.fibonacciLines = [];
        this.patternDetections = [];

        // Undo/Redo
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

        console.log('[ChartUtils] Wrapper initialized with sub-modules');
    }

    // ========================================
    // ChartManager Methods (Delegation)
    // ========================================

    initChart(containerId) {
        const chart = this.chartManager.initChart(containerId);

        // Update backward compatibility properties
        this.chart = this.chartManager.getChart();
        this.candleSeries = this.chartManager.getCandleSeries();
        this.volumeSeries = this.chartManager.getVolumeSeries();
        this.chartContainer = this.chartManager.chartContainer;

        // Setup crosshair listener
        this.utilities.setupCrosshairListener();

        return chart;
    }

    setData(candles, volume = null) {
        this.chartManager.setData(candles, volume);

        // Update backward compatibility property
        this.chartData = this.chartManager.getChartData();
    }

    setTheme(theme) {
        this.chartManager.setTheme(theme);
    }

    destroy() {
        this.chartManager.destroy();

        // Clear backward compatibility properties
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.chartContainer = null;
        this.chartData = [];
    }

    // ========================================
    // IndicatorCalculator Methods (Delegation)
    // ========================================

    calculateMovingAverage(data, period) {
        return this.calculator.calculateMovingAverage(data, period);
    }

    calculateRSI(data, period = 14) {
        return this.calculator.calculateRSI(data, period);
    }

    calculateBollingerBands(data, period = 20, multiplier = 2) {
        return this.calculator.calculateBollingerBands(data, period, multiplier);
    }

    calculateMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        return this.calculator.calculateMACD(data, fastPeriod, slowPeriod, signalPeriod);
    }

    calculateATR(data, period = 14) {
        return this.calculator.calculateATR(data, period);
    }

    calculateSuperTrend(data, period = 10, multiplier = 3.0) {
        return this.calculator.calculateSuperTrend(data, period, multiplier);
    }

    // ========================================
    // IndicatorRenderer Methods (Delegation)
    // ========================================

    addMovingAverage(period, color = '#ff6b6b') {
        const series = this.renderer.addMovingAverage(period, color);

        // Update backward compatibility property
        this.maSeries[period] = series;

        return series;
    }

    addRSI(data, period = 14, color = '#ffa726') {
        const series = this.renderer.addRSI(data, period, color);

        // Update backward compatibility properties
        this.rsiChart = this.renderer.rsiChart;
        this.rsiSeries = series;

        return series;
    }

    removeRSI() {
        this.renderer.removeRSI();

        // Update backward compatibility properties
        this.rsiChart = null;
        this.rsiSeries = null;
    }

    addBollingerBands(data, period = 20, multiplier = 2) {
        const series = this.renderer.addBollingerBands(data, period, multiplier);

        // Update backward compatibility properties
        if (series) {
            this.upperBandSeries = series.upper;
            this.middleBandSeries = series.middle;
            this.lowerBandSeries = series.lower;
        }

        return series;
    }

    removeBollingerBands() {
        this.renderer.removeBollingerBands();

        // Update backward compatibility properties
        this.upperBandSeries = null;
        this.middleBandSeries = null;
        this.lowerBandSeries = null;
    }

    addMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const series = this.renderer.addMACD(data, fastPeriod, slowPeriod, signalPeriod);

        // Update backward compatibility properties
        this.macdChart = this.renderer.macdChart;
        if (series) {
            this.macdLineSeries = series.macd;
            this.macdSignalSeries = series.signal;
        }

        return series;
    }

    removeMACD() {
        this.renderer.removeMACD();

        // Update backward compatibility properties
        this.macdChart = null;
        this.macdLineSeries = null;
        this.macdSignalSeries = null;
        this.macdHistogramSeries = null;
    }

    addSuperTrend(data, period = 10, multiplier = 3.0) {
        const series = this.renderer.addSuperTrend(data, period, multiplier);

        // Update backward compatibility properties
        if (series) {
            this.superTrendUpSeries = series.upSeries;
            this.superTrendDownSeries = series.downSeries;
            this.superTrendData = series.data;
        }

        return series;
    }

    removeSuperTrend() {
        this.renderer.removeSuperTrend();

        // Update backward compatibility properties
        this.superTrendUpSeries = null;
        this.superTrendDownSeries = null;
        this.superTrendData = null;
    }

    getCurrentSuperTrendSignal() {
        return this.renderer.getCurrentSuperTrendSignal();
    }

    // ========================================
    // Ichimoku Cloud Methods
    // ========================================

    calculateIchimoku(data, params = {}) {
        // 기본값 설정
        const tenkanPeriod = params.tenkanPeriod || 9;
        const kijunPeriod = params.kijunPeriod || 26;
        const senkouBPeriod = params.senkouBPeriod || 52;
        const displacement = params.displacement || 26;

        const maxPeriod = Math.max(tenkanPeriod, kijunPeriod, senkouBPeriod);
        if (!data || data.length < maxPeriod) {
            console.warn(`[ChartUtils] Insufficient data for Ichimoku calculation (need ${maxPeriod}, got ${data?.length})`);
            return null;
        }

        const result = {
            tenkan: [],
            kijun: [],
            senkouA: [],
            senkouB: [],
            chikou: []
        };

        // Helper function to calculate high/low average
        const calcHL = (data, start, period) => {
            let high = -Infinity;
            let low = Infinity;
            for (let i = start; i < start + period && i < data.length; i++) {
                high = Math.max(high, data[i].high);
                low = Math.min(low, data[i].low);
            }
            return (high + low) / 2;
        };

        for (let i = 0; i < data.length; i++) {
            const time = data[i].time;

            // Tenkan-sen (전환선): (9-period high + 9-period low) / 2
            if (i >= tenkanPeriod - 1) {
                const tenkan = calcHL(data, i - tenkanPeriod + 1, tenkanPeriod);
                result.tenkan.push({ time, value: tenkan });
            }

            // Kijun-sen (기준선): (26-period high + 26-period low) / 2
            if (i >= kijunPeriod - 1) {
                const kijun = calcHL(data, i - kijunPeriod + 1, kijunPeriod);
                result.kijun.push({ time, value: kijun });
            }

            // Senkou Span B (선행스팬 B): (52-period high + 52-period low) / 2, displaced forward 26 periods
            if (i >= senkouBPeriod - 1) {
                const senkouB = calcHL(data, i - senkouBPeriod + 1, senkouBPeriod);
                const futureIndex = i + displacement;
                if (futureIndex < data.length) {
                    result.senkouB.push({ time: data[futureIndex].time, value: senkouB });
                }
            }

            // Senkou Span A (선행스팬 A): (Tenkan + Kijun) / 2, displaced forward 26 periods
            if (i >= kijunPeriod - 1) {
                const tenkan = calcHL(data, i - tenkanPeriod + 1, tenkanPeriod);
                const kijun = calcHL(data, i - kijunPeriod + 1, kijunPeriod);
                const senkouA = (tenkan + kijun) / 2;
                const futureIndex = i + displacement;
                if (futureIndex < data.length) {
                    result.senkouA.push({ time: data[futureIndex].time, value: senkouA });
                }
            }

            // Chikou Span (후행스팬): Close price, displaced backward 26 periods
            if (i >= displacement) {
                result.chikou.push({ time: data[i - displacement].time, value: data[i].close });
            }
        }

        return result;
    }

    addIchimoku(data, params = {}) {
        if (!this.chartManager || !this.chartManager.chart) {
            console.error('[ChartUtils] Chart not initialized');
            return null;
        }

        const ichimokuData = this.calculateIchimoku(data, params);
        if (!ichimokuData) {
            return null;
        }

        const chart = this.chartManager.chart;

        // Remove existing Ichimoku if any
        this.removeIchimoku();

        // Create line series for each component
        this.ichimokuSeries = {
            tenkan: chart.addLineSeries({
                color: '#ff3366',
                lineWidth: 1,
                title: 'Tenkan-sen'
            }),
            kijun: chart.addLineSeries({
                color: '#3366ff',
                lineWidth: 1,
                title: 'Kijun-sen'
            }),
            senkouA: chart.addLineSeries({
                color: 'rgba(50, 205, 50, 0.5)',
                lineWidth: 1,
                title: 'Senkou Span A'
            }),
            senkouB: chart.addLineSeries({
                color: 'rgba(255, 69, 0, 0.5)',
                lineWidth: 1,
                title: 'Senkou Span B'
            }),
            chikou: chart.addLineSeries({
                color: '#ffaa00',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                title: 'Chikou Span'
            })
        };

        // Set data for each series
        this.ichimokuSeries.tenkan.setData(ichimokuData.tenkan);
        this.ichimokuSeries.kijun.setData(ichimokuData.kijun);
        this.ichimokuSeries.senkouA.setData(ichimokuData.senkouA);
        this.ichimokuSeries.senkouB.setData(ichimokuData.senkouB);
        this.ichimokuSeries.chikou.setData(ichimokuData.chikou);

        console.log('[ChartUtils] Ichimoku Cloud added successfully');
        return this.ichimokuSeries;
    }

    removeIchimoku() {
        if (!this.ichimokuSeries) {
            return;
        }

        const chart = this.chartManager?.chart;
        if (!chart) {
            return;
        }

        // Remove all Ichimoku series
        try {
            if (this.ichimokuSeries.tenkan) chart.removeSeries(this.ichimokuSeries.tenkan);
            if (this.ichimokuSeries.kijun) chart.removeSeries(this.ichimokuSeries.kijun);
            if (this.ichimokuSeries.senkouA) chart.removeSeries(this.ichimokuSeries.senkouA);
            if (this.ichimokuSeries.senkouB) chart.removeSeries(this.ichimokuSeries.senkouB);
            if (this.ichimokuSeries.chikou) chart.removeSeries(this.ichimokuSeries.chikou);
        } catch (error) {
            console.error('[ChartUtils] Error removing Ichimoku series:', error);
        }

        this.ichimokuSeries = null;
        console.log('[ChartUtils] Ichimoku Cloud removed');
    }

    // ========================================
    // ChartUtilities Methods (Delegation)
    // ========================================

    handleCrosshairMove(param) {
        this.utilities.handleCrosshairMove(param);
    }

    setDrawingMode(mode) {
        this.utilities.setDrawingMode(mode);

        // Update backward compatibility property
        this.drawingMode = mode;
    }

    exportChart(format = 'png') {
        return this.utilities.exportChart(format);
    }

    // ========================================
    // Additional Helper Methods
    // ========================================

    /**
     * Get chart instance (backward compatibility)
     */
    getChart() {
        return this.chartManager.getChart();
    }

    /**
     * Get chart data (backward compatibility)
     */
    getChartData() {
        return this.chartManager.getChartData();
    }
}

// Global chart utilities instance
const chartUtils = new ChartUtils();

// Export to window
window.ChartUtils = ChartUtils;
window.chartUtils = chartUtils;

console.log('[ChartUtils] Phase 3 modularization complete - 4 modules loaded');
