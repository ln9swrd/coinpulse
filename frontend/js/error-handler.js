/**
 * Global Error Handler for CoinPulse
 * Provides centralized error handling for fetch calls and DOM operations
 */

// API Base URL with fallback
window.API_BASE = window.API_BASE || window.location.origin;

// Error handler utility
window.ErrorHandler = {
    /**
     * Show user-friendly error message
     */
    showError(message, duration = 5000) {
        console.error('[ErrorHandler]', message);

        // Try to find or create alert container
        let alertContainer = document.getElementById('error-alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'error-alert-container';
            alertContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(alertContainer);
        }

        // Create alert element
        const alert = document.createElement('div');
        alert.className = 'error-alert';
        alert.style.cssText = `
            background: #fee2e2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            color: #991b1b;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
        `;
        alert.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="flex-shrink: 0; font-size: 20px;">⚠️</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 4px;">오류 발생</div>
                    <div style="font-size: 14px;">${message}</div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()"
                        style="background: none; border: none; font-size: 20px; cursor: pointer; color: #991b1b;">
                    ×
                </button>
            </div>
        `;

        alertContainer.appendChild(alert);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                alert.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => alert.remove(), 300);
            }, duration);
        }
    },

    /**
     * Safe fetch with automatic error handling
     * @param {string} url - API endpoint
     * @param {object} options - Fetch options
     * @param {boolean} showErrorAlert - Show error alert to user
     * @returns {Promise} - Fetch promise
     */
    async safeFetch(url, options = {}, showErrorAlert = true) {
        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || errorData.message || `API 오류 (${response.status})`;

                if (showErrorAlert) {
                    this.showError(errorMessage);
                }

                throw new Error(errorMessage);
            }

            return response;
        } catch (error) {
            console.error('[ErrorHandler] Fetch error:', error);

            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                if (showErrorAlert) {
                    this.showError('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.');
                }
            } else if (showErrorAlert && !error.message.includes('API 오류')) {
                this.showError(error.message || '알 수 없는 오류가 발생했습니다.');
            }

            throw error;
        }
    },

    /**
     * Safe getElementById with null check
     * @param {string} id - Element ID
     * @param {boolean} throwError - Throw error if not found
     * @returns {HTMLElement|null}
     */
    safeGetElementById(id, throwError = false) {
        const element = document.getElementById(id);

        if (!element) {
            console.warn(`[ErrorHandler] Element not found: #${id}`);
            if (throwError) {
                throw new Error(`Required element not found: #${id}`);
            }
        }

        return element;
    },

    /**
     * Safe querySelector with null check
     * @param {string} selector - CSS selector
     * @param {boolean} throwError - Throw error if not found
     * @returns {HTMLElement|null}
     */
    safeQuerySelector(selector, throwError = false) {
        const element = document.querySelector(selector);

        if (!element) {
            console.warn(`[ErrorHandler] Element not found: ${selector}`);
            if (throwError) {
                throw new Error(`Required element not found: ${selector}`);
            }
        }

        return element;
    },

    /**
     * Initialize global error handlers
     */
    init() {
        // Add CSS animations
        if (!document.getElementById('error-handler-styles')) {
            const style = document.createElement('style');
            style.id = 'error-handler-styles';
            style.textContent = `
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOutRight {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // Global error handler for uncaught errors
        window.addEventListener('error', (event) => {
            console.error('[ErrorHandler] Uncaught error:', event.error);

            // Don't show alert for script loading errors
            if (event.message && event.message.includes('Script error')) {
                return;
            }

            this.showError('페이지 로드 중 오류가 발생했습니다.');
        });

        // Global handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('[ErrorHandler] Unhandled promise rejection:', event.reason);

            // Don't show alert for AbortError (user cancelled)
            if (event.reason && event.reason.name === 'AbortError') {
                return;
            }

            this.showError('비동기 작업 중 오류가 발생했습니다.');
        });

        console.log('[ErrorHandler] Initialized');
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.ErrorHandler.init());
} else {
    window.ErrorHandler.init();
}

// Create shorthand functions for convenience
window.$id = (id) => window.ErrorHandler.safeGetElementById(id);
window.$q = (selector) => window.ErrorHandler.safeQuerySelector(selector);
window.safeFetch = (url, options, showError) => window.ErrorHandler.safeFetch(url, options, showError);
