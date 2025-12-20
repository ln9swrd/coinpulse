/**
 * ========================================
 * DATA LOADER MODULE
 * ========================================
 * Handles all data loading operations for the trading chart
 * Uses delegation pattern - holds reference to chart instance
 *
 * @class DataLoader
 */

class DataLoader {
    constructor(chart) {
        this.chart = chart;
        console.log('[DataLoader] Module initialized');
    }

        async loadData() {
            try {
                console.log('[Working] Loading initial candles...');
                await this.loadInitialCandles();
                this.setupTradingViewStyleLoading();
                this.chart.realtimeUpdates.startAutoUpdate();
            } catch (error) {
                console.error('[Working] Failed to load data:', error);
            }
        }

        async loadInitialCandles() {
            try {
                console.log(`[Working] Loading initial candles from Upbit... (${this.chart.currentTimeframe}, unit: ${this.chart.currentUnit})`);
    
                // API Handler를 통해 데이터 요청 (설정 파일 기반)
                const result = await window.apiHandler.getCandles(
                    this.chart.currentTimeframe,
                    this.chart.currentMarket,
                    200,
                    this.chart.currentUnit
                );
    
                if (!result.success || !result.data) {
                    throw new Error('Failed to load initial candles');
                }
    
                const upbitData = result.data;
                console.log(`[Working] Received ${upbitData.length} initial candles`);

                // Convert data
                const candles = [];
                const volume = [];

                // 초기 데이터는 최신부터 반환되므로 시간순으로 정렬 (원본 배열 보존)
                [...upbitData].reverse().forEach((item) => {
                    const time = Math.floor(new Date(item.candle_date_time_utc).getTime() / 1000);
                    const open = Number(item.opening_price);
                    const high = Number(item.high_price);
                    const low = Number(item.low_price);
                    const close = Number(item.trade_price);
                    const vol = Number(item.candle_acc_trade_volume);
    
                    // Validate
                    if (!isNaN(time) && !isNaN(open) && !isNaN(high) && !isNaN(low) && !isNaN(close) && !isNaN(vol)) {
                        candles.push({ time, open, high, low, close });
                        volume.push({ time, value: vol, color: close >= open ? '#26a69a' : '#ef5350' });
                    }
                });
    
                this.chart.loadedCandles = candles;
                this.chart.loadedVolume = volume;
                this.chart.chartData = candles;
    
                // 타임스탬프 설정
                if (candles.length > 0) {
                    this.chart.oldestTimestamp = candles[0].time;
                    this.chart.newestTimestamp = candles[candles.length - 1].time;
                }
    
                console.log(`[Working] Converted ${candles.length} initial candles, oldest: ${this.chart.oldestTimestamp}, newest: ${this.chart.newestTimestamp}`);
    
                // 거래량 데이터 확인 로그
                if (volume.length > 0) {
                    const volumeValues = volume.map(v => v.value);
                    const minVol = Math.min(...volumeValues);
                    const maxVol = Math.max(...volumeValues);
                    const avgVol = volumeValues.reduce((a, b) => a + b, 0) / volumeValues.length;
                    console.log('[Working] Volume stats:', {
                        count: volume.length,
                        min: minVol.toFixed(2),
                        max: maxVol.toFixed(2),
                        avg: avgVol.toFixed(2),
                        sample: volume.slice(0, 3)
                    });
                }
    
                // Set data using ChartUtils
                window.chartUtils.setData(candles, volume);
                console.log('[Working] Initial data set successfully');
    
                // 초기 로드시 이평선은 표시하지 않음
                this.chart.clearMAs();
    
                // MA 토글 버튼 상태 업데이트 (하나라도 활성화되어 있으면 active)
                const maToggleBtn = document.getElementById('ma-toggle');
                if (maToggleBtn) {
                    maToggleBtn.classList.remove('active');
                }
    
                // Update price info header
                this.chart.realtimeUpdates.updatePriceInfo();
    
                // Update real-time analysis panel
                this.chart.realtimeUpdates.updateRealTimeAnalysis();
    
                // 평균단가와 미체결 주문 수평선 표시 (차트 데이터 로드 완료 후)
                await this.chart.updateAvgPriceAndPendingOrders().catch(err => {
                    console.error('[Working] Failed to draw avg price and pending orders:', err);
                });
    
            } catch (error) {
                console.error('[Working] Failed to load initial candles:', error);
            }
        }

        setupTradingViewStyleLoading() {
            if (!this.chart.chart) {
                console.error('[Working] Chart not available for setupTradingViewStyleLoading');
                return;
            }
    
            console.log('[Working] Setting up TradingView style loading...');
    
            // 시간 스케일 변경 이벤트 리스너 (활성화)
            this.chart.chart.timeScale().subscribeVisibleLogicalRangeChange(async () => {
                const logicalRange = this.chart.chart.timeScale().getVisibleLogicalRange();
                if (!logicalRange) return;
    
                // 왼쪽 끝에 가까워지면 과거 데이터 로드 (10개 캔들 이내)
                if (logicalRange.from < 10 && !this.chart.isLoading && this.chart.hasMoreData) {
                    console.log('[Working] Near left edge, loading more historical data...');
                    await this.loadHistoricalData();
                }
            });
    
            console.log('[Working] TradingView style loading setup completed');
        }

        async loadHistoricalData() {
            if (this.chart.isLoading || !this.chart.hasMoreData) return;
    
            this.chart.isLoading = true;
            try {
                console.log('[Working] Loading historical data from:', this.chart.oldestTimestamp);
    
                // oldestTimestamp를 기준으로 이전 데이터 요청
                const toDate = new Date(this.chart.oldestTimestamp * 1000);
                toDate.setDate(toDate.getDate() - 1); // 1일 전으로 설정 (겹침 방지)
                const toParam = toDate.toISOString().replace('T', ' ').split('.')[0];
    
                console.log('[Working] TO parameter:', toParam);
    
                // API Handler를 통해 데이터 요청 (설정 파일 기반)
                const result = await window.apiHandler.getCandles(
                    this.chart.currentTimeframe,
                    this.chart.currentMarket,
                    200,
                    this.chart.currentUnit,
                    toParam
                );
                
                if (!result.success || !result.data || result.data.length === 0) {
                    console.log('[Working] No more historical data available');
                    this.chart.hasMoreData = false;
                    return;
                }
                
                const upbitData = result.data;
                console.log(`[Working] Received ${upbitData.length} historical candles`);
    
                // Convert data
                const newCandles = [];
                const newVolume = [];

                // 과거 데이터는 최신순이므로 reverse 필요 (원본 배열 보존)
                [...upbitData].reverse().forEach((item) => {
                    const time = Math.floor(new Date(item.candle_date_time_utc).getTime() / 1000);
                    const open = Number(item.opening_price);
                    const high = Number(item.high_price);
                    const low = Number(item.low_price);
                    const close = Number(item.trade_price);
                    const vol = Number(item.candle_acc_trade_volume);
    
                    // Validate
                    if (!isNaN(time) && !isNaN(open) && !isNaN(high) && !isNaN(low) && !isNaN(close) && !isNaN(vol)) {
                        newCandles.push({ time, open, high, low, close });
                        newVolume.push({ time, value: vol, color: close >= open ? '#26a69a' : '#ef5350' });
                    }
                });
    
                if (newCandles.length > 0) {
                    // 중복 제거: 기존에 없는 새로운 캔들만 추가
                    const existingTimes = new Set(this.chart.loadedCandles.map(c => c.time));
                    const uniqueNewCandles = newCandles.filter(c => !existingTimes.has(c.time));
    
                    if (uniqueNewCandles.length > 0) {
                        // 기존 데이터와 병합 (과거 데이터는 앞에 추가)
                        this.chart.loadedCandles = [...uniqueNewCandles, ...this.chart.loadedCandles];
                        this.chart.chartData = this.chart.loadedCandles; // chartData도 동기화
                        this.chart.oldestTimestamp = uniqueNewCandles[0].time;
    
                        console.log(`[Working] Added ${uniqueNewCandles.length} unique historical candles (${newCandles.length - uniqueNewCandles.length} duplicates filtered), new oldest: ${this.chart.oldestTimestamp}`);
    
                        // 차트 업데이트 (ChartUtils의 setData 사용)
                        if (window.chartUtils) {
                            // 기존 volume 데이터와 새로운 volume 데이터 병합
                            const existingVolumeTimes = new Set(this.chart.loadedVolume.map(v => v.time));
                            const uniqueNewVolume = newVolume.filter(v => !existingVolumeTimes.has(v.time));
                            
                            // 과거 볼륨 데이터는 앞에 추가
                            this.chart.loadedVolume = [...uniqueNewVolume, ...this.chart.loadedVolume];
                            
                            window.chartUtils.setData(this.chart.loadedCandles, this.chart.loadedVolume);
                            console.log(`[Working] Chart updated with ${this.chart.loadedCandles.length} candles and ${this.chart.loadedVolume.length} volume data`);
    
                            // 이평선 업데이트
                            this.chart.realtimeUpdates.updateMAs();
    
                            // 지지저항선 업데이트 (활성화되어 있을 경우)
                            if (this.chart.supportResistanceEnabled) {
                                console.log('[Working] Re-applying support/resistance after historical data load');
                                this.chart.drawSupportResistance();
                            }
    
                            // 가격 정보 업데이트
                            this.chart.realtimeUpdates.updatePriceInfo();
                        } else {
                            console.error('[Working] ChartUtils not available');
                        }
                    } else {
                        console.log('[Working] All historical candles were duplicates, no new data added');
                        // 중복만 있고 새로운 데이터가 없으면 더 이상 데이터가 없을 수 있음
                        if (newCandles.length < 200) {
                            console.log('[Working] Less than 200 candles returned, marking as no more data');
                            this.chart.hasMoreData = false;
                        }
                    }
                }
    
            } catch (error) {
                console.error('[Working] Failed to load historical data:', error);
            } finally {
                this.chart.isLoading = false;
            }
        }

        async loadLatestData() {
            try {
                console.log('[Working] Loading latest data...');
    
                // API Handler를 통해 데이터 요청 (설정 파일 기반)
                const result = await window.apiHandler.getCandles(
                    this.chart.currentTimeframe,
                    this.chart.currentMarket,
                    10,
                    this.chart.currentUnit
                );
                
                if (!result.success || !result.data || result.data.length === 0) return;
                
                const upbitData = result.data;
                console.log(`[Working] Received ${upbitData.length} latest candles`);
                console.log('[Working] Latest candles data:', upbitData);
    
                // Convert data
                const latestCandles = [];
                const latestVolume = [];

                // 최신 데이터는 최신부터 반환되므로 시간순으로 정렬 (원본 배열 보존)
                [...upbitData].reverse().forEach((item) => {
                    const time = Math.floor(new Date(item.candle_date_time_utc).getTime() / 1000);
                    const open = Number(item.opening_price);
                    const high = Number(item.high_price);
                    const low = Number(item.low_price);
                    const close = Number(item.trade_price);
                    const vol = Number(item.candle_acc_trade_volume);
    
                    // Validate
                    if (!isNaN(time) && !isNaN(open) && !isNaN(high) && !isNaN(low) && !isNaN(close) && !isNaN(vol)) {
                        latestCandles.push({ time, open, high, low, close });
                        latestVolume.push({ time, value: vol, color: close >= open ? '#26a69a' : '#ef5350' });
                    }
                });
    
                if (latestCandles.length > 0) {
                    // 기존 데이터와 병합 (최신 데이터는 뒤에 추가)
                    const existingTimes = new Set(this.chart.loadedCandles.map(c => c.time));
                    const newCandles = latestCandles.filter(c => !existingTimes.has(c.time));
    
                    if (newCandles.length > 0) {
                        console.log('[Working] New candles to add:', newCandles);
                        console.log('[Working] Current loadedCandles count:', this.chart.loadedCandles.length);
    
                        this.chart.loadedCandles = [...this.chart.loadedCandles, ...newCandles];
                        this.chart.chartData = this.chart.loadedCandles; // chartData도 동기화
                        // 새로 추가된 캔들 중 가장 최신 시간으로 업데이트
                        this.chart.newestTimestamp = newCandles[newCandles.length - 1].time;
    
                        console.log(`[Working] Added ${newCandles.length} unique latest candles (${latestCandles.length - newCandles.length} duplicates filtered), new newest: ${this.chart.newestTimestamp}`);
                        console.log('[Working] Total loadedCandles after merge:', this.chart.loadedCandles.length);
    
                        // 차트 업데이트 (ChartUtils의 setData 사용)
                        if (window.chartUtils) {
                            // volume 데이터도 함께 업데이트
                            const volumeData = this.chart.loadedCandles.map(c => ({
                                time: c.time,
                                value: 0, // volume 데이터는 별도로 관리 필요
                                color: c.close >= c.open ? '#26a69a' : '#ef5350'
                            }));
    
                            window.chartUtils.setData(this.chart.loadedCandles, volumeData);
                            console.log(`[Working] Chart updated with ${this.chart.loadedCandles.length} candles`);
    
                            // 이평선 업데이트
                            this.chart.realtimeUpdates.updateMAs();
                            
                            // SuperTrend 업데이트 (활성화 되어있을 경우)
                            this.chart.updateSuperTrend();
    
                            // 가격 정보 업데이트
                            this.chart.realtimeUpdates.updatePriceInfo();
                        } else {
                            console.error('[Working] ChartUtils not available');
                        }
                    } else {
                        console.log('[Working] All latest candles were duplicates, no new data added');
                    }
                }
    
            } catch (error) {
                console.error('[Working] Failed to load latest data:', error);
            }
        }

        async loadBackgroundData() {
            try {
                console.log('[Working] Loading background data...');
    
                // 병렬로 로딩 (동시 실행으로 속도 2배 향상)
                await Promise.all([
                    this.loadHoldings().catch(err => {
                        console.error('[Working] Holdings loading failed:', err);
                    }),
                    this.loadTradingHistory().catch(err => {
                        console.error('[Working] Trading history loading failed:', err);
                    })
                ]);
    
                // Note: 평균단가와 미체결 주문은 loadInitialCandles()에서 차트 데이터 로드 완료 후 그려집니다
    
                console.log('[Working] Background data loading completed');
            } catch (error) {
                console.error('[Working] Background data loading failed:', error);
            }
        }

        async loadHoldings() {
            try {
                console.log('[Working] Loading holdings...');
    
                if (!window.apiHandler) {
                    console.error('[Working] APIHandler not available');
                    return;
                }
    
                const holdingsList = document.getElementById('holdings-list');
                if (!holdingsList) {
                    console.error('[Working] Holdings list element not found');
                    return;
                }
    
                // 로딩 상태 표시
                holdingsList.innerHTML = '<div class="loading-state">보유 코인 로딩 중...</div>';
    
                const response = await window.apiHandler.getHoldings();
                console.log('[Working] Holdings response:', response);
    
                // Update KRW Balance Section
                if (response.krw) {
                    const krw = response.krw;
                    const balance = krw.balance || krw || 0;
                    const locked = krw.locked || 0;
                    const total = krw.total || balance;
                    document.getElementById('krw-balance').textContent =
                        `${balance.toLocaleString()} KRW`;
                    document.getElementById('krw-locked').textContent =
                        `${locked.toLocaleString()} KRW`;
                    document.getElementById('krw-total').textContent =
                        `${total.toLocaleString()} KRW`;
                    console.log('[Working] KRW balance updated:', { balance, locked, total });
                }
    
                // Update Portfolio Summary Section
                if (response.summary) {
                    const summary = response.summary;
                    const totalValue = summary.total_value_krw || summary.total_value || 0;
                    const cryptoValue = summary.total_crypto_value || (totalValue - (response.krw || 0)) || 0;
                    const totalProfit = summary.total_profit_loss_krw || summary.total_profit || 0;
                    const profitRate = summary.total_profit_rate || summary.profit_rate || 0;
                    const coinCount = summary.coin_count || 0;

                    document.getElementById('summary-total-value').textContent =
                        `${totalValue.toLocaleString()} KRW`;
                    document.getElementById('summary-crypto-value').textContent =
                        `${cryptoValue.toLocaleString()} KRW`;

                    const profitEl = document.getElementById('summary-profit');
                    profitEl.textContent = `${totalProfit >= 0 ? '+' : ''}${totalProfit.toLocaleString()} KRW`;
                    profitEl.className = `summary-item-value ${totalProfit >= 0 ? 'profit' : 'loss'}`;

                    const profitRateEl = document.getElementById('summary-profit-rate');
                    profitRateEl.textContent = `${profitRate >= 0 ? '+' : ''}${profitRate.toFixed(2)}%`;
                    profitRateEl.className = `summary-item-value ${profitRate >= 0 ? 'profit' : 'loss'}`;

                    document.getElementById('summary-coin-count').textContent =
                        `${coinCount} coins`;
                    console.log('[Working] Portfolio summary updated:', { totalValue, cryptoValue, totalProfit, profitRate, coinCount });
                }
    
                // 서버 응답 처리: 여러 형태 지원
                // 1. {coins: [...]}
                // 2. {success: true, coins: [...]}
                // 3. {success: true, data: {coins: [...]}}
                const coins = response.coins || (response.data && response.data.coins) || [];
    
                if (coins.length === 0) {
                    holdingsList.innerHTML = '<div class="empty-state">보유 코인 없음</div>';
                    console.log('[Working] No holdings found');
                    return;
                }
    
                // Clear loading state
                holdingsList.innerHTML = '';
    
                // Check if unsupported coins should be hidden
                const hideUnsupported = document.getElementById('hide-unsupported')?.checked ?? true;
    
                // Display each holding
                console.log(`[Working] Processing ${coins.length} holdings...`);
    
                let displayedCount = 0;
                coins.forEach((holding, index) => {
                    try {
                        const coinName = holding.symbol || holding.coin || 'Unknown';
    
                        // Filter unsupported coins if toggle is checked
                        if (hideUnsupported && this.chart.unsupportedCoins.includes(coinName.toUpperCase())) {
                            console.log(`[Working] Hiding unsupported coin: ${coinName}`);
                            return; // Skip this coin
                        }
    
                        const holdingItem = document.createElement('div');
                        holdingItem.className = 'coin-item';
    
                        const balance = parseFloat(holding.amount) || 0;
                        const avgPrice = parseFloat(holding.avg_price) || 0;
                        const currentPrice = parseFloat(holding.current_price) || 0;
                        const profitRate = parseFloat(holding.profit_rate) || 0;
                        const totalValue = parseFloat(holding.total_value) || 0;
    
                        // 마켓 코드 추출 (symbol이 XRP 형태면 KRW-XRP로 변환)
                        let marketCode = holding.market || holding.symbol;
                        if (marketCode && !marketCode.startsWith('KRW-')) {
                            marketCode = `KRW-${marketCode}`;
                        }
    
                        // Get policy info for this coin
                        let policyBadgeHTML = '';
                        if (window.policyModalController && window.policyModalController.policies) {
                            const policy = window.policyModalController.policies.coin_policies?.[marketCode];
                            if (policy) {
                                // Check if manual trading
                                if (policy.strategy === 'manual' || policy.enabled === false) {
                                    policyBadgeHTML = `<div class="holding-policy-badge manual" onclick="event.stopPropagation(); window.policyModalController.openModal(); window.policyModalController.onCoinChanged('${marketCode}');">수동</div>`;
                                } else {
                                    const stopLossPct = (policy.stop_loss || 0) * 100;
                                    const takeProfitPct = (policy.take_profit || 0) * 100;
    
                                    let riskLevel = 'balanced';
                                    let riskLabel = '균형';
    
                                    if (stopLossPct <= 2 && takeProfitPct <= 8) {
                                        riskLevel = 'conservative';
                                        riskLabel = '안정';
                                    } else if (stopLossPct >= 5 && takeProfitPct >= 15) {
                                        riskLevel = 'aggressive';
                                        riskLabel = '공격';
                                    }
    
                                    policyBadgeHTML = `<div class="holding-policy-badge ${riskLevel}" onclick="event.stopPropagation(); window.policyModalController.openModal(); window.policyModalController.onCoinChanged('${marketCode}');">${riskLabel}</div>`;
                                }
                            } else {
                                policyBadgeHTML = `<div class="holding-policy-badge none" onclick="event.stopPropagation(); window.policyModalController.openModal(); window.policyModalController.onCoinChanged('${marketCode}');">-</div>`;
                            }
                        } else {
                            policyBadgeHTML = `<div class="holding-policy-badge none">-</div>`;
                        }
    
                        // 코인 아이콘 이미지 URL 가져오기
                        const coinIconUrl = this.getCoinIcon(coinName);
    
                        holdingItem.innerHTML = `
                            <div class="coin-symbol">
                                <img class="coin-icon" src="${coinIconUrl}" alt="${coinName}" onerror="this.style.display='none'">
                                <span class="coin-name">${coinName}</span>
                            </div>
                            <div class="coin-avg-price">${avgPrice.toLocaleString()}원</div>
                            ${policyBadgeHTML}
                            <div class="coin-profit ${profitRate >= 0 ? 'profit' : 'loss'}">
                                    ${profitRate >= 0 ? '+' : ''}${profitRate.toFixed(2)}%
                            </div>
                        `;
    
                        // 클릭 이벤트: 해당 코인 차트로 전환 및 정책 모달 코인 선택
                        holdingItem.style.cursor = 'pointer';
                        holdingItem.addEventListener('click', async () => {
                            console.log(`[Working] Holding clicked: ${marketCode}`);
                            if (marketCode) {
                                // selectbox 값 변경
                                const coinSelect = document.getElementById('coin-select');
                                if (coinSelect) {
                                    // 해당 코인이 selectbox에 있는지 확인
                                    const option = Array.from(coinSelect.options).find(opt => opt.value === marketCode);
                                    if (option) {
                                        coinSelect.value = marketCode;
                                    } else {
                                        console.warn(`[Working] Market ${marketCode} not found in coin list`);
                                    }
                                }
                                // 차트 업데이트
                                await this.chart.changeCoin(marketCode);
    
                                // 정책 모달의 코인 선택도 업데이트
                                if (window.policyModalController) {
                                    window.policyModalController.currentCoin = marketCode;
                                    console.log(`[Working] Policy modal coin updated to: ${marketCode}`);
                                }
                            }
                        });
    
                        holdingsList.appendChild(holdingItem);
                        displayedCount++;
                        
                        console.log(`[Working] ${index + 1}/${coins.length}: ${coinName} (${marketCode}) - ${profitRate.toFixed(2)}%`);
                    } catch (itemError) {
                        console.error(`[Working] Error displaying holding ${index}:`, itemError, holding);
                    }
                });
    
                console.log(`[Working] Holdings loaded successfully: ${displayedCount}/${coins.length} displayed`);
    
                // Auto-create manual policies for holdings without policy
                await this.autoCreateManualPolicies(coins);
            } catch (error) {
                console.error('[Working] Holdings loading failed:', error);
                const holdingsList = document.getElementById('holdings-list');
                if (holdingsList) {
                    holdingsList.innerHTML = '<div class="error-state">Failed to load holdings</div>';
                }
            }
        }

        async autoCreateManualPolicies(coins) {
            try {
                if (!window.policyModalController || !window.policyModalController.policies) {
                    console.log('[Working] Policy controller not ready, skipping auto-create');
                    return;
                }
    
                const policies = window.policyModalController.policies;
                let needsSave = false;
                let createdCount = 0;
    
                // Ensure coin_policies object exists
                if (!policies.coin_policies) {
                    policies.coin_policies = {};
                }
    
                // Check each holding coin
                for (const holding of coins) {
                    let marketCode = holding.market || holding.symbol;
                    if (marketCode && !marketCode.startsWith('KRW-')) {
                        marketCode = `KRW-${marketCode}`;
                    }
    
                    // Skip if policy already exists
                    if (policies.coin_policies[marketCode]) {
                        continue;
                    }
    
                    // Create manual policy for this coin
                    policies.coin_policies[marketCode] = {
                        enabled: false,
                        strategy: 'manual',
                        timeframe: '1d',
                        stop_loss: 0.0,
                        take_profit: 0.0,
                        position_size: 0.0,
                        buy_threshold: 0.02,
                        sell_threshold: 0.05,
                        indicators: []
                    };
    
                    console.log(`[Working] Auto-created manual policy for: ${marketCode}`);
                    createdCount++;
                    needsSave = true;
                }
    
                // Save policies if any were created
                if (needsSave) {
                    console.log(`[Working] Saving ${createdCount} new manual policies...`);
    
                    const baseUrl = window.apiHandler?.API_CONFIG?.tradingServer || window.location.origin;
                    const response = await fetch(`${baseUrl}/api/trading/policies`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(policies)
                    });
    
                    if (response.ok) {
                        console.log(`[Working] Successfully saved ${createdCount} manual policies`);
    
                        // Reload policies in modal controller
                        if (window.policyModalController) {
                            await window.policyModalController.loadPolicies();
                        }
                    } else {
                        console.error('[Working] Failed to save manual policies');
                    }
                } else {
                    console.log('[Working] All holdings already have policies');
                }
            } catch (error) {
                console.error('[Working] Error auto-creating manual policies:', error);
            }
        }

        /**
         * Load trading history for modal display (skip chart_actions)
         */
        async loadTradingHistoryForModal(forceRefresh = false) {
            console.log('[DataLoader] loadTradingHistoryForModal called (for modal display)');
            // Skip chart_actions and go directly to modal display logic
            await this.loadTradingHistoryImpl(forceRefresh);
        }

        async loadTradingHistory(forceRefresh = false) {
            // Use ChartActions module if available
            if (this.chart.chartActions) {
                await this.chart.chartActions.loadTradingHistory(forceRefresh);
                return;
            }

            // Fallback to original implementation
            await this.loadTradingHistoryImpl(forceRefresh);
        }

        async loadTradingHistoryImpl(forceRefresh = false) {
            try {
                console.log(`[DataLoader] Loading trading history for ${this.chart.currentMarket}... (forceRefresh: ${forceRefresh})`);

                if (!window.apiHandler) {
                    console.error('[DataLoader] APIHandler not available');
                    return;
                }

                const historyList = document.getElementById('history-list');
                console.log('[DataLoader] History list element:', historyList);
                if (!historyList) {
                    console.error('[DataLoader] History list element not found - cannot display trading history');
                    return;
                }
    
                // Show loading state
                historyList.innerHTML = '<div class="loading-state">Loading trading history...</div>';
                console.log('[DataLoader] Loading state displayed');

                // forceRefresh가 true면 캐시를 무시하고 새로 로드
                // limit을 100으로 증가하여 더 많은 이력 조회
                console.log('[DataLoader] Calling getOrders API...');
                console.log('[DataLoader] - Market:', this.chart.currentMarket);
                console.log('[DataLoader] - State: done, Limit: 100');
                console.log('[DataLoader] - Use cache:', !forceRefresh);

                const response = await window.apiHandler.getOrders(this.chart.currentMarket, 'done', 100, !forceRefresh);
                console.log(`[DataLoader] Trading history response for ${this.chart.currentMarket}:`, response);
                console.log('[DataLoader] Response success:', response?.success);
                console.log('[DataLoader] Response orders count:', response?.orders?.length);

                // 서버 응답: {success: true, orders: [...]}
                const orders = response.orders || (response.data && response.data.orders) || [];
                console.log('[DataLoader] Extracted orders count:', orders.length);

                if (!response.success || orders.length === 0) {
                    console.warn('[DataLoader] No orders to display');
                    historyList.innerHTML = `<div class="empty-state">${this.chart.currentMarket} 매매 이력 없음</div>`;
                    return;
                }
    
                // Clear loading state
                historyList.innerHTML = '';
    
                // Display each order
                console.log(`[Working] Displaying ${orders.length} orders for ${this.chart.currentMarket}`);
                
                // 최대 50개까지 표시 (100개 조회했지만 화면에는 50개만)
                orders.slice(0, 50).forEach((order, index) => {
                    const orderItem = document.createElement('div');
                    orderItem.className = 'history-item';
    
                    const side = order.side || 'unknown';
                    const price = parseFloat(order.price) || 0;
                    const volume = parseFloat(order.volume) || parseFloat(order.executed_volume) || 0;
                    const createdAt = order.created_at_kr || order.created_at || new Date().toISOString();
                    const state = order.state || 'done';
                    const market = order.market || this.chart.currentMarket;
                    const coin = order.coin || market.split('-')[1] || '???';
                    
                    const typeClass = side === 'bid' ? 'buy' : 'sell';
                    const typeText = side === 'bid' ? '매수' : '매도';
                    const typeIcon = side === 'bid' ? '📈' : '📉';
                    const typeColor = side === 'bid' ? '#00c851' : '#ff4444';
                    
                    const stateText = state === 'done' ? '체결' : 
                                    state === 'cancel' ? '취소' : 
                                    state === 'wait' ? '대기' : state;
                    const stateClass = state === 'done' ? 'completed' : 
                                     state === 'cancel' ? 'cancelled' : 
                                     state === 'wait' ? 'pending' : 'unknown';
                    
                    // 날짜 파싱 (한글 날짜 형식 또는 ISO 형식 지원)
                    let timeString;
                    if (createdAt.includes('T')) {
                        const date = new Date(createdAt);
                        const month = String(date.getMonth() + 1).padStart(2, '0');
                        const day = String(date.getDate()).padStart(2, '0');
                        const hours = String(date.getHours()).padStart(2, '0');
                        const minutes = String(date.getMinutes()).padStart(2, '0');
                        timeString = `${month}.${day} ${hours}:${minutes}`;
                    } else {
                        // 이미 "2025-09-23 03:52:38" 형식
                        const parts = createdAt.split(' ');
                        if (parts.length >= 2) {
                            const dateParts = parts[0].split('-');
                            const timeParts = parts[1].split(':');
                            timeString = `${dateParts[1]}.${dateParts[2]} ${timeParts[0]}:${timeParts[1]}`;
                        } else {
                            timeString = createdAt;
                        }
                    }
                    
                    const totalAmount = price * volume;
    
                    orderItem.style.borderLeft = `3px solid ${typeColor}`;
                    orderItem.innerHTML = `
                        <div class="history-type ${typeClass}" style="color: ${typeColor}">
                            ${typeIcon} ${typeText}
                        </div>
                        <div class="history-details">
                            <div class="history-time">${timeString}</div>
                            <div class="history-info">${volume.toFixed(4)} ${coin} × ${price.toLocaleString()}원</div>
                        </div>
                    `;
    
                    historyList.appendChild(orderItem);
                    
                    if (index === 0) {
                        console.log(`[Working] First order: ${typeText} ${volume} ${coin} at ${price} (${timeString})`);
                    }
                });
    
                console.log(`[Working] Trading history loaded successfully: ${orders.length} orders for ${this.chart.currentMarket}`);
                
                // 매매 이력을 차트에 마커로 표시
                this.addTradingHistoryMarkers(orders);
                
            } catch (error) {
                console.error('[Working] Trading history loading failed:', error);
                const historyList = document.getElementById('history-list');
                if (historyList) {
                    historyList.innerHTML = '<div class="error-state">Failed to load trading history</div>';
                }
            }
        }

        /**
         * Get visible time range from chart
         * @returns {Object|null} {from: timestamp, to: timestamp} or null
         */
        getVisibleTimeRange() {
            try {
                if (!this.chart.chartData || this.chart.chartData.length === 0) {
                    return null;
                }

                const chartData = this.chart.chartData;
                const chart = window.chartUtils?.chart;

                if (!chart) {
                    // Fallback: return full range
                    return {
                        from: chartData[0].time,
                        to: chartData[chartData.length - 1].time
                    };
                }

                const timeScale = chart.timeScale();
                if (!timeScale) {
                    return {
                        from: chartData[0].time,
                        to: chartData[chartData.length - 1].time
                    };
                }

                try {
                    const visibleLogicalRange = timeScale.getVisibleLogicalRange();
                    if (visibleLogicalRange) {
                        const fromIndex = Math.max(0, Math.floor(visibleLogicalRange.from));
                        const toIndex = Math.min(chartData.length - 1, Math.ceil(visibleLogicalRange.to));

                        return {
                            from: chartData[fromIndex].time,
                            to: chartData[toIndex].time
                        };
                    }
                } catch (e) {
                    console.warn('[DataLoader] Could not get visible logical range:', e);
                }

                // Fallback: return full range
                return {
                    from: chartData[0].time,
                    to: chartData[chartData.length - 1].time
                };
            } catch (error) {
                console.error('[DataLoader] Error getting visible time range:', error);
                return null;
            }
        }

        addTradingHistoryMarkers(orders) {
            if (!window.chartUtils || !this.chart.candleSeries) {
                console.log('[Working] Chart not ready for markers');
                return;
            }

            // 마커 표시가 꺼져있으면 무시
            if (!this.chart.showTradeMarkers) {
                console.log('[Working] Trade markers are disabled');
                this.chart.candleSeries.setMarkers([]);
                return;
            }

            try {
                // Get visible time range
                const visibleRange = this.getVisibleTimeRange();

                // Filter orders to only those in visible range
                let visibleOrders = orders;
                if (visibleRange) {
                    visibleOrders = orders.filter(order => {
                        try {
                            const timeStr = [order.executed_at, order.created_at, order.kr_time, order.created_at_kr]
                                .find(t => t && t !== 'N/A' && t !== 'null');

                            if (!timeStr) return false;

                            let timestamp;
                            if (timeStr.includes('T')) {
                                timestamp = Math.floor(new Date(timeStr).getTime() / 1000);
                            } else {
                                timestamp = Math.floor(new Date(timeStr.replace(' ', 'T')).getTime() / 1000);
                            }

                            if (isNaN(timestamp)) return false;

                            return timestamp >= visibleRange.from && timestamp <= visibleRange.to;
                        } catch (e) {
                            return false;
                        }
                    });

                    const fromDate = new Date(visibleRange.from * 1000).toLocaleDateString('ko-KR');
                    const toDate = new Date(visibleRange.to * 1000).toLocaleDateString('ko-KR');
                    console.log(`[DataLoader] Filtered ${orders.length} orders to ${visibleOrders.length} visible orders (${fromDate} ~ ${toDate})`);
                }

                const markers = [];

                visibleOrders.forEach(order => {
                    // Find first valid timestamp (not null, not undefined, not 'N/A')
                    const timeStr = [order.executed_at, order.created_at, order.kr_time, order.created_at_kr]
                        .find(t => t && t !== 'N/A' && t !== 'null');

                    if (!timeStr) {
                        console.warn('[Working] Order missing valid timestamp:', order.uuid || order.market);
                        return;
                    }

                    // 날짜를 타임스탬프로 변환
                    let timestamp;
                    try {
                        if (timeStr.includes('T')) {
                            // ISO format: "2025-10-11T06:18:06+09:00"
                            timestamp = Math.floor(new Date(timeStr).getTime() / 1000);
                        } else {
                            // Korean format: "2025-10-14 13:45:00"
                            timestamp = Math.floor(new Date(timeStr.replace(' ', 'T')).getTime() / 1000);
                        }

                        // Check if timestamp is valid
                        if (isNaN(timestamp)) {
                            console.warn('[Working] Invalid timestamp for order:', timeStr, order);
                            return;
                        }
                    } catch (e) {
                        console.warn('[Working] Error parsing timestamp:', timeStr, e);
                        return;
                    }

                    const side = order.side || 'unknown';
                    const price = parseFloat(order.avg_price || order.price);
                    const volume = parseFloat(order.executed_volume || order.volume);

                    // Validate price and volume (must be valid numbers > 0)
                    if (!price || isNaN(price) || !Number.isFinite(price) || price <= 0) {
                        console.warn('[Working] Invalid price for marker:', price, order);
                        return;
                    }
                    if (!volume || isNaN(volume) || !Number.isFinite(volume) || volume <= 0) {
                        console.warn('[Working] Invalid volume for marker:', volume, order);
                        return;
                    }

                    // 매수/매도에 따라 마커 스타일 설정
                    const isBuy = side === 'bid';

                    markers.push({
                        time: timestamp,
                        position: isBuy ? 'belowBar' : 'aboveBar',
                        color: isBuy ? '#26a69a' : '#ef5350',
                        shape: isBuy ? 'arrowUp' : 'arrowDown',
                        text: isBuy ? `BUY ${volume.toFixed(4)}` : `SELL ${volume.toFixed(4)}`
                    });
                });

                // 마커를 시간순으로 정렬
                markers.sort((a, b) => a.time - b.time);

                // Final validation: filter out any invalid markers
                const validMarkers = markers.filter(marker => {
                    if (!marker || typeof marker !== 'object') return false;
                    if (!marker.time || typeof marker.time !== 'number' || !Number.isFinite(marker.time)) return false;
                    if (!marker.position || !marker.color || !marker.shape) return false;
                    return true;
                });

                if (validMarkers.length < markers.length) {
                    console.warn(`[Working] Filtered out ${markers.length - validMarkers.length} invalid markers`);
                }

                // 차트에 마커 추가
                this.chart.candleSeries.setMarkers(validMarkers);

                console.log(`[DataLoader] ✅ Trading markers added: ${validMarkers.length}/${orders.length} total orders, ${visibleOrders.length} in visible range`);

            } catch (error) {
                console.error('[Working] Failed to add trading history markers:', error);
            }
        }

        async loadCoinList() {
            try {
                console.log('[Working] Loading coin list...');
    
                if (!window.apiHandler) {
                    console.error('[Working] APIHandler not available');
                    return;
                }
    
                const response = await window.apiHandler.getMarketList();
                console.log('[Working] Market list response:', response);
    
                // API는 배열을 직접 반환함
                const marketList = Array.isArray(response) ? response : (response.data || []);
    
                if (!marketList || marketList.length === 0) {
                    console.error('[Working] Failed to load market list or empty list');
                    return;
                }
    
                // KRW 마켓만 필터링하고 저장
                this.chart.allMarkets = marketList.filter(market => market.market.startsWith('KRW-'));
                console.log(`[Working] Found ${this.chart.allMarkets.length} KRW markets`);
    
                // 코인 셀렉트 박스 업데이트
                this.updateCoinSelectBox(this.chart.allMarkets);
    
                console.log('[Working] Coin list loaded successfully');
            } catch (error) {
                console.error('[Working] Failed to load coin list:', error);
            }
        }

        updateCoinSelectBox(markets, keepSelection = false) {
            const coinSelect = document.getElementById('coin-select');
            if (!coinSelect) {
                console.error('[Working] Coin select element not found');
                return;
            }
    
            // 현재 선택된 값 저장
            const currentValue = keepSelection ? coinSelect.value : this.chart.currentMarket;
    
            // 기존 옵션 클리어
            coinSelect.innerHTML = '';
    
            // 옵션 추가
            markets.forEach(market => {
                const option = document.createElement('option');
                option.value = market.market;
                option.textContent = `${market.korean_name} (${market.market})`;
    
                // 데이터 속성 추가 (검색 및 매칭용)
                option.dataset.koreanName = market.korean_name;
                option.dataset.englishName = market.english_name;
    
                // 이전 선택값 복원 또는 기본값 설정
                if (market.market === currentValue) {
                    option.selected = true;
                }
    
                coinSelect.appendChild(option);
            });
    
            // 선택값이 없으면 첫 번째 항목 선택
            if (coinSelect.options.length > 0 && !coinSelect.value) {
                coinSelect.options[0].selected = true;
            }
        }

        searchCoins(searchTerm) {
            if (!searchTerm || searchTerm.trim() === '') {
                // 검색어가 없으면 전체 목록 표시
                this.updateCoinSelectBox(this.chart.allMarkets, true);
                return;
            }
    
            const term = searchTerm.toLowerCase().trim();
    
            // 한글명, 영문명, 코드로 검색
            const filtered = this.chart.allMarkets.filter(market => {
                const koreanName = market.korean_name.toLowerCase();
                const englishName = market.english_name.toLowerCase();
                const marketCode = market.market.toLowerCase();
                const symbol = market.market.split('-')[1].toLowerCase(); // KRW-BTC -> btc
    
                return koreanName.includes(term) ||
                       englishName.includes(term) ||
                       marketCode.includes(term) ||
                       symbol.includes(term);
            });
    
            console.log(`[Working] Search "${searchTerm}": found ${filtered.length} results`);
    
            // 필터링된 목록으로 업데이트
            this.updateCoinSelectBox(filtered, true);
        }

        getCoinIcon(symbol) {
            const lowerSymbol = symbol.toLowerCase();
            // GitHub CDN에서 32x32 컬러 아이콘 사용
            // Fallback: 이미지 로드 실패 시 onerror로 처리
            return `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/32/color/${lowerSymbol}.png`;
        }

}

// Export for module usage
if (typeof window !== 'undefined') {
    window.DataLoader = DataLoader;
}
