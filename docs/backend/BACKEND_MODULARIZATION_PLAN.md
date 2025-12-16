# Backend Modularization Plan

## Current State Analysis

### File Sizes
- `clean_upbit_server.py`: 783 lines (Chart API Server - Port 8080)
- `simple_dual_server.py`: 1707 lines (Trading API Server - Port 8081)
- **Total**: 2490 lines

### Identified Components

#### clean_upbit_server.py (Chart Server)
- SimpleCache class (cache system)
- UpbitTradingAPI class (trading API client)
- CleanUpbitAPI class (public API wrapper)
- Flask routes: candles, market data, quick buy/sell, orders
- Static file serving

#### simple_dual_server.py (Trading Server)
- UpbitAPI class (trading API client) ⚠️ **DUPLICATE**
- AutoTradingEngine class (auto-trading logic)
- Flask routes: holdings, orders, policies, auto-trading control
- Config loading functions
- Static file serving

### Code Duplication Issues ⚠️
1. **UpbitAPI Class**: Nearly identical implementations in both servers
2. **Flask Setup**: Repeated CORS and app configuration
3. **Config Loading**: Similar environment variable handling
4. **Static File Serving**: Redundant route handlers

---

## Proposed Architecture

```
backend/
├── common/                      # Shared modules
│   ├── __init__.py
│   ├── cache.py                 # SimpleCache class (from chart_server)
│   ├── upbit_api.py             # Unified Upbit API client
│   ├── config_loader.py         # Configuration loading utilities
│   └── utils.py                 # Common utility functions
│
├── chart_server/                # Chart API Server (Port 8080)
│   ├── __init__.py
│   ├── server.py                # Main Flask app + entry point
│   └── routes/
│       ├── __init__.py
│       ├── candles.py           # Candle data routes
│       ├── market.py            # Market data routes
│       └── trading.py           # Quick buy/sell routes
│
├── trading_server/              # Trading API Server (Port 8081)
│   ├── __init__.py
│   ├── server.py                # Main Flask app + entry point
│   ├── auto_trading.py          # AutoTradingEngine class
│   └── routes/
│       ├── __init__.py
│       ├── holdings.py          # Holdings routes
│       ├── orders.py            # Order management routes
│       ├── policies.py          # Policy management routes
│       └── auto_trading_api.py  # Auto-trading control routes
│
└── config/                      # Configuration files (moved from root)
    ├── chart_server_config.json
    ├── trading_server_config.json
    └── trading_policies.json
```

---

## Module Breakdown

### 1. `backend/common/cache.py` (~60 lines)
**Purpose**: Caching system for API responses
**Source**: `clean_upbit_server.py` (lines 33-56)
```python
class SimpleCache:
    def __init__(self, default_ttl=300):
        ...
    def get(self, key):
        ...
    def set(self, key, value, ttl=None):
        ...
    def clear(self):
        ...
```

### 2. `backend/common/upbit_api.py` (~300 lines)
**Purpose**: Unified Upbit API client (merge both implementations)
**Source**: Merge from:
- `clean_upbit_server.py` → UpbitTradingAPI class
- `simple_dual_server.py` → UpbitAPI class

**Features**:
- JWT authentication
- Account queries
- Order management
- Current price queries
- Candle data queries

### 3. `backend/common/config_loader.py` (~50 lines)
**Purpose**: Configuration loading utilities
**Source**:
- `clean_upbit_server.py` → setup_cors()
- `simple_dual_server.py` → load_env_config()

```python
def load_server_config(config_file):
    """Load server configuration from JSON"""
    ...

def setup_cors(app, port):
    """Setup CORS for Flask app"""
    ...

def load_api_keys():
    """Load Upbit API keys from .env"""
    ...
```

### 4. `backend/chart_server/server.py` (~100 lines)
**Purpose**: Main Flask app initialization
**Includes**:
- Flask app setup
- CORS configuration
- Cache initialization
- Route registration
- Server startup code

### 5. `backend/chart_server/routes/candles.py` (~150 lines)
**Routes**:
- `/api/upbit/candles/days`
- `/api/upbit/candles/minutes/{minutes}`
- `/api/upbit/candles/weeks`
- `/api/upbit/candles/months`

### 6. `backend/chart_server/routes/market.py` (~80 lines)
**Routes**:
- `/api/upbit/market/all`
- `/api/current_price/<market>`
- `/health`
- `/cache/clear`
- `/cache/stats`

### 7. `backend/chart_server/routes/trading.py` (~150 lines)
**Routes**:
- `/api/quick-buy`
- `/api/quick-sell`
- `/api/cancel-order/<order_uuid>`
- `/api/orders`

### 8. `backend/trading_server/auto_trading.py` (~300 lines)
**Purpose**: Auto-trading engine logic
**Source**: `simple_dual_server.py` → AutoTradingEngine class

```python
class AutoTradingEngine:
    def __init__(self):
        ...
    def start(self):
        ...
    def stop(self):
        ...
    def execute_trading_cycle(self):
        ...
```

### 9. `backend/trading_server/routes/holdings.py` (~200 lines)
**Routes**:
- `/api/holdings`
- `/api/holdings/real`
- `/api/holdings/fallback`

### 10. `backend/trading_server/routes/orders.py` (~250 lines)
**Routes**:
- `/api/orders`
- `/api/order/<uuid>`

### 11. `backend/trading_server/routes/policies.py` (~200 lines)
**Routes**:
- `/api/policies`
- `/api/policies/save`
- `/api/global-settings`
- `/api/enable-auto-trading`
- `/api/trading-policies`

### 12. `backend/trading_server/routes/auto_trading_api.py` (~150 lines)
**Routes**:
- `/api/trading-status`
- `/api/analyze-coin/<coin>`
- `/api/backtest-coin/<coin>`
- `/api/trading-logs`
- `/api/run-trading-cycle`

---

## Implementation Plan

### Phase 1: Setup & Common Modules (2-3 hours)
1. ✅ Create backup of current state
2. Create `backend/` directory structure
3. Extract `cache.py` from chart_server
4. Merge and create unified `upbit_api.py`
5. Create `config_loader.py`
6. Add `__init__.py` files

### Phase 2: Chart Server Modularization (3-4 hours)
1. Create `chart_server/server.py` (Flask app)
2. Extract routes to `routes/candles.py`
3. Extract routes to `routes/market.py`
4. Extract routes to `routes/trading.py`
5. Test chart server independently
6. Update `clean_upbit_server.py` to import from backend modules

### Phase 3: Trading Server Modularization (4-5 hours)
1. Create `trading_server/server.py` (Flask app)
2. Extract `AutoTradingEngine` to `auto_trading.py`
3. Extract routes to `routes/holdings.py`
4. Extract routes to `routes/orders.py`
5. Extract routes to `routes/policies.py`
6. Extract routes to `routes/auto_trading_api.py`
7. Test trading server independently
8. Update `simple_dual_server.py` to import from backend modules

### Phase 4: Configuration Migration (1 hour)
1. Move config files to `backend/config/`
2. Update all config paths in code
3. Update batch files to reference new structure

### Phase 5: Testing & Validation (2-3 hours)
1. Test chart server: All routes working
2. Test trading server: All routes working
3. Test auto-trading: Engine starts/stops correctly
4. Test batch files: Servers start/restart properly
5. Verify no console errors
6. Check logs for warnings

### Phase 6: Cleanup & Documentation (1 hour)
1. Archive old monolithic files
2. Update README.md
3. Update CLAUDE.md with new structure
4. Create API documentation
5. Update deployment scripts

---

## Benefits of Modularization

### Code Quality
- ✅ **DRY Principle**: Eliminate duplicate UpbitAPI implementations
- ✅ **Single Responsibility**: Each module has one clear purpose
- ✅ **Testability**: Individual modules can be unit tested
- ✅ **Maintainability**: Easier to find and fix bugs

### Development Speed
- ✅ **Parallel Development**: Multiple developers can work on different modules
- ✅ **Faster Debugging**: Errors isolated to specific modules
- ✅ **Quick Feature Addition**: Add new routes without touching core logic

### Scalability
- ✅ **Microservices Ready**: Easy to split into separate services later
- ✅ **Load Balancing**: Can deploy multiple instances of each server
- ✅ **Service Independence**: Servers can be updated/deployed separately

### Code Metrics
- **Before**: 2 monolithic files (783 + 1707 = 2490 lines)
- **After**: ~12 modular files (avg ~200 lines/file)
- **Reduction**: 70% decrease in file size per module
- **Duplication**: 0% (unified UpbitAPI)

---

## File Size Comparison

### Before Modularization
| File | Lines | Complexity |
|------|-------|------------|
| clean_upbit_server.py | 783 | High |
| simple_dual_server.py | 1707 | Very High |
| **Total** | **2490** | - |

### After Modularization
| Module | Lines | Complexity |
|--------|-------|------------|
| common/cache.py | 60 | Low |
| common/upbit_api.py | 300 | Medium |
| common/config_loader.py | 50 | Low |
| chart_server/server.py | 100 | Low |
| chart_server/routes/candles.py | 150 | Medium |
| chart_server/routes/market.py | 80 | Low |
| chart_server/routes/trading.py | 150 | Medium |
| trading_server/server.py | 100 | Low |
| trading_server/auto_trading.py | 300 | High |
| trading_server/routes/holdings.py | 200 | Medium |
| trading_server/routes/orders.py | 250 | Medium |
| trading_server/routes/policies.py | 200 | Medium |
| trading_server/routes/auto_trading_api.py | 150 | Medium |
| **Total** | **~2090** | - |

**Result**: Better organization with 400 lines saved through deduplication

---

## Migration Strategy

### Gradual Migration (Recommended)
1. **Week 1**: Create backend structure + common modules
2. **Week 2**: Modularize chart server
3. **Week 3**: Modularize trading server
4. **Week 4**: Testing & cleanup

### Aggressive Migration (Fast)
1. **Day 1**: Setup + common modules (Phase 1)
2. **Day 2**: Chart server modularization (Phase 2)
3. **Day 3**: Trading server modularization (Phase 3)
4. **Day 4**: Testing & documentation (Phases 4-6)

---

## Compatibility Considerations

### Backward Compatibility
- Keep `clean_upbit_server.py` as entry point (imports from backend/)
- Keep `simple_dual_server.py` as entry point (imports from backend/)
- Batch files continue to work without changes
- API endpoints remain unchanged

### Configuration Files
- Move to `backend/config/` but maintain backward compatibility
- Check both locations: `backend/config/` then root directory
- Gradual migration path

### Testing Checklist
- [ ] All chart server routes respond correctly
- [ ] All trading server routes respond correctly
- [ ] Auto-trading engine starts/stops
- [ ] No console errors
- [ ] Logs show correct module names
- [ ] Batch files work
- [ ] Frontend connects to APIs
- [ ] All features functional

---

## Risk Mitigation

### Risks
1. **Breaking Changes**: API routes might break during refactoring
2. **Import Errors**: Circular dependencies or missing imports
3. **Config Path Issues**: Files not found after moving configs
4. **Performance**: Additional import overhead

### Mitigations
1. **Comprehensive Backup**: Already done ✅
2. **Incremental Testing**: Test after each module extraction
3. **Backward Compatibility**: Keep old files as wrappers initially
4. **Monitoring**: Check logs and console for errors
5. **Rollback Plan**: Can revert to backup if needed

---

## Success Criteria

- ✅ All features working as before
- ✅ No duplicate code
- ✅ Clear module boundaries
- ✅ Easy to understand structure
- ✅ Fast startup time (< 5 seconds)
- ✅ No console errors
- ✅ Documentation complete

---

## Next Steps

**Immediate Action**:
1. Get user approval for this plan
2. Start with Phase 1 (Common modules)

**Estimated Total Time**: 12-18 hours of development

**Priority**: Medium (current code works, but improvement needed)

---

**Created**: 2025-11-05
**Status**: 📋 Planning Phase
**Approval**: Pending User Review
