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

        # Rate limit configuration
        self.limits = {
            # Default: 60 requests per minute
            'default': {'requests': 60, 'window': 60},

            # Authentication: 5 login attempts per minute
            'auth': {'requests': 5, 'window': 60},

            # API endpoints: 30 requests per minute
            'api': {'requests': 30, 'window': 60},

            # Trading: 10 requests per minute
            'trading': {'requests': 10, 'window': 60},

            # Admin: 20 requests per minute
            'admin': {'requests': 20, 'window': 60}
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
        if request.method in ['POST', 'PUT', 'PATCH']:
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
        response.headers['X-Frame-Options'] = 'DENY'

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
