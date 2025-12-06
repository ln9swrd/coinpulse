/**
 * Technical Indicators Module
 * Handles RSI, MACD, Bollinger Bands, and SuperTrend indicators
 *
 * Features:
 * - RSI (Relative Strength Index) with visual status
 * - MACD (Moving Average Convergence Divergence)
 * - Bollinger Bands (BB)
 * - SuperTrend indicator
 * - Independent toggle for each indicator
 * - Real-time signal analysis
 */

class TechnicalIndicators {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.rsiSeries = null;
        this.macdSeries = {
            macd: null,
            signal: null,
            histogram: null
        };
        this.bbSeries = {
            upper: null,
            middle: null,
            lower: null
        };

        console.log('[TechnicalIndicators] Module initialized');
    }

    /**
     * Toggle RSI indicator
     */
    toggleRSI() {
        try {
            const btn = document.getElementById('rsi-toggle');
            if (!btn) {
                console.warn('[TechnicalIndicators] RSI button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                this.hideRSI();
                btn.classList.remove('active');
            } else {
                this.showRSI();
                btn.classList.add('active');
            }

            console.log('[TechnicalIndicators] RSI toggled:', !isActive);
        } catch (error) {
            console.error('[TechnicalIndicators] Error in toggleRSI:', error);
        }
    }

    /**
     * Show RSI indicator
     */
    showRSI() {
        try {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[TechnicalIndicators] No chart data for RSI');
                return;
            }

            // Use chart_utils.js addRSI method to create independent RSI chart
            console.log('[TechnicalIndicators] Creating independent RSI chart...');
            this.rsiSeries = window.chartUtils.addRSI(this.chart.chartData, 14, '#9C27B0');

            if (!this.rsiSeries) {
                console.warn('[TechnicalIndicators] Failed to create RSI chart');
                return;
            }

            console.log('[TechnicalIndicators] RSI chart created successfully');

            // Resize main chart to accommodate RSI panel
            this.resizeMainChart();

            // Calculate RSI data for info display
            const rsiData = window.chartUtils.calculateRSI(this.chart.chartData, 14);

            // Update RSI info display
            if (rsiData && rsiData.length > 0) {
                this.updateRSIInfo(rsiData);
            }
        } catch (error) {
            console.error('[TechnicalIndicators] Error in showRSI:', error);
        }
    }

    /**
     * Hide RSI indicator
     */
    hideRSI() {
        try {
            // Remove RSI chart using chart_utils
            if (window.chartUtils && window.chartUtils.rsiChart) {
                window.chartUtils.rsiChart.remove();
                window.chartUtils.rsiChart = null;
                console.log('[TechnicalIndicators] RSI chart removed');
            }

            // Hide RSI container
            const rsiContainer = document.getElementById('rsi-container');
            if (rsiContainer) {
                rsiContainer.style.display = 'none';
            }

            // Reset series reference
            this.rsiSeries = null;

            // Reset RSI info panel
            const rsiInfo = document.getElementById('rsi-status');
            const rsiValue = document.getElementById('rsi-value');
            if (rsiInfo && rsiValue) {
                rsiInfo.textContent = '-';
                rsiValue.textContent = '-';
                rsiInfo.style.cssText = '';
                rsiValue.style.cssText = '';
            }

            console.log('[TechnicalIndicators] RSI hidden successfully');

            // Resize main chart
            this.resizeMainChart();
        } catch (error) {
            console.error('[TechnicalIndicators] Error in hideRSI:', error);
        }
    }

    /**
     * Update RSI info display with visual signals
     */
    updateRSIInfo(rsiData) {
        if (!rsiData || rsiData.length === 0) return;

        try {
            const latestRSI = rsiData[rsiData.length - 1];
            const rsiValue = document.getElementById('rsi-value');
            const rsiStatus = document.getElementById('rsi-status');
            const tradingSignal = document.getElementById('trading-signal');

            if (!rsiValue || !latestRSI) return;

            rsiValue.textContent = latestRSI.value.toFixed(1);

            let statusText = '';
            let signalText = '';
            let backgroundColor = '';
            let textColor = '';

            if (rsiStatus) {
                // Determine RSI status and signals
                if (latestRSI.value >= 80) {
                    statusText = '🔥 극심한 과매수';
                    signalText = '강한 매도 신호 (조정 임박)';
                    backgroundColor = '#ff1744';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 70) {
                    statusText = '⚠️ 과매수';
                    signalText = '매도 고려 (고점 근처)';
                    backgroundColor = '#ff9800';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 60) {
                    statusText = '📈 강세';
                    signalText = '상승세 유지';
                    backgroundColor = '#4caf50';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 40) {
                    statusText = '⏸️ 중립';
                    signalText = '대기 (방향 불명)';
                    backgroundColor = '#9e9e9e';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 30) {
                    statusText = '📉 약세';
                    signalText = '하락세 지속';
                    backgroundColor = '#f44336';
                    textColor = '#ffffff';
                } else if (latestRSI.value >= 20) {
                    statusText = '⚠️ 과매도';
                    signalText = '매수 고려 (저점 근처)';
                    backgroundColor = '#ff9800';
                    textColor = '#ffffff';
                } else {
                    statusText = '💎 극심한 과매도';
                    signalText = '강한 매수 신호 (반등 가능)';
                    backgroundColor = '#00e676';
                    textColor = '#000000';
                }

                rsiStatus.textContent = statusText;
                rsiStatus.style.cssText = `
                    background-color: ${backgroundColor};
                    color: ${textColor};
                    padding: 6px 16px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    transition: all 0.3s ease;
                    border: 2px solid ${backgroundColor};
                    text-transform: uppercase;
                `;

                // Add pulse animation for extreme zones
                if (latestRSI.value >= 80 || latestRSI.value <= 20) {
                    rsiStatus.style.animation = 'pulse 1.5s infinite';
                } else {
                    rsiStatus.style.animation = 'none';
                }

                // Style RSI value
                rsiValue.style.cssText = `
                    font-size: 22px;
                    font-weight: bold;
                    color: ${backgroundColor};
                    text-shadow: 0 2px 4px ${backgroundColor}40;
                `;

                // Update trading signal
                if (tradingSignal) {
                    tradingSignal.textContent = signalText;
                    tradingSignal.style.cssText = `
                        font-size: 15px;
                        padding: 4px 12px;
                        border-radius: 6px;
                        transition: all 0.3s ease;
                        display: inline-block;
                        margin-top: 4px;
                        color: ${textColor};
                        background-color: ${backgroundColor};
                        font-weight: ${latestRSI.value >= 70 || latestRSI.value <= 30 ? 'bold' : '500'};
                        box-shadow: 0 2px 8px ${backgroundColor}66;
                    `;
                }

                console.log(`[TechnicalIndicators] RSI: ${latestRSI.value.toFixed(1)} | ${statusText}`);
            }
        } catch (error) {
            console.error('[TechnicalIndicators] Error in updateRSIInfo:', error);
        }
    }

    /**
     * Toggle MACD indicator
     */
    toggleMACD() {
        try {
            const btn = document.getElementById('macd-toggle');
            if (!btn) {
                console.warn('[TechnicalIndicators] MACD button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                this.hideMACD();
                btn.classList.remove('active');
            } else {
                this.showMACD();
                btn.classList.add('active');
            }

            console.log('[TechnicalIndicators] MACD toggled:', !isActive);
        } catch (error) {
            console.error('[TechnicalIndicators] Error in toggleMACD:', error);
        }
    }

    /**
     * Show MACD indicator
     */
    showMACD() {
        try {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[TechnicalIndicators] No chart data for MACD');
                return;
            }

            // Use chart_utils.js addMACD method to create independent MACD chart
            console.log('[TechnicalIndicators] Creating independent MACD chart...');
            const macdSeries = window.chartUtils.addMACD(this.chart.chartData, 12, 26, 9);

            if (!macdSeries) {
                console.warn('[TechnicalIndicators] Failed to create MACD chart');
                return;
            }

            // Store reference to MACD series
            this.macdSeries = macdSeries;

            console.log('[TechnicalIndicators] MACD chart created successfully');

            // Resize main chart to accommodate MACD panel
            this.resizeMainChart();
        } catch (error) {
            console.error('[TechnicalIndicators] Error in showMACD:', error);
        }
    }

    /**
     * Hide MACD indicator
     */
    hideMACD() {
        try {
            // Remove MACD chart using chart_utils
            if (window.chartUtils && window.chartUtils.macdChart) {
                window.chartUtils.macdChart.remove();
                window.chartUtils.macdChart = null;
                console.log('[TechnicalIndicators] MACD chart removed');
            }

            // Hide MACD container
            const macdContainer = document.getElementById('macd-container');
            if (macdContainer) {
                macdContainer.style.display = 'none';
            }

            // Reset series reference
            this.macdSeries = {
                macd: null,
                signal: null,
                histogram: null
            };

            console.log('[TechnicalIndicators] MACD hidden successfully');

            // Resize main chart
            this.resizeMainChart();
        } catch (error) {
            console.error('[TechnicalIndicators] Error in hideMACD:', error);
        }
    }

    /**
     * Toggle Bollinger Bands
     */
    toggleBollingerBands() {
        try {
            const btn = document.getElementById('bollinger-toggle');
            if (!btn) {
                console.warn('[TechnicalIndicators] Bollinger button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                this.hideBollingerBands();
                btn.classList.remove('active');
            } else {
                this.showBollingerBands();
                btn.classList.add('active');
            }

            console.log('[TechnicalIndicators] Bollinger Bands toggled:', !isActive);
        } catch (error) {
            console.error('[TechnicalIndicators] Error in toggleBollingerBands:', error);
        }
    }

    /**
     * Show Bollinger Bands
     */
    showBollingerBands() {
        try {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[TechnicalIndicators] No chart data for Bollinger Bands');
                return;
            }

            const bbData = window.chartUtils.calculateBollingerBands(this.chart.chartData, 20, 2);
            console.log('[TechnicalIndicators] Bollinger Bands calculated:', bbData.upper.length, 'values');

            // Upper Band
            this.bbSeries.upper = window.chartUtils.chart.addLineSeries({
                color: '#FF6B6B',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                title: 'BB Upper',
                priceLineVisible: false,
                lastValueVisible: false
            });
            this.bbSeries.upper.setData(bbData.upper);

            // Middle Band (SMA)
            this.bbSeries.middle = window.chartUtils.chart.addLineSeries({
                color: '#4ECDC4',
                lineWidth: 1,
                title: 'BB Middle',
                priceLineVisible: false,
                lastValueVisible: false
            });
            this.bbSeries.middle.setData(bbData.middle);

            // Lower Band
            this.bbSeries.lower = window.chartUtils.chart.addLineSeries({
                color: '#95E1D3',
                lineWidth: 1,
                lineStyle: 2, // Dashed
                title: 'BB Lower',
                priceLineVisible: false,
                lastValueVisible: false
            });
            this.bbSeries.lower.setData(bbData.lower);

            console.log('[TechnicalIndicators] Bollinger Bands added to chart');
        } catch (error) {
            console.error('[TechnicalIndicators] Error in showBollingerBands:', error);
        }
    }

    /**
     * Hide Bollinger Bands
     */
    hideBollingerBands() {
        try {
            if (this.bbSeries.upper) {
                window.chartUtils.chart.removeSeries(this.bbSeries.upper);
                this.bbSeries.upper = null;
            }
            if (this.bbSeries.middle) {
                window.chartUtils.chart.removeSeries(this.bbSeries.middle);
                this.bbSeries.middle = null;
            }
            if (this.bbSeries.lower) {
                window.chartUtils.chart.removeSeries(this.bbSeries.lower);
                this.bbSeries.lower = null;
            }
            console.log('[TechnicalIndicators] Bollinger Bands removed');
        } catch (error) {
            console.error('[TechnicalIndicators] Error in hideBollingerBands:', error);
        }
    }

    /**
     * Toggle SuperTrend indicator
     */
    toggleSuperTrend() {
        try {
            const btn = document.getElementById('supertrend-toggle');
            if (!btn) {
                console.warn('[TechnicalIndicators] SuperTrend button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                this.hideSuperTrend();
                btn.classList.remove('active');
            } else {
                this.showSuperTrend();
                btn.classList.add('active');
            }

            console.log('[TechnicalIndicators] SuperTrend toggled:', !isActive);
        } catch (error) {
            console.error('[TechnicalIndicators] Error in toggleSuperTrend:', error);
        }
    }

    /**
     * Show SuperTrend indicator
     */
    showSuperTrend() {
        try {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[TechnicalIndicators] No chart data for SuperTrend');
                return;
            }

            if (!window.chartUtils) {
                console.error('[TechnicalIndicators] chartUtils not available');
                return;
            }

            // TradingView default settings: period=10, multiplier=3.0
            const result = window.chartUtils.addSuperTrend(this.chart.chartData, 10, 3.0);

            if (result) {
                console.log('[TechnicalIndicators] SuperTrend added successfully');

                // Get current signal
                const signal = window.chartUtils.getCurrentSuperTrendSignal();
                if (signal && this.chart.showNotification) {
                    console.log(`[TechnicalIndicators] SuperTrend Signal: ${signal.signal} (${signal.trend})`);
                    this.chart.showNotification(`SuperTrend: ${signal.signal}`, signal.color);
                }
            } else {
                console.error('[TechnicalIndicators] Failed to add SuperTrend');
                const btn = document.getElementById('supertrend-toggle');
                if (btn) btn.classList.remove('active');
            }
        } catch (error) {
            console.error('[TechnicalIndicators] Error in showSuperTrend:', error);
            const btn = document.getElementById('supertrend-toggle');
            if (btn) btn.classList.remove('active');
        }
    }

    /**
     * Hide SuperTrend indicator
     */
    hideSuperTrend() {
        try {
            if (window.chartUtils && window.chartUtils.removeSuperTrend) {
                window.chartUtils.removeSuperTrend();
                console.log('[TechnicalIndicators] SuperTrend removed');
            }
        } catch (error) {
            console.error('[TechnicalIndicators] Error in hideSuperTrend:', error);
        }
    }

    /**
     * Update SuperTrend (called on auto-update)
     */
    updateSuperTrend() {
        try {
            const superTrendBtn = document.getElementById('supertrend-toggle');
            const isSuperTrendActive = superTrendBtn && superTrendBtn.classList.contains('active');

            if (isSuperTrendActive && this.chart.chartData && this.chart.chartData.length > 0) {
                if (window.chartUtils && window.chartUtils.addSuperTrend) {
                    window.chartUtils.addSuperTrend(this.chart.chartData, 10, 3.0);
                    console.log('[TechnicalIndicators] SuperTrend updated');
                }
            }
        } catch (error) {
            console.error('[TechnicalIndicators] Error in updateSuperTrend:', error);
        }
    }

    /**
     * Update all active indicators (called when chart data changes)
     */
    updateAll() {
        try {
            // Update RSI if active
            const rsiBtn = document.getElementById('rsi-toggle');
            if (rsiBtn && rsiBtn.classList.contains('active')) {
                this.hideRSI();
                this.showRSI();
            }

            // Update MACD if active
            const macdBtn = document.getElementById('macd-toggle');
            if (macdBtn && macdBtn.classList.contains('active')) {
                this.hideMACD();
                this.showMACD();
            }

            // Update Bollinger Bands if active
            const bbBtn = document.getElementById('bollinger-toggle');
            if (bbBtn && bbBtn.classList.contains('active')) {
                this.hideBollingerBands();
                this.showBollingerBands();
            }

            // Update SuperTrend if active
            this.updateSuperTrend();

            console.log('[TechnicalIndicators] All indicators updated');
        } catch (error) {
            console.error('[TechnicalIndicators] Error in updateAll:', error);
        }
    }

    /**
     * Resize main chart to accommodate indicator panels
     */
    resizeMainChart() {
        try {
            const mainContainer = document.getElementById('chart-container');
            if (!mainContainer || !window.chartUtils || !window.chartUtils.chart) {
                return;
            }

            // Force layout recalculation
            setTimeout(() => {
                const newHeight = mainContainer.clientHeight;
                const newWidth = mainContainer.clientWidth;

                if (newHeight > 0 && newWidth > 0) {
                    window.chartUtils.chart.resize(newWidth, newHeight);
                    console.log('[TechnicalIndicators] Main chart resized:', newWidth, 'x', newHeight);
                }
            }, 100);
        } catch (error) {
            console.error('[TechnicalIndicators] Error in resizeMainChart:', error);
        }
    }
}

// Export to window for global access
if (typeof window !== 'undefined') {
    window.TechnicalIndicators = TechnicalIndicators;
}
