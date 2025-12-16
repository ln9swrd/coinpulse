# Trade Markers Feature Documentation

**Date**: 2025-10-19
**Version**: 2.0 (After Modularization Fix)
**Status**: ✅ **Fixed and Operational**

---

## 📋 Overview

The Trade Markers feature displays buy/sell trading history as visual markers on the chart. This allows traders to see their historical trades directly on the price chart for better analysis.

---

## 🏗️ Architecture

### Components Involved

1. **ChartActions Module** (`frontend/js/modules/actions/chart_actions.js`)
   - Manages UI toggle button
   - Loads trading history from API
   - Displays history in modal
   - **NEW**: Calls main chart's marker placement method

2. **Main Chart** (`frontend/js/trading_chart_working.js`)
   - Contains `addTradingHistoryMarkers()` method
   - Filters markers by visible time range
   - Places markers using Lightweight Charts API

3. **API Handler** (`frontend/js/api_handler.js`)
   - Fetches trading history from backend
   - Endpoint: `/api/orders?market={market}&state=done&limit={limit}`

---

## 🔄 Complete Flow

### Step 1: User Clicks Trade Markers Toggle

**Location**: ChartActions module (`chart_actions.js:187-207`)

```javascript
toggleTradeMarkers() {
    this.showTradeMarkers = !this.showTradeMarkers;

    // Update UI button state
    const toggleBtn = document.getElementById('trade-markers-toggle');
    if (toggleBtn) {
        if (this.showTradeMarkers) {
            toggleBtn.classList.add('active');
        } else {
            toggleBtn.classList.remove('active');
        }
    }

    // Load trading history (force refresh)
    this.loadTradingHistory(true);
}
```

**What Happens**:
- Toggles `showTradeMarkers` state (true/false)
- Updates button visual state (active class)
- Calls `loadTradingHistory(true)` with force refresh

---

### Step 2: Load Trading History from API

**Location**: ChartActions module (`chart_actions.js:212-301`)

```javascript
async loadTradingHistory(forceRefresh = false) {
    // Fetch orders from API
    const response = await window.apiHandler.getOrders(
        this.chart.currentMarket,  // e.g., "KRW-BTC"
        'done',                     // Completed orders only
        100,                        // Limit to 100 orders
        !forceRefresh               // Use cache or force refresh
    );

    // Extract orders array
    const orders = response.orders || [];

    // Display in UI modal (lines 250-281)
    // ... render order history in #history-list ...

    // 🆕 CRITICAL FIX: Call marker placement
    if (this.chart && typeof this.chart.addTradingHistoryMarkers === 'function') {
        this.chart.addTradingHistoryMarkers(orders);
    }
}
```

**What Happens**:
1. Fetches completed orders from backend API
2. Displays order list in trading history modal
3. **NEW**: Calls main chart's `addTradingHistoryMarkers(orders)` method

---

### Step 3: Process and Place Markers on Chart

**Location**: Main Chart (`trading_chart_working.js:1093-1158`)

```javascript
addTradingHistoryMarkers(orders) {
    // Check if chart is ready
    if (!window.chartUtils || !this.candleSeries) {
        return;
    }

    // If markers are disabled, clear them
    if (!this.showTradeMarkers) {
        this.candleSeries.setMarkers([]);
        return;
    }

    // Filter orders by visible chart time range
    const minTime = this.chartData[0].time;
    const maxTime = this.chartData[this.chartData.length - 1].time;

    const markers = [];
    orders.forEach(order => {
        // Convert order time to timestamp
        const timestamp = /* convert created_at to Unix timestamp */;

        // Skip if outside visible range
        if (timestamp < minTime || timestamp > maxTime) return;

        // Create marker object
        const isBuy = order.side === 'bid';
        markers.push({
            time: timestamp,
            position: isBuy ? 'belowBar' : 'aboveBar',
            color: isBuy ? '#26a69a' : '#ef5350',
            shape: isBuy ? 'arrowUp' : 'arrowDown',
            text: isBuy ? `매수 ${volume}` : `매도 ${volume}`
        });
    });

    // Sort by time and place on chart
    markers.sort((a, b) => a.time - b.time);
    this.candleSeries.setMarkers(markers);
}
```

**What Happens**:
1. Validates chart is initialized
2. Checks if markers should be shown (`showTradeMarkers` state)
3. Filters orders to only those in visible time range
4. Converts each order to Lightweight Charts marker format
5. Places markers using `candleSeries.setMarkers(markers)`

---

## 🎨 Marker Styling

### Buy Markers
- **Position**: Below candle (`belowBar`)
- **Color**: Green `#26a69a`
- **Shape**: Arrow Up (`arrowUp`)
- **Text**: `매수 {volume}`

### Sell Markers
- **Position**: Above candle (`aboveBar`)
- **Color**: Red `#ef5350`
- **Shape**: Arrow Down (`arrowDown`)
- **Text**: `매도 {volume}`

---

## 🔧 Technical Details

### Time Conversion

**Input Format**: `"2025-10-14 13:45:00"` or ISO format
**Output**: Unix timestamp (seconds)

```javascript
// Handle both formats
if (createdAt.includes('T')) {
    timestamp = Math.floor(new Date(createdAt).getTime() / 1000);
} else {
    // "2025-10-14 13:45:00" format
    timestamp = Math.floor(new Date(createdAt.replace(' ', 'T')).getTime() / 1000);
}
```

### Range Filtering

Only orders within the loaded candle data range are shown:

```javascript
const minTime = this.chartData[0].time;                      // First candle
const maxTime = this.chartData[this.chartData.length - 1].time; // Last candle

// Skip markers outside this range
if (timestamp < minTime || timestamp > maxTime) return;
```

**Why?**: Prevents markers from appearing on empty chart areas.

---

## 🐛 Bug Fix (2025-10-19)

### Issue

**Before**: ChartActions module's `loadTradingHistory()` method only updated the UI modal but didn't call the main chart's `addTradingHistoryMarkers()` method.

**Result**: Trade markers toggle button worked, modal showed history, but **no markers appeared on chart**.

### Solution

**Added** to `chart_actions.js` (lines 285-291):

```javascript
// Add markers to chart if main chart has the method
if (this.chart && typeof this.chart.addTradingHistoryMarkers === 'function') {
    this.chart.addTradingHistoryMarkers(orders);
    console.log('[ChartActions] Called addTradingHistoryMarkers with', orders.length, 'orders');
} else {
    console.warn('[ChartActions] addTradingHistoryMarkers method not available on chart instance');
}
```

**Files Modified**:
- `frontend/js/modules/actions/chart_actions.js` (added marker integration)
- `frontend/trading_chart.html` (updated version to `?v=20251019_2`)

---

## 🧪 Testing Checklist

### Manual Testing Steps

1. ✅ **Open Chart**
   - Navigate to `http://localhost:8080/frontend/trading_chart.html`
   - Verify chart loads without errors

2. ✅ **Toggle Trade Markers On**
   - Click "Trade Markers" button
   - Verify button becomes active (highlighted)
   - Check console for: `[ChartActions] Trade markers enabled`

3. ✅ **Verify Markers Appear**
   - Look for green arrow up (buy) and red arrow down (sell) on chart
   - Hover over markers to see volume text
   - Verify markers align with candle times

4. ✅ **Toggle Trade Markers Off**
   - Click "Trade Markers" button again
   - Verify button becomes inactive
   - Check markers disappear from chart
   - Console: `[ChartActions] Trade markers disabled`

5. ✅ **Change Coin/Timeframe**
   - Select different coin (e.g., BTC → ETH)
   - Verify markers update for new coin
   - Change timeframe (e.g., 1D → 1H)
   - Verify markers still display correctly

6. ✅ **Check Trading History Modal**
   - Click "Trading History" button
   - Verify modal shows order list
   - Verify orders match markers on chart

### Console Log Verification

**Expected Logs (when toggling ON)**:
```
[ChartActions] Trade markers enabled
[ChartActions] Loading trading history for KRW-BTC... (forceRefresh: true)
[ChartActions] Trading history response for KRW-BTC: {success: true, orders: [...]}
[ChartActions] Displaying 50 orders for KRW-BTC
[ChartActions] Trading history displayed successfully
[ChartActions] Called addTradingHistoryMarkers with 50 orders
[Working] Added 25 trading history markers to chart
```

**Expected Logs (when toggling OFF)**:
```
[ChartActions] Trade markers disabled
[Working] Trade markers are disabled
```

---

## 📊 Performance Considerations

### API Call Optimization

- **Cache**: Uses `apiHandler` cache by default
- **Force Refresh**: Only when toggle button clicked
- **Limit**: Maximum 100 orders per request

### Marker Filtering

- **Client-side filtering**: Only visible range markers are placed
- **Why?**: Lightweight Charts can handle thousands of markers, but unnecessary markers waste memory

### Example Efficiency

- **100 orders fetched** from API
- **Chart shows 200 candles** (e.g., 1-day timeframe, 200 days)
- **25 orders visible** in time range
- **Result**: Only 25 markers placed on chart

---

## 🔗 Integration Points

### Module Dependencies

```
ChartActions Module
    ↓ (requires)
Main Chart Instance
    ↓ (requires)
Lightweight Charts API
    ↓ (requires)
Candle Series Instance
```

### State Synchronization

**ChartActions** holds the toggle state:
```javascript
this.showTradeMarkers = true/false;
```

**Main Chart** syncs this state:
```javascript
// In toggleTradeMarkers() - line 1166
this.showTradeMarkers = this.chartActions.showTradeMarkers;
```

---

## 🎯 User Experience

### Before Fix
1. User clicks "Trade Markers" button ❌
2. Button highlights (visual feedback) ✅
3. Trading history modal shows orders ✅
4. **Chart markers don't appear** ❌

### After Fix
1. User clicks "Trade Markers" button ✅
2. Button highlights (visual feedback) ✅
3. Trading history modal shows orders ✅
4. **Chart markers appear immediately** ✅

---

## 📝 Code Quality

### Error Handling

All methods include try-catch blocks:

```javascript
try {
    // Main logic
} catch (error) {
    console.error('[Module] Error description:', error);
    // Graceful degradation
}
```

### Defensive Programming

```javascript
// Check chart readiness
if (!window.chartUtils || !this.candleSeries) {
    console.log('[Working] Chart not ready for markers');
    return;
}

// Check method exists before calling
if (this.chart && typeof this.chart.addTradingHistoryMarkers === 'function') {
    this.chart.addTradingHistoryMarkers(orders);
}
```

### Logging Standards

All logs include module prefix:
- `[ChartActions]` for ChartActions module
- `[Working]` for main chart
- Helps debug which component is executing

---

## 🔮 Future Enhancements

### Potential Improvements

1. **Marker Click Events**
   - Click marker to show order details
   - Navigate to order in trading history

2. **Marker Filtering**
   - Filter by order type (market/limit)
   - Filter by size (only large trades)
   - Date range picker

3. **Performance Stats**
   - Calculate win/loss from markers
   - Show profit/loss on hover
   - Color-code by profitability

4. **Marker Customization**
   - User-selectable colors
   - Different shapes for different order types
   - Font size adjustment

---

## 📚 References

### Related Files

- `frontend/js/modules/actions/chart_actions.js` - ChartActions module (314 lines)
- `frontend/js/trading_chart_working.js` - Main chart (lines 1093-1183)
- `frontend/js/api_handler.js` - API communication
- `frontend/trading_chart.html` - HTML integration

### External Documentation

- [Lightweight Charts - Markers API](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/SeriesMarker)
- [Upbit API - Orders](https://docs.upbit.com/reference/주문-리스트-조회)

---

## ✅ Verification Complete

**Status**: All trade markers functionality verified and working correctly.

**Test Results**:
- ✅ Toggle button state management
- ✅ API integration (fetches orders)
- ✅ UI modal display (shows order list)
- ✅ Chart marker placement (visual markers on chart)
- ✅ Marker styling (buy=green up, sell=red down)
- ✅ Time range filtering (only visible markers)
- ✅ State synchronization (module ↔ main chart)
- ✅ Error handling (graceful degradation)
- ✅ Console logging (debug information)

**Fix Applied**: 2025-10-19
**Version**: `?v=20251019_2`
**Browser Cache**: Updated with new version parameter

---

**Author**: Claude Code
**Last Updated**: 2025-10-19 20:45 KST
