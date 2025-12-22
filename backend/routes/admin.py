"""
Beta Tester Admin API Routes
베타 테스터 관리 API 엔드포인트
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import text
from backend.database.connection import get_db_session
from backend.middleware.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/beta-testers', methods=['GET'])
@admin_required
def get_beta_testers():
    """베타 테스터 목록 조회"""
    try:
        status = request.args.get('status')
        
        with get_db_session() as session:
            query = "SELECT * FROM beta_testers"
            params = {}
            
            if status:
                query += " WHERE is_active = :is_active"
                params['is_active'] = (status == 'active')
            
            query += " ORDER BY joined_at DESC"

            result = session.execute(text(query), params)
            testers = [dict(row._mapping) for row in result]

            # Convert datetime to string
            for tester in testers:
                if tester.get('joined_at'):
                    tester['joined_at'] = tester['joined_at'].isoformat()
                if tester.get('expires_at'):
                    tester['expires_at'] = tester['expires_at'].isoformat()
            
            return jsonify({
                "success": True,
                "testers": testers,
                "count": len(testers)
            }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/beta-testers', methods=['POST'])
@admin_required
def add_beta_tester():
    """베타 테스터 추가"""
    try:
        data = request.get_json()
        email = data.get('email')
        duration_days = data.get('duration_days', 30)
        
        if not email:
            return jsonify({
                "success": False,
                "error": "Email is required"
            }), 400
        
        with get_db_session() as session:
            # Check if already exists
            check_query = text("SELECT COUNT(*) FROM beta_testers WHERE email = :email")
            exists = session.execute(check_query, {"email": email}).scalar()
            
            if exists:
                return jsonify({
                    "success": False,
                    "error": "Email already exists"
                }), 400
            
            # Insert new beta tester
            expires_at = datetime.now() + timedelta(days=duration_days)
            insert_query = text("""
                INSERT INTO beta_testers (email, is_active, expires_at, joined_at)
                VALUES (:email, true, :expires_at, :joined_at)
            """)

            session.execute(insert_query, {
                "email": email,
                "expires_at": expires_at,
                "joined_at": datetime.now()
            })
            session.commit()
            
            return jsonify({
                "success": True,
                "message": "Beta tester added successfully"
            }), 201
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/beta-testers/<int:tester_id>', methods=['DELETE'])
@admin_required
def delete_beta_tester(tester_id):
    """베타 테스터 삭제"""
    try:
        with get_db_session() as session:
            delete_query = text("DELETE FROM beta_testers WHERE id = :id")
            result = session.execute(delete_query, {"id": tester_id})
            session.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    "success": False,
                    "error": "Beta tester not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Beta tester deleted successfully"
            }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/beta-testers/<int:tester_id>/status', methods=['PUT'])
@admin_required
def update_beta_tester_status(tester_id):
    """베타 테스터 상태 변경"""
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({
                "success": False,
                "error": "is_active is required"
            }), 400
        
        with get_db_session() as session:
            update_query = text("""
                UPDATE beta_testers 
                SET is_active = :is_active
                WHERE id = :id
            """)
            
            result = session.execute(update_query, {
                "is_active": is_active,
                "id": tester_id
            })
            session.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    "success": False,
                    "error": "Beta tester not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Status updated successfully"
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# User Plan Management (Manual Payment)
# ============================================

@admin_bp.route('/users/<user_id>/plan', methods=['GET'])
@admin_required
def get_user_plan(user_id):
    """사용자 플랜 조회"""
    try:
        from backend.middleware.subscription_check import get_user_plan as get_plan

        plan = get_plan(user_id=user_id)

        return jsonify({
            "success": True,
            "user_id": user_id,
            "plan": plan
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/users/<user_id>/plan', methods=['POST'])
@admin_required
def update_user_plan(user_id):
    """
    사용자 플랜 변경 (수동 결제 후 관리자가 직접 변경)

    Request Body:
    {
        "plan_code": "PREMIUM",
        "duration_days": 30,
        "notes": "계좌이체 확인 완료"
    }
    """
    try:
        data = request.json
        plan_code = data.get('plan_code')
        duration_days = data.get('duration_days', 30)
        notes = data.get('notes', '')

        if not plan_code:
            return jsonify({
                "success": False,
                "error": "plan_code required"
            }), 400

        # Updated 2025.12.22: Support new plan codes (free, basic, pro)
        valid_plans = ['free', 'basic', 'pro', 'FREE', 'PREMIUM']  # Support legacy codes
        if plan_code not in valid_plans:
            return jsonify({
                "success": False,
                "error": f"Invalid plan_code. Must be one of: {', '.join(valid_plans)}"
            }), 400

        # Convert legacy plan codes to new format
        plan_mapping = {
            'FREE': 'free',
            'PREMIUM': 'pro'
        }
        plan_code = plan_mapping.get(plan_code, plan_code)

        with get_db_session() as session:
            # 기존 구독 비활성화
            deactivate_query = text("""
                UPDATE user_subscriptions
                SET status = 'cancelled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id
                AND status = 'active'
            """)
            session.execute(deactivate_query, {"user_id": user_id})

            # 새 구독 생성
            if plan_code != 'free':
                expires_at = datetime.now() + timedelta(days=duration_days)

                insert_query = text("""
                    INSERT INTO user_subscriptions (
                        user_id, plan_code, status,
                        payment_method, started_at, expires_at,
                        created_at, updated_at
                    )
                    VALUES (
                        :user_id, :plan_code, 'active',
                        'manual', CURRENT_TIMESTAMP, :expires_at,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """)

                session.execute(insert_query, {
                    "user_id": user_id,
                    "plan_code": plan_code,
                    "expires_at": expires_at
                })

            session.commit()

            return jsonify({
                "success": True,
                "message": f"User plan updated to {plan_code}",
                "user_id": user_id,
                "plan_code": plan_code,
                "expires_at": expires_at.isoformat() if plan_code != 'free' else None,
                "notes": notes
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# NOTE: /users endpoint is handled by users_admin.py to avoid route conflict
# This duplicate route has been removed
