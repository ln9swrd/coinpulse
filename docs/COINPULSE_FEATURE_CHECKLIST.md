# CoinPulse Feature Checklist
Generated: 2025-10-16

## 1. Chart Settings (차트 설정)

### 1.1 Timeframe Selection
- [ ] 1분 (1m)
- [ ] 5분 (5m)
- [ ] 15분 (15m)
- [ ] 1시간 (1h)
- [ ] 4시간 (4h)
- [ ] 일봉 (1d) - Default
- [ ] 주봉 (1w)

### 1.2 Coin Selection
- [ ] Coin search input (코인 검색)
- [ ] Coin dropdown list
- [ ] Refresh coins button (🔄)
- [ ] Korean coin name support
- [ ] English coin name support
- [ ] Market code search (KRW-BTC)

### 1.3 Chart Type (Hidden)
- [ ] Candlestick (default)
- [ ] Line chart
- [ ] Area chart

## 2. Technical Indicators (기술적 지표)

### 2.1 Moving Averages
- [ ] MA Settings Button (⚙️ 이평선설정)
- [ ] MA20 toggle
- [ ] MA50 toggle
- [ ] MA100 toggle
- [ ] MA200 toggle
- [ ] MA300 toggle
- [ ] MA500 toggle
- [ ] MA1000 toggle
- [ ] MA visibility toggle
- [ ] MA settings modal (open/close)
- [ ] Apply MA settings
- [ ] Cancel MA settings
- [ ] Save MA settings to localStorage

### 2.2 RSI Indicator
- [ ] RSI toggle button
- [ ] RSI chart display (separate panel)
- [ ] RSI calculation
- [ ] RSI overbought/oversold status

### 2.3 MACD Indicator
- [ ] MACD toggle button
- [ ] MACD chart display (separate panel)
- [ ] MACD line
- [ ] Signal line
- [ ] Histogram

### 2.4 Bollinger Bands
- [ ] BB toggle button
- [ ] Upper band display
- [ ] Middle band display
- [ ] Lower band display

### 2.5 SuperTrend
- [ ] SuperTrend toggle button
- [ ] SuperTrend calculation
- [ ] SuperTrend display

## 3. Drawing Tools (그리기 도구)

### 3.1 Trendline Tools
- [ ] Draw trendline (추세선)
- [ ] Draw Fibonacci retracement (피보나치)
- [ ] Draw horizontal line (수평선)
- [ ] Draw vertical line (수직선)

### 3.2 Drawing Management
- [ ] Clear all drawings (🗑️ 모두 지우기)
- [ ] Show drawings list (📋 그리기 목록)
- [ ] Drawings list modal
- [ ] Delete individual drawing
- [ ] Save drawings to localStorage

## 4. Chart Actions (차트 액션)

### 4.1 Theme Toggle
- [ ] Dark/Light theme switch (🌙 테마)
- [ ] Theme persistence (localStorage)
- [ ] Theme apply to all chart elements

### 4.2 Support/Resistance Lines
- [ ] Support/Resistance toggle button (지지저항선)
- [ ] Auto-calculate support levels
- [ ] Auto-calculate resistance levels
- [ ] Display lines on chart

### 4.3 Moving Average Toggle
- [ ] MA visibility toggle (이평선)
- [ ] Show/hide all MAs at once

### 4.4 Trade Markers
- [ ] Trade markers toggle (💰 매매마커)
- [ ] Buy marker display (green)
- [ ] Sell marker display (red)
- [ ] Marker text with price
- [ ] Active by default

### 4.5 Trading History
- [ ] Show history modal (📊 매매이력)
- [ ] Load trading history
- [ ] Display buy/sell transactions
- [ ] Show transaction time
- [ ] Refresh history button
- [ ] Close modal

### 4.6 Pending Orders
- [ ] Pending order toggle (미체결)
- [ ] Load pending orders (state='wait')
- [ ] Display buy orders (green, below bar)
- [ ] Display sell orders (red, above bar)
- [ ] Active state UI update
- [ ] Remove markers on toggle off

### 4.7 Volume Toggle
- [ ] Volume visibility toggle (거래량)
- [ ] Show/hide volume chart
- [ ] Active by default

## 5. Portfolio & Holdings (보유 코인)

### 5.1 Holdings Display
- [ ] Holdings list panel
- [ ] Coin symbol display
- [ ] Average price display
- [ ] Profit/loss percentage
- [ ] Color coding (green/red)
- [ ] Click to view coin chart
- [ ] Refresh holdings button
- [ ] Loading state
- [ ] Error handling

### 5.2 Portfolio Stats
- [ ] Long-term count (장기)
- [ ] Short-term count (단기)
- [ ] Investment count (투자: 0/3)
- [ ] Budget amount (예산)
- [ ] Total profit rate (수익률)

## 6. Price Analysis (가격 정보 & 분석)

### 6.1 Price Info
- [ ] Current coin name
- [ ] Current timeframe display
- [ ] Current price (₩)
- [ ] Price change amount
- [ ] Price change percentage
- [ ] Up/down arrow indicator
- [ ] Color coding (green/red)

### 6.2 Technical Analysis Display
- [ ] RSI value
- [ ] RSI status (과매수/과매도/중립)
- [ ] MA20 value
- [ ] MA50 value
- [ ] MA100 value
- [ ] MA200 value

### 6.3 Real-time Analysis
- [ ] Trend direction (추세: 상승/하락/횡보)
- [ ] Volatility level (변동성: 높음/중간/낮음)
- [ ] Support level price
- [ ] Resistance level price
- [ ] Trading signal
- [ ] Last update time

## 7. Auto Trading (자동매매)

### 7.1 Holdings Auto-trading
- [ ] Holdings auto-trading toggle button
- [ ] Enable/disable holdings auto-trading
- [ ] Status display (활성화/비활성화)
- [ ] UI state update

### 7.2 Active Trading
- [ ] Active trading toggle button
- [ ] Enable/disable active trading
- [ ] Status display (활성화/비활성화)
- [ ] UI state update

### 7.3 Policy Management
- [ ] Policy settings button (정책 설정)
- [ ] Open policy modal
- [ ] Load trading policies
- [ ] Edit policies
- [ ] Save policies

## 8. Chart Core Functions

### 8.1 Chart Display
- [ ] Main price chart (candlestick)
- [ ] Volume chart (histogram)
- [ ] RSI chart (separate panel)
- [ ] MACD chart (separate panel)
- [ ] Chart resize on window resize
- [ ] Chart scrolling/panning
- [ ] Chart zoom (mouse wheel)

### 8.2 Data Loading
- [ ] Initial data load (200 candles)
- [ ] Load more data on scroll left
- [ ] Real-time data update
- [ ] Auto-update interval (optional)
- [ ] Loading overlay
- [ ] Error handling

### 8.3 Crosshair & Tooltip
- [ ] Crosshair display
- [ ] Price tooltip
- [ ] Time tooltip
- [ ] OHLCV data display

## 9. API Integration

### 9.1 Chart Server (Port 8080)
- [ ] GET /api/upbit/candles/days
- [ ] GET /api/upbit/candles/minutes
- [ ] GET /api/upbit/candles/weeks
- [ ] GET /api/upbit/candles/months
- [ ] GET /api/upbit/market/all
- [ ] GET /health

### 9.2 Trading Server (Port 8081)
- [ ] GET /api/holdings
- [ ] GET /api/orders
- [ ] POST /api/trading/buy
- [ ] POST /api/trading/sell
- [ ] DELETE /api/trading/cancel/:uuid
- [ ] GET /api/trading/current-price/:market
- [ ] GET /api/policies
- [ ] GET /api/health

### 9.3 API Error Handling
- [ ] Network error handling
- [ ] Server error handling
- [ ] Timeout handling
- [ ] Retry logic
- [ ] User notification

## 10. Data Caching

### 10.1 Chart Data Cache
- [ ] Candle data cache (1 minute)
- [ ] Market list cache (1 minute)
- [ ] Cache invalidation

### 10.2 Trading Data Cache
- [ ] Holdings cache (5 minutes)
- [ ] Orders cache (1 minute)
- [ ] Manual cache clear
- [ ] Market-specific cache clear

## 11. UI/UX Features

### 11.1 Responsive Design
- [ ] Desktop layout (1920px+)
- [ ] Tablet layout (768px-1920px)
- [ ] Mobile layout (< 768px)
- [ ] Touch support
- [ ] Keyboard shortcuts (optional)

### 11.2 Loading States
- [ ] Chart loading overlay
- [ ] Holdings loading text
- [ ] History loading text
- [ ] Button loading states

### 11.3 Error States
- [ ] API error notification
- [ ] Chart load error
- [ ] Holdings load error
- [ ] Network error display

### 11.4 Modals
- [ ] MA Settings modal
- [ ] Trading History modal
- [ ] Drawings List modal
- [ ] Click outside to close
- [ ] ESC key to close (optional)

## 12. Configuration Management

### 12.1 Config Files
- [ ] frontend/config.json exists
- [ ] chart_server_config.json exists
- [ ] trading_server_config.json exists
- [ ] trading_policies.json exists

### 12.2 Config Loading
- [ ] Load config on startup
- [ ] Fallback to default config
- [ ] Config validation
- [ ] Config error handling

### 12.3 LocalStorage
- [ ] MA settings persistence
- [ ] Theme persistence
- [ ] Chart preferences (optional)
- [ ] Drawings persistence (optional)

## 13. Performance

### 13.1 Optimization
- [ ] Debounced API calls
- [ ] Efficient data caching
- [ ] Minimal DOM updates
- [ ] Chart render optimization

### 13.2 Resource Management
- [ ] Memory leak prevention
- [ ] Event listener cleanup
- [ ] Chart instance cleanup
- [ ] Interval cleanup

## Status Summary
- Total Features: TBD
- Implemented: TBD
- Not Implemented: TBD
- Issues Found: TBD
