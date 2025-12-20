// Manual Order Extension for WorkingTradingChart
// Add these methods to the WorkingTradingChart class

// In setupEventListeners(), add this line after the hide-unsupported toggle:
// this.initializeManualOrders();

WorkingTradingChart.prototype.initializeManualOrders = function() {
    console.log('[ManualOrders] Initializing manual order functionality');

    // Update order panel with current coin info
    this.updateOrderPanelCoin();
    this.updateAvailableBalances();

    // Buy price/quantity inputs - calculate total
    const buyPrice = document.getElementById('buy-price');
    const buyQuantity = document.getElementById('buy-quantity');
    const buyTotal = document.getElementById('buy-total-amount');

    if (buyPrice && buyQuantity && buyTotal) {
        const updateBuyTotal = () => {
            const price = parseFloat(buyPrice.value) || 0;
            const quantity = parseFloat(buyQuantity.value) || 0;
            const total = price * quantity;
            buyTotal.textContent = total.toLocaleString() + '원';
        };

        buyPrice.addEventListener('input', updateBuyTotal);
        buyQuantity.addEventListener('input', updateBuyTotal);
    }

    // Sell price/quantity inputs - calculate total
    const sellPrice = document.getElementById('sell-price');
    const sellQuantity = document.getElementById('sell-quantity');
    const sellTotal = document.getElementById('sell-total-amount');

    if (sellPrice && sellQuantity && sellTotal) {
        const updateSellTotal = () => {
            const price = parseFloat(sellPrice.value) || 0;
            const quantity = parseFloat(sellQuantity.value) || 0;
            const total = price * quantity;
            sellTotal.textContent = total.toLocaleString() + '원';
        };

        sellPrice.addEventListener('input', updateSellTotal);
        sellQuantity.addEventListener('input', updateSellTotal);
    }

    // Percentage buttons for buy orders
    const buyPercentButtons = document.querySelectorAll('.btn-percentage[data-side="buy"]');
    buyPercentButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active class from all buy buttons
            buyPercentButtons.forEach(b => b.classList.remove('active'));
            // Add active to clicked button
            btn.classList.add('active');

            const percent = parseInt(btn.dataset.percent);
            this.calculateBuyQuantity(percent);
        });
    });

    // Percentage buttons for sell orders
    const sellPercentButtons = document.querySelectorAll('.btn-percentage[data-side="sell"]');
    sellPercentButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Remove active class from all sell buttons
            sellPercentButtons.forEach(b => b.classList.remove('active'));
            // Add active to clicked button
            btn.classList.add('active');

            const percent = parseInt(btn.dataset.percent);
            this.calculateSellQuantity(percent);
        });
    });

    // Chart click to set price
    this.enableChartPriceSelection();

    // Buy order button
    const submitBuyBtn = document.getElementById('submit-buy-order');
    if (submitBuyBtn) {
        submitBuyBtn.addEventListener('click', () => this.submitBuyOrder());
    }

    // Sell order button
    const submitSellBtn = document.getElementById('submit-sell-order');
    if (submitSellBtn) {
        submitSellBtn.addEventListener('click', () => this.submitSellOrder());
    }

    // Refresh orders button
    const refreshOrdersBtn = document.getElementById('refresh-orders');
    if (refreshOrdersBtn) {
        refreshOrdersBtn.addEventListener('click', async () => {
            await this.loadPendingOrders();
            await this.displayOrdersOnChart();
        });
    }

    // Load pending orders
    this.loadPendingOrders();

    // Display orders on chart and enable dragging
    this.displayOrdersOnChart();
    this.enableOrderLineDragging();
};

WorkingTradingChart.prototype.updateOrderPanelCoin = function() {
    const coinSymbol = document.getElementById('order-coin-symbol');
    const currentPrice = document.getElementById('order-current-price');

    if (coinSymbol) {
        const symbol = this.currentMarket?.replace('KRW-', '') || 'BTC';
        coinSymbol.textContent = symbol;
        console.log('[ManualOrders] Updated coin symbol to:', symbol);
    }

    if (currentPrice && this.chartData && this.chartData.length > 0) {
        const latestCandle = this.chartData[this.chartData.length - 1];
        const price = latestCandle.close;
        currentPrice.textContent = price.toLocaleString() + '원';
        console.log('[ManualOrders] Updated current price to:', price.toLocaleString());
    }
};

WorkingTradingChart.prototype.submitBuyOrder = async function() {
    console.log('[ManualOrders] Submitting buy order');

    const priceInput = document.getElementById('buy-price');
    const quantityInput = document.getElementById('buy-quantity');

    const price = parseFloat(priceInput.value);
    const quantity = parseFloat(quantityInput.value);

    if (!price || price <= 0) {
        alert('매수 가격을 입력하세요');
        return;
    }

    if (!quantity || quantity <= 0) {
        alert('매수 수량을 입력하세요');
        return;
    }

    const market = this.currentMarket || 'KRW-BTC';

    try {
        const response = await fetch('http://localhost:8081/api/trading/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market: market,
                side: 'bid',
                price: price,
                volume: quantity,
                ord_type: 'limit'
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`매수 주문 성공!\n코인: ${market}\n가격: ${price.toLocaleString()}원\n수량: ${quantity}`);

            // Clear inputs
            priceInput.value = '';
            quantityInput.value = '';
            document.getElementById('buy-total-amount').textContent = '0원';

            // Reload pending orders and holdings
            await this.loadPendingOrders();
            await this.loadHoldings();
            await this.displayOrdersOnChart();
        } else {
            throw new Error(result.message || 'Order failed');
        }
    } catch (error) {
        console.error('[ManualOrders] Buy order error:', error);
        alert(`매수 주문 실패: ${error.message}`);
    }
};

WorkingTradingChart.prototype.submitSellOrder = async function() {
    console.log('[ManualOrders] Submitting sell order');

    const priceInput = document.getElementById('sell-price');
    const quantityInput = document.getElementById('sell-quantity');

    const price = parseFloat(priceInput.value);
    const quantity = parseFloat(quantityInput.value);

    if (!price || price <= 0) {
        alert('매도 가격을 입력하세요');
        return;
    }

    if (!quantity || quantity <= 0) {
        alert('매도 수량을 입력하세요');
        return;
    }

    const market = this.currentMarket || 'KRW-BTC';

    try {
        const response = await fetch('http://localhost:8081/api/trading/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market: market,
                side: 'ask',
                price: price,
                volume: quantity,
                ord_type: 'limit'
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(`매도 주문 성공!\n코인: ${market}\n가격: ${price.toLocaleString()}원\n수량: ${quantity}`);

            // Clear inputs
            priceInput.value = '';
            quantityInput.value = '';
            document.getElementById('sell-total-amount').textContent = '0원';

            // Reload pending orders and holdings
            await this.loadPendingOrders();
            await this.loadHoldings();
            await this.displayOrdersOnChart();
        } else {
            throw new Error(result.message || 'Order failed');
        }
    } catch (error) {
        console.error('[ManualOrders] Sell order error:', error);
        alert(`매도 주문 실패: ${error.message}`);
    }
};

WorkingTradingChart.prototype.loadPendingOrders = async function() {
    console.log('[ManualOrders] Loading pending orders');

    const orderList = document.getElementById('order-history-list');
    if (!orderList) return;

    try {
        const response = await fetch('http://localhost:8081/api/trading/orders?state=wait');
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error('Failed to load orders');
        }

        const orders = result.orders || [];

        if (orders.length === 0) {
            orderList.innerHTML = '<div class="empty-orders">주문 내역이 없습니다</div>';
            return;
        }

        orderList.innerHTML = orders.map(order => {
            const side = order.side === 'bid' ? 'buy' : 'sell';
            const sideText = order.side === 'bid' ? '매수' : '매도';
            const coinSymbol = order.market.replace('KRW-', '');
            const price = parseFloat(order.price).toLocaleString();
            const volume = parseFloat(order.volume).toFixed(4);

            return `
                <div class="order-item">
                    <div class="order-item-info">
                        <div class="order-item-type ${side}">${sideText}</div>
                        <div class="order-item-details">${coinSymbol} | ${price}원 × ${volume}</div>
                    </div>
                    <button class="order-item-cancel" onclick="window.tradingChart.cancelOrder('${order.uuid}')">취소</button>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('[ManualOrders] Error loading orders:', error);
        orderList.innerHTML = '<div class="empty-orders">주문 조회 실패</div>';
    }
};

WorkingTradingChart.prototype.cancelOrder = async function(uuid) {
    console.log('[ManualOrders] Cancelling order:', uuid);

    if (!confirm('이 주문을 취소하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`http://localhost:8081/api/trading/order/${uuid}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert('주문이 취소되었습니다');
            await this.loadPendingOrders();
        } else {
            throw new Error(result.message || 'Cancel failed');
        }
    } catch (error) {
        console.error('[ManualOrders] Cancel order error:', error);
        alert(`주문 취소 실패: ${error.message}`);
    }
};

// Update available balances for buy/sell
WorkingTradingChart.prototype.updateAvailableBalances = async function() {
    console.log('[ManualOrders] Updating available balances');

    try {
        // Get KRW balance for buying
        const response = await fetch('http://localhost:8081/api/account/balance');
        const result = await response.json();

        if (response.ok && result.success) {
            const krwBalance = result.balance || 0;
            const buyBalanceInfo = document.getElementById('buy-balance-info');
            if (buyBalanceInfo) {
                buyBalanceInfo.textContent = `잔액: ${krwBalance.toLocaleString()}원`;
            }
            this.krwBalance = krwBalance;
        }

        // Get current coin holding for selling
        const market = this.currentMarket || 'KRW-BTC';
        const holdingsResponse = await fetch('http://localhost:8081/api/holdings');
        const holdingsResult = await holdingsResponse.json();

        if (holdingsResponse.ok && holdingsResult.success) {
            const holdings = holdingsResult.holdings || [];
            const coinHolding = holdings.find(h => {
                const hMarket = h.market || `KRW-${h.symbol}`;
                return hMarket === market;
            });

            const quantity = coinHolding ? parseFloat(coinHolding.balance) : 0;
            const sellBalanceInfo = document.getElementById('sell-balance-info');
            if (sellBalanceInfo) {
                sellBalanceInfo.textContent = `보유: ${quantity.toFixed(4)}개`;
            }
            this.coinHolding = quantity;
        }

    } catch (error) {
        console.error('[ManualOrders] Error updating balances:', error);
    }
};

// Calculate buy quantity based on percentage
WorkingTradingChart.prototype.calculateBuyQuantity = function(percent) {
    console.log(`[ManualOrders] Calculating buy quantity: ${percent}%`);

    const buyPrice = document.getElementById('buy-price');
    const buyQuantity = document.getElementById('buy-quantity');
    const buyTotal = document.getElementById('buy-total-amount');

    const price = parseFloat(buyPrice.value);
    if (!price || price <= 0) {
        alert('먼저 차트에서 매수 가격을 선택하세요');
        return;
    }

    const balance = this.krwBalance || 0;
    const amountToUse = balance * (percent / 100);
    const quantity = Math.floor(amountToUse / price);

    buyQuantity.value = quantity;
    buyTotal.textContent = (price * quantity).toLocaleString() + '원';
};

// Calculate sell quantity based on percentage
WorkingTradingChart.prototype.calculateSellQuantity = function(percent) {
    console.log(`[ManualOrders] Calculating sell quantity: ${percent}%`);

    const sellPrice = document.getElementById('sell-price');
    const sellQuantity = document.getElementById('sell-quantity');
    const sellTotal = document.getElementById('sell-total-amount');

    const price = parseFloat(sellPrice.value);
    if (!price || price <= 0) {
        alert('먼저 차트에서 매도 가격을 선택하세요');
        return;
    }

    const holding = this.coinHolding || 0;
    const quantityToSell = holding * (percent / 100);

    sellQuantity.value = quantityToSell.toFixed(4);
    sellTotal.textContent = (price * quantityToSell).toLocaleString() + '원';
};

// Enable chart click to set order price
WorkingTradingChart.prototype.enableChartPriceSelection = function() {
    console.log('[ManualOrders] Enabling chart price selection');

    if (!this.chart || !this.priceSeries) {
        console.warn('[ManualOrders] Chart not ready for price selection');
        return;
    }

    // Subscribe to chart clicks
    this.chart.subscribeClick((param) => {
        if (param.time) {
            const price = param.seriesData.get(this.priceSeries);
            if (price) {
                // Use close price
                const clickedPrice = price.close || price.value;
                console.log(`[ManualOrders] Chart clicked at price: ${clickedPrice}`);

                // Set both buy and sell prices
                const buyPriceInput = document.getElementById('buy-price');
                const sellPriceInput = document.getElementById('sell-price');

                if (buyPriceInput) {
                    buyPriceInput.value = Math.floor(clickedPrice);
                    buyPriceInput.dispatchEvent(new Event('input'));
                }

                if (sellPriceInput) {
                    sellPriceInput.value = Math.floor(clickedPrice);
                    sellPriceInput.dispatchEvent(new Event('input'));
                }

                // Show feedback
                const orderCoinInfo = document.getElementById('order-current-price');
                if (orderCoinInfo) {
                    orderCoinInfo.textContent = Math.floor(clickedPrice).toLocaleString() + '원 선택';
                    orderCoinInfo.style.color = '#10b981';

                    setTimeout(() => {
                        orderCoinInfo.style.color = '';
                    }, 2000);
                }
            }
        }
    });
};

// Display pending orders on chart as draggable lines
WorkingTradingChart.prototype.displayOrdersOnChart = async function() {
    console.log('[ManualOrders] Displaying orders on chart');

    if (!this.chart || !this.priceSeries) {
        console.warn('[ManualOrders] Chart not ready for order display');
        return;
    }

    try {
        const market = this.selectedMarket || 'KRW-XRP';
        const response = await fetch(`http://localhost:8081/api/trading/orders?state=wait&market=${market}`);
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error('Failed to load orders');
        }

        const orders = result.orders || [];

        // Remove existing order lines
        if (this.orderLines) {
            this.orderLines.forEach(line => {
                this.priceSeries.removePriceLine(line.line);
            });
        }
        this.orderLines = [];

        // Add new order lines
        orders.forEach(order => {
            const price = parseFloat(order.price);
            const side = order.side; // 'bid' or 'ask'
            const volume = parseFloat(order.volume);

            const lineColor = side === 'bid' ? '#26a69a' : '#ef5350';
            const lineStyle = 2; // Dashed

            const priceLine = this.priceSeries.createPriceLine({
                price: price,
                color: lineColor,
                lineWidth: 2,
                lineStyle: lineStyle,
                axisLabelVisible: true,
                title: `${side === 'bid' ? 'BUY' : 'SELL'} ${volume.toFixed(4)}`
            });

            this.orderLines.push({
                line: priceLine,
                order: order,
                originalPrice: price
            });
        });

        console.log(`[ManualOrders] Displayed ${orders.length} orders on chart`);

    } catch (error) {
        console.error('[ManualOrders] Error displaying orders on chart:', error);
    }
};

// Enable dragging order lines to modify price
WorkingTradingChart.prototype.enableOrderLineDragging = function() {
    console.log('[ManualOrders] Enabling order line dragging');

    if (!this.chart || !this.priceSeries) {
        console.warn('[ManualOrders] Chart not ready for dragging');
        return;
    }

    let isDragging = false;
    let draggedOrderLine = null;

    // Mouse down - start dragging
    this.chart.subscribeClick((param) => {
        if (!param.point) return;

        const price = this.priceSeries.coordinateToPrice(param.point.y);

        // Find if user clicked near an order line
        if (this.orderLines) {
            for (let orderLine of this.orderLines) {
                const linePriceDiff = Math.abs(orderLine.originalPrice - price);
                const priceRange = this.getPriceRange();
                const tolerance = priceRange * 0.01; // 1% tolerance

                if (linePriceDiff < tolerance) {
                    isDragging = true;
                    draggedOrderLine = orderLine;
                    console.log('[ManualOrders] Started dragging order:', orderLine.order.uuid);
                    break;
                }
            }
        }
    });

    // Mouse move - update line position
    this.chart.subscribeCrosshairMove((param) => {
        if (!isDragging || !draggedOrderLine || !param.point) return;

        const newPrice = this.priceSeries.coordinateToPrice(param.point.y);

        // Update price line position
        draggedOrderLine.line.applyOptions({
            price: newPrice
        });
    });

    // Mouse up - commit change
    document.addEventListener('mouseup', async (e) => {
        if (isDragging && draggedOrderLine) {
            console.log('[ManualOrders] Finished dragging order');

            // Get final price from chart
            const chartRect = this.chart.chartElement().getBoundingClientRect();
            const y = e.clientY - chartRect.top;
            const finalPrice = this.priceSeries.coordinateToPrice(y);

            if (finalPrice && finalPrice !== draggedOrderLine.originalPrice) {
                await this.modifyOrder(draggedOrderLine.order.uuid, finalPrice);
            }

            isDragging = false;
            draggedOrderLine = null;
        }
    });
};

// Get current price range for tolerance calculation
WorkingTradingChart.prototype.getPriceRange = function() {
    if (!this.chartData || this.chartData.length === 0) return 1000;

    const prices = this.chartData.map(c => c.high);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);

    return maxPrice - minPrice;
};

// Modify order price via API
WorkingTradingChart.prototype.modifyOrder = async function(uuid, newPrice) {
    console.log(`[ManualOrders] Modifying order ${uuid} to price ${newPrice}`);

    try {
        // Cancel old order
        const cancelResponse = await fetch(`http://localhost:8081/api/trading/order/${uuid}`, {
            method: 'DELETE'
        });

        const cancelResult = await cancelResponse.json();

        if (!cancelResponse.ok || !cancelResult.success) {
            throw new Error('Failed to cancel order');
        }

        console.log('[ManualOrders] Old order cancelled, creating new order');

        // Get order details from the cancelled order
        const order = this.orderLines.find(ol => ol.order.uuid === uuid)?.order;
        if (!order) {
            throw new Error('Order not found in orderLines');
        }

        // Create new order with new price
        const createResponse = await fetch('http://localhost:8081/api/trading/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market: order.market,
                side: order.side,
                price: Math.floor(newPrice),
                volume: parseFloat(order.volume),
                ord_type: 'limit'
            })
        });

        const createResult = await createResponse.json();

        if (createResponse.ok && createResult.success) {
            alert(`주문 가격 변경 완료!\n새 가격: ${Math.floor(newPrice).toLocaleString()}원`);

            // Reload orders
            await this.loadPendingOrders();
            await this.displayOrdersOnChart();
        } else {
            throw new Error(createResult.message || 'Failed to create new order');
        }

    } catch (error) {
        console.error('[ManualOrders] Error modifying order:', error);
        alert(`주문 변경 실패: ${error.message}`);

        // Reload to restore correct state
        await this.displayOrdersOnChart();
    }
};
