"""
Health Monitoring Routes

Provides health check endpoints for monitoring system status.
"""

from flask import Blueprint, jsonify
from datetime import datetime
import os
import psutil
from backend.database.connection import get_db_session
from backend.database.models import User

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Returns: 200 OK if service is running
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'CoinPulse API'
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with database and system metrics
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }

    # Database connectivity check
    try:
        session = get_db_session()
        try:
            # Test query
            user_count = session.query(User).count()
            health_status['checks']['database'] = {
                'status': 'healthy',
                'user_count': user_count,
                'type': 'postgresql' if 'postgresql' in os.getenv('DATABASE_URL', '') else 'sqlite'
            }
        finally:
            session.close()
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')

        health_status['checks']['system'] = {
            'status': 'healthy',
            'cpu_usage_percent': cpu_percent,
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': disk.percent
            }
        }

        # Mark as degraded if resources are low
        if memory.percent > 90 or disk.percent > 90 or cpu_percent > 90:
            health_status['status'] = 'degraded'
            health_status['checks']['system']['warning'] = 'High resource usage'

    except Exception as e:
        health_status['checks']['system'] = {
            'status': 'unknown',
            'error': str(e)
        }

    # Environment check
    required_env_vars = ['DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    health_status['checks']['environment'] = {
        'status': 'healthy' if not missing_vars else 'degraded',
        'missing_variables': missing_vars
    }

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code


@health_bp.route('/health/db', methods=['GET'])
def database_health():
    """
    Database-specific health check
    """
    try:
        from backend.database.connection import engine, get_db_session
        from backend.database.models import User, Session as UserSession

        session = get_db_session()
        try:
            # Test queries
            user_count = session.query(User).count()
            session_count = session.query(UserSession).filter(
                UserSession.revoked == False
            ).count()

            # Pool statistics (PostgreSQL only)
            pool_stats = {}
            if engine and hasattr(engine.pool, 'size'):
                pool_stats = {
                    'pool_size': engine.pool.size(),
                    'checked_out': engine.pool.checkedout(),
                    'overflow': engine.pool.overflow(),
                    'total_capacity': engine.pool.size() + getattr(engine.pool, '_max_overflow', 0)
                }

            return jsonify({
                'status': 'healthy',
                'database': {
                    'type': 'postgresql' if 'postgresql' in os.getenv('DATABASE_URL', '') else 'sqlite',
                    'users': user_count,
                    'active_sessions': session_count,
                    'pool': pool_stats if pool_stats else None
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for load balancers
    Returns 200 only if service is ready to accept traffic
    """
    try:
        # Check database
        session = get_db_session()
        try:
            session.query(User).count()
        finally:
            session.close()

        # Check required environment variables
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        if not all(os.getenv(var) for var in required_vars):
            raise Exception("Missing required environment variables")

        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for load balancers
    Returns 200 if service is alive (simple ping)
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
