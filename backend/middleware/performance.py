"""
Performance Middleware

Provides:
- Response compression (gzip)
- Cache headers
- Response time logging
"""

import gzip
import time
from io import BytesIO
from flask import request, g
from functools import wraps


def compress_response(response):
    """Compress response with gzip if client supports it"""
    accept_encoding = request.headers.get('Accept-Encoding', '')

    if 'gzip' not in accept_encoding.lower():
        return response

    # Skip compression for small responses
    if response.content_length and response.content_length < 500:
        return response

    # Skip if already compressed
    if response.headers.get('Content-Encoding') == 'gzip':
        return response

    # Compress response data
    gzip_buffer = BytesIO()
    gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
    gzip_file.write(response.get_data())
    gzip_file.close()

    # Update response
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())

    return response


def add_cache_headers(response, max_age=60):
    """Add cache control headers to response"""
    # Don't cache POST/PUT/DELETE requests
    if request.method in ['POST', 'PUT', 'DELETE']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Cache GET requests
    response.headers['Cache-Control'] = f'public, max-age={max_age}'
    return response


def log_request_time(response):
    """Log request processing time"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        # Log slow requests (> 500ms)
        if elapsed > 0.5:
            print(f"[Performance] Slow request: {request.method} {request.path} took {elapsed:.3f}s")

    return response


def setup_performance_middleware(app):
    """Setup performance middleware for Flask app"""

    @app.before_request
    def before_request():
        """Record request start time"""
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Apply performance optimizations"""
        # Log request time
        response = log_request_time(response)

        # Add cache headers (60 seconds for API responses)
        if request.path.startswith('/api/'):
            # Different cache times for different endpoints
            if 'holdings' in request.path or 'orders' in request.path:
                response = add_cache_headers(response, max_age=5)  # 5 seconds
            elif 'surge' in request.path:
                response = add_cache_headers(response, max_age=60)  # 1 minute
            elif 'plan' in request.path or 'user' in request.path:
                response = add_cache_headers(response, max_age=300)  # 5 minutes
            else:
                response = add_cache_headers(response, max_age=30)  # 30 seconds

        # Compress response
        if response.status_code == 200 and response.content_type and \
           'application/json' in response.content_type:
            response = compress_response(response)

        # Add timing header
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{elapsed:.3f}s"

        return response

    print("[Performance] Middleware configured - gzip compression + cache headers enabled")


def cache_result(timeout=60):
    """
    Decorator to cache function results

    Usage:
        @cache_result(timeout=300)
        def expensive_function():
            # ...
            return result
    """
    def decorator(f):
        cache = {}
        cache_time = {}

        @wraps(f)
        def wrapped(*args, **kwargs):
            # Create cache key
            key = str(args) + str(kwargs)

            # Check if cached and not expired
            if key in cache:
                if time.time() - cache_time[key] < timeout:
                    return cache[key]

            # Call function and cache result
            result = f(*args, **kwargs)
            cache[key] = result
            cache_time[key] = time.time()

            # Clean old cache entries (> 1 hour)
            now = time.time()
            expired_keys = [k for k, t in cache_time.items() if now - t > 3600]
            for k in expired_keys:
                del cache[k]
                del cache_time[k]

            return result

        return wrapped
    return decorator
