/**
 * IndicatorRenderer - Render technical indicators on chart
 * Handles adding/removing indicator series: MA, RSI, BB, MACD, SuperTrend
 */

class IndicatorRenderer {
    constructor(chartManager, calculator) {
        this.chartManager = chartManager;
        this.calculator = calculator;

        // Series references
        this.maSeries = { 20: null, 50: null, 100: null, 200: null };
        this.rsiChart = null;
        this.rsiSeries = null;
        this.upperBandSeries = null;
        this.middleBandSeries = null;
        this.lowerBandSeries = null;
        this.macdChart = null;
        this.macdLineSeries = null;
        this.macdSignalSeries = null;
        this.macdHistogramSeries = null;
        this.superTrendUpSeries = null;
        this.superTrendDownSeries = null;
        this.superTrendData = null;

        console.log('[IndicatorRenderer] Module initialized');
    }

    /**
     * Validate and filter series data to remove null/invalid values
     * @param {Array} data - Series data [{time, value}]
     * @returns {Array} Filtered data
     */
    validateSeriesData(data) {
        if (!Array.isArray(data)) {
            console.warn('[IndicatorRenderer] Invalid data type, expected array');
            return [];
        }

        const filtered = data.filter(point => {
            if (!point || typeof point !== 'object') return false;
            if (!point.time || typeof point.time !== 'number') return false;
            if (point.value === null || point.value === undefined) return false;
            if (typeof point.value !== 'number') return false;
            if (!Number.isFinite(point.value) || isNaN(point.value)) return false;
            return true;
        });

        if (filtered.length < data.length) {
            console.warn(`[IndicatorRenderer] Filtered out ${data.length - filtered.length} invalid data points`);
        }

        return filtered;
    }

    /**
     * Add Moving Average to chart
     * @param {number} period - MA period
     * @param {string} color - Line color (default: '#ff6b6b')
     * @returns {Object} MA series
     */
    addMovingAverage(period, color = '#ff6b6b') {
        const chart = this.chartManager.getChart();
        if (!chart) {
            console.warn('[IndicatorRenderer] Chart not available for MA');
            return null;
        }

        // Remove existing MA series
        if (this.maSeries[period]) {
            chart.removeSeries(this.maSeries[period]);
        }

        this.maSeries[period] = chart.addLineSeries({
            color: color,
            lineWidth: 2,
            title: `MA${period}`,
        });

        console.log(`[IndicatorRenderer] MA${period} series added`);
        return this.maSeries[period];
    }

    /**
     * Add RSI indicator (independent chart panel)
     * @param {Array} data - OHLC data
     * @param {number} period - RSI period (default: 14)
     * @param {string} color - Line color (default: '#ffa726')
     * @returns {Object} RSI series
     */
    addRSI(data, period = 14, color = '#ffa726') {
        console.log('[IndicatorRenderer] Creating RSI chart panel...');

        if (!data || !Array.isArray(data) || data.length < period + 1) {
            console.error('[IndicatorRenderer] Insufficient data for RSI');
            return null;
        }

        // Show RSI container
        const rsiContainer = document.getElementById('rsi-container');
        if (!rsiContainer) {
            console.error('[IndicatorRenderer] RSI container not found');
            return null;
        }
        rsiContainer.style.display = 'block';

        // Remove existing RSI chart
        if (this.rsiChart) {
            this.rsiChart.remove();
            this.rsiChart = null;
        }

        // Calculate RSI data
        const rsiData = this.calculator.calculateRSI(data, period);
        console.log('[IndicatorRenderer] RSI data calculated:', rsiData.length, 'points');

        if (rsiData.length === 0) {
            console.error('[IndicatorRenderer] Failed to calculate RSI data');
            rsiContainer.style.display = 'none';
            return null;
        }

        // Create RSI chart
        this.rsiChart = LightweightCharts.createChart(rsiContainer, {
            width: rsiContainer.clientWidth,
            height: 150,
            layout: {
                background: { color: '#131722' },
                textColor: '#d1d4dc',
                fontSize: 11,
                fontFamily: 'Trebuchet MS, Arial, sans-serif',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { color: '#2a2e39', style: 1 },
            },
            rightPriceScale: {
                borderColor: '#2a2e39',
                scaleMargins: { top: 0.1, bottom: 0.1 },
            },
            timeScale: {
                borderColor: '#2a2e39',
                visible: true,
                timeVisible: true,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
        });

        // Add RSI line series
        this.rsiSeries = this.rsiChart.addLineSeries({
            color: color,
            lineWidth: 2,
            title: `RSI${period}`,
            priceLineVisible: false,
            lastValueVisible: true,
        });

        const validRsiData = this.validateSeriesData(rsiData);
        if (validRsiData.length > 0) {
            this.rsiSeries.setData(validRsiData);
            console.log(`[IndicatorRenderer] RSI data set successfully (${validRsiData.length} points)`);
        } else {
            console.warn('[IndicatorRenderer] No valid RSI data to display');
        }

        // Synchronize timescale with main chart
        const mainChart = this.chartManager.getChart();
        if (mainChart) {
            mainChart.timeScale().subscribeVisibleTimeRangeChange(() => {
                const timeRange = mainChart.timeScale().getVisibleRange();
                if (timeRange && this.rsiChart) {
                    this.rsiChart.timeScale().setVisibleRange(timeRange);
                }
            });
            console.log('[IndicatorRenderer] RSI timescale synchronized');
        }

        console.log('[IndicatorRenderer] RSI chart panel created');
        return this.rsiSeries;
    }

    /**
     * Remove RSI indicator
     */
    removeRSI() {
        if (this.rsiSeries && this.rsiChart) {
            this.rsiChart.removeSeries(this.rsiSeries);
            this.rsiSeries = null;
        }
        if (this.rsiChart) {
            this.rsiChart.remove();
            this.rsiChart = null;
        }
        const rsiContainer = document.getElementById('rsi-container');
        if (rsiContainer) {
            rsiContainer.style.display = 'none';
        }
        console.log('[IndicatorRenderer] RSI chart removed');
    }

    /**
     * Add Bollinger Bands to chart
     * @param {Array} data - OHLC data
     * @param {number} period - BB period (default: 20)
     * @param {number} multiplier - Standard deviation multiplier (default: 2)
     * @returns {Object} BB series {upper, middle, lower}
     */
    addBollingerBands(data, period = 20, multiplier = 2) {
        console.log('[IndicatorRenderer] Adding Bollinger Bands:', period, multiplier);

        if (!data || data.length < period) {
            console.warn('[IndicatorRenderer] Insufficient data for BB');
            return null;
        }

        const chart = this.chartManager.getChart();
        if (!chart) {
            console.warn('[IndicatorRenderer] Chart not available for BB');
            return null;
        }

        // Remove existing BB
        this.removeBollingerBands();

        // Calculate BB data
        const bbData = this.calculator.calculateBollingerBands(data, period, multiplier);

        if (!bbData || bbData.upper.length === 0) {
            console.warn('[IndicatorRenderer] Failed to calculate BB');
            return null;
        }

        // Upper band (purple)
        this.upperBandSeries = chart.addLineSeries({
            color: '#9c27b0',
            lineWidth: 3,
            title: 'BB Upper',
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true,
        });
        const validUpperData = this.validateSeriesData(bbData.upper);
        if (validUpperData.length > 0) {
            this.upperBandSeries.setData(validUpperData);
        }

        // Middle band (orange)
        this.middleBandSeries = chart.addLineSeries({
            color: '#ff9800',
            lineWidth: 3,
            title: 'BB Middle',
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true,
        });
        const validMiddleData = this.validateSeriesData(bbData.middle);
        if (validMiddleData.length > 0) {
            this.middleBandSeries.setData(validMiddleData);
        }

        // Lower band (purple)
        this.lowerBandSeries = chart.addLineSeries({
            color: '#9c27b0',
            lineWidth: 3,
            title: 'BB Lower',
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true,
        });
        const validLowerData = this.validateSeriesData(bbData.lower);
        if (validLowerData.length > 0) {
            this.lowerBandSeries.setData(validLowerData);
        }

        console.log(`[IndicatorRenderer] Bollinger Bands added with ${bbData.upper.length} points`);
        return { upper: this.upperBandSeries, middle: this.middleBandSeries, lower: this.lowerBandSeries };
    }

    /**
     * Remove Bollinger Bands
     */
    removeBollingerBands() {
        const chart = this.chartManager.getChart();
        if (!chart) return;

        if (this.upperBandSeries) {
            chart.removeSeries(this.upperBandSeries);
            this.upperBandSeries = null;
        }
        if (this.middleBandSeries) {
            chart.removeSeries(this.middleBandSeries);
            this.middleBandSeries = null;
        }
        if (this.lowerBandSeries) {
            chart.removeSeries(this.lowerBandSeries);
            this.lowerBandSeries = null;
        }
        console.log('[IndicatorRenderer] Bollinger Bands removed');
    }

    /**
     * Add MACD indicator (independent chart panel)
     * @param {Array} data - OHLC data
     * @param {number} fastPeriod - Fast EMA period (default: 12)
     * @param {number} slowPeriod - Slow EMA period (default: 26)
     * @param {number} signalPeriod - Signal line period (default: 9)
     * @returns {Object} MACD series {macd, signal}
     */
    addMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        if (!data || data.length < slowPeriod + signalPeriod) {
            console.warn('[IndicatorRenderer] Insufficient data for MACD');
            return null;
        }

        console.log('[IndicatorRenderer] Creating MACD chart panel...');

        // Show MACD container
        const macdContainer = document.getElementById('macd-container');
        if (!macdContainer) {
            console.error('[IndicatorRenderer] MACD container not found');
            return null;
        }
        macdContainer.style.display = 'block';

        // Remove existing MACD chart
        if (this.macdChart) {
            this.macdChart.remove();
            this.macdChart = null;
        }

        // Calculate MACD
        const macdData = this.calculator.calculateMACD(data, fastPeriod, slowPeriod, signalPeriod);

        if (!macdData || macdData.macd.length === 0) {
            console.warn('[IndicatorRenderer] Failed to calculate MACD');
            return null;
        }

        // Create MACD chart
        this.macdChart = LightweightCharts.createChart(macdContainer, {
            width: macdContainer.clientWidth,
            height: 150,
            layout: {
                background: { color: '#131722' },
                textColor: '#d1d4dc',
                fontSize: 11,
                fontFamily: 'Trebuchet MS, Arial, sans-serif',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { color: '#2a2e39', style: 1 },
            },
            rightPriceScale: {
                borderColor: '#2a2e39',
                scaleMargins: { top: 0.1, bottom: 0.1 },
            },
            timeScale: {
                borderColor: '#2a2e39',
                visible: true,
                timeVisible: true,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
        });

        // Add MACD line (blue)
        this.macdLineSeries = this.macdChart.addLineSeries({
            color: '#2196f3',
            lineWidth: 2,
            title: 'MACD',
            priceLineVisible: false,
            lastValueVisible: true,
        });
        const validMacdData = this.validateSeriesData(macdData.macd);
        if (validMacdData.length > 0) {
            this.macdLineSeries.setData(validMacdData);
        }

        // Add Signal line (orange)
        this.macdSignalSeries = this.macdChart.addLineSeries({
            color: '#ff9800',
            lineWidth: 2,
            title: 'Signal',
            priceLineVisible: false,
            lastValueVisible: true,
        });
        const validSignalData = this.validateSeriesData(macdData.signal);
        if (validSignalData.length > 0) {
            this.macdSignalSeries.setData(validSignalData);
        }

        // NO HISTOGRAM (per user request)

        // Synchronize timescale with main chart
        const mainChart = this.chartManager.getChart();
        if (mainChart) {
            mainChart.timeScale().subscribeVisibleTimeRangeChange(() => {
                const timeRange = mainChart.timeScale().getVisibleRange();
                if (timeRange && this.macdChart) {
                    this.macdChart.timeScale().setVisibleRange(timeRange);
                }
            });
            console.log('[IndicatorRenderer] MACD timescale synchronized');
        }

        console.log(`[IndicatorRenderer] MACD chart created with ${macdData.macd.length} points (NO histogram)`);
        return { macd: this.macdLineSeries, signal: this.macdSignalSeries };
    }

    /**
     * Remove MACD indicator
     */
    removeMACD() {
        if (this.macdLineSeries && this.macdChart) {
            this.macdChart.removeSeries(this.macdLineSeries);
            this.macdLineSeries = null;
        }
        if (this.macdSignalSeries && this.macdChart) {
            this.macdChart.removeSeries(this.macdSignalSeries);
            this.macdSignalSeries = null;
        }
        if (this.macdChart) {
            this.macdChart.remove();
            this.macdChart = null;
        }
        const macdContainer = document.getElementById('macd-container');
        if (macdContainer) {
            macdContainer.style.display = 'none';
        }
        console.log('[IndicatorRenderer] MACD chart removed');
    }

    /**
     * Add SuperTrend indicator to chart
     * @param {Array} data - OHLC data
     * @param {number} period - ATR period (default: 10)
     * @param {number} multiplier - ATR multiplier (default: 3.0)
     * @returns {Object} SuperTrend series {upSeries, downSeries, data}
     */
    addSuperTrend(data, period = 10, multiplier = 3.0) {
        const chart = this.chartManager.getChart();
        if (!chart) {
            console.error('[IndicatorRenderer] Chart not available for SuperTrend');
            return null;
        }

        try {
            // Remove existing SuperTrend
            this.removeSuperTrend();

            // Calculate SuperTrend
            const stData = this.calculator.calculateSuperTrend(data, period, multiplier);

            // Up Trend line (green)
            this.superTrendUpSeries = chart.addLineSeries({
                color: '#26a69a',
                lineWidth: 2,
                title: 'SuperTrend Up',
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Down Trend line (red)
            this.superTrendDownSeries = chart.addLineSeries({
                color: '#ef5350',
                lineWidth: 2,
                title: 'SuperTrend Down',
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Filter out null values
            const upData = stData.upTrend.filter(p => p.value !== null);
            const downData = stData.downTrend.filter(p => p.value !== null);

            if (upData.length > 0) {
                this.superTrendUpSeries.setData(upData);
                console.log(`[IndicatorRenderer] SuperTrend Up: ${upData.length} points`);
            }

            if (downData.length > 0) {
                this.superTrendDownSeries.setData(downData);
                console.log(`[IndicatorRenderer] SuperTrend Down: ${downData.length} points`);
            }

            // Store trend data
            this.superTrendData = stData;

            console.log('[IndicatorRenderer] SuperTrend added successfully');
            return {
                upSeries: this.superTrendUpSeries,
                downSeries: this.superTrendDownSeries,
                data: stData
            };

        } catch (error) {
            console.error('[IndicatorRenderer] Error adding SuperTrend:', error);
            return null;
        }
    }

    /**
     * Remove SuperTrend indicator
     */
    removeSuperTrend() {
        const chart = this.chartManager.getChart();
        if (!chart) return;

        if (this.superTrendUpSeries) {
            chart.removeSeries(this.superTrendUpSeries);
            this.superTrendUpSeries = null;
            console.log('[IndicatorRenderer] SuperTrend Up removed');
        }

        if (this.superTrendDownSeries) {
            chart.removeSeries(this.superTrendDownSeries);
            this.superTrendDownSeries = null;
            console.log('[IndicatorRenderer] SuperTrend Down removed');
        }

        this.superTrendData = null;
    }

    /**
     * Get current SuperTrend signal
     * @returns {Object} {trend: 'UP'|'DOWN', signal: string, color: string}
     */
    getCurrentSuperTrendSignal() {
        if (!this.superTrendData || !this.superTrendData.trend || this.superTrendData.trend.length === 0) {
            return null;
        }

        const lastTrend = this.superTrendData.trend[this.superTrendData.trend.length - 1];
        return {
            trend: lastTrend.trend === 1 ? 'UP' : 'DOWN',
            signal: lastTrend.trend === 1 ? '매수' : '매도',
            color: lastTrend.trend === 1 ? '#26a69a' : '#ef5350'
        };
    }
}

// Export to window
if (typeof window !== 'undefined') {
    window.IndicatorRenderer = IndicatorRenderer;
}
