/**
 * IndicatorCalculator - Technical indicator calculations
 * Pure calculation functions for MA, RSI, Bollinger Bands, MACD, ATR, SuperTrend
 */

class IndicatorCalculator {
    constructor() {
        console.log('[IndicatorCalculator] Module initialized');
    }

    /**
     * Calculate Simple Moving Average (SMA)
     * @param {Array} data - OHLC data
     * @param {number} period - MA period
     * @returns {Array} MA data [{time, value}]
     */
    calculateMovingAverage(data, period) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            console.warn('[IndicatorCalculator] Invalid data for MA');
            return [];
        }

        if (period <= 0 || period > data.length) {
            console.warn(`[IndicatorCalculator] Invalid MA period ${period} for data length ${data.length}`);
            return [];
        }

        const result = [];
        for (let i = period - 1; i < data.length; i++) {
            const slice = data.slice(i - period + 1, i + 1);
            const validItems = slice.filter(item => item && typeof item.close === 'number' && !isNaN(item.close) && Number.isFinite(item.close));

            if (validItems.length === period) {
                const sum = validItems.reduce((acc, item) => acc + item.close, 0);
                const maValue = sum / period;

                if (maValue !== null && maValue !== undefined && !isNaN(maValue) && Number.isFinite(maValue) && maValue > 0) {
                    result.push({
                        time: data[i].time,
                        value: maValue
                    });
                }
            }
        }
        console.log(`[IndicatorCalculator] MA${period}: Generated ${result.length} values from ${data.length} data points`);
        return result;
    }

    /**
     * Calculate Relative Strength Index (RSI)
     * @param {Array} data - OHLC data
     * @param {number} period - RSI period (default: 14)
     * @returns {Array} RSI data [{time, value}]
     */
    calculateRSI(data, period = 14) {
        if (!data || !Array.isArray(data) || data.length < period + 1) {
            console.warn('[IndicatorCalculator] Insufficient data for RSI');
            return [];
        }

        const result = [];
        const gains = [];
        const losses = [];

        for (let i = 1; i < data.length; i++) {
            if (!data[i] || !data[i - 1] || typeof data[i].close !== 'number' || typeof data[i - 1].close !== 'number') {
                continue;
            }
            const change = data[i].close - data[i - 1].close;
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? -change : 0);
        }

        for (let i = period - 1; i < gains.length; i++) {
            const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
            const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;

            const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
            const rsi = 100 - (100 / (1 + rs));

            if (rsi !== null && rsi !== undefined && !isNaN(rsi) && Number.isFinite(rsi) && rsi >= 0 && rsi <= 100) {
                result.push({
                    time: data[i + 1].time,
                    value: rsi
                });
            }
        }

        console.log(`[IndicatorCalculator] RSI${period}: Generated ${result.length} values from ${data.length} data points`);
        return result;
    }

    /**
     * Calculate Bollinger Bands
     * @param {Array} data - OHLC data
     * @param {number} period - BB period (default: 20)
     * @param {number} multiplier - Standard deviation multiplier (default: 2)
     * @returns {Object} BB data {upper: [], middle: [], lower: []}
     */
    calculateBollingerBands(data, period = 20, multiplier = 2) {
        if (!data || !Array.isArray(data) || data.length < period) {
            console.warn('[IndicatorCalculator] Insufficient data for Bollinger Bands');
            return { upper: [], middle: [], lower: [] };
        }

        const result = { upper: [], middle: [], lower: [] };

        for (let i = period - 1; i < data.length; i++) {
            const slice = data.slice(i - period + 1, i + 1);
            const validItems = slice.filter(item => item && typeof item.close === 'number' && !isNaN(item.close) && Number.isFinite(item.close));

            if (validItems.length !== period) {
                continue;
            }

            const sma = validItems.reduce((sum, item) => sum + item.close, 0) / period;
            const variance = validItems.reduce((sum, item) => sum + Math.pow(item.close - sma, 2), 0) / period;
            const stdDev = Math.sqrt(variance);

            const upperValue = sma + (stdDev * multiplier);
            const middleValue = sma;
            const lowerValue = sma - (stdDev * multiplier);

            if (upperValue !== null && !isNaN(upperValue) && Number.isFinite(upperValue) &&
                middleValue !== null && !isNaN(middleValue) && Number.isFinite(middleValue) &&
                lowerValue !== null && !isNaN(lowerValue) && Number.isFinite(lowerValue)) {

                result.upper.push({ time: data[i].time, value: upperValue });
                result.middle.push({ time: data[i].time, value: middleValue });
                result.lower.push({ time: data[i].time, value: lowerValue });
            }
        }

        console.log(`[IndicatorCalculator] BB(${period},${multiplier}): Generated ${result.upper.length} values from ${data.length} data points`);
        return result;
    }

    /**
     * Calculate Exponential Moving Average (EMA)
     * @param {Array} data - Data array with close prices
     * @param {number} period - EMA period
     * @returns {Array} EMA data [{time, value}]
     */
    calculateEMA(data, period) {
        const k = 2 / (period + 1);
        const emaArray = [];
        let ema = data[0].close;

        for (let i = 0; i < data.length; i++) {
            if (i === 0) {
                if (Number.isFinite(ema) && !isNaN(ema)) {
                    emaArray.push({ time: data[i].time, value: ema });
                }
            } else {
                ema = (data[i].close * k) + (ema * (1 - k));
                if (Number.isFinite(ema) && !isNaN(ema)) {
                    emaArray.push({ time: data[i].time, value: ema });
                }
            }
        }
        return emaArray;
    }

    /**
     * Calculate MACD (Moving Average Convergence Divergence)
     * @param {Array} data - OHLC data
     * @param {number} fastPeriod - Fast EMA period (default: 12)
     * @param {number} slowPeriod - Slow EMA period (default: 26)
     * @param {number} signalPeriod - Signal line period (default: 9)
     * @returns {Object} MACD data {macd: [], signal: [], histogram: []}
     */
    calculateMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        if (!data || !Array.isArray(data) || data.length < slowPeriod + signalPeriod) {
            console.warn('[IndicatorCalculator] Insufficient data for MACD');
            return { macd: [], signal: [], histogram: [] };
        }

        // Filter valid data
        const validData = data.filter(item =>
            item &&
            item.time != null &&
            typeof item.close === 'number' &&
            !isNaN(item.close) &&
            Number.isFinite(item.close)
        );

        if (validData.length < slowPeriod + signalPeriod) {
            console.warn('[IndicatorCalculator] Insufficient valid data for MACD after filtering');
            return { macd: [], signal: [], histogram: [] };
        }

        // Calculate Fast and Slow EMA
        const fastEMA = this.calculateEMA(validData, fastPeriod);
        const slowEMA = this.calculateEMA(validData, slowPeriod);

        // Calculate MACD Line (Fast EMA - Slow EMA)
        const macdLine = [];
        const minLength = Math.min(fastEMA.length, slowEMA.length, validData.length);
        for (let i = 0; i < minLength; i++) {
            const macdValue = fastEMA[i].value - slowEMA[i].value;
            if (Number.isFinite(macdValue) && !isNaN(macdValue)) {
                macdLine.push({ time: validData[i].time, value: macdValue });
            }
        }

        // Calculate Signal Line (EMA of MACD Line)
        const signalLine = this.calculateEMA(macdLine.map((item, idx) => ({
            time: item.time,
            close: item.value
        })), signalPeriod);

        // Calculate Histogram (MACD - Signal)
        const histogram = [];
        const histMinLength = Math.min(macdLine.length, signalLine.length);
        for (let i = 0; i < histMinLength; i++) {
            const histValue = macdLine[i].value - signalLine[i].value;
            if (Number.isFinite(histValue) && !isNaN(histValue)) {
                histogram.push({
                    time: macdLine[i].time,
                    value: histValue,
                    color: histValue >= 0 ? '#26a69a' : '#ef5350'
                });
            }
        }

        const result = {
            macd: macdLine,
            signal: signalLine,
            histogram: histogram
        };

        console.log(`[IndicatorCalculator] MACD(${fastPeriod},${slowPeriod},${signalPeriod}): Generated ${macdLine.length} values from ${data.length} data points`);
        return result;
    }

    /**
     * Calculate Average True Range (ATR)
     * @param {Array} data - OHLC data
     * @param {number} period - ATR period (default: 14)
     * @returns {Array} ATR data [{time, value}]
     */
    calculateATR(data, period = 14) {
        if (!data || !Array.isArray(data) || data.length < period + 1) {
            console.warn('[IndicatorCalculator] Insufficient data for ATR');
            return [];
        }

        const trueRanges = [];

        // Calculate True Range
        for (let i = 1; i < data.length; i++) {
            const high = data[i].high;
            const low = data[i].low;
            const prevClose = data[i - 1].close;

            const tr1 = high - low;
            const tr2 = Math.abs(high - prevClose);
            const tr3 = Math.abs(low - prevClose);

            const trueRange = Math.max(tr1, tr2, tr3);
            trueRanges.push(trueRange);
        }

        // Calculate ATR using Wilder's Smoothing Method
        const atrValues = [];
        let atr = 0;

        // First ATR is simple average
        for (let i = 0; i < period; i++) {
            atr += trueRanges[i];
        }
        atr = atr / period;
        atrValues.push({ time: data[period].time, value: atr });

        // Subsequent ATRs use Wilder's smoothing
        for (let i = period; i < trueRanges.length; i++) {
            atr = ((atr * (period - 1)) + trueRanges[i]) / period;
            atrValues.push({ time: data[i + 1].time, value: atr });
        }

        console.log(`[IndicatorCalculator] ATR${period}: Generated ${atrValues.length} values from ${data.length} data points`);
        return atrValues;
    }

    /**
     * Calculate SuperTrend indicator
     * @param {Array} data - OHLC data
     * @param {number} period - ATR period (default: 10)
     * @param {number} multiplier - ATR multiplier (default: 3.0)
     * @returns {Object} SuperTrend data {upTrend: [], downTrend: [], trend: []}
     */
    calculateSuperTrend(data, period = 10, multiplier = 3.0) {
        if (!data || !Array.isArray(data) || data.length < period + 1) {
            console.warn('[IndicatorCalculator] Insufficient data for SuperTrend');
            return { upTrend: [], downTrend: [], trend: [] };
        }

        console.log(`[IndicatorCalculator] Calculating SuperTrend: period=${period}, multiplier=${multiplier}`);

        // Calculate ATR
        const atrValues = this.calculateATR(data, period);

        const upTrend = [];
        const downTrend = [];
        const trendDirection = [];

        let prevUpTrend = 0;
        let prevDownTrend = 0;
        let prevTrend = 1; // Default: uptrend

        for (let i = 0; i < atrValues.length; i++) {
            const dataIndex = i + period;
            const candle = data[dataIndex];
            const atr = atrValues[i].value;

            // HL/2 (High + Low) / 2
            const hl2 = (candle.high + candle.low) / 2;

            // Basic Upper Band = HL/2 + (Multiplier × ATR)
            // Basic Lower Band = HL/2 - (Multiplier × ATR)
            const basicUpperBand = hl2 + (multiplier * atr);
            const basicLowerBand = hl2 - (multiplier * atr);

            // Final Upper Band
            let finalUpperBand = basicUpperBand;
            if (i > 0 && (basicUpperBand < prevUpTrend || data[dataIndex - 1].close > prevUpTrend)) {
                finalUpperBand = basicUpperBand;
            } else if (i > 0) {
                finalUpperBand = prevUpTrend;
            }

            // Final Lower Band
            let finalLowerBand = basicLowerBand;
            if (i > 0 && (basicLowerBand > prevDownTrend || data[dataIndex - 1].close < prevDownTrend)) {
                finalLowerBand = basicLowerBand;
            } else if (i > 0) {
                finalLowerBand = prevDownTrend;
            }

            // Trend Direction
            let trend = prevTrend;
            if (i > 0) {
                if (prevTrend === 1) {
                    // Uptrend -> check if price falls below lower band
                    if (candle.close <= finalLowerBand) {
                        trend = -1;
                    }
                } else {
                    // Downtrend -> check if price rises above upper band
                    if (candle.close >= finalUpperBand) {
                        trend = 1;
                    }
                }
            }

            // SuperTrend value
            const superTrend = trend === 1 ? finalLowerBand : finalUpperBand;

            if (trend === 1) {
                upTrend.push({ time: candle.time, value: superTrend });
                downTrend.push({ time: candle.time, value: null });
            } else {
                upTrend.push({ time: candle.time, value: null });
                downTrend.push({ time: candle.time, value: superTrend });
            }

            trendDirection.push({ time: candle.time, trend: trend });

            prevUpTrend = finalUpperBand;
            prevDownTrend = finalLowerBand;
            prevTrend = trend;
        }

        console.log(`[IndicatorCalculator] SuperTrend: Generated ${upTrend.length} data points`);
        console.log(`[IndicatorCalculator] Up trend points: ${upTrend.filter(p => p.value !== null).length}`);
        console.log(`[IndicatorCalculator] Down trend points: ${downTrend.filter(p => p.value !== null).length}`);

        return {
            upTrend: upTrend,
            downTrend: downTrend,
            trend: trendDirection
        };
    }
}

// Export to window
if (typeof window !== 'undefined') {
    window.IndicatorCalculator = IndicatorCalculator;
}
