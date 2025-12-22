/**
 * Order Interactions Module
 *
 * Handles interactive order management on the trading chart:
 * - Click on order line to show details/cancel button
 * - Drag order line to modify price
 * - Upbit API integration for order modification/cancellation
 *
 * @version 1.0.0
 * @date 2025-12-22
 */

class OrderInteractions {
    constructor(chartInstance) {
        this.chart = chartInstance;
        this.chartContainer = null;
        this.isDragging = false;
        this.draggedOrder = null;
        this.dragStartY = null;
        this.originalPrice = null;
        this.selectedOrder = null;
        this.detailsPopup = null;

        // Mouse position tracking
        this.mouseY = null;
        this.priceAtMouse = null;

        // Click detection tolerance (pixels)
        this.clickTolerance = 10;

        console.log('[OrderInteractions] Module initialized');
    }

    /**
     * Initialize order interactions
     */
    init() {
        if (!this.chart || !this.chart.chart) {
            console.error('[OrderInteractions] Chart not available');
            return;
        }

        this.chartContainer = document.getElementById('chart');
        if (!this.chartContainer) {
            console.error('[OrderInteractions] Chart container not found');
            return;
        }

        // Subscribe to crosshair move (for mouse position tracking)
        this.chart.chart.subscribeCrosshairMove((param) => {
            if (param.point) {
                this.mouseY = param.point.y;
                this.priceAtMouse = param.seriesData.get(this.chart.candleSeries);
                if (this.priceAtMouse && this.priceAtMouse.close) {
                    this.priceAtMouse = this.priceAtMouse.close;
                }
            }
        });

        // Add mouse event listeners
        this.chartContainer.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.chartContainer.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.chartContainer.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.chartContainer.addEventListener('mouseleave', this.handleMouseLeave.bind(this));

        console.log('[OrderInteractions] Event listeners attached');
    }

    /**
     * Handle mouse down event
     */
    handleMouseDown(event) {
        if (!this.mouseY) return;

        // Check if clicking on an order line
        const clickedOrder = this.getOrderAtPosition(this.mouseY);

        if (clickedOrder) {
            event.preventDefault();
            this.isDragging = true;
            this.draggedOrder = clickedOrder;
            this.dragStartY = this.mouseY;
            this.originalPrice = clickedOrder.price;

            // Change cursor
            this.chartContainer.style.cursor = 'ns-resize';

            console.log('[OrderInteractions] Started dragging order:', clickedOrder);
        }
    }

    /**
     * Handle mouse move event
     */
    handleMouseMove(event) {
        if (this.isDragging && this.draggedOrder) {
            // Update order line position
            const priceDelta = this.calculatePriceDelta(this.dragStartY, this.mouseY);
            const newPrice = this.originalPrice + priceDelta;

            // Update visual feedback
            this.updateOrderLinePosition(this.draggedOrder, newPrice);

            console.log(`[OrderInteractions] Dragging: ${this.originalPrice.toFixed(0)} → ${newPrice.toFixed(0)}`);
        } else if (!this.isDragging) {
            // Check if hovering over order line
            const hoveredOrder = this.getOrderAtPosition(this.mouseY);
            if (hoveredOrder) {
                this.chartContainer.style.cursor = 'pointer';
            } else {
                this.chartContainer.style.cursor = 'default';
            }
        }
    }

    /**
     * Handle mouse up event
     */
    async handleMouseUp(event) {
        if (this.isDragging && this.draggedOrder) {
            const priceDelta = this.calculatePriceDelta(this.dragStartY, this.mouseY);
            const newPrice = this.originalPrice + priceDelta;

            // Check if price actually changed (minimum 0.5% change)
            const priceChangePercent = Math.abs((newPrice - this.originalPrice) / this.originalPrice * 100);

            if (priceChangePercent >= 0.5) {
                // Price changed significantly - confirm modification
                this.confirmOrderModification(this.draggedOrder, newPrice);
            } else if (Math.abs(this.mouseY - this.dragStartY) < this.clickTolerance) {
                // No significant drag - treat as click
                this.showOrderDetails(this.draggedOrder);
            }

            // Reset drag state
            this.isDragging = false;
            this.draggedOrder = null;
            this.dragStartY = null;
            this.originalPrice = null;
            this.chartContainer.style.cursor = 'default';
        }
    }

    /**
     * Handle mouse leave event
     */
    handleMouseLeave(event) {
        if (this.isDragging) {
            // Cancel drag
            if (this.draggedOrder && this.originalPrice) {
                this.updateOrderLinePosition(this.draggedOrder, this.originalPrice);
            }

            this.isDragging = false;
            this.draggedOrder = null;
            this.dragStartY = null;
            this.originalPrice = null;
            this.chartContainer.style.cursor = 'default';
        }
    }

    /**
     * Get order at Y position (if any)
     */
    getOrderAtPosition(y) {
        if (!this.chart.pendingOrderLines || this.chart.pendingOrderLines.length === 0) {
            return null;
        }

        // Convert Y position to price
        const priceScale = this.chart.chart.priceScale('right');
        const chartHeight = this.chartContainer.clientHeight;

        for (const orderLine of this.chart.pendingOrderLines) {
            const orderY = priceScale.priceToCoordinate(orderLine.price);

            // Check if click is within tolerance
            if (Math.abs(y - orderY) < this.clickTolerance) {
                return orderLine;
            }
        }

        return null;
    }

    /**
     * Calculate price delta based on Y movement
     */
    calculatePriceDelta(startY, currentY) {
        const priceScale = this.chart.chart.priceScale('right');

        // Get price at start and current Y
        const startPrice = priceScale.coordinateToPrice(startY);
        const currentPrice = priceScale.coordinateToPrice(currentY);

        return currentPrice - startPrice;
    }

    /**
     * Update order line visual position (temporary)
     */
    updateOrderLinePosition(orderLine, newPrice) {
        // Update the price line data
        const lineData = this.chart.chartData.map(candle => ({
            time: candle.time,
            value: newPrice
        }));

        if (orderLine.series) {
            orderLine.series.setData(lineData);
        }
    }

    /**
     * Show order details popup with cancel button
     */
    showOrderDetails(orderLine) {
        // Remove existing popup
        this.hideOrderDetails();

        // Create popup
        this.detailsPopup = document.createElement('div');
        this.detailsPopup.className = 'order-details-popup';
        this.detailsPopup.style.cssText = `
            position: fixed;
            background: #1e293b;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            min-width: 250px;
            color: white;
        `;

        const sideText = orderLine.side === 'bid' ? '매수' : '매도';
        const sideColor = orderLine.side === 'bid' ? '#22c55e' : '#ef4444';

        this.detailsPopup.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">미체결 주문</h3>
                <button id="close-order-details" style="
                    background: none;
                    border: none;
                    color: #94a3b8;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                ">×</button>
            </div>
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8;">구분:</span>
                    <span style="color: ${sideColor}; font-weight: 600;">${sideText}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8;">가격:</span>
                    <span style="font-weight: 600;">₩${orderLine.price.toLocaleString('ko-KR')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8;">수량:</span>
                    <span>${orderLine.volume.toFixed(8)}</span>
                </div>
            </div>
            <div style="display: flex; gap: 8px;">
                <button id="modify-order-btn" style="
                    flex: 1;
                    padding: 10px;
                    background: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    font-size: 14px;
                ">가격 수정</button>
                <button id="cancel-order-btn" style="
                    flex: 1;
                    padding: 10px;
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    font-size: 14px;
                ">주문 취소</button>
            </div>
        `;

        // Position popup near mouse
        const rect = this.chartContainer.getBoundingClientRect();
        const popupX = Math.min(event.clientX || rect.left + 100, window.innerWidth - 270);
        const popupY = Math.min(event.clientY || rect.top + 100, window.innerHeight - 200);

        this.detailsPopup.style.left = `${popupX}px`;
        this.detailsPopup.style.top = `${popupY}px`;

        document.body.appendChild(this.detailsPopup);

        // Add event listeners
        document.getElementById('close-order-details').addEventListener('click', () => {
            this.hideOrderDetails();
        });

        document.getElementById('modify-order-btn').addEventListener('click', () => {
            this.hideOrderDetails();
            // Enable drag mode
            alert('주문 라인을 위아래로 드래그하여 가격을 변경하세요.');
        });

        document.getElementById('cancel-order-btn').addEventListener('click', () => {
            this.cancelOrder(orderLine);
        });

        this.selectedOrder = orderLine;

        console.log('[OrderInteractions] Order details shown');
    }

    /**
     * Hide order details popup
     */
    hideOrderDetails() {
        if (this.detailsPopup) {
            this.detailsPopup.remove();
            this.detailsPopup = null;
        }
        this.selectedOrder = null;
    }

    /**
     * Confirm order price modification
     */
    async confirmOrderModification(orderLine, newPrice) {
        const confirmed = confirm(
            `주문 가격을 변경하시겠습니까?\n\n` +
            `현재 가격: ₩${orderLine.price.toLocaleString('ko-KR')}\n` +
            `새 가격: ₩${newPrice.toLocaleString('ko-KR')}\n\n` +
            `※ Upbit API에서 주문 수정은 지원하지 않습니다.\n` +
            `기존 주문을 취소하고 새 주문을 생성합니다.`
        );

        if (confirmed) {
            await this.modifyOrder(orderLine, newPrice);
        } else {
            // Restore original price
            this.updateOrderLinePosition(orderLine, orderLine.price);
        }
    }

    /**
     * Modify order (cancel + create new)
     */
    async modifyOrder(orderLine, newPrice) {
        try {
            console.log('[OrderInteractions] Modifying order...', orderLine);

            // Show loading
            alert('주문을 수정하고 있습니다...\n잠시만 기다려주세요.');

            // Step 1: Cancel existing order
            // TODO: Get order UUID (need to track this when creating order lines)
            // For now, show error message

            alert('주문 수정 기능은 현재 개발 중입니다.\n\n' +
                  'Upbit API에서는 주문 수정 API를 제공하지 않아,\n' +
                  '기존 주문을 취소하고 새 주문을 생성해야 합니다.\n\n' +
                  '수동으로 주문을 취소한 후 새 주문을 생성해주세요.');

            // Restore original price
            this.updateOrderLinePosition(orderLine, orderLine.price);

        } catch (error) {
            console.error('[OrderInteractions] Order modification failed:', error);
            alert('주문 수정에 실패했습니다.\n\n' + error.message);

            // Restore original price
            this.updateOrderLinePosition(orderLine, orderLine.price);
        }
    }

    /**
     * Cancel order
     */
    async cancelOrder(orderLine) {
        // Check if UUID exists
        if (!orderLine.uuid) {
            alert('주문 UUID를 찾을 수 없습니다.\n\n' +
                  '차트를 새로고침한 후 다시 시도해주세요.');
            return;
        }

        const confirmed = confirm(
            `주문을 취소하시겠습니까?\n\n` +
            `구분: ${orderLine.side === 'bid' ? '매수' : '매도'}\n` +
            `가격: ₩${orderLine.price.toLocaleString('ko-KR')}\n` +
            `수량: ${orderLine.volume.toFixed(8)}\n` +
            `UUID: ${orderLine.uuid.substring(0, 8)}...`
        );

        if (!confirmed) return;

        try {
            console.log('[OrderInteractions] Canceling order...', orderLine);

            this.hideOrderDetails();

            // Call Upbit API to cancel order
            if (!window.apiHandler || !window.apiHandler.cancelOrder) {
                throw new Error('API Handler not available');
            }

            const result = await window.apiHandler.cancelOrder(orderLine.uuid);

            if (result && result.success) {
                alert('주문이 성공적으로 취소되었습니다.');

                // Refresh pending order lines
                if (this.chart && this.chart.updateAvgPriceAndPendingOrders) {
                    await this.chart.updateAvgPriceAndPendingOrders();
                }

                console.log('[OrderInteractions] Order canceled successfully');
            } else {
                throw new Error(result.error || 'Unknown error');
            }

        } catch (error) {
            console.error('[OrderInteractions] Order cancellation failed:', error);
            alert('주문 취소에 실패했습니다.\n\n' + error.message);
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        if (this.chartContainer) {
            this.chartContainer.removeEventListener('mousedown', this.handleMouseDown.bind(this));
            this.chartContainer.removeEventListener('mousemove', this.handleMouseMove.bind(this));
            this.chartContainer.removeEventListener('mouseup', this.handleMouseUp.bind(this));
            this.chartContainer.removeEventListener('mouseleave', this.handleMouseLeave.bind(this));
        }

        this.hideOrderDetails();

        console.log('[OrderInteractions] Cleaned up');
    }
}

// Export for use
window.OrderInteractions = OrderInteractions;
