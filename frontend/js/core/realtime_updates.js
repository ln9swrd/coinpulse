/**
 * ========================================
 * REALTIME UPDATES MODULE
 * ========================================
 * Handles real-time data updates and UI refresh
 * Uses delegation pattern - holds reference to chart instance
 *
 * @class RealtimeUpdates
 */

class RealtimeUpdates {
    constructor(chart) {
        this.chart = chart;
        console.log('[RealtimeUpdates] Module initialized');
    }

    /**
     * Validate MA data before passing to setData()
     * Filters out null, undefined, NaN, and non-finite values
     */
    validateMAData(data, period) {
        if (!Array.isArray(data)) {
            console.warn(`[RealtimeUpdates] MA${period}: Invalid data type, expected array`);
            return [];
        }

        const filtered = data.filter(point => {
            if (!point || typeof point !== 'object') return false;
            if (!point.time || typeof point.time !== 'number') return false;
            if (point.value === null || point.value === undefined) return false;
            if (typeof point.value !== 'number') return false;
            if (!Number.isFinite(point.value) || isNaN(point.value)) return false;
            if (point.value <= 0) return false; // MA values should be positive
            return true;
        });

        if (filtered.length < data.length) {
            console.warn(`[RealtimeUpdates] MA${period}: Filtered out ${data.length - filtered.length} invalid data points`);
        }

        return filtered;
    }

        startAutoUpdate() {
            if (this.chart.autoUpdateInterval) {
                clearInterval(this.chart.autoUpdateInterval);
            }
    
            // 30초마다 최신 데이터 업데이트 (더 빠른 갱신)
            this.chart.autoUpdateInterval = setInterval(() => {
                console.log('[Working] Auto update triggered');
                this.chart.dataLoader.loadLatestData();
            }, 30000);
    
            console.log('[Working] Auto update started (30s interval)');
        }

        stopAutoUpdate() {
            if (this.chart.autoUpdateInterval) {
                clearInterval(this.chart.autoUpdateInterval);
                this.chart.autoUpdateInterval = null;
                console.log('[Working] Auto update stopped');
            }
        }

        updatePriceInfo() {
            console.log('[Working] Updating price info header...');
    
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[Working] No data for price info update');
                return;
            }
    
            // Timeframe 표시 텍스트
            const timeframeText = {
                'minutes': this.chart.currentUnit ? `${this.chart.currentUnit}분봉` : '분봉',
                'days': '일봉',
                'weeks': '주봉',
                'months': '월봉'
            };
    
            // 코인 이름 가져오기 (selectbox에서)
            const coinSelect = document.getElementById('coin-select');
            let coinName = '비트코인';
            if (coinSelect && coinSelect.selectedOptions.length > 0) {
                const selectedOption = coinSelect.selectedOptions[0];
                coinName = selectedOption.dataset.koreanName || selectedOption.textContent.split('(')[0].trim();
            }
    
            // DOM 업데이트 - 코인 이름과 캔들 타입만 표시
            const coinNameEl = document.getElementById('coin-name');
            const candleTypeEl = document.getElementById('candle-type');
            const updateTimeEl = document.getElementById('update-time');
    
            if (coinNameEl) {
                coinNameEl.textContent = coinName;
            }
    
            if (candleTypeEl) {
                candleTypeEl.textContent = timeframeText[this.chart.currentTimeframe] || '일봉';
            }
    
            if (updateTimeEl) {
                const now = new Date();
                const timeString = now.toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                });
                updateTimeEl.textContent = timeString;
            }
    
            // MA 값 업데이트
            this.updateMAValues();
    
            console.log('[Working] Price info updated');
        }

        updateMAValues() {
            // Use MovingAverages module if available
            if (this.chart.movingAverages) {
                this.chart.movingAverages.updateMAValues();
                return;
            }
    
            // Fallback
            if (!this.chart.chartData || this.chart.chartData.length === 0) return;
    
            const maConfigs = [
                { period: 20, id: 'ma20-value' },
                { period: 50, id: 'ma50-value' },
                { period: 100, id: 'ma100-value' },
                { period: 200, id: 'ma200-value' }
            ];
    
            maConfigs.forEach(({ period, id }) => {
                try {
                    const maData = window.chartUtils.calculateMovingAverage(this.chart.chartData, period);
                    if (maData.length > 0) {
                        const latestMA = maData[maData.length - 1];
                        const maValueEl = document.getElementById(id);
                        if (maValueEl && latestMA && !isNaN(latestMA.value)) {
                            maValueEl.textContent = latestMA.value.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
                        }
                    }
                } catch (error) {
                    console.error(`[Working] MA${period} value update failed:`, error);
                }
            });
        }

        updateRealTimeAnalysis() {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[Working] No data for real-time analysis');
                return;
            }
    
            try {
                // 1. Update RSI values and status (if TechnicalIndicators module available)
                if (this.chart.technicalIndicators) {
                    const rsiData = window.chartUtils.calculateRSI(this.chart.chartData, 14);
                    if (rsiData && rsiData.length > 0) {
                        this.chart.technicalIndicators.updateRSIInfo(rsiData);
                    }
                }
    
                // 2. Update trend direction (based on MA20 vs current price)
                this.updateTrendDirection();
    
                // 3. Update volatility (based on ATR)
                this.updateVolatility();
    
                // 4. Update support/resistance levels
                this.updateSupportResistanceLevels();
    
                console.log('[Working] Real-time analysis updated');
            } catch (error) {
                console.error('[Working] Error updating real-time analysis:', error);
            }
        }

        updateTrendDirection() {
            try {
                const trendEl = document.getElementById('trend-direction');
                if (!trendEl) return;
    
                const latestCandle = this.chart.chartData[this.chart.chartData.length - 1];
                const ma20Data = window.chartUtils.calculateMovingAverage(this.chart.chartData, 20);
                const ma50Data = window.chartUtils.calculateMovingAverage(this.chart.chartData, 50);
    
                if (ma20Data.length === 0 || ma50Data.length === 0) {
                    trendEl.textContent = '중립';
                    trendEl.className = 'trend-value neutral';
                    return;
                }
    
                const currentPrice = latestCandle.close;
                const ma20 = ma20Data[ma20Data.length - 1].value;
                const ma50 = ma50Data[ma50Data.length - 1].value;
    
                // Determine trend: price > MA20 > MA50 = uptrend, price < MA20 < MA50 = downtrend
                if (currentPrice > ma20 && ma20 > ma50) {
                    trendEl.textContent = '상승';
                    trendEl.className = 'trend-value uptrend';
                } else if (currentPrice < ma20 && ma20 < ma50) {
                    trendEl.textContent = '하락';
                    trendEl.className = 'trend-value downtrend';
                } else {
                    trendEl.textContent = '중립';
                    trendEl.className = 'trend-value neutral';
                }
            } catch (error) {
                console.error('[Working] Error updating trend direction:', error);
            }
        }

        updateVolatility() {
            try {
                const volatilityEl = document.getElementById('volatility-level');
                if (!volatilityEl) return;
    
                // Calculate ATR (Average True Range) for last 14 periods
                const atrData = window.chartUtils.calculateATR(this.chart.chartData, 14);
                if (!atrData || atrData.length === 0) {
                    volatilityEl.textContent = '중간';
                    volatilityEl.className = 'volatility-value medium';
                    return;
                }
    
                const latestATR = atrData[atrData.length - 1].value;
                const latestPrice = this.chart.chartData[this.chart.chartData.length - 1].close;
                const atrPercent = (latestATR / latestPrice) * 100;
    
                // Categorize volatility based on ATR percentage
                if (atrPercent > 3) {
                    volatilityEl.textContent = '높음';
                    volatilityEl.className = 'volatility-value high';
                } else if (atrPercent > 1.5) {
                    volatilityEl.textContent = '중간';
                    volatilityEl.className = 'volatility-value medium';
                } else {
                    volatilityEl.textContent = '낮음';
                    volatilityEl.className = 'volatility-value low';
                }
            } catch (error) {
                console.error('[Working] Error updating volatility:', error);
            }
        }

        updateSupportResistanceLevels() {
            try {
                const supportEl = document.getElementById('support-level');
                const resistanceEl = document.getElementById('resistance-level');
    
                if (!supportEl || !resistanceEl) return;
    
                // Use SupportResistance module if available
                if (this.chart.supportResistance) {
                    const levels = this.chart.supportResistance.calculate();
                    if (levels && levels.length > 0) {
                        const currentPrice = this.chart.chartData[this.chart.chartData.length - 1].close;
    
                        // Find nearest support (below current price)
                        const supports = levels
                            .filter(l => l.price < currentPrice)
                            .sort((a, b) => b.price - a.price);
    
                        // Find nearest resistance (above current price)
                        const resistances = levels
                            .filter(l => l.price > currentPrice)
                            .sort((a, b) => a.price - b.price);
    
                        if (supports.length > 0) {
                            supportEl.textContent = '₩' + supports[0].price.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
                        } else {
                            supportEl.textContent = '없음';
                        }
    
                        if (resistances.length > 0) {
                            resistanceEl.textContent = '₩' + resistances[0].price.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
                        } else {
                            resistanceEl.textContent = '없음';
                        }
    
                        return;
                    }
                }
    
                // Fallback: simple calculation based on recent high/low
                const recentData = this.chart.chartData.slice(-20);
                const highs = recentData.map(d => d.high);
                const lows = recentData.map(d => d.low);
    
                const support = Math.min(...lows);
                const resistance = Math.max(...highs);
    
                supportEl.textContent = '₩' + support.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
                resistanceEl.textContent = '₩' + resistance.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
    
            } catch (error) {
                console.error('[Working] Error updating support/resistance levels:', error);
            }
        }

        updateMAs() {
            // Use MovingAverages module if available
            if (this.chart.movingAverages) {
                this.chart.movingAverages.updateMAs();
                this.chart.maSeries = this.chart.movingAverages.maSeries;
                return;
            }
    
            // Fallback
            console.log('[Working] Updating MA lines with settings:', this.chart.maSettings);
            if (!this.chart.movingAveragesVisible) {
                this.chart.clearMAs();
                console.log('[Working] MAs are hidden by policy; skipping update');
                return;
            }
    
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[Working] No data for MA update');
                return;
            }
    
            const maConfigs = [
                { period: 20, key: 'ma20', color: '#ff6b6b' },
                { period: 50, key: 'ma50', color: '#4ecdc4' },
                { period: 100, key: 'ma100', color: '#45b7d1' },
                { period: 200, key: 'ma200', color: '#96ceb4' },
                { period: 300, key: 'ma300', color: '#feca57' },
                { period: 500, key: 'ma500', color: '#ff9ff3' },
                { period: 1000, key: 'ma1000', color: '#54a0ff' }
            ];
    
            maConfigs.forEach(({ period, key, color }) => {
                try {
                    const isEnabled = this.chart.maSettings[period];
    
                    // If MA is disabled, remove it
                    if (!isEnabled) {
                        if (this.chart.maSeries[key]) {
                            window.chartUtils.chart.removeSeries(this.chart.maSeries[key]);
                            this.chart.maSeries[key] = null;
                            console.log(`[Working] MA${period} removed`);
                        }
                        return;
                    }
    
                    // If MA is enabled, calculate and show it
                    const maData = window.chartUtils.calculateMovingAverage(this.chart.chartData, period);

                    // Validate MA data before setData()
                    const validMaData = this.validateMAData(maData, period);

                    if (validMaData.length === 0) {
                        console.warn(`[Working] MA${period} has no valid data`);
                        return;
                    }

                    // Create series if it doesn't exist
                    if (!this.chart.maSeries[key]) {
                        this.chart.maSeries[key] = window.chartUtils.chart.addLineSeries({
                            color: color,
                            lineWidth: 2,
                            title: `MA${period}`,
                            priceLineVisible: false,
                            lastValueVisible: true
                        });
                        console.log(`[Working] MA${period} series created`);
                    }

                    // Update data with validated data
                    this.chart.maSeries[key].setData(validMaData);
                    console.log(`[Working] MA${period} updated with ${validMaData.length} valid values`);
    
                } catch (error) {
                    console.error(`[Working] MA${period} update failed:`, error);
                }
            });
    
            console.log('[Working] MA update completed');
        }

}

// Export for module usage
if (typeof window !== 'undefined') {
    window.RealtimeUpdates = RealtimeUpdates;
}
