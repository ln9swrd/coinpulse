"""
Admin Authentication Middleware
관리자 권한 확인 미들웨어
"""
from functools import wraps
from flask import request, jsonify
from backend.database.connection import get_db_session
from backend.database.models import User

def admin_required(f):
    """관리자 권한 확인 데코레이터 (JWT 기반)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # JWT 토큰 검증 및 사용자 확인
        from backend.routes.auth_routes import get_current_user

        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # 사용자 정보 조회
        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # 관리자 권한 확인
            if not user.is_admin:
                return jsonify({
                    'success': False,
                    'error': 'Admin access required',
                    'code': 'FORBIDDEN'
                }), 403

            # Pass user object as first argument to the decorated function
            return f(user, *args, **kwargs)

        finally:
            session.close()

    return decorated_function