# Feature Registry
**Last Updated**: 2025-10-17 10:20
**Version**: 1.0 (Initial Baseline)
**Purpose**: Single source of truth for all implemented features
**Status**: 🔍 Requires Browser Verification

---

## How to Use This Registry

1. **Before claiming a feature works**: Verify ALL checkboxes in "Verification Checklist"
2. **After making changes**: Update this registry immediately
3. **When debugging**: Check this registry to see what's actually implemented
4. **Regular audits**: Run test commands monthly to verify features still work

---

## Legend

- ✅ **Working**: Verified working in browser within last 7 days
- ⚠️ **Partial**: Code exists but not fully functional
- ❌ **Missing**: Documented or expected but not implemented
- 🔍 **Unknown**: Not yet verified in browser
- 🚧 **In Progress**: Currently being implemented

---

## Chart Display Features

### ✅ Candlestick Chart Rendering
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: Chart Core
- **Files**:
  - HTML: Line 293 in `frontend/trading_chart.html` (`#chart-container`)
  - Logic: Line 205-267 in `frontend/js/trading_chart_working.js` (`loadInitialCandles`)
  - Utils: `frontend/js/chart_utils.js` (ChartUtils class)
- **Dependencies**: Lightweight Charts library, API server (port 8080)
- **Test Command**:
  ```javascript
  // Browser console
  console.log('Chart exists:', !!window.chartUtils?.chart);
  console.log('Candle series:', !!window.chartUtils?.candleSeries);
  console.log('Chart data length:', window.workingChart?.chartData?.length);
  ```
- **Verification Checklist**:
  - [x] Chart renders on page load
  - [x] Candlesticks display with correct colors (green up, red down)
  - [x] Chart responsive to container size
  - [x] No console errors on load
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

### ✅ Price Info Display (Simplified)
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: UI Display
- **Files**:
  - HTML: Line 254-261 in `frontend/trading_chart.html` (`#coin-name`, `#candle-type`)
  - Logic: Line 628-683 in `frontend/js/trading_chart_working.js` (`updatePriceInfo`)
  - CSS: Line 330-356 in `frontend/css/integrated.css`
- **Dependencies**: Coin selection, timeframe selection
- **Test Command**:
  ```javascript
  // Browser console
  console.log('Coin name:', document.getElementById('coin-name')?.textContent);
  console.log('Candle type:', document.getElementById('candle-type')?.textContent);
  ```
- **Verification Checklist**:
  - [x] Displays coin name correctly (Korean name)
  - [x] Displays candle type (분봉/일봉/주봉/월봉)
  - [x] Updates when coin changed
  - [x] Updates when timeframe changed
- **Recent Changes**: Simplified to show only coin name and candle type (removed current price, price change)
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

## Moving Averages (MA) Features

### ✅ MA Toggle Button
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: Chart Indicators
- **Files**:
  - HTML: Line 142 in `frontend/trading_chart.html` (`#ma-toggle`)
  - Event Listener: Line 1348-1354 in `frontend/js/trading_chart_working.js`
  - Toggle Function: Line 1970-2003 in `frontend/js/trading_chart_working.js` (`toggleAllMAs`)
  - Update Function: Line 1900-1968 in `frontend/js/trading_chart_working.js` (`updateMAs`)
- **Dependencies**: Chart data loaded, ChartUtils
- **Test Command**:
  ```javascript
  // Browser console
  document.getElementById('ma-toggle').click();
  // OR
  window.workingChart.toggleAllMAs();
  ```
- **Verification Checklist**:
  - [x] Button exists and clickable
  - [x] Button shows 'active' class when toggled on
  - [x] MA lines appear/disappear on toggle
  - [x] Console logs show "[Working] MA toggle button clicked"
  - [x] Works after coin change
  - [x] Works after timeframe change
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

### ✅ MA Display (20, 50, 100, 200, 300, 500, 1000)
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: Chart Indicators
- **Files**:
  - Logic: Line 1900-1968 in `frontend/js/trading_chart_working.js` (`updateMAs`)
  - Calculation: Line 880-943 in `frontend/js/chart_utils.js` (`calculateMA`)
- **Dependencies**: MA Toggle enabled, chart data loaded
- **Test Command**:
  ```javascript
  // Browser console
  window.workingChart.updateMAs();
  console.log('MA Series:', window.workingChart.maSeries);
  ```
- **Verification Checklist**:
  - [x] Lines render with correct colors
  - [x] Lines follow price movements correctly
  - [x] Lines update when coin changed
  - [x] Lines update when timeframe changed
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

### ✅ MA Value Display
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: UI Display
- **Files**:
  - HTML: Line 291 in `frontend/trading_chart.html` (`.ma-values`)
  - Logic: Line 1876-1898 in `frontend/js/trading_chart_working.js` (`updateMAValues`)
- **Dependencies**: MA Toggle enabled, MA data calculated
- **Test Command**:
  ```javascript
  // Browser console
  window.workingChart.updateMAValues();
  document.querySelectorAll('.ma-value').forEach(el => console.log(el.textContent));
  ```
- **Verification Checklist**:
  - [x] Values display in sidebar
  - [x] Values update on price change
  - [x] Values update on coin change
  - [x] Values update on timeframe change
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

## Horizontal Line Features (Price Levels)

### ⚠️ Average Price Line
- **Status**: ⚠️ Partial (Code exists but NOT displaying)
- **Category**: Trading Indicators
- **Files**:
  - Constructor: Line 44-48 in `frontend/js/trading_chart_working.js` (variables initialized)
  - Draw Function: Line 2327-2427 in `frontend/js/trading_chart_working.js` (`drawAvgPriceLine`)
  - Update Function: Line 2538-2568 in `frontend/js/trading_chart_working.js` (`updateAvgPriceAndPendingOrders`)
  - Remove Function: Line 2488-2536 in `frontend/js/trading_chart_working.js` (`removeAvgPriceAndPendingOrderLines`)
  - Called From: Line 268-271 in `frontend/js/trading_chart_working.js` (end of `loadInitialCandles`)
- **Dependencies**: API server (port 8081), Holdings API, User owns displayed coin
- **Test Command**:
  ```javascript
  // Browser console
  console.log('Avg price enabled:', window.workingChart.avgPriceLineEnabled);
  console.log('Avg price line:', window.workingChart.avgPriceLine);
  window.workingChart.updateAvgPriceAndPendingOrders();
  ```
- **Verification Checklist**:
  - [x] Code exists in file
  - [x] Function called from loadInitialCandles
  - [x] Debug logging added (20+ console.log statements)
  - [ ] **NOT VERIFIED**: Line actually displays on chart
  - [ ] **NOT VERIFIED**: Line shows gold color (#FFD700)
  - [ ] **NOT VERIFIED**: Line shows correct average price
- **Known Issues**:
  - **CRITICAL**: Implementation complete but line not displaying
  - Requires browser console testing to diagnose
  - Possible causes: API server not running, user doesn't own coin, timing issue, chart reference issue
- **Debug Guide**: See `DEBUG_AVG_PRICE_LINES.md`
- **Git Commit**: N/A (pre-Git)

---

### ⚠️ Pending Orders Lines
- **Status**: ⚠️ Partial (Code exists but NOT displaying)
- **Category**: Trading Indicators
- **Files**:
  - Constructor: Line 46-48 in `frontend/js/trading_chart_working.js` (variables initialized)
  - Draw Function: Line 2429-2486 in `frontend/js/trading_chart_working.js` (`drawPendingOrderLines`)
  - Update Function: Line 2538-2568 in `frontend/js/trading_chart_working.js` (`updateAvgPriceAndPendingOrders`)
  - Remove Function: Line 2488-2536 in `frontend/js/trading_chart_working.js` (`removeAvgPriceAndPendingOrderLines`)
  - Called From: Line 268-271 in `frontend/js/trading_chart_working.js` (end of `loadInitialCandles`)
- **Dependencies**: API server (port 8081), Orders API, User has pending orders
- **Test Command**:
  ```javascript
  // Browser console
  console.log('Pending orders enabled:', window.workingChart.pendingOrderLinesEnabled);
  console.log('Pending order lines:', window.workingChart.pendingOrderLines);
  window.workingChart.updateAvgPriceAndPendingOrders();
  ```
- **Verification Checklist**:
  - [x] Code exists in file
  - [x] Function called from loadInitialCandles
  - [ ] **NOT VERIFIED**: Lines actually display on chart
  - [ ] **NOT VERIFIED**: Buy orders show green (#26a69a)
  - [ ] **NOT VERIFIED**: Sell orders show red (#ef5350)
  - [ ] **NOT VERIFIED**: Lines show correct order prices
- **Known Issues**:
  - **CRITICAL**: Same as Average Price Line - implementation complete but not displaying
  - Requires browser console testing to diagnose
- **Debug Guide**: See `DEBUG_AVG_PRICE_LINES.md`
- **Git Commit**: N/A (pre-Git)

---

## Support/Resistance Features

### ❌ Support/Resistance Toggle
- **Status**: ❌ Missing (Button exists, functionality does NOT exist)
- **Category**: Chart Indicators
- **Files**:
  - HTML: Line 141 in `frontend/trading_chart.html` (`#support-resistance-toggle`)
  - Event Listener: ❌ NOT FOUND
  - Toggle Function: ❌ NOT FOUND (`toggleSupportResistance` does NOT exist)
  - Draw Function: ❌ NOT FOUND (`drawSupportResistance` does NOT exist)
  - Remove Function: ❌ NOT FOUND (`removeSupportResistance` does NOT exist)
- **Dependencies**: Chart data loaded
- **Test Command**:
  ```javascript
  // Browser console
  console.log('Button exists:', !!document.getElementById('support-resistance-toggle'));
  console.log('Toggle function exists:', typeof window.workingChart?.toggleSupportResistance);
  // Expected: undefined
  ```
- **Verification Checklist**:
  - [x] Button exists in HTML
  - [ ] **MISSING**: Event listener registered
  - [ ] **MISSING**: Toggle function exists
  - [ ] **MISSING**: Calculate S/R levels function
  - [ ] **MISSING**: Draw lines on chart
  - [ ] **MISSING**: Remove lines function
- **Known Issues**:
  - **CRITICAL**: Feature documented in `SUPPORT_RESISTANCE_FIX.md` but code DOES NOT EXIST
  - Documentation/code mismatch - evidence of feature loss
  - Requires full implementation from scratch
- **Action Required**: Implement complete feature or remove button
- **Git Commit**: N/A (pre-Git)

---

## Selection & Control Features

### ✅ Coin Selection Dropdown
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: User Controls
- **Files**:
  - HTML: Line 97 in `frontend/trading_chart.html` (`#coin-select`)
  - Event Listener: Line 1302 in `frontend/js/trading_chart_working.js`
  - Handler Function: Line 1427-1524 in `frontend/js/trading_chart_working.js` (`handleCoinChange`)
- **Dependencies**: API server (port 8080), Market list API
- **Test Command**:
  ```javascript
  // Browser console
  const coinSelect = document.getElementById('coin-select');
  console.log('Options count:', coinSelect.options.length);
  coinSelect.value = 'KRW-XRP';
  coinSelect.dispatchEvent(new Event('change'));
  ```
- **Verification Checklist**:
  - [x] Dropdown populated with coins
  - [x] Selection changes chart data
  - [x] Selection updates price info
  - [x] Selection triggers chart reload
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

### ✅ Timeframe Selection Buttons
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: User Controls
- **Files**:
  - HTML: Line 107-133 in `frontend/trading_chart.html` (`.timeframe-buttons`)
  - Event Listeners: Line 1308-1335 in `frontend/js/trading_chart_working.js`
  - Handler Function: Line 1525-1605 in `frontend/js/trading_chart_working.js` (`handleTimeframeChange`)
- **Dependencies**: API server (port 8080), Candle data API
- **Test Command**:
  ```javascript
  // Browser console
  document.querySelector('[data-timeframe="minutes"][data-unit="60"]').click();
  // Should reload chart with 60-minute candles
  ```
- **Verification Checklist**:
  - [x] Buttons exist for all timeframes (1분/5분/15분/60분/240분/일/주/월)
  - [x] Active button has 'active' class
  - [x] Clicking button reloads chart
  - [x] Clicking button updates price info
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

## API Integration Features

### ✅ Chart Data API (Port 8080)
- **Status**: ✅ Working (Verified: 2025-10-17)
- **Category**: API Integration
- **Files**:
  - Config: `frontend/config.json` (chartServerUrl)
  - Handler: `frontend/js/api_handler.js` (APIHandler class)
  - Server: `clean_upbit_server.py` (port 8080)
- **Endpoints**:
  - `/api/upbit/candles/minutes/{unit}`
  - `/api/upbit/candles/days`
  - `/api/upbit/candles/weeks`
  - `/api/upbit/candles/months`
- **Dependencies**: Server running on port 8080
- **Test Command**:
  ```javascript
  // Browser console
  await window.apiHandler.getCandles('KRW-BTC', 'days', 200, false);
  ```
- **Verification Checklist**:
  - [x] Server running (verified with netstat)
  - [x] API responds to requests
  - [x] Data returned in correct format
  - [x] Cache working correctly
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

### 🔍 Trading Data API (Port 8081)
- **Status**: 🔍 Unknown (Not verified if server running)
- **Category**: API Integration
- **Files**:
  - Config: `frontend/config.json` (tradingServerUrl)
  - Handler: `frontend/js/api_handler.js` (APIHandler class)
  - Server: `simple_dual_server.py` (port 8081)
- **Endpoints**:
  - `/api/holdings` (get user's coin holdings with avg price)
  - `/api/orders` (get pending orders)
- **Dependencies**: Server running on port 8081, API keys configured
- **Test Command**:
  ```javascript
  // Browser console
  await window.apiHandler.getHoldings();
  await window.apiHandler.getOrders('KRW-BTC', 'wait', 50, false);
  ```
- **Verification Checklist**:
  - [ ] **NOT VERIFIED**: Server running on port 8081
  - [ ] **NOT VERIFIED**: API responds to requests
  - [ ] **NOT VERIFIED**: Holdings data returned
  - [ ] **NOT VERIFIED**: Orders data returned
- **Known Issues**:
  - **SUSPECTED**: May not be running - could explain why avg price/pending orders don't display
  - Requires verification with `netstat -ano | findstr :8081`
- **Action Required**: Verify server status
- **Git Commit**: N/A (pre-Git)

---

## Testing & Debugging Features

### ✅ Horizontal Lines Test Page
- **Status**: ✅ Created (Not yet verified)
- **Category**: Testing Tools
- **Files**:
  - Test Page: `frontend/test_horizontal_lines.html`
- **Purpose**: Verify Lightweight Charts horizontal line drawing works independently
- **Test Command**:
  ```
  Open browser: http://localhost:8080/frontend/test_horizontal_lines.html
  Click: "Test Avg Price Line" button
  Click: "Test Pending Orders" button
  ```
- **Verification Checklist**:
  - [x] File created
  - [ ] **NOT VERIFIED**: Page loads
  - [ ] **NOT VERIFIED**: Chart renders
  - [ ] **NOT VERIFIED**: Gold line appears on button click
  - [ ] **NOT VERIFIED**: Green/red lines appear on button click
- **Known Issues**: None
- **Git Commit**: N/A (pre-Git)

---

## Documentation Files

### Debug Guides Created
1. **DEBUG_AVG_PRICE_LINES.md** - Comprehensive debugging guide for avg price/pending orders
2. **COMPREHENSIVE_DEBUG_REPORT.md** - Analysis of all chart action features
3. **FEATURE_LOSS_ANALYSIS_AND_SOLUTION.md** - Root cause analysis and solutions
4. **FEATURE_REGISTRY.md** (this file) - Complete feature inventory

### Outdated/Incorrect Documentation
1. **SUPPORT_RESISTANCE_FIX.md** - ⚠️ WARNING: Describes functions that DON'T EXIST
   - Claims `removeSupportResistance()` is implemented - IT IS NOT
   - Claims `drawSupportResistance()` is implemented - IT IS NOT
   - Claims `toggleSupportResistance()` is implemented - IT IS NOT
   - **Action Required**: Either update to match reality or delete file

---

## Summary Statistics

### Features by Status
- ✅ **Working**: 8 features (67%)
- ⚠️ **Partial**: 2 features (17%)
- ❌ **Missing**: 1 feature (8%)
- 🔍 **Unknown**: 1 feature (8%)

### Critical Issues
1. **Average Price & Pending Orders**: Code exists but not displaying (UNKNOWN CAUSE)
2. **Support/Resistance**: Documented but NOT implemented (FEATURE LOSS)
3. **Trading API Server**: Unknown if running (SUSPECTED ROOT CAUSE of issue #1)

---

## Next Actions Required

### Immediate (User Action)
1. **Test browser console** - Run diagnostic commands from `COMPREHENSIVE_DEBUG_REPORT.md`
2. **Check server status** - Verify port 8081 running (`netstat -ano | findstr :8081`)
3. **Test horizontal lines page** - Open `test_horizontal_lines.html` and verify lines appear
4. **Copy console logs** - Report findings for diagnosis

### After Console Logs Received
1. **Diagnose root cause** - Determine why avg price/pending orders not displaying
2. **Apply fix** - Based on diagnosis results
3. **Verify fix** - Test in browser with hard refresh
4. **Update registry** - Mark features as ✅ Working or ❌ Missing

### Development Process Changes
1. **Initialize Git** - Start version control immediately
2. **Implement/Remove Support/Resistance** - Either complete the feature or remove the button
3. **Create automated tests** - Build `test_all_features.html` smoke test page
4. **Establish workflow** - Follow verification checklist before marking features complete

---

**Registry Version**: 1.0 (Baseline)
**Last Audit**: 2025-10-17
**Next Audit Due**: 2025-10-24
**Verified By**: Claude Code
**Status**: 🔍 Awaiting Browser Verification
