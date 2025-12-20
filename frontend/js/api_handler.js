// API Handler - API 통신 전용 파일
let API_CONFIG = {};

// 설정 파일 로드
async function loadConfig() {
    try {
        const response = await fetch('/frontend/config.json');
        const config = await response.json();

        // "auto" 값이면 현재 origin 사용 (환경 자동 감지)
        const resolveUrl = (url) => {
            return url === 'auto' ? window.location.origin : url;
        };

        API_CONFIG = {
            chartServer: resolveUrl(config.api.chartServerUrl),
            tradingServer: resolveUrl(config.api.tradingServerUrl),
            endpoints: {
                chart: {
                    candles: {
                        days: '/api/upbit/candles/days',
                        minutes: '/api/upbit/candles/minutes',
                        weeks: '/api/upbit/candles/weeks',
                        months: '/api/upbit/candles/months'
                    },
                    market: '/api/upbit/market/all'
                },
                trading: {
                    holdings: '/api/holdings',
                    buy: '/api/trading/buy',
                    sell: '/api/trading/sell',
                    cancel: '/api/trading/cancel',
                    currentPrice: '/api/trading/current-price',
                    orders: '/api/orders'
                }
            }
        };
    } catch (error) {
        console.error('Failed to load config:', error);
        // 기본값: 현재 origin 사용 (환경 자동 감지)
        API_CONFIG = {
            chartServer: window.location.origin,
            tradingServer: window.location.origin,
            endpoints: {
                chart: {
                    candles: {
                        days: '/api/upbit/candles/days',
                        minutes: '/api/upbit/candles/minutes',
                        weeks: '/api/upbit/candles/weeks',
                        months: '/api/upbit/candles/months'
                    },
                    market: '/api/upbit/market/all'
                },
                trading: {
                    holdings: '/api/holdings',
                    buy: '/api/trading/buy',
                    sell: '/api/trading/sell',
                    cancel: '/api/trading/cancel',
                    currentPrice: '/api/trading/current-price',
                    orders: '/api/orders'
                }
            }
        };
    }
}

class APIHandler {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 60000; // 1분
        this.holdingsCache = null;
        this.holdingsCacheTime = 0;
        this.holdingsCacheDuration = 300000; // 5분 (holdings는 거의 변경되지 않음)
        this.ordersCache = new Map(); // market별 캐시
        this.ordersCacheTime = new Map();
        this.ordersCacheDuration = 60000; // 1분 (orders도 자주 변경되지 않음)
    }

    // 캐시 관리
    getCacheKey(url, params = {}) {
        return `${url}?${new URLSearchParams(params).toString()}`;
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }

    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    // 공통 API 호출 메서드
    async makeRequest(url, options = {}) {
        try {
            // JWT 토큰을 localStorage에서 가져오기
            const accessToken = localStorage.getItem('access_token');

            // 헤더 구성
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // JWT 토큰이 있으면 Authorization 헤더 추가
            if (accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await fetch(url, {
                headers,
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // 차트 데이터 API
    async getCandles(timeframe, market, count = 200, unit = null, to = null) {
        try {
            // API_CONFIG가 로드되었는지 확인
            if (!API_CONFIG.chartServer || !API_CONFIG.endpoints) {
                throw new Error('API configuration not loaded yet');
            }

            const params = { market, count };
            if (unit) params.unit = unit;
            if (to) params.to = to;

            const url = `${API_CONFIG.chartServer}${API_CONFIG.endpoints.chart.candles[timeframe]}`;
            const cacheKey = this.getCacheKey(url, params);

            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }

            const queryString = new URLSearchParams(params).toString();
            const fullUrl = `${url}?${queryString}`;

            const data = await this.makeRequest(fullUrl);

            // Wrap response for consistency with other methods
            const response = {
                success: true,
                data: data
            };

            this.setCache(cacheKey, response);
            console.log('[API] Candles loaded:', data.length, 'candles for', market);

            return response;
        } catch (error) {
            console.error('[API] getCandles failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getMarketList() {
        try {
            if (!API_CONFIG.chartServer || !API_CONFIG.endpoints) {
                throw new Error('API configuration not loaded yet');
            }

            const url = `${API_CONFIG.chartServer}${API_CONFIG.endpoints.chart.market}`;
            const cacheKey = this.getCacheKey(url);

            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }

            const data = await this.makeRequest(url);

            // Wrap response for consistency
            const response = {
                success: true,
                data: data
            };

            this.setCache(cacheKey, response);
            console.log('[API] Market list loaded:', data.length, 'markets');

            return response;
        } catch (error) {
            console.error('[API] getMarketList failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 거래 API
    async getHoldings(useCache = true, retryCount = 0) {
        try {
            if (!API_CONFIG.tradingServer || !API_CONFIG.endpoints) {
                throw new Error('API configuration not loaded yet');
            }

            // 캐시 확인
            const now = Date.now();
            if (useCache && this.holdingsCache && (now - this.holdingsCacheTime) < this.holdingsCacheDuration) {
                console.log('[API] Using cached holdings (age:', Math.round((now - this.holdingsCacheTime) / 1000), 'seconds)');
                return this.holdingsCache;
            }

            const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.holdings}`;
            
            // 타임아웃을 60초로 증가 (보유코인이 많을 경우 시간 소요)
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Holdings request timeout')), 60000)
            );
            
            const data = await Promise.race([
                this.makeRequest(url),
                timeoutPromise
            ]);

            // 서버 응답이 이미 {success: true, coins: [...]} 형태이므로
            // 추가 래핑 없이 그대로 반환
            console.log('[API] Holdings response:', data);
            
            // data를 그대로 사용하되, success 필드가 없으면 추가
            const response = data.success !== undefined ? data : {
                success: true,
                data: data
            };

            // 캐시 저장
            this.holdingsCache = response;
            this.holdingsCacheTime = now;
            console.log('[API] Holdings cached at', new Date(now).toLocaleTimeString());

            return response;
        } catch (error) {
            console.error('[API] getHoldings failed (attempt', retryCount + 1, '):', error);
            
            // 재시도 로직 (최대 2번 재시도)
            if (retryCount < 2 && error.message.includes('timeout')) {
                console.log('[API] Retrying holdings request in 2 seconds...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                return await this.getHoldings(useCache, retryCount + 1);
            }
            
            // 재시도 실패 또는 다른 에러
            return {
                success: false,
                error: error.message,
                retryCount: retryCount + 1
            };
        }
    }

    async getCurrentPrice(market) {
        if (!API_CONFIG.tradingServer || !API_CONFIG.endpoints) {
            throw new Error('API configuration not loaded yet');
        }
        
        const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.currentPrice}/${market}`;
        return await this.makeRequest(url);
    }

    async placeOrder(orderData) {
        const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.buy}`;
        return await this.makeRequest(url, {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async sellOrder(orderData) {
        const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.sell}`;
        return await this.makeRequest(url, {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async cancelOrder(orderUuid) {
        const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.cancel}/${orderUuid}`;
        return await this.makeRequest(url, {
            method: 'DELETE'
        });
    }

    async getOrders(market = null, state = 'done', limit = 100, useCache = true) {
        try {
            if (!API_CONFIG.tradingServer || !API_CONFIG.endpoints) {
                throw new Error('API configuration not loaded yet');
            }

            const cacheKey = `${market || 'all'}_${state}_${limit}`;
            const now = Date.now();

            // 캐시 확인
            if (useCache && this.ordersCache.has(cacheKey)) {
                const cacheTime = this.ordersCacheTime.get(cacheKey) || 0;
                if ((now - cacheTime) < this.ordersCacheDuration) {
                    console.log('[API] Using cached orders for', market || 'all markets', '(age:', Math.round((now - cacheTime) / 1000), 'seconds)');
                    return this.ordersCache.get(cacheKey);
                }
            }

            const params = {
                state,
                limit,
                include_exec: 'true'  // 체결 시간 정보 포함 (executed_at)
            };
            if (market) params.market = market;

            const url = `${API_CONFIG.tradingServer}${API_CONFIG.endpoints.trading.orders}`;
            const queryString = new URLSearchParams(params).toString();
            const fullUrl = `${url}?${queryString}`;

            const data = await this.makeRequest(fullUrl);

            // 서버 응답이 이미 {success: true, orders: [...]} 형태이므로
            // 추가 래핑 없이 그대로 반환
            console.log('[API] Orders response:', data);
            
            // data를 그대로 사용하되, success 필드가 없으면 추가
            const response = data.success !== undefined ? data : {
                success: true,
                data: data
            };

            // 캐시 저장
            this.ordersCache.set(cacheKey, response);
            this.ordersCacheTime.set(cacheKey, now);
            console.log('[API] Orders cached for', market || 'all markets', 'at', new Date(now).toLocaleTimeString());

            return response;
        } catch (error) {
            console.error('[API] getOrders failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // ========================================
    // DATABASE QUERY METHODS
    // ========================================

    async getOrdersFromDB(params = {}) {
        try {
            if (!API_CONFIG.tradingServer) {
                throw new Error('API configuration not loaded yet');
            }

            const queryParams = new URLSearchParams(params).toString();
            const url = `${API_CONFIG.tradingServer}/api/orders/db${queryParams ? '?' + queryParams : ''}`;

            console.log('[API] Fetching orders from database:', url);
            const data = await this.makeRequest(url);

            return data;
        } catch (error) {
            console.error('[API] getOrdersFromDB failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getOrderStatistics() {
        try {
            if (!API_CONFIG.tradingServer) {
                throw new Error('API configuration not loaded yet');
            }

            const url = `${API_CONFIG.tradingServer}/api/analytics/orders/stats`;

            console.log('[API] Fetching order statistics from database');
            const data = await this.makeRequest(url);

            return data;
        } catch (error) {
            console.error('[API] getOrderStatistics failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async getMarketAnalytics(market) {
        try {
            if (!API_CONFIG.tradingServer) {
                throw new Error('API configuration not loaded yet');
            }

            const url = `${API_CONFIG.tradingServer}/api/analytics/market/${market}`;

            console.log('[API] Fetching market analytics for', market);
            const data = await this.makeRequest(url);

            return data;
        } catch (error) {
            console.error('[API] getMarketAnalytics failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 캐시 클리어
    clearCache() {
        this.cache.clear();
        this.holdingsCache = null;
        this.holdingsCacheTime = 0;
        this.ordersCache.clear();
        this.ordersCacheTime.clear();
        console.log('[API] All caches cleared');
    }

    // Holdings 캐시만 클리어
    clearHoldingsCache() {
        this.holdingsCache = null;
        this.holdingsCacheTime = 0;
        console.log('[API] Holdings cache cleared');
    }

    // Orders 캐시만 클리어
    clearOrdersCache(market = null) {
        if (market) {
            // 특정 마켓의 캐시만 클리어
            const keysToDelete = [];
            for (const key of this.ordersCache.keys()) {
                if (key.startsWith(market)) {
                    keysToDelete.push(key);
                }
            }
            keysToDelete.forEach(key => {
                this.ordersCache.delete(key);
                this.ordersCacheTime.delete(key);
            });
            console.log('[API] Orders cache cleared for', market);
        } else {
            // 모든 orders 캐시 클리어
            this.ordersCache.clear();
            this.ordersCacheTime.clear();
            console.log('[API] All orders caches cleared');
        }
    }

    // 서버 상태 확인
    async checkServerHealth() {
        try {
            const chartHealth = await this.makeRequest(`${API_CONFIG.chartServer}/health`);
            const tradingHealth = await this.makeRequest(`${API_CONFIG.tradingServer}/health`);
            
            return {
                chart: chartHealth.status === 'healthy',
                trading: tradingHealth.status === 'healthy'
            };
        } catch (error) {
            console.error('Server health check failed:', error);
            return {
                chart: false,
                trading: false
            };
        }
    }
}

// 전역 API 핸들러 인스턴스
const apiHandler = new APIHandler();

// 유틸리티 함수들
const formatPrice = (price) => {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
};

const formatChange = (change, changeRate) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${formatPrice(change)} (${sign}${changeRate.toFixed(2)}%)`;
};

const formatNumber = (num, decimals = 0) => {
    return new Intl.NumberFormat('ko-KR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
};

const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
};

// 에러 처리
const handleAPIError = (error, context = '') => {
    console.error(`API Error ${context}:`, error);
    
    // 사용자에게 에러 표시
    const errorMessage = error.message || '알 수 없는 오류가 발생했습니다.';
    showNotification(`오류: ${errorMessage}`, 'error');
};

// 알림 표시 함수
const showNotification = (message, type = 'info') => {
    // 간단한 알림 구현 (실제로는 더 정교한 알림 시스템 사용)
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // DOM에 알림 표시 (선택사항)
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 16px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        border-radius: 6px;
        z-index: 10000;
        font-size: 14px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
};

// 전역으로 내보내기
window.APIHandler = APIHandler;
window.formatPrice = formatPrice;
window.formatChange = formatChange;
window.formatNumber = formatNumber;
window.formatTime = formatTime;
window.handleAPIError = handleAPIError;
window.showNotification = showNotification;

// 설정 로드 후 APIHandler 초기화
loadConfig().then(() => {
    window.apiHandler = new APIHandler();
    console.log('API Handler initialized with config:', API_CONFIG);
}).catch(error => {
    console.error('Failed to load API configuration:', error);
    // 기본 설정으로 APIHandler 초기화
    window.apiHandler = new APIHandler();
});
