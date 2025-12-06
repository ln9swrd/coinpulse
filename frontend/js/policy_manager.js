/**
 * Policy Manager Controller
 * Manages auto-trading policies and real-time monitoring
 */

class PolicyManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8081';
        this.policies = null;
        this.autoRefreshInterval = null;
        this.init();
    }

    async init() {
        console.log('[PolicyManager] Initializing...');
        this.setupEventListeners();
        await this.loadPolicies();
        await this.loadLogs();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Global controls
        document.getElementById('auto-trading-toggle').addEventListener('click', () => {
            this.toggleAutoTrading();
        });

        document.getElementById('save-global-btn').addEventListener('click', () => {
            this.saveGlobalSettings();
        });

        document.getElementById('run-cycle-btn').addEventListener('click', () => {
            this.runOneCycle();
        });

        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refresh();
        });

        // Add policy button
        document.getElementById('add-policy-btn').addEventListener('click', () => {
            this.showAddPolicyModal();
        });

        // Modal controls
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('policy-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.savePolicyFromForm();
        });
    }

    async loadPolicies() {
        try {
            console.log('[PolicyManager] Loading policies...');
            const response = await fetch(`${this.apiBaseUrl}/api/trading/policies`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.policies = await response.json();
            console.log('[PolicyManager] Policies loaded:', this.policies);

            this.updateUI();
        } catch (error) {
            console.error('[PolicyManager] Failed to load policies:', error);
            this.showError('Failed to load policies. Make sure the server is running on port 8081.');
        }
    }

    updateUI() {
        if (!this.policies) return;

        // Update global status
        const isEnabled = this.policies.auto_trading_enabled;
        const statusBadge = document.getElementById('global-status');
        const statusText = document.getElementById('status-text');
        const toggle = document.getElementById('auto-trading-toggle');

        statusBadge.className = `status-badge ${isEnabled ? 'active' : 'inactive'}`;
        statusText.textContent = isEnabled ? 'Active' : 'Inactive';
        toggle.className = `toggle-switch ${isEnabled ? 'active' : ''}`;

        // Update global settings inputs
        const globalSettings = this.policies.global_settings || {};
        document.getElementById('check-interval').value = globalSettings.check_interval || 60;
        document.getElementById('max-position').value = (globalSettings.max_position_size || 0.1) * 100;
        document.getElementById('risk-level').value = globalSettings.risk_level || 'medium';

        // Update coin policies
        this.renderCoinPolicies();
    }

    renderCoinPolicies() {
        const container = document.getElementById('coin-policies-list');
        const coinPolicies = this.policies.coin_policies || {};

        if (Object.keys(coinPolicies).length === 0) {
            container.innerHTML = `
                <div class="policy-card">
                    <p style="text-align: center; color: #6b7280;">No policies configured yet. Click "Add New Coin Policy" to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';

        for (const [coinSymbol, policy] of Object.entries(coinPolicies)) {
            const card = this.createPolicyCard(coinSymbol, policy);
            container.appendChild(card);
        }
    }

    createPolicyCard(coinSymbol, policy) {
        const card = document.createElement('div');
        card.className = `policy-card ${policy.enabled ? 'enabled' : ''}`;

        card.innerHTML = `
            <div class="policy-header">
                <div class="coin-name">${coinSymbol}</div>
                <div style="display: flex; gap: 10px;">
                    <div class="toggle-switch ${policy.enabled ? 'active' : ''}" data-coin="${coinSymbol}">
                        <div class="toggle-slider"></div>
                    </div>
                    <button class="btn btn-secondary btn-sm" data-action="edit" data-coin="${coinSymbol}">✏️</button>
                    <button class="btn btn-danger btn-sm" data-action="delete" data-coin="${coinSymbol}">🗑️</button>
                </div>
            </div>
            <div class="policy-settings">
                <div class="setting-item">
                    <div class="setting-label">Strategy</div>
                    <div class="setting-value">${policy.strategy || 'N/A'}</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Timeframe</div>
                    <div class="setting-value">${policy.timeframe || 'N/A'}</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Buy Threshold</div>
                    <div class="setting-value">${(policy.buy_threshold * 100).toFixed(1)}%</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Sell Threshold</div>
                    <div class="setting-value">${(policy.sell_threshold * 100).toFixed(1)}%</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Stop Loss</div>
                    <div class="setting-value">${(policy.stop_loss * 100).toFixed(1)}%</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Take Profit</div>
                    <div class="setting-value">${(policy.take_profit * 100).toFixed(1)}%</div>
                </div>
                <div class="setting-item">
                    <div class="setting-label">Position Size</div>
                    <div class="setting-value">${(policy.position_size * 100).toFixed(1)}%</div>
                </div>
            </div>
        `;

        // Add event listeners
        const toggle = card.querySelector('.toggle-switch');
        toggle.addEventListener('click', () => {
            this.toggleCoinPolicy(coinSymbol);
        });

        const editBtn = card.querySelector('[data-action="edit"]');
        editBtn.addEventListener('click', () => {
            this.editPolicy(coinSymbol);
        });

        const deleteBtn = card.querySelector('[data-action="delete"]');
        deleteBtn.addEventListener('click', () => {
            this.deletePolicy(coinSymbol);
        });

        return card;
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
                throw new Error('Failed to toggle auto trading');
            }

            const data = await response.json();
            console.log('[PolicyManager] Auto trading toggled:', data);

            this.policies.auto_trading_enabled = data.enabled;
            this.updateUI();

            this.showSuccess(`Auto trading ${data.enabled ? 'enabled' : 'disabled'}`);
        } catch (error) {
            console.error('[PolicyManager] Toggle failed:', error);
            this.showError('Failed to toggle auto trading');
        }
    }

    async toggleCoinPolicy(coinSymbol) {
        try {
            const policy = this.policies.coin_policies[coinSymbol];
            policy.enabled = !policy.enabled;

            await this.savePolicies();
            this.updateUI();

            this.showSuccess(`${coinSymbol} ${policy.enabled ? 'enabled' : 'disabled'}`);
        } catch (error) {
            console.error('[PolicyManager] Failed to toggle coin policy:', error);
            this.showError('Failed to toggle coin policy');
        }
    }

    async saveGlobalSettings() {
        try {
            const checkInterval = parseInt(document.getElementById('check-interval').value);
            const maxPosition = parseFloat(document.getElementById('max-position').value) / 100;
            const riskLevel = document.getElementById('risk-level').value;

            this.policies.global_settings = {
                ...this.policies.global_settings,
                check_interval: checkInterval,
                max_position_size: maxPosition,
                risk_level: riskLevel
            };

            await this.savePolicies();
            this.showSuccess('Global settings saved');
        } catch (error) {
            console.error('[PolicyManager] Failed to save global settings:', error);
            this.showError('Failed to save global settings');
        }
    }

    async savePolicies() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/trading/policies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.policies)
            });

            if (!response.ok) {
                throw new Error('Failed to save policies');
            }

            console.log('[PolicyManager] Policies saved successfully');
            return true;
        } catch (error) {
            console.error('[PolicyManager] Save failed:', error);
            throw error;
        }
    }

    showAddPolicyModal() {
        document.getElementById('modal-title').textContent = 'Add New Policy';
        document.getElementById('policy-form').reset();
        document.getElementById('coin-symbol').disabled = false;
        document.getElementById('policy-modal').classList.add('active');
    }

    editPolicy(coinSymbol) {
        const policy = this.policies.coin_policies[coinSymbol];

        document.getElementById('modal-title').textContent = `Edit Policy: ${coinSymbol}`;
        document.getElementById('coin-symbol').value = coinSymbol;
        document.getElementById('coin-symbol').disabled = true;
        document.getElementById('strategy').value = policy.strategy || 'trend_following';
        document.getElementById('timeframe').value = policy.timeframe || '1h';
        document.getElementById('buy-threshold').value = (policy.buy_threshold * 100).toFixed(1);
        document.getElementById('sell-threshold').value = (policy.sell_threshold * 100).toFixed(1);
        document.getElementById('stop-loss').value = (policy.stop_loss * 100).toFixed(1);
        document.getElementById('take-profit').value = (policy.take_profit * 100).toFixed(1);
        document.getElementById('position-size').value = (policy.position_size * 100).toFixed(1);

        document.getElementById('policy-modal').classList.add('active');
    }

    closeModal() {
        document.getElementById('policy-modal').classList.remove('active');
        document.getElementById('policy-form').reset();
    }

    async savePolicyFromForm() {
        try {
            const coinSymbol = document.getElementById('coin-symbol').value.toUpperCase();

            const policy = {
                enabled: true,
                strategy: document.getElementById('strategy').value,
                timeframe: document.getElementById('timeframe').value,
                buy_threshold: parseFloat(document.getElementById('buy-threshold').value) / 100,
                sell_threshold: parseFloat(document.getElementById('sell-threshold').value) / 100,
                stop_loss: parseFloat(document.getElementById('stop-loss').value) / 100,
                take_profit: parseFloat(document.getElementById('take-profit').value) / 100,
                position_size: parseFloat(document.getElementById('position-size').value) / 100,
                indicators: ['sma_20', 'rsi_14', 'macd']
            };

            this.policies.coin_policies[coinSymbol] = policy;

            await this.savePolicies();
            this.closeModal();
            this.updateUI();

            this.showSuccess(`Policy for ${coinSymbol} saved`);
        } catch (error) {
            console.error('[PolicyManager] Failed to save policy:', error);
            this.showError('Failed to save policy');
        }
    }

    async deletePolicy(coinSymbol) {
        if (!confirm(`Are you sure you want to delete the policy for ${coinSymbol}?`)) {
            return;
        }

        try {
            delete this.policies.coin_policies[coinSymbol];
            await this.savePolicies();
            this.updateUI();

            this.showSuccess(`Policy for ${coinSymbol} deleted`);
        } catch (error) {
            console.error('[PolicyManager] Failed to delete policy:', error);
            this.showError('Failed to delete policy');
        }
    }

    async runOneCycle() {
        try {
            this.showInfo('Running auto-trading cycle...');

            const response = await fetch(`${this.apiBaseUrl}/api/trading/cycle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Failed to run cycle');
            }

            const result = await response.json();
            console.log('[PolicyManager] Cycle result:', result);

            this.showSuccess('Cycle completed');
            await this.loadLogs();
        } catch (error) {
            console.error('[PolicyManager] Cycle failed:', error);
            this.showError('Failed to run cycle');
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
            console.error('[PolicyManager] Failed to load logs:', error);
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('trading-logs');

        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="log-entry info">[INFO] No trading activity yet</div>';
            return;
        }

        container.innerHTML = '';

        // Show last 50 logs
        const recentLogs = logs.slice(-50).reverse();

        for (const log of recentLogs) {
            const entry = document.createElement('div');
            const type = log.action === 'buy' ? 'buy' : log.action === 'sell' ? 'sell' : 'info';
            entry.className = `log-entry ${type}`;

            const timestamp = new Date(log.timestamp).toLocaleString();
            const action = log.action ? log.action.toUpperCase() : 'INFO';
            const coin = log.coin || 'N/A';
            const price = log.price ? log.price.toLocaleString() : 'N/A';
            const reason = log.reason || '';

            entry.textContent = `[${timestamp}] ${action} ${coin} @ ${price} KRW - ${reason}`;
            container.appendChild(entry);
        }

        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    async refresh() {
        this.showInfo('Refreshing...');
        await this.loadPolicies();
        await this.loadLogs();
        this.showSuccess('Refreshed');
    }

    startAutoRefresh() {
        // Refresh every 10 seconds
        this.autoRefreshInterval = setInterval(() => {
            this.loadLogs();
        }, 10000);
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showInfo(message) {
        this.showToast(message, 'info');
    }

    showToast(message, type) {
        // Simple console log for now
        // TODO: Implement actual toast notifications
        console.log(`[${type.toUpperCase()}] ${message}`);

        const logsContainer = document.getElementById('trading-logs');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logsContainer.insertBefore(entry, logsContainer.firstChild);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[PolicyManager] DOM loaded, initializing...');
    window.policyManager = new PolicyManager();
});
