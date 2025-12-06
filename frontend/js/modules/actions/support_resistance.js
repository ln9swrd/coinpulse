/**
 * Support/Resistance Module
 * Handles support and resistance level calculation and visualization
 *
 * Features:
 * - Improved pivot point detection (5-candle lookback)
 * - ATR-based dynamic tolerance
 * - Level clustering and merging
 * - Time-weighted strength calculation
 * - Distance filtering
 * - Balanced support/resistance display
 */

class SupportResistance {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.enabled = false;
        this.lines = [];

        console.log('[SupportResistance] Module initialized');
    }

    /**
     * Toggle support/resistance display
     */
    toggle() {
        this.enabled = !this.enabled;
        this.updateToggleButton();

        if (this.enabled) {
            this.draw();
        } else {
            this.remove();
        }

        console.log('[SupportResistance] Toggled:', this.enabled);
    }

    /**
     * Calculate support/resistance levels
     */
    calculate() {
        if (!this.chart.chartData || this.chart.chartData.length < 50) {
            console.warn('[SupportResistance] Insufficient data (need at least 50 candles)');
            return [];
        }

        const lookback = 5;
        const levels = [];
        const currentPrice = this.chart.chartData[this.chart.chartData.length - 1].close;

        // Calculate ATR for dynamic tolerance
        const atr = this.calculateATR(14);
        const dynamicTolerance = atr > 0 ? (atr / currentPrice) : 0.015;

        console.log('[SupportResistance] Dynamic tolerance:', (dynamicTolerance * 100).toFixed(2) + '%', 'ATR:', atr.toFixed(2));

        // Find pivot points
        for (let i = lookback; i < this.chart.chartData.length - lookback; i++) {
            const candle = this.chart.chartData[i];
            let isResistance = true;
            let isSupport = true;

            // Check pivot high (resistance)
            for (let j = 1; j <= lookback; j++) {
                if (candle.high <= this.chart.chartData[i - j].high ||
                    candle.high <= this.chart.chartData[i + j].high) {
                    isResistance = false;
                    break;
                }
            }

            // Check pivot low (support)
            for (let j = 1; j <= lookback; j++) {
                if (candle.low >= this.chart.chartData[i - j].low ||
                    candle.low >= this.chart.chartData[i + j].low) {
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

        console.log('[SupportResistance] Found', levels.length, 'pivot points');

        // Merge similar levels
        const mergedLevels = this.mergeSimilarLevels(levels, dynamicTolerance);
        console.log('[SupportResistance] After merging:', mergedLevels.length, 'levels');

        // Calculate strength
        const allPrices = this.chart.chartData.map(c => [c.high, c.low]).flat();
        mergedLevels.forEach(level => {
            level.strength = this.calculateStrength(level.price, allPrices, dynamicTolerance, level.index);
            level.distanceFromCurrent = Math.abs(level.price - currentPrice) / currentPrice;
        });

        // Filter clustered levels
        const filteredLevels = this.filterClusteredLevels(mergedLevels, 0.03);
        console.log('[SupportResistance] After distance filter:', filteredLevels.length, 'levels');

        // Score and sort
        const scoredLevels = filteredLevels.map(level => ({
            ...level,
            score: level.strength * (1 + (1 - Math.min(level.distanceFromCurrent * 2, 1)))
        }));

        const sortedLevels = scoredLevels.sort((a, b) => b.score - a.score);

        // Balance support/resistance
        const supports = sortedLevels.filter(l => l.type === 'support').slice(0, 3);
        const resistances = sortedLevels.filter(l => l.type === 'resistance').slice(0, 3);
        const balancedLevels = [...supports, ...resistances]
            .sort((a, b) => b.score - a.score)
            .slice(0, 6);

        console.log('[SupportResistance] Final levels:', balancedLevels.map(l => ({
            type: l.type,
            price: l.price.toFixed(0),
            strength: l.strength,
            distance: (l.distanceFromCurrent * 100).toFixed(1) + '%'
        })));

        return balancedLevels;
    }

    /**
     * Draw support/resistance lines on chart
     */
    draw() {
        const lwChart = window.chartUtils?.chart;
        if (!lwChart || !this.chart.chartData || this.chart.chartData.length === 0) {
            console.warn('[SupportResistance] Cannot draw: missing data or chart');
            return;
        }

        try {
            this.remove();
            const levels = this.calculate();

            levels.forEach((level) => {
                this.drawHorizontalLine(level.price, level.type, level.strength);
            });

            console.log('[SupportResistance] Lines drawn successfully');
        } catch (error) {
            console.error('[SupportResistance] Failed to draw:', error);
        }
    }

    /**
     * Draw a single horizontal line
     */
    drawHorizontalLine(price, type, strength) {
        const lwChart = window.chartUtils?.chart;
        if (!lwChart) return;

        try {
            const color = type === 'support' ? '#26a69a' : '#ef5350';
            const lineWidth = Math.min(Math.max(strength / 5, 1), 3);

            const lineSeries = lwChart.addLineSeries({
                color: color,
                lineWidth: lineWidth,
                lineStyle: 2, // Dashed
                crosshairMarkerVisible: false,
                lastValueVisible: true,
                priceLineVisible: false,
                title: `${type === 'support' ? 'Support' : 'Resistance'}: ${price.toFixed(0)}`
            });

            const startTime = this.chart.chartData[0].time;
            const endTime = this.chart.chartData[this.chart.chartData.length - 1].time;

            lineSeries.setData([
                { time: startTime, value: price },
                { time: endTime, value: price }
            ]);

            this.lines.push({ lineSeries, price, type, strength });
        } catch (error) {
            console.error('[SupportResistance] Failed to draw line:', error);
        }
    }

    /**
     * Remove all support/resistance lines
     */
    remove() {
        const lwChart = window.chartUtils?.chart;
        if (!lwChart) return;

        this.lines.forEach(({ lineSeries }) => {
            try {
                if (lineSeries) {
                    lwChart.removeSeries(lineSeries);
                }
            } catch (error) {
                console.error('[SupportResistance] Failed to remove line:', error);
            }
        });

        this.lines = [];
        console.log('[SupportResistance] All lines removed');
    }

    /**
     * Calculate ATR (Average True Range)
     */
    calculateATR(period) {
        if (!this.chart.chartData || this.chart.chartData.length < period + 1) {
            return 0;
        }

        const trueRanges = [];
        for (let i = 1; i < this.chart.chartData.length; i++) {
            const current = this.chart.chartData[i];
            const previous = this.chart.chartData[i - 1];

            const tr = Math.max(
                current.high - current.low,
                Math.abs(current.high - previous.close),
                Math.abs(current.low - previous.close)
            );
            trueRanges.push(tr);
        }

        const recentTR = trueRanges.slice(-period);
        const atr = recentTR.reduce((sum, tr) => sum + tr, 0) / period;

        return atr;
    }

    /**
     * Merge similar levels (clustering)
     */
    mergeSimilarLevels(levels, tolerance) {
        if (levels.length === 0) return [];

        const merged = [];
        const used = new Set();

        levels.forEach((level, i) => {
            if (used.has(i)) return;

            const cluster = [level];
            used.add(i);

            for (let j = i + 1; j < levels.length; j++) {
                if (used.has(j)) continue;

                const other = levels[j];
                if (level.type === other.type &&
                    Math.abs(level.price - other.price) / level.price <= tolerance) {
                    cluster.push(other);
                    used.add(j);
                }
            }

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
    }

    /**
     * Filter levels that are too close together
     */
    filterClusteredLevels(levels, minDistance) {
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
    }

    /**
     * Calculate level strength with time weighting
     */
    calculateStrength(price, prices, tolerance, levelIndex) {
        const priceWithTolerance = price * tolerance;
        let strength = 0;
        const dataLength = this.chart.chartData.length;

        prices.forEach((p, idx) => {
            if (Math.abs(p - price) <= priceWithTolerance) {
                const candleIndex = Math.floor(idx / 2);
                const age = dataLength - candleIndex;
                const timeWeight = Math.exp(-age / (dataLength * 0.3));

                strength += (0.5 + timeWeight * 0.5);
            }
        });

        return strength;
    }

    /**
     * Update toggle button state
     */
    updateToggleButton() {
        const btn = document.getElementById('support-resistance-toggle');
        if (btn) {
            if (this.enabled) {
                btn.textContent = '지지저항선';
                btn.classList.add('active');
            } else {
                btn.textContent = '지지저항선';
                btn.classList.remove('active');
            }
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.SupportResistance = SupportResistance;
}
