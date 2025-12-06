/**
 * DrawingTools Module
 *
 * Manages interactive drawing tools on the chart:
 * - Trendlines (2-point lines)
 * - Fibonacci retracement (levels)
 * - Horizontal/Vertical lines
 * - Drawing list management
 * - Save/load persistence
 *
 * @class DrawingTools
 * @param {Object} chartInstance - Main chart instance
 */

class DrawingTools {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.drawings = [];
        this.drawingMode = null; // 'trendline', 'fibonacci', 'horizontal', 'vertical'
        this.tempPoints = [];
        this.activeDrawingButton = null;

        // Undo/Redo system
        this.undoStack = []; // Stack of deleted drawings for undo
        this.redoStack = []; // Stack of undone drawings for redo

        console.log('[DrawingTools] Module initialized');
    }

    /**
     * Setup event handlers for drawing tool buttons
     */
    setupEventHandlers() {
        try {
            // Trendline button
            const trendlineBtn = document.getElementById('draw-trendline');
            if (trendlineBtn) {
                trendlineBtn.addEventListener('click', () => {
                    this.enableDrawingMode('trendline', trendlineBtn);
                });
            }

            // Fibonacci button
            const fibonacciBtn = document.getElementById('draw-fibonacci');
            if (fibonacciBtn) {
                fibonacciBtn.addEventListener('click', () => {
                    this.enableDrawingMode('fibonacci', fibonacciBtn);
                });
            }

            // Horizontal line button
            const horizontalBtn = document.getElementById('draw-horizontal');
            if (horizontalBtn) {
                horizontalBtn.addEventListener('click', () => {
                    this.enableDrawingMode('horizontal', horizontalBtn);
                });
            }

            // Vertical line button
            const verticalBtn = document.getElementById('draw-vertical');
            if (verticalBtn) {
                verticalBtn.addEventListener('click', () => {
                    this.enableDrawingMode('vertical', verticalBtn);
                });
            }

            // Clear all drawings button
            const clearBtn = document.getElementById('clear-trendlines');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    this.clearAllDrawings();
                });
            }

            // Show drawings list button
            const showListBtn = document.getElementById('show-drawings');
            if (showListBtn) {
                showListBtn.addEventListener('click', () => {
                    this.showDrawingsList();
                });
            }

            // Close drawings modal
            const closeModalBtn = document.getElementById('close-drawings-modal');
            if (closeModalBtn) {
                closeModalBtn.addEventListener('click', () => {
                    this.closeDrawingsList();
                });
            }

            const closeBtn = document.getElementById('close-drawings-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.closeDrawingsList();
                });
            }

            // Refresh drawings list
            const refreshBtn = document.getElementById('refresh-drawings');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    this.updateDrawingsList();
                });
            }

            // Keyboard shortcuts
            document.addEventListener('keydown', (event) => {
                // ESC to cancel drawing mode
                if (event.key === 'Escape' || event.key === 'Esc') {
                    if (this.drawingMode) {
                        console.log('[DrawingTools] ESC pressed - canceling drawing mode');
                        this.disableDrawingMode();
                    }
                }

                // Ctrl+Z to undo (remove last drawing)
                if ((event.ctrlKey || event.metaKey) && event.key === 'z') {
                    event.preventDefault();
                    this.undo();
                }

                // Ctrl+Y or Ctrl+Shift+Z to redo
                if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.shiftKey && event.key === 'z'))) {
                    event.preventDefault();
                    this.redo();
                }
            });

            console.log('[DrawingTools] Event handlers setup complete');

        } catch (error) {
            console.error('[DrawingTools] Error setting up event handlers:', error);
        }
    }

    /**
     * Enable drawing mode
     * @param {string} type - Drawing type ('trendline', 'fibonacci', etc.)
     * @param {HTMLElement} button - Button element that was clicked
     */
    enableDrawingMode(type, button) {
        try {
            // If already in this mode, disable it
            if (this.drawingMode === type) {
                this.disableDrawingMode();
                return;
            }

            // Disable previous mode
            if (this.drawingMode) {
                this.disableDrawingMode();
            }

            this.drawingMode = type;
            this.tempPoints = [];
            this.activeDrawingButton = button;

            // Update UI
            if (button) {
                button.classList.add('active');
            }

            // Change cursor
            const chartContainer = document.getElementById('chart-container');
            if (chartContainer) {
                chartContainer.style.cursor = 'crosshair';
            }

            console.log(`[DrawingTools] Enabled ${type} drawing mode`);

            // Show instruction
            const instructions = {
                'trendline': '첫 번째 포인트를 클릭하세요',
                'fibonacci': '시작 포인트를 클릭하세요',
                'horizontal': '수평선 위치를 클릭하세요',
                'vertical': '수직선 위치를 클릭하세요'
            };
            this.showInstruction(instructions[type] || '차트를 클릭하세요');

        } catch (error) {
            console.error('[DrawingTools] Error enabling drawing mode:', error);
        }
    }

    /**
     * Disable drawing mode
     */
    disableDrawingMode() {
        try {
            if (this.activeDrawingButton) {
                this.activeDrawingButton.classList.remove('active');
            }

            this.drawingMode = null;
            this.tempPoints = [];
            this.activeDrawingButton = null;

            // Reset cursor
            const chartContainer = document.getElementById('chart-container');
            if (chartContainer) {
                chartContainer.style.cursor = 'default';
            }

            // Hide instruction
            this.hideInstruction();

            console.log('[DrawingTools] Drawing mode disabled');

        } catch (error) {
            console.error('[DrawingTools] Error disabling drawing mode:', error);
        }
    }

    /**
     * Handle chart click for drawing
     * @param {number} time - Unix timestamp
     * @param {number} price - Price value
     */
    handleChartClick(time, price) {
        try {
            if (!this.drawingMode) return;

            console.log(`[DrawingTools] Chart clicked at time=${time}, price=${price}`);

            this.tempPoints.push({ time, price });

            // Trendline and Fibonacci need 2 points
            if (this.drawingMode === 'trendline' && this.tempPoints.length === 2) {
                this.drawTrendline(this.tempPoints[0], this.tempPoints[1]);
                this.disableDrawingMode();
            } else if (this.drawingMode === 'fibonacci' && this.tempPoints.length === 2) {
                this.drawFibonacci(this.tempPoints[0], this.tempPoints[1]);
                this.disableDrawingMode();
            } else if (this.drawingMode === 'horizontal') {
                this.drawHorizontalLine(price);
                this.disableDrawingMode();
            } else if (this.drawingMode === 'vertical') {
                this.drawVerticalLine(time);
                this.disableDrawingMode();
            } else {
                // Waiting for second point
                const secondPointInstructions = {
                    'trendline': '두 번째 포인트를 클릭하세요',
                    'fibonacci': '끝 포인트를 클릭하세요'
                };
                this.showInstruction(secondPointInstructions[this.drawingMode] || '두 번째 포인트를 클릭하세요');
            }

        } catch (error) {
            console.error('[DrawingTools] Error handling chart click:', error);
        }
    }

    /**
     * Draw trendline between two points
     * @param {Object} point1 - First point {time, price}
     * @param {Object} point2 - Second point {time, price}
     */
    drawTrendline(point1, point2) {
        try {
            if (!this.chart || !this.chart.chart || !this.chart.chartData) {
                console.error('[DrawingTools] Chart not ready');
                return;
            }

            // Calculate slope
            const slope = (point2.price - point1.price) / (point2.time - point1.time);

            // Get chart time range
            const chartData = this.chart.chartData;
            const minTime = chartData[0].time;
            const maxTime = chartData[chartData.length - 1].time;

            // Calculate extended line points
            const calculatePrice = (time) => {
                return point1.price + slope * (time - point1.time);
            };

            // Create line series
            const lineSeries = this.chart.chart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
                priceScaleId: 'right',
                lastValueVisible: false,
                priceLineVisible: false,
            });

            // Set line data (extended to chart edges)
            const lineData = [
                { time: minTime, value: calculatePrice(minTime) },
                { time: point1.time, value: point1.price },
                { time: point2.time, value: point2.price },
                { time: maxTime, value: calculatePrice(maxTime) }
            ];

            lineSeries.setData(lineData);

            // Save drawing
            const drawing = {
                id: Date.now(),
                type: 'trendline',
                series: lineSeries,
                point1,
                point2,
                slope,
                color: '#2962FF'
            };

            this.drawings.push(drawing);
            this.saveDrawings();
            this.updateDrawingsList();

            console.log('[DrawingTools] Trendline created:', drawing.id);

        } catch (error) {
            console.error('[DrawingTools] Failed to draw trendline:', error);
        }
    }

    /**
     * Draw Fibonacci retracement levels
     * @param {Object} point1 - Start point {time, price}
     * @param {Object} point2 - End point {time, price}
     */
    drawFibonacci(point1, point2) {
        try {
            if (!this.chart || !this.chart.chart) {
                console.error('[DrawingTools] Chart not ready');
                return;
            }

            const levels = [
                { level: 0, label: '0.0', color: '#787B86' },
                { level: 0.236, label: '0.236', color: '#F23645' },
                { level: 0.382, label: '0.382', color: '#FFA726' },
                { level: 0.5, label: '0.5', color: '#26A69A' },
                { level: 0.618, label: '0.618', color: '#2962FF' },
                { level: 0.786, label: '0.786', color: '#9C27B0' },
                { level: 1.0, label: '1.0', color: '#787B86' }
            ];

            const priceDiff = point2.price - point1.price;
            const lines = [];

            levels.forEach(({ level, label, color }) => {
                const price = point1.price + priceDiff * level;

                const lineSeries = this.chart.chart.addLineSeries({
                    color: color,
                    lineWidth: level === 0.5 ? 2 : 1,
                    lineStyle: 2, // Dashed
                    priceScaleId: 'right',
                    lastValueVisible: false,
                    priceLineVisible: false,
                });

                // Create horizontal line at this level
                const chartData = this.chart.chartData;
                const minTime = chartData[0].time;
                const maxTime = chartData[chartData.length - 1].time;

                lineSeries.setData([
                    { time: minTime, value: price },
                    { time: maxTime, value: price }
                ]);

                lines.push({ level, label, series: lineSeries, price });
            });

            // Save drawing
            const drawing = {
                id: Date.now(),
                type: 'fibonacci',
                point1,
                point2,
                lines
            };

            this.drawings.push(drawing);
            this.saveDrawings();
            this.updateDrawingsList();

            console.log('[DrawingTools] Fibonacci retracement created:', drawing.id);

        } catch (error) {
            console.error('[DrawingTools] Failed to draw Fibonacci:', error);
        }
    }

    /**
     * Draw horizontal line at specific price
     * @param {number} price - Price level
     */
    drawHorizontalLine(price) {
        try {
            // Validate chart readiness
            if (!this.chart || !this.chart.chart || !this.chart.chartData) {
                console.error('[DrawingTools] Chart not ready');
                return;
            }

            const chartData = this.chart.chartData;
            if (!Array.isArray(chartData) || chartData.length < 2) {
                console.error('[DrawingTools] Insufficient chart data');
                return;
            }

            // Validate price input - CRITICAL FIX for "Value is null"
            if (typeof price !== 'number' || !Number.isFinite(price) || isNaN(price) || price === null) {
                console.error('[DrawingTools] Invalid price value:', price);
                return;
            }

            // Validate time data
            const minTime = chartData[0].time;
            const maxTime = chartData[chartData.length - 1].time;

            if (minTime == null || maxTime == null) {
                console.error('[DrawingTools] Invalid time data in chartData');
                return;
            }

            const lineSeries = this.chart.chart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
                lineStyle: 0, // Solid
                priceScaleId: 'right',
                lastValueVisible: true,
                priceLineVisible: true,
                priceFormat: {
                    type: 'price',
                    precision: 2,
                    minMove: 0.01,
                },
            });

            // Set data with validated values
            lineSeries.setData([
                { time: minTime, value: price },
                { time: maxTime, value: price }
            ]);

            const drawing = {
                id: Date.now(),
                type: 'horizontal',
                series: lineSeries,
                price,
                color: '#2962FF'
            };

            this.drawings.push(drawing);
            this.saveDrawings();
            this.updateDrawingsList();

            console.log('[DrawingTools] Horizontal line created:', drawing.id, 'at price:', price);

        } catch (error) {
            console.error('[DrawingTools] Failed to draw horizontal line:', error);
        }
    }

    /**
     * Draw vertical line at specific time
     * @param {number} time - Unix timestamp
     */
    drawVerticalLine(time) {
        try {
            // Validate chart readiness
            if (!this.chart || !this.chart.chart || !this.chart.chartData) {
                console.error('[DrawingTools] Chart not ready');
                return;
            }

            const chartData = this.chart.chartData;
            if (!Array.isArray(chartData) || chartData.length === 0) {
                console.error('[DrawingTools] Insufficient chart data');
                return;
            }

            // Validate time input - CRITICAL FIX for "Value is null"
            if (typeof time !== 'number' || !Number.isFinite(time) || isNaN(time) || time === null) {
                console.error('[DrawingTools] Invalid time value:', time);
                return;
            }

            console.log('[DrawingTools] Drawing vertical line at time:', time);

            // Get price range from chart data with validation
            const prices = chartData
                .map(d => d && d.high)
                .filter(p => typeof p === 'number' && Number.isFinite(p) && !isNaN(p));

            if (prices.length === 0) {
                console.error('[DrawingTools] No valid price data found');
                return;
            }

            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);

            // Validate calculated prices - CRITICAL FIX
            if (!Number.isFinite(minPrice) || !Number.isFinite(maxPrice) || isNaN(minPrice) || isNaN(maxPrice)) {
                console.error('[DrawingTools] Invalid price range:', { minPrice, maxPrice });
                return;
            }

            // Create a line series for vertical line
            const lineSeries = this.chart.chart.addLineSeries({
                color: '#9C27B0',  // Purple color
                lineWidth: 2,
                lineStyle: 0,  // Solid line
                crosshairMarkerVisible: false,
                lastValueVisible: false,
                priceLineVisible: false,
                title: `수직선: ${new Date(time * 1000).toLocaleDateString()}`
            });

            // Draw vertical line with validated values
            lineSeries.setData([
                { time: time, value: minPrice },
                { time: time, value: maxPrice }
            ]);

            const drawing = {
                id: Date.now(),
                type: 'vertical',
                series: lineSeries,
                time,
                color: '#9C27B0'
            };

            this.drawings.push(drawing);
            this.saveDrawings();
            this.updateDrawingsList();

            console.log('[DrawingTools] Vertical line created:', drawing.id, 'at time:', new Date(time * 1000).toLocaleDateString());

        } catch (error) {
            console.error('[DrawingTools] Failed to draw vertical line:', error);
        }
    }

    /**
     * Save drawings to localStorage (per coin)
     */
    saveDrawings() {
        try {
            const currentMarket = this.chart.currentMarket || 'UNKNOWN';

            const data = this.drawings.map(d => ({
                id: d.id,
                type: d.type,
                point1: d.point1,
                point2: d.point2,
                price: d.price,
                time: d.time,
                slope: d.slope,
                color: d.color
            }));

            // Get all drawings from localStorage
            const allDrawings = JSON.parse(localStorage.getItem('coinpulse_drawings_all') || '{}');

            // Save current coin's drawings
            allDrawings[currentMarket] = data;

            localStorage.setItem('coinpulse_drawings_all', JSON.stringify(allDrawings));
            console.log(`[DrawingTools] Saved ${data.length} drawings for ${currentMarket}`);

        } catch (error) {
            console.error('[DrawingTools] Failed to save drawings:', error);
        }
    }

    /**
     * Load drawings from localStorage (per coin)
     */
    loadDrawings() {
        try {
            const currentMarket = this.chart.currentMarket || 'UNKNOWN';

            // Get all drawings from localStorage
            const allDrawings = JSON.parse(localStorage.getItem('coinpulse_drawings_all') || '{}');

            // Get drawings for current coin
            const data = allDrawings[currentMarket] || [];

            if (data.length === 0) {
                console.log('[DrawingTools] No saved drawings to load');
                // Update list to show empty state
                this.updateDrawingsList();
                return;
            }

            // Clear existing drawings first
            this.clearAllDrawingsWithoutSave();

            // Restore each drawing
            data.forEach(d => {
                if (d.type === 'trendline' && d.point1 && d.point2) {
                    this.drawTrendline(d.point1, d.point2);
                } else if (d.type === 'fibonacci' && d.point1 && d.point2) {
                    this.drawFibonacci(d.point1, d.point2);
                } else if (d.type === 'horizontal' && d.price) {
                    this.drawHorizontalLine(d.price);
                } else if (d.type === 'vertical' && d.time) {
                    this.drawVerticalLine(d.time);
                }
            });

            console.log('[DrawingTools] Loaded', data.length, 'drawings from localStorage');

            // ✨ CRITICAL FIX: Update list after loading drawings
            this.updateDrawingsList();

        } catch (error) {
            console.error('[DrawingTools] Failed to load drawings:', error);
        }
    }

    /**
     * Update drawings list UI
     */
    updateDrawingsList() {
        try {
            console.log('[DrawingTools] 🔧 updateDrawingsList() called');

            const drawingsList = document.getElementById('drawings-list');
            if (!drawingsList) {
                console.error('[DrawingTools] drawings-list element not found');
                return;
            }

            console.log('[DrawingTools] 🔍 Updating list with', this.drawings ? this.drawings.length : 0, 'drawings');

            // If no drawings, show empty message
            if (!this.drawings || this.drawings.length === 0) {
                console.log('[DrawingTools] ⚠️ No drawings to display');
                drawingsList.innerHTML = '<div class="empty-text-small">그리기가 없습니다</div>';
                return;
            }

            // Generate HTML for drawing list
            let html = '';
            this.drawings.forEach((drawing, index) => {
                console.log(`[DrawingTools] 🔍 Processing drawing ${index}:`, drawing);
                const typeNames = {
                    'trendline': '📈 트렌드라인',
                    'horizontal': '━ 수평선',
                    'vertical': '│ 수직선',
                    'fibonacci': '🌀 피보나치'
                };

                const typeName = typeNames[drawing.type] || drawing.type;
                let details = '';

                if (drawing.type === 'horizontal') {
                    details = `가격: ${drawing.price ? drawing.price.toLocaleString() + '원' : 'N/A'}`;
                } else if (drawing.type === 'vertical') {
                    details = `시간: ${drawing.time ? new Date(drawing.time * 1000).toLocaleString() : 'N/A'}`;
                } else if (drawing.type === 'trendline') {
                    details = `${drawing.point1 ? new Date(drawing.point1.time * 1000).toLocaleDateString() : 'N/A'} → ${drawing.point2 ? new Date(drawing.point2.time * 1000).toLocaleDateString() : 'N/A'}`;
                } else if (drawing.type === 'fibonacci') {
                    details = `레벨: 0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0`;
                }

                html += `
                    <div class="drawing-item" data-drawing-id="${drawing.id}">
                        <div class="drawing-info">
                            <div class="drawing-type">${typeName}</div>
                            <div class="drawing-details">${details}</div>
                        </div>
                        <div class="drawing-actions">
                            <button class="btn-delete-drawing" onclick="window.workingChart.drawingTools.deleteDrawing(${index})">삭제</button>
                        </div>
                    </div>
                `;
            });

            drawingsList.innerHTML = html;
            console.log('[DrawingTools] List updated with', this.drawings.length, 'items');

            // 🔍 DEBUG: Verify HTML was actually set
            console.log('[DrawingTools] 🔍 drawingsList.innerHTML length:', drawingsList.innerHTML.length);
            console.log('[DrawingTools] 🔍 drawingsList.children.length:', drawingsList.children.length);
            console.log('[DrawingTools] 🔍 First 500 chars:', drawingsList.innerHTML.substring(0, 500));

        } catch (error) {
            console.error('[DrawingTools] Error updating drawings list:', error);
        }
    }

    /**
     * Delete drawing by index
     * @param {number} index - Drawing index
     */
    deleteDrawing(index) {
        try {
            console.log('[DrawingTools] Deleting drawing at index', index);

            if (this.drawings && this.drawings[index]) {
                const drawing = this.drawings[index];

                // Remove from chart
                if (drawing.series) {
                    this.chart.chart.removeSeries(drawing.series);
                }

                // Remove Fibonacci lines
                if (drawing.lines) {
                    drawing.lines.forEach(line => {
                        if (line && line.series) {
                            this.chart.chart.removeSeries(line.series);
                        }
                    });
                }

                // Remove from array
                this.drawings.splice(index, 1);

                // Save and update UI
                this.saveDrawings();
                this.updateDrawingsList();

                console.log('[DrawingTools] Drawing deleted successfully');
            }

        } catch (error) {
            console.error('[DrawingTools] Error deleting drawing:', error);
        }
    }

    /**
     * Clear all drawings
     */
    clearAllDrawings() {
        try {
            if (!this.drawings || this.drawings.length === 0) {
                console.log('[DrawingTools] No drawings to clear');
                return;
            }

            const count = this.drawings.length;

            // Remove all from chart
            this.drawings.forEach(drawing => {
                try {
                    if (drawing.series) {
                        this.chart.chart.removeSeries(drawing.series);
                    }
                    if (drawing.lines) {
                        drawing.lines.forEach(line => {
                            if (line && line.series) {
                                this.chart.chart.removeSeries(line.series);
                            }
                        });
                    }
                } catch (e) {
                    console.warn('[DrawingTools] Failed to remove drawing:', e);
                }
            });

            // Clear array
            this.drawings = [];

            // Save and update UI
            this.saveDrawings();
            this.updateDrawingsList();

            console.log(`[DrawingTools] Cleared ${count} drawings`);

        } catch (error) {
            console.error('[DrawingTools] Error clearing drawings:', error);
        }
    }

    /**
     * Clear all drawings without saving (for reload)
     */
    clearAllDrawingsWithoutSave() {
        try {
            this.drawings.forEach(drawing => {
                try {
                    if (drawing.series) {
                        this.chart.chart.removeSeries(drawing.series);
                    }
                    if (drawing.lines) {
                        drawing.lines.forEach(line => {
                            if (line && line.series) {
                                this.chart.chart.removeSeries(line.series);
                            }
                        });
                    }
                } catch (e) {
                    console.warn('[DrawingTools] Failed to remove drawing:', e);
                }
            });

            this.drawings = [];

        } catch (error) {
            console.error('[DrawingTools] Error clearing drawings:', error);
        }
    }

    /**
     * Show drawings list modal
     */
    showDrawingsList() {
        try {
            // 🔍 DEBUG: Show current drawings array
            console.log('[DrawingTools] 🔍 DEBUG - Current drawings array:', this.drawings);
            console.log('[DrawingTools] 🔍 DEBUG - Number of drawings:', this.drawings ? this.drawings.length : 0);
            if (this.drawings && this.drawings.length > 0) {
                this.drawings.forEach((d, i) => {
                    console.log(`[DrawingTools] 🔍 Drawing ${i}:`, {
                        type: d.type,
                        price: d.price,
                        time: d.time,
                        id: d.id
                    });
                });
            }

            this.updateDrawingsList();

            const modal = document.getElementById('drawings-modal');
            if (modal) {
                modal.style.display = 'flex';
                console.log('[DrawingTools] Drawings list modal opened');
            }

        } catch (error) {
            console.error('[DrawingTools] Error showing drawings list:', error);
        }
    }

    /**
     * Close drawings list modal
     */
    closeDrawingsList() {
        try {
            const modal = document.getElementById('drawings-modal');
            if (modal) {
                modal.style.display = 'none';
                console.log('[DrawingTools] Drawings list modal closed');
            }

        } catch (error) {
            console.error('[DrawingTools] Error closing drawings list:', error);
        }
    }

    /**
     * Show drawing instruction
     * @param {string} message - Instruction message
     */
    showInstruction(message) {
        try {
            const instructionEl = document.getElementById('drawing-instruction');
            const instructionText = document.getElementById('drawing-instruction-text');

            if (instructionEl && instructionText) {
                instructionText.textContent = message;
                instructionEl.style.display = 'block';
                console.log('[DrawingTools] Showing instruction:', message);
            } else {
                console.log('[DrawingTools] Instruction:', message);
            }
        } catch (error) {
            console.error('[DrawingTools] Error showing instruction:', error);
        }
    }

    /**
     * Hide drawing instruction
     */
    hideInstruction() {
        try {
            const instructionEl = document.getElementById('drawing-instruction');
            if (instructionEl) {
                instructionEl.style.display = 'none';
                console.log('[DrawingTools] Hiding instruction');
            }
        } catch (error) {
            console.error('[DrawingTools] Error hiding instruction:', error);
        }
    }

    /**
     * Undo - Remove last drawing and add to redo stack
     */
    undo() {
        try {
            if (this.drawings.length === 0) {
                console.log('[DrawingTools] No drawings to undo');
                return;
            }

            // Get last drawing
            const lastDrawing = this.drawings[this.drawings.length - 1];

            // Remove from chart
            if (lastDrawing.series) {
                this.chart.chart.removeSeries(lastDrawing.series);
            }

            // Remove Fibonacci lines
            if (lastDrawing.lines) {
                lastDrawing.lines.forEach(line => {
                    if (line && line.series) {
                        this.chart.chart.removeSeries(line.series);
                    }
                });
            }

            // Remove from drawings array
            this.drawings.pop();

            // Add to undo stack (save data, not series objects)
            this.undoStack.push({
                type: lastDrawing.type,
                point1: lastDrawing.point1,
                point2: lastDrawing.point2,
                price: lastDrawing.price,
                time: lastDrawing.time,
                slope: lastDrawing.slope,
                color: lastDrawing.color
            });

            // Clear redo stack when new action is performed
            this.redoStack = [];

            // Save and update UI
            this.saveDrawings();
            this.updateDrawingsList();

            console.log('[DrawingTools] Undo: Removed last drawing, now', this.drawings.length, 'drawings');

        } catch (error) {
            console.error('[DrawingTools] Error in undo:', error);
        }
    }

    /**
     * Redo - Restore last undone drawing
     */
    redo() {
        try {
            if (this.undoStack.length === 0) {
                console.log('[DrawingTools] No drawings to redo');
                return;
            }

            // Get last undone drawing
            const drawing = this.undoStack.pop();

            // Restore drawing based on type
            if (drawing.type === 'trendline' && drawing.point1 && drawing.point2) {
                this.drawTrendline(drawing.point1, drawing.point2);
            } else if (drawing.type === 'fibonacci' && drawing.point1 && drawing.point2) {
                this.drawFibonacci(drawing.point1, drawing.point2);
            } else if (drawing.type === 'horizontal' && drawing.price) {
                this.drawHorizontalLine(drawing.price);
            } else if (drawing.type === 'vertical' && drawing.time) {
                this.drawVerticalLine(drawing.time);
            }

            // Note: drawTrendline/drawFibonacci/drawHorizontalLine/drawVerticalLine will add to drawings array and save

            console.log('[DrawingTools] Redo: Restored drawing, now', this.drawings.length, 'drawings');

        } catch (error) {
            console.error('[DrawingTools] Error in redo:', error);
        }
    }

    /**
     * Clear all drawings - called when coin changes
     */
    clearAllDrawings() {
        try {
            console.log('[DrawingTools] Clearing all drawings for coin change...');

            // Remove all drawings from chart
            this.drawings.forEach(drawing => {
                if (drawing.series) {
                    this.chart.chart.removeSeries(drawing.series);
                }

                // Remove Fibonacci lines
                if (drawing.lines) {
                    drawing.lines.forEach(line => {
                        if (line && line.series) {
                            this.chart.chart.removeSeries(line.series);
                        }
                    });
                }
            });

            // Clear arrays
            this.drawings = [];
            this.undoStack = [];
            this.redoStack = [];

            // Cancel any active drawing mode
            if (this.drawingMode) {
                this.disableDrawingMode();
            }

            // Clear localStorage
            this.saveDrawings();

            // Update drawings list
            this.updateDrawingsList();

            console.log('[DrawingTools] All drawings cleared');
        } catch (error) {
            console.error('[DrawingTools] Error clearing drawings:', error);
        }
    }
}

// Expose to window for global access
if (typeof window !== 'undefined') {
    window.DrawingTools = DrawingTools;
}
