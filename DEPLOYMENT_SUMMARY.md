# Upbit API Key System Deployment Summary

## Deployment Date: 2025-12-27

### Problem Solved
**Issue**: Auto-trading was always executing in simulation mode instead of real market orders because the system couldn't load user-specific API keys.

**Root Causes**:
1. `load_api_keys()` function didn't accept `user_id` parameter
2. SQLAlchemy mapper conflict between two `UserAPIKey` classes:
   - Old: CoinPulse API tokens (for external API access)
   - New: Upbit API credentials (for auto-trading)

### Solution Implemented

#### 1. Class Rename
- **Before**: `UserAPIKey` (conflicted with existing class)
- **After**: `UpbitAPIKey` (specific to Upbit credentials)

#### 2. Database Changes
- **Table**: `user_api_keys` → `upbit_api_keys`
- **Schema**: Encrypted storage for Upbit access_key + secret_key
- **Status**: Deployed to production PostgreSQL

#### 3. Files Modified
- `backend/models/user_api_key.py` - Renamed class to UpbitAPIKey
- `backend/routes/api_key_routes.py` - Updated all references
- `backend/common/config_loader.py` - Updated load_api_keys() function
- `scripts/create_user_api_keys_table.sql` - Updated table name

### System Status
✅ Service running: Active (PID 1630275)
✅ Database table: `upbit_api_keys` created successfully
✅ Mapper conflict: Resolved (0 errors in new process)
✅ API endpoint: `/api/api-keys/` accessible
✅ Frontend: `https://coinpulse.sinsi.ai/api_keys.html` accessible (200 OK)
✅ Encryption: Fernet key configured in production .env

### Next Steps for Users
1. Navigate to https://coinpulse.sinsi.ai/api_keys.html
2. Register Upbit API keys (Access Key + Secret Key)
3. System will verify keys with Upbit API
4. Future surge signals will execute real market orders (not simulation)

### Technical Details
- **Encryption**: Fernet symmetric encryption (cryptography library)
- **Fallback**: Global keys from .env if user has no registered keys
- **Security**: Encrypted storage, auto-disable after 5 consecutive errors
- **Verification**: Test API call to Upbit before saving keys

### Commits
- `2e6f44a`: [FEATURE] Add user-specific API key system for auto-trading
- `8f0d589`: [FIX] Rename UserAPIKey to UpbitAPIKey to avoid conflict
- `65b2b57`: [FIX] Fix unlimited weekly limit check for Enterprise plan
- `cc12f5c`: [SCRIPT] Add retry script for pending auto-trade alerts
- `689193d`: [FIX] Fix import in retry script
- `a59decc`: [FIX] Fix retry script - column name and transaction handling
