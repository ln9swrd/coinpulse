/**
 * PageLoader - External HTML Page Loader for Dashboard Integration
 *
 * Loads external HTML pages into the dashboard container without full page reload.
 * Extracts body content and re-executes scripts for full functionality.
 *
 * @version 1.0.0
 * @date 2025-12-21
 */

export class PageLoader {
    constructor() {
        this.cache = new Map();
        this.currentPage = null;
        this.abortController = null;
    }

    /**
     * Load external HTML page into container
     *
     * @param {string} url - URL of the page to load
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Loading options
     * @returns {Promise<void>}
     */
    async loadPage(url, container, options = {}) {
        const {
            useCache = true,
            showLoading = true,
            extractBody = true,
            executeScripts = true
        } = options;

        try {
            // Show loading state
            if (showLoading) {
                this.showLoadingState(container);
            }

            // Cancel previous request if any
            if (this.abortController) {
                this.abortController.abort();
            }

            this.abortController = new AbortController();

            // Check cache
            let html;
            if (useCache && this.cache.has(url)) {
                console.log('[PageLoader] Loading from cache:', url);
                html = this.cache.get(url);
            } else {
                console.log('[PageLoader] Fetching page:', url);
                const response = await fetch(url, {
                    signal: this.abortController.signal,
                    cache: 'no-cache'  // Force fresh fetch
                });

                if (!response.ok) {
                    // Do NOT cache failed responses
                    const error = new Error(`Failed to load page: ${response.status} ${response.statusText}`);
                    error.status = response.status;
                    throw error;
                }

                html = await response.text();

                // Only cache successful responses
                if (useCache && html && html.length > 0) {
                    this.cache.set(url, html);
                    console.log('[PageLoader] Cached page:', url);
                }
            }

            // Extract content
            const content = extractBody ? this.extractBodyContent(html) : html;

            // Clear container and insert content
            container.innerHTML = '';
            container.innerHTML = content;

            // Execute scripts if needed
            if (executeScripts) {
                await this.executeScripts(container);
            }

            // Update current page
            this.currentPage = url;

            console.log('[PageLoader] Page loaded successfully:', url);

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('[PageLoader] Page load aborted:', url);
                return;
            }

            console.error('[PageLoader] Failed to load page:', error);

            // Clear cache for this URL to allow retry
            this.clearCache(url);

            // Show error with specific message based on error type
            let errorMessage = error.message;
            if (error.status === 404) {
                errorMessage = '요청한 페이지를 찾을 수 없습니다. (404)';
            } else if (error.status >= 500) {
                errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '네트워크 연결을 확인해주세요.';
            }

            this.showErrorState(container, errorMessage, url);
        } finally {
            this.abortController = null;
        }
    }

    /**
     * Extract body content from HTML string
     *
     * @param {string} html - Full HTML string
     * @returns {string} - Body content HTML
     */
    extractBodyContent(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Get body content
        const bodyContent = doc.body.innerHTML;

        // Extract and append styles from head
        const styles = doc.querySelectorAll('style');
        let styleContent = '';
        styles.forEach(style => {
            styleContent += style.innerHTML + '\n';
        });

        // Wrap styles in <style> tag
        if (styleContent) {
            return `<style>${styleContent}</style>\n${bodyContent}`;
        }

        return bodyContent;
    }

    /**
     * Execute scripts in loaded content
     *
     * @param {HTMLElement} container - Container with loaded content
     */
    async executeScripts(container) {
        const scripts = container.querySelectorAll('script');

        for (const oldScript of scripts) {
            const newScript = document.createElement('script');

            // Copy attributes
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });

            // Copy content
            if (oldScript.src) {
                // External script - load it
                newScript.src = oldScript.src;
                await this.loadScriptAsync(newScript);
            } else {
                // Inline script - wrap in IIFE to avoid variable conflicts
                const scriptContent = oldScript.textContent;
                newScript.textContent = `(function() {\n${scriptContent}\n})();`;
            }

            // Replace old script with new one (check parentNode exists)
            if (oldScript.parentNode) {
                oldScript.parentNode.replaceChild(newScript, oldScript);
            } else {
                console.warn('[PageLoader] Script has no parent node, skipping replacement');
            }
        }
    }

    /**
     * Load external script asynchronously
     *
     * @param {HTMLScriptElement} script - Script element to load
     * @returns {Promise<void>}
     */
    loadScriptAsync(script) {
        return new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Show loading state in container
     *
     * @param {HTMLElement} container - Container element
     */
    showLoadingState(container) {
        container.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 400px;
                color: #666;
            ">
                <div style="
                    width: 48px;
                    height: 48px;
                    border: 4px solid #f3f4f6;
                    border-top-color: #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <p style="margin-top: 16px; font-size: 14px;">페이지 로딩 중...</p>
            </div>
            <style>
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            </style>
        `;
    }

    /**
     * Show error state in container
     *
     * @param {HTMLElement} container - Container element
     * @param {string} message - Error message
     * @param {string} url - Failed page URL (for retry)
     */
    showErrorState(container, message, url = null) {
        const retryButtonId = 'page-loader-retry-btn';

        container.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 400px;
                color: #dc2626;
                text-align: center;
                padding: 20px;
            ">
                <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">
                    페이지 로딩 실패
                </h3>
                <p style="margin: 0; font-size: 14px; color: #666;">
                    ${message}
                </p>
                <div style="margin-top: 20px; display: flex; gap: 12px;">
                    ${url ? `<button id="${retryButtonId}" style="
                        padding: 10px 24px;
                        background: #667eea;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        다시 시도
                    </button>` : ''}
                    <button onclick="window.location.reload()" style="
                        padding: 10px 24px;
                        background: #9ca3af;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        새로고침
                    </button>
                </div>
            </div>
        `;

        // Add retry button handler
        if (url) {
            const retryBtn = container.querySelector(`#${retryButtonId}`);
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    console.log('[PageLoader] Retrying page load:', url);
                    this.loadPage(url, container, { useCache: false });  // Force fresh fetch
                });
            }
        }
    }

    /**
     * Clear cache for specific URL or all URLs
     *
     * @param {string|null} url - URL to clear (null = clear all)
     */
    clearCache(url = null) {
        if (url) {
            this.cache.delete(url);
            console.log('[PageLoader] Cache cleared for:', url);
        } else {
            this.cache.clear();
            console.log('[PageLoader] All cache cleared');
        }
    }

    /**
     * Get current page URL
     *
     * @returns {string|null}
     */
    getCurrentPage() {
        return this.currentPage;
    }
}

// Create singleton instance
const pageLoader = new PageLoader();

// Export singleton
export default pageLoader;
