/**
 * Moving Averages Module
 * Handles moving average calculation, display, and settings management
 *
 * Features:
 * - MA settings modal and persistence (localStorage)
 * - Toggle all MAs on/off
 * - Individual MA enable/disable (20, 50, 100, 200, 300, 500, 1000)
 * - MA calculation and rendering with custom colors
 * - MA value display in analysis panel
 */

class MovingAverages {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.maSeries = {};
        this.maSettings = this.loadMASettings();
        this.movingAveragesVisible = false; // MAs are hidden by default

        console.log('[MovingAverages] Module initialized with settings:', this.maSettings);
    }

    /**
     * Validate MA data before passing to setData()
     * Filters out null, undefined, NaN, and non-finite values
     */
    validateMAData(data, period) {
        if (!Array.isArray(data)) {
            console.warn(`[MovingAverages] MA${period}: Invalid data type, expected array`);
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
            console.warn(`[MovingAverages] MA${period}: Filtered out ${data.length - filtered.length} invalid data points`);
        }

        return filtered;
    }

    /**
     * Load MA settings from localStorage
     */
    loadMASettings() {
        try {
            const saved = localStorage.getItem('maSettings');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (error) {
            console.warn('[MovingAverages] Failed to load settings:', error);
        }

        // Default: all MAs disabled
        return {
            20: false,
            50: false,
            100: false,
            200: false,
            300: false,
            500: false,
            1000: false
        };
    }

    /**
     * Save MA settings to localStorage
     */
    saveMASettings() {
        try {
            localStorage.setItem('maSettings', JSON.stringify(this.maSettings));
            console.log('[MovingAverages] Settings saved:', this.maSettings);
        } catch (error) {
            console.error('[MovingAverages] Failed to save settings:', error);
        }
    }

    /**
     * Toggle all MAs on/off
     */
    toggleAllMAs() {
        try {
            const btn = document.getElementById('ma-toggle');
            if (!btn) {
                console.warn('[MovingAverages] Toggle button not found');
                return;
            }

            const isActive = btn.classList.contains('active');

            if (isActive) {
                // Hide all MAs
                btn.classList.remove('active');
                this.movingAveragesVisible = false;
                console.log('[MovingAverages] Hiding all MAs');

                this.clearMAs();
            } else {
                // Show all MAs based on settings
                btn.classList.add('active');
                this.movingAveragesVisible = true;
                console.log('[MovingAverages] Showing MAs based on settings');

                this.updateMAs();
            }

            console.log('[MovingAverages] Toggle completed. Visible:', this.movingAveragesVisible);
        } catch (error) {
            console.error('[MovingAverages] Error in toggleAllMAs:', error);
        }
    }

    /**
     * Clear all MA series from chart
     */
    clearMAs() {
        try {
            console.log('[MovingAverages] Clearing all MA series...');

            const maKeys = ['ma20', 'ma50', 'ma100', 'ma200', 'ma300', 'ma500', 'ma1000'];

            maKeys.forEach(key => {
                if (this.maSeries[key]) {
                    try {
                        window.chartUtils.chart.removeSeries(this.maSeries[key]);
                        this.maSeries[key] = null;
                        console.log(`[MovingAverages] ${key.toUpperCase()} series removed`);
                    } catch (error) {
                        console.error(`[MovingAverages] Failed to remove ${key}:`, error);
                    }
                }
            });

            console.log('[MovingAverages] All MA series cleared');
        } catch (error) {
            console.error('[MovingAverages] Error in clearMAs:', error);
        }
    }

    /**
     * Draw all enabled MAs based on saved settings
     */
    drawMAs() {
        try {
            console.log('[MovingAverages] Drawing MA lines based on saved settings...');

            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[MovingAverages] No data for MA calculation');
                return;
            }

            // Clear existing MAs first
            this.clearMAs();

            const maConfigs = [
                { period: 20, color: '#ff6b6b' },
                { period: 50, color: '#4ecdc4' },
                { period: 100, color: '#45b7d1' },
                { period: 200, color: '#96ceb4' },
                { period: 300, color: '#feca57' },
                { period: 500, color: '#ff9ff3' },
                { period: 1000, color: '#54a0ff' }
            ];

            maConfigs.forEach(({ period, color }) => {
                // Check if this MA is enabled in settings
                if (!this.maSettings[period]) {
                    console.log(`[MovingAverages] MA${period} is disabled, skipping...`);
                    return;
                }

                try {
                    const maData = window.chartUtils.calculateMovingAverage(this.chart.chartData, period);
                    console.log(`[MovingAverages] MA${period}: ${maData.length} raw values`);

                    // Validate MA data before setData()
                    const validMaData = this.validateMAData(maData, period);

                    if (validMaData.length > 0) {
                        const maSeries = window.chartUtils.addMovingAverage(period, color);
                        maSeries.setData(validMaData);
                        this.maSeries[`ma${period}`] = maSeries;
                        console.log(`[MovingAverages] MA${period} added with ${validMaData.length} valid points`);
                    } else {
                        console.warn(`[MovingAverages] MA${period} has no valid data points`);
                    }
                } catch (error) {
                    console.error(`[MovingAverages] MA${period} failed:`, error);
                }
            });

            console.log('[MovingAverages] MA drawing completed');
        } catch (error) {
            console.error('[MovingAverages] Error in drawMAs:', error);
        }
    }

    /**
     * Update MA series based on current settings
     */
    updateMAs() {
        try {
            console.log('[MovingAverages] Updating MA lines with settings:', this.maSettings);

            // If MAs are globally hidden, clear them
            if (!this.movingAveragesVisible) {
                this.clearMAs();
                console.log('[MovingAverages] MAs are hidden by policy; skipping update');
                return;
            }

            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                console.warn('[MovingAverages] No data for MA update');
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
                    const isEnabled = this.maSettings[period];

                    // If MA is disabled, remove it
                    if (!isEnabled) {
                        if (this.maSeries[key]) {
                            window.chartUtils.chart.removeSeries(this.maSeries[key]);
                            this.maSeries[key] = null;
                            console.log(`[MovingAverages] MA${period} removed`);
                        }
                        return;
                    }

                    // If MA is enabled, calculate and show it
                    const maData = window.chartUtils.calculateMovingAverage(this.chart.chartData, period);

                    // Validate MA data before setData()
                    const validMaData = this.validateMAData(maData, period);

                    if (validMaData.length === 0) {
                        console.warn(`[MovingAverages] MA${period} has no valid data`);
                        return;
                    }

                    // Create series if it doesn't exist
                    if (!this.maSeries[key]) {
                        this.maSeries[key] = window.chartUtils.chart.addLineSeries({
                            color: color,
                            lineWidth: 2,
                            title: `MA${period}`
                        });
                    }

                    // Update series data with validated data
                    this.maSeries[key].setData(validMaData);
                    console.log(`[MovingAverages] MA${period} updated with ${validMaData.length} valid points`);

                } catch (error) {
                    console.error(`[MovingAverages] MA${period} update failed:`, error);
                }
            });

            console.log('[MovingAverages] MA update completed');
        } catch (error) {
            console.error('[MovingAverages] Error in updateMAs:', error);
        }
    }

    /**
     * Update MA values in analysis panel
     */
    updateMAValues() {
        try {
            if (!this.chart.chartData || this.chart.chartData.length === 0) {
                return;
            }

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
                            maValueEl.textContent = latestMA.value.toLocaleString('ko-KR', {
                                maximumFractionDigits: 0
                            });
                        }
                    }
                } catch (error) {
                    console.error(`[MovingAverages] MA${period} value update failed:`, error);
                }
            });
        } catch (error) {
            console.error('[MovingAverages] Error in updateMAValues:', error);
        }
    }

    /**
     * Open MA settings modal
     */
    openMASettingsModal() {
        try {
            const modal = document.getElementById('ma-settings-modal');
            if (!modal) {
                console.error('[MovingAverages] MA settings modal not found');
                return;
            }

            // Load current settings to checkboxes
            const periods = [20, 50, 100, 200, 300];
            periods.forEach(period => {
                const checkbox = document.getElementById(`ma${period}-toggle`);
                if (checkbox) {
                    checkbox.checked = this.maSettings[period] || false;
                }
            });

            modal.style.display = 'flex';
            console.log('[MovingAverages] MA settings modal opened');
        } catch (error) {
            console.error('[MovingAverages] Error opening MA settings modal:', error);
        }
    }

    /**
     * Close MA settings modal
     */
    closeMASettingsModal() {
        try {
            const modal = document.getElementById('ma-settings-modal');
            if (modal) {
                modal.style.display = 'none';
                console.log('[MovingAverages] MA settings modal closed');
            }
        } catch (error) {
            console.error('[MovingAverages] Error closing MA settings modal:', error);
        }
    }

    /**
     * Apply MA settings from modal
     */
    applyMASettings() {
        try {
            console.log('[MovingAverages] Applying MA settings from modal...');

            // Read checkbox states
            const periods = [20, 50, 100, 200, 300];
            periods.forEach(period => {
                const checkbox = document.getElementById(`ma${period}-toggle`);
                if (checkbox) {
                    this.maSettings[period] = checkbox.checked;
                }
            });

            // Save settings to localStorage
            this.saveMASettings();

            // Update chart if MAs are visible
            if (this.movingAveragesVisible) {
                this.updateMAs();
            }

            // Close modal
            this.closeMASettingsModal();

            console.log('[MovingAverages] MA settings applied:', this.maSettings);
        } catch (error) {
            console.error('[MovingAverages] Error applying MA settings:', error);
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.MovingAverages = MovingAverages;
}
