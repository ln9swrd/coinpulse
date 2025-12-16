# CoinPulse Testing Guide
Generated: 2025-10-17 02:00

## Quick Start

✅ **Servers Running:**
- Chart API Server (Port 8080): PID 28932
- Trading API Server (Port 8081): PID 17940

✅ **Browser Opened:**
- URL: http://localhost:8080/frontend/trading_chart.html
- Cache Version: 20251017_0200

---

## Feature Testing Checklist

### 1. Support/Resistance Toggle ✅

**Location:** Chart Actions section, button labeled "지지저항선"

**Test Steps:**
1. [ ] Click "지지저항선" button
2. [ ] Verify button becomes active (highlighted)
3. [ ] Check chart for horizontal lines:
   - Green dashed lines (support) - should see 3 lines below current price
   - Red dashed lines (resistance) - should see 3 lines above current price
4. [ ] Open browser console (F12)
5. [ ] Look for logs:
   - `[Working] Support/Resistance enabled, drawing lines...`
   - `[Working] Calculated support/resistance levels: Array(6)`
   - `[Working] Drew support/resistance lines: 6`
6. [ ] Click button again to disable
7. [ ] Verify lines disappear
8. [ ] Check console for: `[Working] Removed all support/resistance lines`

**Expected Result:**
- 6 horizontal lines appear/disappear on toggle
- Lines are at local high/low points
- No console errors

---

### 2. Auto-Trading Button Handlers ✅

#### 2a. Holdings Auto-Trading

**Location:** Top right header, "보유코인 자동매매" section

**Test Steps:**
1. [ ] Click "비활성화" button under "보유코인 자동매매"
2. [ ] Verify alert appears: "Holdings Auto-Trading Enabled..."
3. [ ] Click OK on alert
4. [ ] Verify button text changes (should update status)
5. [ ] Verify button gets highlighted/active style
6. [ ] Open browser console (F12)
7. [ ] Look for log: `[Working] Holdings auto-trading ENABLED`
8. [ ] Click button again
9. [ ] Verify alert: "Holdings Auto-Trading Disabled"
10. [ ] Verify button returns to normal state

**Expected Result:**
- Button toggles on/off
- Alerts appear correctly
- Console shows state changes
- No errors

#### 2b. Active Trading

**Location:** Top right header, "단기투자 자동매매" section

**Test Steps:**
1. [ ] Click "비활성화" button under "단기투자 자동매매"
2. [ ] Verify alert appears: "Active Trading Enabled..."
3. [ ] Follow same steps as Holdings Auto-Trading test
4. [ ] Verify independent state (doesn't affect holdings toggle)

**Expected Result:**
- Same as Holdings test
- Two toggles work independently

#### 2c. Policy Settings

**Location:** Top right header, "정책 설정" button

**Test Steps:**
1. [ ] Click "정책 설정" button
2. [ ] Verify alert appears with text:
   ```
   Policy Settings Modal

   This feature will allow you to:
   - Configure buy/sell policies
   - Set profit targets
   - Configure stop-loss rules
   - Manage risk parameters

   Modal UI coming soon!
   ```
3. [ ] Check console for: `[Working] Opening policy settings modal`

**Expected Result:**
- Alert appears with feature description
- No errors in console

---

### 3. Price Analysis Updates ✅

**Location:** Right side panel "코인분석"

#### 3a. Price Info Panel (💰 가격 정보)

**Test Steps:**
1. [ ] Verify coin name shows: "비트코인 Daily" (or current selection)
2. [ ] Verify current price shows with ₩ symbol and thousands separator
3. [ ] Verify price change shows:
   - Arrow (▲ for up, ▼ for down)
   - Change amount in won
   - Change percentage with + or -
   - Green color for positive, red for negative
4. [ ] Change timeframe to "1시간"
5. [ ] Verify coin name updates to: "비트코인 1hour"
6. [ ] Change coin to "이더리움" (ETH)
7. [ ] Verify coin name updates to: "이더리움 1hour"
8. [ ] Verify price values update for new coin

**Expected Result:**
- All fields update correctly
- Formatting is proper (₩, commas, decimals)
- Colors change based on price movement

#### 3b. Technical Analysis Panel (📊 기술적 분석)

**Test Steps:**
1. [ ] Verify RSI value shows (number between 0-100)
2. [ ] Verify RSI status shows one of:
   - "Overbought" (red) if RSI >= 70
   - "Oversold" (green) if RSI <= 30
   - "Neutral" (gray) if 30 < RSI < 70
3. [ ] Verify MA values show:
   - MA20: (price with ₩)
   - MA50: (price with ₩)
   - MA100: (price with ₩)
   - MA200: (price with ₩)
4. [ ] Change coin
5. [ ] Verify all MA values update
6. [ ] Open console (F12)
7. [ ] Look for log: `[Working] Price analysis updated`

**Expected Result:**
- RSI value and status display correctly
- All 4 MA values show
- Values update when changing coin/timeframe

#### 3c. Real-time Analysis Panel (📈 실시간 분석)

**Test Steps:**
1. [ ] Verify Trend (추세) shows one of:
   - "Uptrend" (green)
   - "Downtrend" (red)
   - "Sideways" (gray)
2. [ ] Verify Volatility (변동성) shows one of:
   - "High" (red)
   - "Medium" (yellow)
   - "Low" (green)
3. [ ] Verify Support level (지지) shows price with ₩
4. [ ] Verify Resistance level (저항) shows price with ₩
5. [ ] Verify Trading Signal (신호) shows one of:
   - "BUY"
   - "SELL"
   - "HOLD"
6. [ ] Verify timestamp at bottom updates
7. [ ] Wait 30 seconds and check if timestamp auto-updates

**Expected Result:**
- All analysis fields populate
- Values make sense (support < current price < resistance)
- Signal matches trend
- Colors apply correctly

#### 3d. Integration Testing

**Test Steps:**
1. [ ] Start with Bitcoin (BTC) on Daily timeframe
2. [ ] Note all analysis values
3. [ ] Change to XRP
4. [ ] Verify ALL panels update:
   - Price info changes to XRP data
   - Technical analysis recalculates
   - Real-time analysis updates
   - Timestamp refreshes
5. [ ] Change timeframe to 1시간
6. [ ] Verify all panels update again
7. [ ] Open console
8. [ ] Look for multiple `[Working] Price analysis updated` logs

**Expected Result:**
- Complete panel refresh on coin/timeframe change
- No stale data
- No console errors

---

## Console Testing

**Open Browser Console (F12) and look for these logs:**

### Initialization
```
[Working] Chart class initialized
[Working] Setting up event handlers...
[Working] Event handlers set up successfully
```

### Support/Resistance
```
[Working] Support/Resistance toggle button clicked
[Working] Support/Resistance enabled, drawing lines...
[Working] Calculated support/resistance levels: Array(6)
[Working] Drew support/resistance lines: 6
```

### Auto-Trading
```
[Working] Holdings auto-trading button clicked
[Working] Holdings auto-trading ENABLED
[Working] Active trading button clicked
[Working] Active trading ENABLED
[Working] Policy settings button clicked
[Working] Opening policy settings modal
```

### Price Analysis
```
[Working] Price analysis updated
[Working] Calculated support/resistance levels: Array(6)
```

---

## Error Checking

### Look for These ERRORS (should NOT appear):
- ❌ `Uncaught TypeError`
- ❌ `Uncaught ReferenceError`
- ❌ `Failed to load`
- ❌ `404 Not Found` (except for expected missing files)
- ❌ `Cannot read property of undefined`

### Acceptable Warnings:
- ⚠️ `[Working] Cannot draw support/resistance: no chart data` (before data loads)
- ⚠️ `[Working] API Handler not available` (during initialization)

---

## Performance Testing

### CPU Usage
1. [ ] Open Task Manager
2. [ ] Check Chrome/Edge CPU usage
3. [ ] Should be < 10% when idle
4. [ ] Should be < 30% when toggling features

### Memory Usage
1. [ ] Note initial memory usage
2. [ ] Toggle support/resistance 10 times
3. [ ] Check memory - should not grow significantly
4. [ ] No memory leaks expected

### Response Time
1. [ ] Click support/resistance toggle
2. [ ] Lines should appear instantly (< 100ms)
3. [ ] Change coin
4. [ ] Price analysis should update in < 500ms

---

## Browser Compatibility

Test in these browsers:
- [ ] Chrome (recommended)
- [ ] Edge
- [ ] Firefox
- [ ] Safari (if available)

---

## Known Issues (Expected)

### Not Implemented Yet:
1. **Drawing Tools** - Buttons exist but do nothing (Issue #2)
   - 추세선 (Trendline)
   - 피보나치 (Fibonacci)
   - 수평선 (Horizontal line)
   - 수직선 (Vertical line)
   - 모두 지우기 (Clear all)
   - 그리기 목록 (Drawings list)

2. **Auto-Trading Backend**
   - Toggles work but don't connect to backend
   - Shows alerts instead of actual trading

3. **Policy Modal**
   - Shows placeholder alert
   - Modal UI not created yet

---

## Troubleshooting

### Issue: Chart doesn't load
**Solution:**
- Press Ctrl+Shift+R to hard refresh
- Check both servers are running
- Check console for errors

### Issue: Support/Resistance doesn't show lines
**Solution:**
- Wait for chart data to load fully
- Check if you have enough data (needs 100+ candles)
- Try changing timeframe to Daily

### Issue: Price analysis shows old values
**Solution:**
- Change coin or timeframe to trigger update
- Check console for "[Working] Price analysis updated" log
- Refresh browser (Ctrl+Shift+R)

### Issue: Buttons don't respond
**Solution:**
- Check console for JavaScript errors
- Verify cache version is 20251017_0200
- Hard refresh browser (Ctrl+Shift+R)

---

## Success Criteria

All tests pass if:
- ✅ Support/Resistance toggle works (lines appear/disappear)
- ✅ All 3 auto-trading buttons work (alerts appear)
- ✅ All 3 price analysis panels update correctly
- ✅ No console errors (except expected warnings)
- ✅ Changing coin/timeframe updates everything
- ✅ Performance is smooth (no lag)

---

## Reporting Issues

If you find issues:
1. Note the exact steps to reproduce
2. Copy console error messages
3. Take screenshot if visual issue
4. Note browser and OS version
5. Check if issue persists after hard refresh

---

**Happy Testing!** 🎉

If all tests pass, the implementation is successful and ready for production use (except Drawing Tools which are still pending).
