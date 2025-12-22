"""
Users & Payment Admin API Routes
사용자 관리 + 결제 요청 관리 API - SQLAlchemy 직접 사용 버전
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.database import get_db_session
from backend.middleware.auth import admin_required
from sqlalchemy import text
import secrets
import string

users_admin_bp = Blueprint('users_admin', __name__, url_prefix='/api/admin')

def generate_payment_code():
    """고유 결제 코드 생성 (CP + 6자리)"""
    chars = string.ascii_uppercase + string.digits
    return 'CP' + ''.join(secrets.choice(chars) for _ in range(6))

# ============================================
# 사용자 관리 API
# ============================================

@users_admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """전체 사용자 목록 조회"""
    try:
        with get_db_session() as session:
            query = text("""
                SELECT
                    u.id, u.username, u.email, u.is_active, u.created_at, u.last_login_at,
                    COALESCE(s.plan, 'free') as plan_code,
                    s.status as subscription_status,
                    s.expires_at
                FROM users u
                LEFT JOIN user_subscriptions s ON u.id = s.user_id
                ORDER BY u.created_at DESC
            """)
            result = session.execute(query)
            
            users = []
            for row in result:
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'is_active': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'last_login_at': row[5].isoformat() if row[5] else None,
                    'plan_code': row[6],
                    'subscription_status': row[7],
                    'expires_at': row[8].isoformat() if row[8] else None
                })
        
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_admin_bp.route('/users/<int:user_id>/subscription', methods=['PUT'])
@admin_required
def update_user_subscription():
    """사용자 구독 수동 수정"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        plan_code = data.get('plan_code')
        
        if not user_id or not plan_code:
            return jsonify({
                'success': False,
                'error': 'user_id and plan_code required'
            }), 400
        
        with get_db_session() as session:
            # 기존 구독 확인
            check_query = text("SELECT id FROM user_subscriptions WHERE user_id = :user_id")
            existing = session.execute(check_query, {'user_id': user_id}).fetchone()
            
            if existing:
                # 업데이트
                update_query = text("""
                    UPDATE user_subscriptions
                    SET plan = :plan_code,
                        status = 'active',
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """)
                session.execute(update_query, {
                    'plan_code': plan_code,
                    'user_id': user_id
                })
            else:
                # 신규 생성
                insert_query = text("""
                    INSERT INTO user_subscriptions (user_id, plan, status)
                    VALUES (:user_id, :plan_code, 'active')
                """)
                session.execute(insert_query, {
                    'user_id': user_id,
                    'plan_code': plan_code
                })
            
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subscription updated'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@users_admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """사용자 계정 삭제 (소프트 삭제)"""
    try:
        with get_db_session() as session:
            # 자신을 삭제하려는 경우 방지
            from flask import g
            if hasattr(g, 'user_id') and g.user_id == user_id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete your own account'
                }), 403

            # 사용자 존재 확인
            user_query = text("SELECT id, username, email FROM users WHERE id = :user_id")
            result = session.execute(user_query, {'user_id': user_id})
            user = result.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404

            # 소프트 삭제: is_active를 False로 설정
            update_query = text("""
                UPDATE users
                SET is_active = false,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
            """)
            session.execute(update_query, {'user_id': user_id})

            # 구독 비활성화
            subscription_query = text("""
                UPDATE user_subscriptions
                SET status = 'cancelled',
                    expires_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id
            """)
            session.execute(subscription_query, {'user_id': user_id})

            session.commit()

            print(f"[Admin] User {user_id} ({user[2]}) deleted by admin")

        return jsonify({
            'success': True,
            'message': 'User account deactivated successfully'
        })

    except Exception as e:
        print(f"[Admin] Error deleting user: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# 결제 요청 관리 API
# ============================================

@users_admin_bp.route('/payment-requests', methods=['GET'])
@admin_required
def get_payment_requests():
    """결제 요청 목록 조회"""
    try:
        status = request.args.get('status', 'pending')
        
        with get_db_session() as session:
            query = text("""
                SELECT 
                    pr.id, pr.email, pr.plan_code, pr.payment_code, 
                    pr.status, pr.amount, pr.created_at, pr.approved_at, pr.notes,
                    u.username
                FROM payment_requests pr
                LEFT JOIN users u ON pr.email = u.email
                WHERE pr.status = :status
                ORDER BY pr.created_at DESC
            """)
            result = session.execute(query, {'status': status})
            
            requests = []
            for row in result:
                requests.append({
                    'id': row[0],
                    'email': row[1],
                    'plan_code': row[2],
                    'payment_code': row[3],
                    'status': row[4],
                    'amount': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'approved_at': row[7].isoformat() if row[7] else None,
                    'notes': row[8],
                    'username': row[9]
                })
        
        return jsonify({
            'success': True,
            'requests': requests,
            'count': len(requests)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_admin_bp.route('/payment-requests', methods=['POST'])
@admin_required
def create_payment_request():
    """결제 요청 생성 (관리자용)"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['email', 'plan_code', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        with get_db_session() as session:
            # 플랜 검증
            plan_query = text("SELECT id FROM plan_configs WHERE plan_code = :plan_code AND is_active = true")
            plan_result = session.execute(plan_query, {'plan_code': data['plan_code']}).fetchone()
            
            if not plan_result:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or inactive plan'
                }), 400
            
            # 결제 코드 생성
            payment_code = generate_payment_code()
            
            # 결제 요청 생성
            insert_query = text("""
                INSERT INTO payment_requests 
                (email, plan_code, payment_code, amount, duration_days, bank_info, notes)
                VALUES (:email, :plan_code, :payment_code, :amount, :duration_days, :bank_info, :notes)
                RETURNING id
            """)
            
            result = session.execute(insert_query, {
                'email': data['email'],
                'plan_code': data['plan_code'],
                'payment_code': payment_code,
                'amount': data['amount'],
                'duration_days': data.get('duration_days', 30),
                'bank_info': data.get('bank_info'),
                'notes': data.get('notes')
            })
            
            request_id = result.fetchone()[0]
            session.commit()
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'payment_code': payment_code
        }), 201
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_admin_bp.route('/payment-requests/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_payment_request(request_id):
    """결제 요청 승인"""
    try:
        with get_db_session() as session:
            # 요청 정보 조회
            query = text("SELECT email, plan_code, duration_days FROM payment_requests WHERE id = :id")
            req = session.execute(query, {'id': request_id}).fetchone()
            
            if not req:
                return jsonify({
                    'success': False,
                    'error': 'Request not found'
                }), 404
            
            email, plan_code, duration_days = req
            
            # 사용자 ID 조회
            user_query = text("SELECT id FROM users WHERE email = :email")
            user_result = session.execute(user_query, {'email': email}).fetchone()
            
            if not user_result:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
            
            user_id = user_result[0]
            
            # 결제 요청 승인
            update_req = text("""
                UPDATE payment_requests 
                SET status = 'approved', approved_at = NOW()
                WHERE id = :id
            """)
            session.execute(update_req, {'id': request_id})
            
            # 구독 업데이트
            check_sub = text("SELECT id FROM user_subscriptions WHERE user_id = :user_id")
            existing_sub = session.execute(check_sub, {'user_id': user_id}).fetchone()
            
            expires_at = datetime.now() + timedelta(days=duration_days)
            
            if existing_sub:
                update_sub = text("""
                    UPDATE user_subscriptions
                    SET plan = :plan_code, status = 'active',
                        expires_at = :expires_at, updated_at = NOW()
                    WHERE user_id = :user_id
                """)
                session.execute(update_sub, {
                    'plan_code': plan_code,
                    'expires_at': expires_at,
                    'user_id': user_id
                })
            else:
                insert_sub = text("""
                    INSERT INTO user_subscriptions (user_id, plan, status, expires_at)
                    VALUES (:user_id, :plan_code, 'active', :expires_at)
                """)
                session.execute(insert_sub, {
                    'user_id': user_id,
                    'plan_code': plan_code,
                    'expires_at': expires_at
                })
            
            session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment approved and subscription activated'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
