/**
 * Policy Modal Controller
 * Integrated policy management modal for trading chart
 */

class PolicyModalController {
    constructor() {
        this.modal = document.getElementById('policy-modal');
        this.currentCoin = 'KRW-BTC';
        this.policies = null;
        this.apiBaseUrl = window.location.origin;
        this.init();
    }

    init() {
        console.log('[PolicyModal] Initializing...');
        this.setupEventListeners();
        this.loadPolicies();
    }

    setupEventListeners() {
        // Policy button to open modal
        const policyBtn = document.getElementById('policy-btn');
        if (policyBtn) {
            policyBtn.addEventListener('click', () => {
                this.openModal();
            });
        }

        // Close buttons
        document.getElementById('close-policy-modal').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('policy-modal-overlay').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('cancel-policy-modal').addEventListener('click', () => {
            this.closeModal();
        });

        // Tab switching
        document.querySelectorAll('.policy-modal-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Preset buttons
        document.querySelectorAll('.policy-preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const preset = e.currentTarget.dataset.preset;
                this.applyPreset(preset);
            });
        });

        // Toggle switches
        document.getElementById('modal-auto-toggle').addEventListener('click', () => {
            this.toggleAutoTrading();
        });

        document.getElementById('quick-coin-toggle').addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
        });

        // Save button
        document.getElementById('save-policy-modal').addEventListener('click', () => {
            this.savePolicies();
        });

        // Test cycle
        document.getElementById('run-test-cycle').addEventListener('click', () => {
            this.runTestCycle();
        });

        // Refresh logs
        document.getElementById('refresh-policy-logs').addEventListener('click', () => {
            this.loadLogs();
        });

        // Coin selector
        const coinSelector = document.getElementById('coin-selector');
        if (coinSelector) {
            coinSelector.addEventListener('change', (e) => {
                this.onCoinChanged(e.target.value);
            });
        }

        // Add coin button
        const addCoinBtn = document.getElementById('add-coin-btn');
        if (addCoinBtn) {
            addCoinBtn.addEventListener('click', () => {
                this.addNewCoin();
            });
        }

        // Style selector toggle
        document.querySelectorAll('.preset-style-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchPresetStyle(e.currentTarget.dataset.style);
            });
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.closeModal();
            }
        });
    }

    switchPresetStyle(style) {
        // Toggle active state
        document.querySelectorAll('.preset-style-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.style === style);
        });

        // Update preset buttons
        const presetButtons = document.querySelectorAll('.policy-preset-btn');

        if (style === 'long') {
            // Long-term presets
            presetButtons[0].dataset.preset = 'long-conservative';
            presetButtons[0].querySelector('.preset-desc').textContent = '손절 3% | 익절 8%';
            presetButtons[0].querySelector('.preset-time').textContent = '시간: 1일';

            presetButtons[1].dataset.preset = 'long-balanced';
            presetButtons[1].querySelector('.preset-desc').textContent = '손절 5% | 익절 15%';
            presetButtons[1].querySelector('.preset-time').textContent = '시간: 4시간';

            presetButtons[2].dataset.preset = 'long-aggressive';
            presetButtons[2].querySelector('.preset-desc').textContent = '손절 8% | 익절 25%';
            presetButtons[2].querySelector('.preset-time').textContent = '시간: 4시간';
        } else {
            // Short-term presets
            presetButtons[0].dataset.preset = 'short-conservative';
            presetButtons[0].querySelector('.preset-desc').textContent = '손절 1% | 익절 2%';
            presetButtons[0].querySelector('.preset-time').textContent = '시간: 15분';

            presetButtons[1].dataset.preset = 'short-balanced';
            presetButtons[1].querySelector('.preset-desc').textContent = '손절 2% | 익절 4%';
            presetButtons[1].querySelector('.preset-time').textContent = '시간: 15분';

            presetButtons[2].dataset.preset = 'short-aggressive';
            presetButtons[2].querySelector('.preset-desc').textContent = '손절 3% | 익절 6%';
            presetButtons[2].querySelector('.preset-time').textContent = '시간: 5분';
        }
    }

    async loadPolicies() {
        try {
            console.log('[PolicyModal] Loading policies...');
            const response = await fetch(`${this.apiBaseUrl}/api/trading/policies`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            this.policies = await response.json();
            console.log('[PolicyModal] Policies loaded:', this.policies);
            this.updateModalContent();

            // Update header and badges
            this.updateHeaderPolicyStatus(this.currentCoin);
            this.updateCoinSelectorBadges();
            this.updateHoldingsPolicyBadges();
        } catch (error) {
            console.error('[PolicyModal] Failed to load policies:', error);
            this.showNotification('정책 로드 실패. 8081 포트에서 서버가 실행 중인지 확인하세요.');
        }
    }

    updateModalContent() {
        if (!this.policies) return;

        // Update coin selector in modal to match current coin
        const coinSelector = document.getElementById('coin-selector');
        if (coinSelector && this.currentCoin) {
            coinSelector.value = this.currentCoin;
        }

        // Update global status
        const isEnabled = this.policies.auto_trading_enabled || false;
        const autoToggle = document.getElementById('modal-auto-toggle');
        const autoStatus = document.getElementById('modal-auto-status');

        autoToggle.classList.toggle('active', isEnabled);
        autoStatus.textContent = isEnabled ? '활성' : '비활성';

        // Update quick setup for current coin
        const coinPolicy = this.policies.coin_policies ? this.policies.coin_policies[this.currentCoin] : null;
        if (coinPolicy) {
            document.getElementById('quick-strategy').value = coinPolicy.strategy || 'trend_following';
            document.getElementById('quick-timeframe').value = coinPolicy.timeframe || '1h';
            document.getElementById('quick-stop-loss').value = ((coinPolicy.stop_loss || 0.03) * 100).toFixed(1);
            document.getElementById('quick-take-profit').value = ((coinPolicy.take_profit || 0.1) * 100).toFixed(1);
            document.getElementById('quick-position-size').value = ((coinPolicy.position_size || 0.05) * 100).toFixed(1);

            const coinToggle = document.getElementById('quick-coin-toggle');
            coinToggle.classList.toggle('active', coinPolicy.enabled || false);
        }

        // Update status cards
        if (this.policies.coin_policies) {
            const activeCount = Object.values(this.policies.coin_policies).filter(p => p.enabled).length;
            const totalCount = Object.keys(this.policies.coin_policies).length;
            document.getElementById('active-policies-count').textContent = `${activeCount}/${totalCount}`;

            const totalPosition = Object.values(this.policies.coin_policies)
                .filter(p => p.enabled)
                .reduce((sum, p) => sum + ((p.position_size || 0) * 100), 0);
            document.getElementById('total-position').textContent = `${totalPosition.toFixed(1)}%`;
        }

        // Update global settings
        if (this.policies.global_settings) {
            document.getElementById('modal-check-interval').value = this.policies.global_settings.check_interval || 60;
            document.getElementById('modal-max-position').value = ((this.policies.global_settings.max_position_size || 0.1) * 100).toFixed(0);
            document.getElementById('modal-risk-level').value = this.policies.global_settings.risk_level || 'medium';
        }

        // Update policies table in Advanced tab
        this.renderPoliciesTable();
    }

    renderPoliciesTable() {
        const tbody = document.getElementById('policies-table-body');
        if (!tbody) return;

        if (!this.policies || !this.policies.coin_policies) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #6b7280;">정책이 없습니다</td></tr>';
            return;
        }

        const strategyNames = {
            'trend_following': '추세 추종',
            'momentum': '모멘텀',
            'mean_reversion': '평균 회귀'
        };

        tbody.innerHTML = '';
        for (const [coinSymbol, policy] of Object.entries(this.policies.coin_policies)) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="coin-name">${coinSymbol}</span></td>
                <td>${strategyNames[policy.strategy] || policy.strategy}</td>
                <td>${policy.timeframe || '1h'}</td>
                <td>${((policy.stop_loss || 0) * 100).toFixed(1)}</td>
                <td>${((policy.take_profit || 0) * 100).toFixed(1)}</td>
                <td>${((policy.position_size || 0) * 100).toFixed(1)}</td>
                <td>
                    <span class="status-badge ${policy.enabled ? 'status-active' : 'status-inactive'}">
                        ${policy.enabled ? '활성' : '비활성'}
                    </span>
                </td>
                <td>
                    <button class="action-btn action-edit" data-coin="${coinSymbol}">편집</button>
                    <button class="action-btn action-delete" data-coin="${coinSymbol}">삭제</button>
                </td>
            `;
            tbody.appendChild(row);
        }

        // Add event listeners to action buttons
        tbody.querySelectorAll('.action-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const coin = e.target.dataset.coin;
                this.editCoinPolicy(coin);
            });
        });

        tbody.querySelectorAll('.action-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const coin = e.target.dataset.coin;
                this.deleteCoinPolicy(coin);
            });
        });
    }

    editCoinPolicy(coinSymbol) {
        // Switch to Quick Setup tab and load that coin
        this.switchTab('quick');
        const coinSelector = document.getElementById('coin-selector');
        if (coinSelector) {
            coinSelector.value = coinSymbol;
        }
        this.onCoinChanged(coinSymbol);
    }

    deleteCoinPolicy(coinSymbol) {
        if (!confirm(`${coinSymbol} 정책을 삭제하시겠습니까?`)) {
            return;
        }

        if (this.policies.coin_policies) {
            delete this.policies.coin_policies[coinSymbol];
            this.savePolicies();
        }
    }

    openModal() {
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        this.loadPolicies(); // Refresh data
        this.loadLogs(); // Load logs
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    switchTab(tabName) {
        // Remove active from all tabs
        document.querySelectorAll('.policy-modal-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.policy-tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Add active to selected tab
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`policy-${tabName}-tab`).classList.add('active');

        // Load logs when switching to logs tab
        if (tabName === 'logs') {
            this.loadLogs();
        }
    }

    applyPreset(presetName) {
        const presets = {
            // Long-term presets (Swing Trading)
            'long-conservative': {
                strategy: 'trend_following',
                timeframe: '1d',
                stop_loss: 3.0,
                take_profit: 8.0,
                position_size: 3.0
            },
            'long-balanced': {
                strategy: 'momentum',
                timeframe: '4h',
                stop_loss: 5.0,
                take_profit: 15.0,
                position_size: 5.0
            },
            'long-aggressive': {
                strategy: 'momentum',
                timeframe: '4h',
                stop_loss: 8.0,
                take_profit: 25.0,
                position_size: 8.0
            },
            // Short-term presets (Day Trading)
            'short-conservative': {
                strategy: 'mean_reversion',
                timeframe: '15m',
                stop_loss: 1.0,
                take_profit: 2.0,
                position_size: 2.0
            },
            'short-balanced': {
                strategy: 'momentum',
                timeframe: '15m',
                stop_loss: 2.0,
                take_profit: 4.0,
                position_size: 4.0
            },
            'short-aggressive': {
                strategy: 'momentum',
                timeframe: '5m',
                stop_loss: 3.0,
                take_profit: 6.0,
                position_size: 6.0
            },
            // Manual trading (no auto-trading)
            'manual': {
                strategy: 'manual',
                timeframe: '1d',
                stop_loss: 0.0,
                take_profit: 0.0,
                position_size: 0.0,
                enabled: false
            }
        };

        const preset = presets[presetName];
        if (preset) {
            document.getElementById('quick-strategy').value = preset.strategy;
            document.getElementById('quick-timeframe').value = preset.timeframe;
            document.getElementById('quick-stop-loss').value = preset.stop_loss;
            document.getElementById('quick-take-profit').value = preset.take_profit;
            document.getElementById('quick-position-size').value = preset.position_size;

            const presetLabels = {
                'long-conservative': '장기 안정형',
                'long-balanced': '장기 균형형',
                'long-aggressive': '장기 공격형',
                'short-conservative': '단타 안정형',
                'short-balanced': '단타 균형형',
                'short-aggressive': '단타 공격형',
                'manual': '수동 거래'
            };
            this.showNotification(`${presetLabels[presetName]} 프리셋이 적용되었습니다`);
        }
    }

    async toggleAutoTrading() {
        try {
            const newState = !this.policies.auto_trading_enabled;

            const response = await fetch(`${this.apiBaseUrl}/api/trading/enable`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newState })
            });

            if (!response.ok) {
                throw new Error('Failed to toggle');
            }

            const data = await response.json();
            this.policies.auto_trading_enabled = data.enabled;
            this.updateModalContent();

            this.showNotification(`자동매매가 ${data.enabled ? '활성화' : '비활성화'}되었습니다`);
        } catch (error) {
            console.error('[PolicyModal] Toggle failed:', error);
            this.showNotification('자동매매 토글에 실패했습니다');
        }
    }

    async savePolicies() {
        try {
            // Get values from quick setup
            const coinPolicy = {
                enabled: document.getElementById('quick-coin-toggle').classList.contains('active'),
                strategy: document.getElementById('quick-strategy').value,
                timeframe: document.getElementById('quick-timeframe').value,
                buy_threshold: 0.02,
                sell_threshold: 0.05,
                stop_loss: parseFloat(document.getElementById('quick-stop-loss').value) / 100,
                take_profit: parseFloat(document.getElementById('quick-take-profit').value) / 100,
                position_size: parseFloat(document.getElementById('quick-position-size').value) / 100,
                indicators: ['sma_20', 'rsi_14', 'macd']
            };

            // Update policies object
            if (!this.policies.coin_policies) {
                this.policies.coin_policies = {};
            }
            this.policies.coin_policies[this.currentCoin] = coinPolicy;

            // Update global settings
            if (!this.policies.global_settings) {
                this.policies.global_settings = {};
            }
            this.policies.global_settings.check_interval = parseInt(document.getElementById('modal-check-interval').value);
            this.policies.global_settings.max_position_size = parseFloat(document.getElementById('modal-max-position').value) / 100;
            this.policies.global_settings.risk_level = document.getElementById('modal-risk-level').value;

            // Save to server
            const response = await fetch(`${this.apiBaseUrl}/api/trading/policies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.policies)
            });

            if (response.ok) {
                this.showNotification('정책이 성공적으로 저장되었습니다');
                await this.loadPolicies(); // Reload to confirm
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            console.error('[PolicyModal] Save failed:', error);
            this.showNotification('정책 저장에 실패했습니다');
        }
    }

    async runTestCycle() {
        try {
            this.showNotification('테스트 사이클 실행 중...');

            const response = await fetch(`${this.apiBaseUrl}/api/trading/cycle`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showNotification('테스트 사이클이 완료되었습니다');
                this.switchTab('logs');
                await this.loadLogs();
            } else {
                throw new Error('Cycle failed');
            }
        } catch (error) {
            console.error('[PolicyModal] Test cycle failed:', error);
            this.showNotification('테스트 사이클 실행에 실패했습니다');
        }
    }

    async loadLogs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trading/logs`);

            if (!response.ok) {
                throw new Error('Failed to load logs');
            }

            const logs = await response.json();
            this.renderLogs(logs);
        } catch (error) {
            console.error('[PolicyModal] Failed to load logs:', error);
            const logsContainer = document.getElementById('modal-policy-logs');
            logsContainer.innerHTML = '<div class="policy-log-entry">로그 로딩에 실패했습니다</div>';
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('modal-policy-logs');

        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="policy-log-entry">아직 거래 활동이 없습니다</div>';
            return;
        }

        container.innerHTML = '';

        // Show last 50 logs
        const recentLogs = logs.slice(-50).reverse();

        for (const log of recentLogs) {
            const entry = document.createElement('div');
            entry.className = 'policy-log-entry';

            const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A';
            const action = (log.action || 'INFO').toUpperCase();
            const coin = log.coin || 'N/A';
            const price = log.price ? log.price.toLocaleString() : 'N/A';
            const reason = log.reason || '';

            entry.textContent = `[${timestamp}] ${action} ${coin} @ ${price} KRW - ${reason}`;
            container.appendChild(entry);
        }
    }

    setCurrentCoin(coinSymbol) {
        this.currentCoin = coinSymbol;
        const coinSelector = document.getElementById('coin-selector');
        if (coinSelector) {
            coinSelector.value = coinSymbol;
        }
        this.updateModalContent();
    }

    onCoinChanged(coinSymbol) {
        console.log('[PolicyModal] Coin changed to:', coinSymbol);
        this.currentCoin = coinSymbol;
        this.updateModalContent();
        this.updateHeaderPolicyStatus(coinSymbol);
    }

    addNewCoin() {
        const coinName = prompt('추가할 코인 심볼을 입력하세요 (예: KRW-SOL):');
        if (!coinName || !coinName.startsWith('KRW-')) {
            console.log('[PolicyModal] Invalid coin symbol');
            return;
        }

        // Add to selector
        const selector = document.getElementById('coin-selector');
        const option = document.createElement('option');
        option.value = coinName;
        option.textContent = coinName;
        selector.appendChild(option);

        // Select the new coin
        selector.value = coinName;
        this.onCoinChanged(coinName);

        console.log('[PolicyModal] Added new coin:', coinName);
    }

    updateHeaderPolicyStatus(coinSymbol) {
        // Get elements
        const coinLabel = document.getElementById('policy-coin-label');
        const presetBadge = document.getElementById('policy-preset-badge');
        const stopLoss = document.querySelector('.policy-level-item.stop-loss');
        const takeProfit = document.querySelector('.policy-level-item.take-profit');
        const statusIndicator = document.getElementById('policy-status-indicator');

        if (!coinLabel || !presetBadge || !stopLoss || !takeProfit || !statusIndicator) {
            console.warn('[PolicyModal] Header elements not found');
            return;
        }

        // Update coin label
        const coinSymbols = {
            'KRW-BTC': '₿ BTC',
            'KRW-ETH': 'Ξ ETH',
            'KRW-XRP': '✕ XRP',
            'KRW-ADA': '₳ ADA',
            'KRW-DOGE': 'Ð DOGE'
        };
        coinLabel.textContent = coinSymbols[coinSymbol] || coinSymbol;

        // Check if policy exists for this coin
        const policy = this.policies?.coin_policies?.[coinSymbol];

        if (!policy) {
            // No policy
            presetBadge.textContent = '⚠️ 정책없음';
            presetBadge.className = 'policy-preset-badge none';
            stopLoss.textContent = '손절 --';
            takeProfit.textContent = '익절 --';
            statusIndicator.textContent = '비활성';
            statusIndicator.className = 'policy-status-indicator inactive';
            return;
        }

        // Check if manual trading
        if (policy.strategy === 'manual' || policy.enabled === false) {
            presetBadge.textContent = '수동';
            presetBadge.className = 'policy-preset-badge manual';
            stopLoss.textContent = '손절 --';
            takeProfit.textContent = '익절 --';
            statusIndicator.innerHTML = '<span class="status-dot"></span> 수동';
            statusIndicator.className = 'policy-status-indicator inactive';
            return;
        }

        // Determine risk level from stop_loss and take_profit
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

        // Update badge
        presetBadge.textContent = riskLabel;
        presetBadge.className = `policy-preset-badge ${riskLevel}`;

        // Update levels
        stopLoss.textContent = `손절 ${stopLossPct.toFixed(1)}%`;
        takeProfit.textContent = `익절 ${takeProfitPct.toFixed(1)}%`;

        // Update status
        if (policy.enabled) {
            statusIndicator.innerHTML = '<span class="status-dot"></span> 활성';
            statusIndicator.className = 'policy-status-indicator active';
        } else {
            statusIndicator.innerHTML = '<span class="status-dot"></span> 비활성';
            statusIndicator.className = 'policy-status-indicator inactive';
        }

        console.log('[PolicyModal] Updated header status for', coinSymbol);
    }

    updateCoinSelectorBadges() {
        const selector = document.getElementById('coin-selector');
        if (!selector || !this.policies?.coin_policies) return;

        // Add badges to options
        Array.from(selector.options).forEach(option => {
            const coinSymbol = option.value;
            const policy = this.policies.coin_policies[coinSymbol];

            if (policy && policy.enabled) {
                const stopLossPct = (policy.stop_loss || 0) * 100;
                const takeProfitPct = (policy.take_profit || 0) * 100;

                let badge = '⚖️';
                if (stopLossPct <= 2 && takeProfitPct <= 8) {
                    badge = '🛡️';
                } else if (stopLossPct >= 5 && takeProfitPct >= 15) {
                    badge = '🚀';
                }

                // Only add badge if not already present
                if (!option.textContent.includes(badge)) {
                    const originalText = option.textContent.replace(/[🛡️⚖️🚀]/g, '').trim();
                    option.textContent = `${badge} ${originalText}`;
                }
            }
        });

        console.log('[PolicyModal] Updated coin selector badges');
    }

    updateHoldingsPolicyBadges() {
        // Trigger holdings reload in the main chart to refresh policy badges
        if (window.tradingChart && typeof window.tradingChart.loadHoldings === 'function') {
            console.log('[PolicyModal] Refreshing holdings to update policy badges');
            window.tradingChart.loadHoldings();
        }
    }

    showNotification(message) {
        console.log(`[PolicyModal] ${message}`);

        // Simple notification (can be enhanced)
        const notification = document.getElementById('notification');
        if (notification) {
            notification.textContent = message;
            notification.style.display = 'block';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        // No fallback alert - just log to console
    }
}

// Initialize after DOM loaded
if (typeof window !== 'undefined') {
    window.PolicyModalController = PolicyModalController;

    document.addEventListener('DOMContentLoaded', () => {
        console.log('[PolicyModal] DOM loaded, initializing...');
        window.policyModalController = new PolicyModalController();
    });
}
