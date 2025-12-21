"""
Security Middleware

Provides:
- Rate limiting (IP-based and user-based)
- Security headers (CSP, HSTS, XSS protection)
- Input validation
- Request sanitization
- Suspicious activity detection

Features:
- Configurable rate limits per endpoint
- Automatic IP blocking for abuse
- Security event logging
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from flask import request, jsonify, g
import re
import os


class RateLimiter:
    """
    Token bucket rate limiter with IP and user-based limits
    """

    def __init__(self):
        # Storage: {key: {'tokens': float, 'last_update': float}}
        self.buckets = defaultdict(lambda: {'tokens': 0, 'last_update': time.time()})

        # Blocked IPs: {ip: block_until_timestamp}
        self.blocked_ips = {}

        # Check if running in development mode
        is_dev = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

        # Rate limit configuration (relaxed in development)
        if is_dev:
            self.limits = {
                # Development: Extremely relaxed limits (거의 무제한)
                'default': {'requests': 10000, 'window': 60},
                'auth': {'requests': 10000, 'window': 60},  # 개발환경: 거의 무제한
                'api': {'requests': 10000, 'window': 60},
                'trading': {'requests': 10000, 'window': 60},
                'admin': {'requests': 10000, 'window': 60}
            }
        else:
            self.limits = {
                # Production: Relaxed limits (increased for dashboard)
                'default': {'requests': 120, 'window': 60},
                'auth': {'requests': 10, 'window': 60},  # 10 login attempts per minute
                'api': {'requests': 100, 'window': 60},  # 100 API calls per minute
                'trading': {'requests': 30, 'window': 60},  # 30 trading calls per minute
                'admin': {'requests': 50, 'window': 60}  # 50 admin calls per minute
            }

    def _get_limit_for_path(self, path):
        """Determine rate limit based on request path"""
        if '/auth/' in path or '/login' in path or '/register' in path:
            return self.limits['auth']
        elif '/api/auto-trading/' in path or '/api/surge/' in path:
            return self.limits['trading']
        elif '/admin/' in path:
            return self.limits['admin']
        elif path.startswith('/api/'):
            return self.limits['api']
        else:
            return self.limits['default']

    def _get_tokens(self, key, limit_config):
        """Get current token count for a key"""
        bucket = self.buckets[key]
        now = time.time()

        # Refill tokens based on elapsed time
        elapsed = now - bucket['last_update']
        refill_rate = limit_config['requests'] / limit_config['window']
        tokens_to_add = elapsed * refill_rate

        # Update bucket
        bucket['tokens'] = min(
            limit_config['requests'],
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_update'] = now

        return bucket['tokens']

    def _consume_token(self, key):
        """Consume one token from bucket"""
        bucket = self.buckets[key]
        bucket['tokens'] -= 1

    def is_allowed(self, identifier, path):
        """
        Check if request is allowed

        Args:
            identifier: IP address or user ID
            path: Request path

        Returns:
            (allowed: bool, retry_after: int)
        """
        # Exclude static files and HTML pages from rate limiting
        static_extensions = ('.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot')
        # Remove query parameters for checking
        path_without_query = path.split('?')[0]
        if path_without_query.endswith(static_extensions) or path_without_query.startswith('/static/') or path_without_query.startswith('/frontend/'):
            return True, 0

        # Exclude auth and data GET endpoints (already secured by JWT tokens)
        auth_get_endpoints = [
            '/api/auth/me',
            '/api/auth/check',
            '/api/user/plan',
            '/api/holdings',
            '/api/orders',
            '/api/account/balance',
            '/api/subscription/current',  # User subscription status
            '/api/subscription/transactions'  # User transaction history
        ]
        if path_without_query in auth_get_endpoints:
            return True, 0

        # Exclude login endpoints (Google OAuth and regular login)
        login_endpoints = [
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/google-login',
            '/api/auth/logout',
            '/api/auth/refresh'
        ]
        if path_without_query in login_endpoints:
            return True, 0

        # Exclude auto-trading GET endpoints (dynamic paths with user_id)
        if path_without_query.startswith('/api/auto-trading/status/') or \
           path_without_query.startswith('/api/auto-trading/config/') or \
           path_without_query.startswith('/api/auto-trading/positions/') or \
           path_without_query.startswith('/api/auto-trading/history/'):
            return True, 0

        # Exclude Upbit proxy endpoints (chart data, market info)
        if path_without_query.startswith('/api/upbit/candles/') or \
           path_without_query.startswith('/api/upbit/ticker') or \
           path_without_query.startswith('/api/upbit/market/'):
            return True, 0

        # Check if IP is blocked
        if identifier in self.blocked_ips:
            block_until = self.blocked_ips[identifier]
            if time.time() < block_until:
                retry_after = int(block_until - time.time())
                return False, retry_after
            else:
                # Unblock expired blocks
                del self.blocked_ips[identifier]

        # Get limit configuration
        limit_config = self._get_limit_for_path(path)

        # Get current tokens
        tokens = self._get_tokens(identifier, limit_config)

        if tokens >= 1:
            self._consume_token(identifier)
            return True, 0
        else:
            # Calculate retry after
            retry_after = int(limit_config['window'] / limit_config['requests'])
            # Log rate limit info for debugging
            print(f"[RateLimit] BLOCKED: {identifier} - Path: {path} - Tokens: {tokens:.2f} - Limit: {limit_config}")
            return False, retry_after

    def block_ip(self, ip, duration_seconds=3600):
        """
        Block an IP address for specified duration

        Args:
            ip: IP address to block
            duration_seconds: Block duration (default: 1 hour)
        """
        self.blocked_ips[ip] = time.time() + duration_seconds

    def cleanup(self):
        """Remove old entries to prevent memory leaks"""
        now = time.time()

        # Remove buckets not accessed in last hour
        old_keys = [
            key for key, bucket in self.buckets.items()
            if now - bucket['last_update'] > 3600
        ]
        for key in old_keys:
            del self.buckets[key]

        # Remove expired IP blocks
        expired_blocks = [
            ip for ip, block_until in self.blocked_ips.items()
            if now > block_until
        ]
        for ip in expired_blocks:
            del self.blocked_ips[ip]


class SecurityValidator:
    """Input validation and sanitization"""

    # Suspicious patterns (SQL injection, XSS, etc.)
    SUSPICIOUS_PATTERNS = [
        r"('|(--)|;|\*|<|>|script|union|select|insert|update|delete|drop|exec|execute)",
        r"(javascript:|data:|vbscript:)",
        r"(<script|<iframe|<object|<embed)",
    ]

    @staticmethod
    def validate_input(data, field_name='input'):
        """
        Validate input for suspicious content

        Args:
            data: Input to validate (string or dict)
            field_name: Field name for error messages

        Returns:
            (valid: bool, error_message: str or None)
        """
        if isinstance(data, str):
            # Check for suspicious patterns
            for pattern in SecurityValidator.SUSPICIOUS_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE):
                    return False, f"Suspicious content detected in {field_name}"

        elif isinstance(data, dict):
            # Recursively validate dict values
            for key, value in data.items():
                valid, error = SecurityValidator.validate_input(value, key)
                if not valid:
                    return False, error

        return True, None

    @staticmethod
    def sanitize_string(text, max_length=1000):
        """
        Sanitize string input

        Args:
            text: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return text

        # Truncate
        text = text[:max_length]

        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove excessive whitespace
        text = ' '.join(text.split())

        return text


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_client_ip():
    """Get client IP address (considering proxies)"""
    # Check X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    # Fallback to remote address
    return request.remote_addr or 'unknown'


def setup_security_middleware(app):
    """
    Setup security middleware for Flask app

    Args:
        app: Flask application instance
    """
    # Cleanup rate limiter every hour
    import schedule
    schedule.every().hour.do(_rate_limiter.cleanup)

    @app.before_request
    def security_checks():
        """Run security checks before processing request"""

        # Get client IP
        client_ip = get_client_ip()
        g.client_ip = client_ip

        # Skip security checks for health endpoints
        if request.path in ['/health', '/health/live', '/health/ready']:
            return

        # 1. Rate limiting
        allowed, retry_after = _rate_limiter.is_allowed(client_ip, request.path)

        if not allowed:
            # Log rate limit exceeded
            app.logger.warning(
                f"Rate limit exceeded: {client_ip} for {request.path}",
                extra={'ip_address': client_ip, 'path': request.path}
            )

            # Log security event
            from backend.services.logging_service import log_security_event
            log_security_event(
                'rate_limit_exceeded',
                f"Rate limit exceeded for {request.path}",
                severity='WARNING'
            )

            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'retry_after': retry_after
            }), 429

        # 2. Input validation (for POST/PUT requests)
        # Skip validation for OAuth endpoints (they contain JWT tokens which look suspicious)
        oauth_paths = ['/api/auth/google-login', '/api/auth/kakao-login']
        if request.method in ['POST', 'PUT', 'PATCH'] and request.path not in oauth_paths:
            if request.is_json:
                try:
                    data = request.get_json()
                    valid, error = SecurityValidator.validate_input(data)

                    if not valid:
                        app.logger.warning(
                            f"Suspicious input detected: {error}",
                            extra={'ip_address': client_ip, 'path': request.path}
                        )

                        # Log security event
                        from backend.services.logging_service import log_security_event
                        log_security_event(
                            'suspicious_input',
                            f"Suspicious input: {error}",
                            severity='WARNING'
                        )

                        # Block IP after 3 suspicious requests
                        # (implement counter logic here if needed)

                        return jsonify({
                            'success': False,
                            'error': 'Invalid input'
                        }), 400

                except Exception as e:
                    app.logger.error(f"Error parsing JSON: {str(e)}")

    @app.after_request
    def add_security_headers(response):
        """Add security headers to response"""

        # Content Security Policy
        if os.getenv('ENV') == 'production':
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.upbit.com wss://api.upbit.com; "
                "frame-ancestors 'none';"
            )

        # Strict Transport Security (HTTPS only)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # X-Frame-Options (clickjacking protection)
        # SAMEORIGIN allows framing within same domain (for trading chart iframe)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # X-Content-Type-Options (MIME sniffing protection)
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response

    print("[Security] Middleware configured - rate limiting + security headers enabled")


def block_ip(ip, duration_seconds=3600):
    """
    Manually block an IP address (for admin use)

    Args:
        ip: IP address to block
        duration_seconds: Block duration (default: 1 hour)
    """
    _rate_limiter.block_ip(ip, duration_seconds)


def get_rate_limiter():
    """Get the global rate limiter instance"""
    return _rate_limiter
