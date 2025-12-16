"""
Admin Authentication Middleware
관리자 권한 확인 미들웨어
"""
from functools import wraps
from flask import request, jsonify
import os

def admin_required(f):
    """관리자 권한 확인 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 관리자 토큰 확인 (환경 변수에서)
        admin_token = os.getenv('ADMIN_TOKEN', 'coinpulse_admin_2024')
        
        # Authorization 헤더 확인
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'No authorization header'
            }), 401
        
        # Bearer 토큰 파싱
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                raise ValueError('Invalid authentication scheme')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header format'
            }), 401
        
        # 토큰 검증
        if token != admin_token:
            return jsonify({
                'success': False,
                'error': 'Invalid admin token'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function