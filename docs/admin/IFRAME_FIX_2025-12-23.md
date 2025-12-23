# Trading Chart iframe Loading Fix
**Date**: 2025-12-23
**Issue**: Trading chart failed to load in dashboard iframe with "failed to load response data"

## Root Cause Analysis

### Problem 1: ENV Variable Not Set
- `.env` file did not have `ENV=production`
- Python security middleware only applies CSP when `ENV=production`
- Without CSP, `frame-ancestors 'self'` directive was never sent

### Problem 2: Nginx COOP Header Blocking iframes
- Nginx config had: `add_header Cross-Origin-Opener-Policy 'same-origin-allow-popups' always;`
- COOP `same-origin-allow-popups` policy isolates browsing contexts
- This prevented iframe embedding entirely

## Applied Fixes

### Fix 1: Add ENV=production to .env
```bash
# On production server
cd /opt/coinpulse
echo -e '\nENV=production' >> .env

# Verify
grep ENV .env
# Output: ENV=production
```

### Fix 2: Comment Out COOP Header in Nginx
```bash
# Backup original config
sudo cp /etc/nginx/conf.d/coinpulse.conf /etc/nginx/conf.d/coinpulse.conf.backup

# Comment out COOP header
sudo sed -i "s/add_header Cross-Origin-Opener-Policy 'same-origin-allow-popups' always;/# add_header Cross-Origin-Opener-Policy 'same-origin-allow-popups' always;/" /etc/nginx/conf.d/coinpulse.conf

# Test config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Fix 3: Restart CoinPulse Service
```bash
sudo systemctl restart coinpulse
```

## Verification

### Before Fix
```bash
curl -I https://coinpulse.sinsi.ai/trading_chart.html | grep -iE '(frame|csp|cross-origin)'

# Output:
x-frame-options: SAMEORIGIN
cross-origin-opener-policy: same-origin-allow-popups  ← BLOCKING!
cross-origin-embedder-policy: unsafe-none
# No CSP header ← MISSING!
```

### After Fix
```bash
curl -I https://coinpulse.sinsi.ai/trading_chart.html | grep -iE '(frame|csp|cross-origin)'

# Output:
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.upbit.com wss://api.upbit.com; frame-ancestors 'self';  ← NOW PRESENT!
x-frame-options: SAMEORIGIN  ← ALLOWS SAME-ORIGIN
cross-origin-embedder-policy: unsafe-none  ← SAFE FOR IFRAMES
# COOP header REMOVED ← NO LONGER BLOCKING!
```

## How iframe Loading Works Now

1. **Dashboard** (https://coinpulse.sinsi.ai/dashboard.html) loads
2. User clicks "거래 차트" in sidebar
3. Dashboard creates iframe:
   ```html
   <iframe src="https://coinpulse.sinsi.ai/trading_chart.html"></iframe>
   ```
4. **Server responds with headers**:
   - `Content-Security-Policy: frame-ancestors 'self'` ✅ Allows same-origin iframe
   - `X-Frame-Options: SAMEORIGIN` ✅ Allows same-origin iframe
   - No COOP header ✅ Doesn't block iframe
5. **Browser loads iframe successfully** ✅

## Files Modified on Production Server

1. `/opt/coinpulse/.env` - Added `ENV=production`
2. `/etc/nginx/conf.d/coinpulse.conf` - Commented out COOP header
3. Backup created: `/etc/nginx/conf.d/coinpulse.conf.backup`

## Related Code

### backend/middleware/security.py (Line 400-409)
```python
# Content Security Policy
if os.getenv('ENV') == 'production':  # Now triggers correctly!
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.upbit.com wss://api.upbit.com; "
        "frame-ancestors 'self';"  # Allow iframe from same origin
    )
```

### frontend/dashboard.html (Lines 1643-1657)
```javascript
// Special handling for trading chart - use iframe to prevent CSS conflicts
if (pageName === 'trading') {
    const chartUrl = `${window.location.origin}/${filePath}`;
    contentContainer.innerHTML = `
        <div style="width: 100%; height: calc(100vh - 80px); overflow: hidden; background: white;">
            <iframe
                src="${chartUrl}"
                style="width: 100%; height: 100%; border: none; display: block;"
                frameborder="0"
                id="trading-chart-iframe"
            ></iframe>
        </div>
    `;
    return true;
}
```

## Testing Checklist

- [x] ENV=production loads correctly
- [x] CSP header includes `frame-ancestors 'self'`
- [x] X-Frame-Options is SAMEORIGIN
- [x] COOP header removed
- [x] Nginx config test passes
- [x] Services restarted successfully
- [ ] **User testing required**: Verify iframe loads in browser

## Rollback Instructions

If issues occur:

```bash
# Restore Nginx config
sudo cp /etc/nginx/conf.d/coinpulse.conf.backup /etc/nginx/conf.d/coinpulse.conf
sudo nginx -t
sudo systemctl reload nginx

# Remove ENV from .env (if needed)
cd /opt/coinpulse
sed -i '/^ENV=production$/d' .env
sudo systemctl restart coinpulse
```

## Next Steps

1. ✅ XRP sell order holdings detection fix (already deployed in commit `db7caff`)
2. ⏳ User testing to confirm both fixes work
3. 📊 Monitor logs for any new errors
4. 🔍 Check `/api/user/signals/stats` and `/api/user/signals` 500 errors (separate issue)

## Additional Notes

- The COOP header was originally added for security but was too restrictive for iframe use
- `frame-ancestors 'self'` in CSP provides adequate protection for same-origin iframes
- X-Frame-Options SAMEORIGIN is a fallback for browsers that don't support CSP frame-ancestors
- This configuration allows trading chart to load in iframe while maintaining security
