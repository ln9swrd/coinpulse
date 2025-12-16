"""
Enhanced Logging Service

Provides structured logging with:
- Automatic log rotation (daily, size-based)
- Separate logs for errors, access, and general events
- JSON formatting for production
- Console output for development

Log Files:
- logs/app.log - General application logs
- logs/error.log - Error logs only
- logs/access.log - API access logs
- logs/security.log - Security events
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from flask import request, g
import traceback


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console output for development"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(app):
    """
    Setup comprehensive logging for Flask application

    Args:
        app: Flask application instance
    """
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Determine log format based on environment
    is_production = os.getenv('ENV', 'development') == 'production'
    log_level = logging.INFO if is_production else logging.DEBUG

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers = []

    # 1. Console Handler (colored for development, JSON for production)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    if is_production:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_formatter = ColoredConsoleFormatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # 2. Application Log File (rotated daily, keep 30 days)
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = logging.handlers.TimedRotatingFileHandler(
        app_log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(JSONFormatter() if is_production else logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    root_logger.addHandler(app_handler)

    # 3. Error Log File (only ERROR and CRITICAL, rotated by size)
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)

    # 4. Access Log (API requests)
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False  # Don't propagate to root logger

    access_log_file = os.path.join(log_dir, 'access.log')
    access_handler = logging.handlers.TimedRotatingFileHandler(
        access_log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    access_handler.setFormatter(JSONFormatter() if is_production else logging.Formatter(
        '%(asctime)s - %(message)s'
    ))
    access_logger.addHandler(access_handler)

    # 5. Security Log (authentication, authorization events)
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.propagate = False

    security_log_file = os.path.join(log_dir, 'security.log')
    security_handler = logging.handlers.TimedRotatingFileHandler(
        security_log_file,
        when='midnight',
        interval=1,
        backupCount=90,  # Keep 90 days for security events
        encoding='utf-8'
    )
    security_handler.setFormatter(JSONFormatter())
    security_logger.addHandler(security_handler)

    # Setup Flask request logging
    setup_request_logging(app, access_logger, security_logger)

    app.logger.info("Logging system initialized")
    app.logger.info(f"Log directory: {log_dir}")
    app.logger.info(f"Log level: {logging.getLevelName(log_level)}")
    app.logger.info(f"Environment: {os.getenv('ENV', 'development')}")


def setup_request_logging(app, access_logger, security_logger):
    """Setup request/response logging middleware"""

    @app.before_request
    def log_request_start():
        """Log incoming request"""
        # Generate request ID
        import uuid
        g.request_id = str(uuid.uuid4())[:8]

        # Get client IP
        g.client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Log access
        access_logger.info(
            f"{request.method} {request.path}",
            extra={
                'request_id': g.request_id,
                'ip_address': g.client_ip,
                'user_agent': request.headers.get('User-Agent'),
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8') if request.query_string else None
            }
        )

    @app.after_request
    def log_request_end(response):
        """Log response"""
        # Calculate response time
        if hasattr(g, 'start_time'):
            response_time = int((time.time() - g.start_time) * 1000)  # milliseconds

            # Log slow requests as warnings
            if response_time > 1000:
                app.logger.warning(
                    f"Slow request: {request.method} {request.path} took {response_time}ms",
                    extra={
                        'request_id': g.request_id if hasattr(g, 'request_id') else None,
                        'response_time_ms': response_time,
                        'status_code': response.status_code
                    }
                )

        return response

    @app.errorhandler(Exception)
    def log_exception(error):
        """Log unhandled exceptions"""
        app.logger.error(
            f"Unhandled exception: {str(error)}",
            exc_info=True,
            extra={
                'request_id': g.request_id if hasattr(g, 'request_id') else None,
                'ip_address': g.client_ip if hasattr(g, 'client_ip') else None,
                'path': request.path,
                'method': request.method
            }
        )

        # Re-raise to let Flask handle it
        raise


def log_security_event(event_type, message, user_id=None, severity='INFO'):
    """
    Log security-related events

    Args:
        event_type: Type of security event (login, logout, auth_failure, etc.)
        message: Event description
        user_id: User ID if applicable
        severity: Log level (INFO, WARNING, ERROR)
    """
    security_logger = logging.getLogger('security')

    log_method = getattr(security_logger, severity.lower(), security_logger.info)

    log_method(
        message,
        extra={
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.headers.get('X-Forwarded-For', request.remote_addr) if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None
        }
    )


# Import time for response time calculation
import time


if __name__ == '__main__':
    # Test logging setup
    print("Testing logging configuration...")

    class MockApp:
        logger = logging.getLogger('test')
        before_request_funcs = {}
        after_request_funcs = {}
        error_handler_spec = {}

        def before_request(self, f):
            return f

        def after_request(self, f):
            return f

        def errorhandler(self, error_type):
            def decorator(f):
                return f
            return decorator

    app = MockApp()
    setup_logging(app)

    # Test different log levels
    app.logger.debug("This is a debug message")
    app.logger.info("This is an info message")
    app.logger.warning("This is a warning message")
    app.logger.error("This is an error message")
    app.logger.critical("This is a critical message")

    # Test security logging
    log_security_event('test_event', 'Security test event', user_id=123, severity='INFO')

    print("\nLog files created in logs/ directory")
    print("- app.log (general logs)")
    print("- error.log (errors only)")
    print("- access.log (API access)")
    print("- security.log (security events)")
