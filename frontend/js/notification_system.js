/**
 * CoinPulse Notification System
 * 급등 예측 + 자동매매 알림 통합 관리
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 50;
        this.unreadCount = 0;
        this.isOpen = false;
        this.socket = null;

        // Load from localStorage
        this.loadFromStorage();

        // Initialize UI
        this.initializeUI();

        // Connect WebSocket if available
        if (typeof io !== 'undefined') {
            this.connectWebSocket();
        }
    }

    /**
     * Initialize notification UI
     */
    initializeUI() {
        // Check if notification center already exists
        if (document.getElementById('notification-center')) {
            return;
        }

        // Create notification bell icon in header
        const header = document.querySelector('.page-header') || document.querySelector('.header');
        if (!header) {
            console.warn('[Notification] No header found');
            return;
        }

        // Create notification icon container
        const notifContainer = document.createElement('div');
        notifContainer.className = 'notification-icon-container';
        notifContainer.innerHTML = `
            <div class="notification-bell" id="notification-bell">
                <span class="bell-icon">🔔</span>
                <span class="notification-badge" id="notification-badge" style="display: none;">0</span>
            </div>
        `;

        // Add to header (right side)
        if (header.querySelector('h1')) {
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            header.style.alignItems = 'center';
            header.appendChild(notifContainer);
        }

        // Create notification center panel
        const notifCenter = document.createElement('div');
        notifCenter.id = 'notification-center';
        notifCenter.className = 'notification-center';
        notifCenter.innerHTML = `
            <div class="notification-header">
                <h3>알림</h3>
                <div class="notification-actions">
                    <button class="btn-mark-read" id="mark-all-read">모두 읽음</button>
                    <button class="btn-clear" id="clear-all">전체 삭제</button>
                </div>
            </div>
            <div class="notification-filters">
                <button class="filter-btn active" data-filter="all">전체</button>
                <button class="filter-btn" data-filter="surge">급등예측</button>
                <button class="filter-btn" data-filter="auto_trading">자동매매</button>
                <button class="filter-btn" data-filter="trade">거래</button>
            </div>
            <div class="notification-list" id="notification-list">
                <div class="notification-empty">알림이 없습니다</div>
            </div>
        `;
        document.body.appendChild(notifCenter);

        // Add event listeners
        this.attachEventListeners();

        // Update badge
        this.updateBadge();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const bell = document.getElementById('notification-bell');
        const markAllRead = document.getElementById('mark-all-read');
        const clearAll = document.getElementById('clear-all');
        const filterBtns = document.querySelectorAll('.filter-btn');

        // Toggle notification center
        bell?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleNotificationCenter();
        });

        // Mark all as read
        markAllRead?.addEventListener('click', () => {
            this.markAllAsRead();
        });

        // Clear all
        clearAll?.addEventListener('click', () => {
            if (confirm('모든 알림을 삭제하시겠습니까?')) {
                this.clearAll();
            }
        });

        // Filters
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterNotifications(btn.dataset.filter);
            });
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            const center = document.getElementById('notification-center');
            const bell = document.getElementById('notification-bell');
            if (center && !center.contains(e.target) && !bell.contains(e.target)) {
                this.closeNotificationCenter();
            }
        });
    }

    /**
     * Connect to WebSocket for real-time notifications
     */
    connectWebSocket() {
        if (!window.io) {
            console.warn('[Notification] Socket.IO not available');
            return;
        }

        try {
            this.socket = io(window.location.origin);

            this.socket.on('connect', () => {
                console.log('[Notification] WebSocket connected');
            });

            // Listen for surge predictions
            this.socket.on('surge_alert', (data) => {
                console.log('[Notification] Surge alert:', data);
                this.addNotification({
                    type: 'surge',
                    priority: 'high',
                    title: '급등 예측 알림',
                    message: `${data.coin} - 예측 점수: ${data.score}점`,
                    data: data,
                    action: {
                        label: '상세보기',
                        url: `/surge_monitoring.html`
                    }
                });
            });

            // Listen for auto-trading events
            this.socket.on('order_notification', (data) => {
                console.log('[Notification] Order notification:', data);
                this.addNotification({
                    type: 'auto_trading',
                    priority: 'high',
                    title: '자동매매 주문',
                    message: data.message || `${data.market} ${data.side === 'bid' ? '매수' : '매도'} 주문`,
                    data: data,
                    action: {
                        label: '확인',
                        url: `/monitoring_dashboard.html`
                    }
                });
            });

            // Listen for trade execution
            this.socket.on('trade_executed', (data) => {
                console.log('[Notification] Trade executed:', data);
                this.addNotification({
                    type: 'trade',
                    priority: 'medium',
                    title: '거래 체결',
                    message: `${data.market} ${data.side === 'bid' ? '매수' : '매도'} 체결 완료`,
                    data: data
                });
            });

        } catch (error) {
            console.error('[Notification] WebSocket error:', error);
        }
    }

    /**
     * Add notification
     */
    addNotification(notification) {
        const notif = {
            id: Date.now() + Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            read: false,
            ...notification
        };

        this.notifications.unshift(notif);

        // Limit notifications
        if (this.notifications.length > this.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.maxNotifications);
        }

        this.unreadCount++;
        this.saveToStorage();
        this.updateBadge();
        this.renderNotifications();

        // Show browser notification if permission granted
        this.showBrowserNotification(notif);

        return notif.id;
    }

    /**
     * Show browser notification
     */
    async showBrowserNotification(notif) {
        if (!('Notification' in window)) {
            return;
        }

        if (Notification.permission === 'granted') {
            new Notification('CoinPulse - ' + notif.title, {
                body: notif.message,
                icon: '/favicon.ico',
                badge: '/favicon.ico',
                tag: notif.id
            });
        } else if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                this.showBrowserNotification(notif);
            }
        }
    }

    /**
     * Mark notification as read
     */
    markAsRead(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif && !notif.read) {
            notif.read = true;
            this.unreadCount--;
            this.saveToStorage();
            this.updateBadge();
            this.renderNotifications();
        }
    }

    /**
     * Mark all as read
     */
    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.unreadCount = 0;
        this.saveToStorage();
        this.updateBadge();
        this.renderNotifications();
    }

    /**
     * Delete notification
     */
    deleteNotification(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif && !notif.read) {
            this.unreadCount--;
        }
        this.notifications = this.notifications.filter(n => n.id !== id);
        this.saveToStorage();
        this.updateBadge();
        this.renderNotifications();
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        this.notifications = [];
        this.unreadCount = 0;
        this.saveToStorage();
        this.updateBadge();
        this.renderNotifications();
    }

    /**
     * Update badge count
     */
    updateBadge() {
        const badge = document.getElementById('notification-badge');
        if (!badge) return;

        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }

    /**
     * Toggle notification center
     */
    toggleNotificationCenter() {
        this.isOpen = !this.isOpen;
        const center = document.getElementById('notification-center');
        if (center) {
            center.classList.toggle('open', this.isOpen);
        }
        if (this.isOpen) {
            this.renderNotifications();
        }
    }

    /**
     * Close notification center
     */
    closeNotificationCenter() {
        this.isOpen = false;
        const center = document.getElementById('notification-center');
        if (center) {
            center.classList.remove('open');
        }
    }

    /**
     * Filter notifications
     */
    filterNotifications(filter) {
        const filtered = filter === 'all'
            ? this.notifications
            : this.notifications.filter(n => n.type === filter);

        this.renderNotifications(filtered);
    }

    /**
     * Render notifications
     */
    renderNotifications(notificationsToRender = null) {
        const list = document.getElementById('notification-list');
        if (!list) return;

        const notifications = notificationsToRender || this.notifications;

        if (notifications.length === 0) {
            list.innerHTML = '<div class="notification-empty">알림이 없습니다</div>';
            return;
        }

        list.innerHTML = notifications.map(notif => {
            const priorityClass = notif.priority === 'high' ? 'high-priority' : notif.priority === 'medium' ? 'medium-priority' : '';
            const readClass = notif.read ? 'read' : 'unread';
            const timeAgo = this.getTimeAgo(notif.timestamp);

            return `
                <div class="notification-item ${priorityClass} ${readClass}" data-id="${notif.id}">
                    <div class="notification-content">
                        <div class="notification-icon">${this.getNotificationIcon(notif.type)}</div>
                        <div class="notification-body">
                            <div class="notification-title">${notif.title}</div>
                            <div class="notification-message">${notif.message}</div>
                            <div class="notification-time">${timeAgo}</div>
                        </div>
                    </div>
                    <div class="notification-actions-inline">
                        ${notif.action ? `<button class="btn-action" onclick="notificationSystem.handleAction('${notif.id}')">${notif.action.label}</button>` : ''}
                        <button class="btn-delete" onclick="notificationSystem.deleteNotification('${notif.id}')">✕</button>
                    </div>
                </div>
            `;
        }).join('');

        // Add click listeners to mark as read
        list.querySelectorAll('.notification-item.unread').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('btn-delete') && !e.target.classList.contains('btn-action')) {
                    this.markAsRead(item.dataset.id);
                }
            });
        });
    }

    /**
     * Get notification icon
     */
    getNotificationIcon(type) {
        const icons = {
            surge: '🚀',
            auto_trading: '🤖',
            trade: '💰',
            portfolio: '📊',
            system: '⚙️',
            security: '🔒'
        };
        return icons[type] || '🔔';
    }

    /**
     * Get time ago
     */
    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000);

        if (diff < 60) return '방금 전';
        if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}일 전`;
        return time.toLocaleDateString('ko-KR');
    }

    /**
     * Handle action button click
     */
    handleAction(id) {
        const notif = this.notifications.find(n => n.id === id);
        if (notif && notif.action) {
            this.markAsRead(id);
            if (notif.action.url) {
                window.location.href = notif.action.url;
            }
        }
    }

    /**
     * Save to localStorage
     */
    saveToStorage() {
        try {
            localStorage.setItem('coinpulse_notifications', JSON.stringify(this.notifications));
            localStorage.setItem('coinpulse_unread_count', this.unreadCount.toString());
        } catch (error) {
            console.error('[Notification] Failed to save to storage:', error);
        }
    }

    /**
     * Load from localStorage
     */
    loadFromStorage() {
        try {
            const stored = localStorage.getItem('coinpulse_notifications');
            if (stored) {
                this.notifications = JSON.parse(stored);
            }
            const unreadCount = localStorage.getItem('coinpulse_unread_count');
            if (unreadCount) {
                this.unreadCount = parseInt(unreadCount);
            }
        } catch (error) {
            console.error('[Notification] Failed to load from storage:', error);
        }
    }
}

// Global instance
let notificationSystem = null;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        notificationSystem = new NotificationSystem();
        window.notificationSystem = notificationSystem;
    });
} else {
    notificationSystem = new NotificationSystem();
    window.notificationSystem = notificationSystem;
}
