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
