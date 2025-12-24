"""
Referral System API Routes
친구 초대 시스템 API
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from backend.database import get_db_session
from backend.models.referral import ReferralCode, Referral
from backend.database.models import User
from backend.models.subscription_models import Subscription
from backend.middleware.auth_middleware import require_auth
from sqlalchemy import func

referral_bp = Blueprint('referral', __name__, url_prefix='/api/referral')


@referral_bp.route('/code', methods=['GET'])
@require_auth
def get_referral_code():
    """내 추천 코드 조회 (없으면 자동 생성)"""
    try:
        user_id = g.user_id
        session = get_db_session()

        try:
            # 기존 코드 조회
            referral_code = session.query(ReferralCode).filter_by(user_id=user_id).first()

            if not referral_code:
                # 코드 생성
                while True:
                    code = ReferralCode.generate_code()
                    # 중복 확인
                    existing = session.query(ReferralCode).filter_by(code=code).first()
                    if not existing:
                        break

                referral_code = ReferralCode(
                    user_id=user_id,
                    code=code
                )
                session.add(referral_code)
                session.commit()
                session.refresh(referral_code)

            # 추천 링크 생성
            referral_link = f"https://coinpulse.sinsi.ai/signup.html?ref={referral_code.code}"

            return jsonify({
                'success': True,
                'code': referral_code.code,
                'link': referral_link
            })

        finally:
            session.close()

    except Exception as e:
        error_msg = str(e)
        print(f"[Referral] Error getting code: {error_msg}")

        # Handle specific error types
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'API 요청 한도 초과: 잠시 후 다시 시도해주세요',
                'error_code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        else:
            return jsonify({
                'success': False,
                'error': '추천 코드를 불러올 수 없습니다',
                'detail': error_msg
            }), 500


@referral_bp.route('/stats', methods=['GET'])
@require_auth
def get_referral_stats():
    """추천 통계 조회"""
    try:
        user_id = g.user_id
        session = get_db_session()

        try:
            # 내가 추천한 사람 수
            total_referrals = session.query(func.count(Referral.id)).filter_by(referrer_id=user_id).scalar()

            # 보상 받은 추천 수
            rewarded_referrals = session.query(func.count(Referral.id)).filter_by(
                referrer_id=user_id,
                reward_granted=True
            ).scalar()

            # 최근 추천 목록 (최대 10개)
            recent_referrals = session.query(Referral).filter_by(referrer_id=user_id).order_by(
                Referral.created_at.desc()
            ).limit(10).all()

            recent_list = []
            for ref in recent_referrals:
                referred_user = session.query(User).filter_by(id=ref.referred_id).first()
                recent_list.append({
                    'email': referred_user.email if referred_user else 'Unknown',
                    'created_at': ref.created_at.isoformat(),
                    'reward_granted': ref.reward_granted
                })

            return jsonify({
                'success': True,
                'stats': {
                    'total_referrals': total_referrals or 0,
                    'rewarded_referrals': rewarded_referrals or 0,
                    'pending_referrals': (total_referrals or 0) - (rewarded_referrals or 0),
                    'recent_referrals': recent_list
                }
            })

        finally:
            session.close()

    except Exception as e:
        error_msg = str(e)
        print(f"[Referral] Error getting stats: {error_msg}")

        # Handle specific error types
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'API 요청 한도 초과: 잠시 후 다시 시도해주세요',
                'error_code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        else:
            return jsonify({
                'success': False,
                'error': '통계를 불러올 수 없습니다',
                'detail': error_msg
            }), 500


@referral_bp.route('/apply', methods=['POST'])
def apply_referral_code():
    """회원가입 시 추천 코드 적용"""
    try:
        data = request.get_json()
        referral_code = data.get('referral_code')
        referred_email = data.get('email')

        if not referral_code or not referred_email:
            return jsonify({
                'success': False,
                'error': 'Missing referral_code or email'
            }), 400

        session = get_db_session()

        try:
            # 추천 코드 존재 확인
            code_obj = session.query(ReferralCode).filter_by(code=referral_code).first()

            if not code_obj:
                return jsonify({
                    'success': False,
                    'error': 'Invalid referral code'
                }), 404

            # 추천받은 사용자 찾기
            referred_user = session.query(User).filter_by(email=referred_email).first()

            if not referred_user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404

            # 자기 자신 추천 방지
            if code_obj.user_id == referred_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot refer yourself'
                }), 400

            # 이미 추천 관계가 있는지 확인
            existing = session.query(Referral).filter_by(referred_id=referred_user.id).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'User already referred'
                }), 400

            # 추천 관계 생성
            referral = Referral(
                referrer_id=code_obj.user_id,
                referred_id=referred_user.id,
                referral_code_id=code_obj.id
            )
            session.add(referral)

            # 보상 지급: 추천인과 피추천인 모두에게 30일 무료
            # 추천인 보상
            referrer_sub = session.query(Subscription).filter_by(user_id=code_obj.user_id).first()
            if referrer_sub:
                if referrer_sub.expires_at:
                    referrer_sub.expires_at = referrer_sub.expires_at + timedelta(days=30)
                else:
                    referrer_sub.expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                # 구독 생성
                referrer_sub = Subscription(
                    user_id=code_obj.user_id,
                    plan='basic',
                    status='active',
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                session.add(referrer_sub)

            # 피추천인 보상
            referred_sub = session.query(Subscription).filter_by(user_id=referred_user.id).first()
            if referred_sub:
                if referred_sub.expires_at:
                    referred_sub.expires_at = referred_sub.expires_at + timedelta(days=30)
                else:
                    referred_sub.expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                referred_sub = Subscription(
                    user_id=referred_user.id,
                    plan='basic',
                    status='active',
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                session.add(referred_sub)

            # 보상 지급 표시
            referral.reward_granted = True
            referral.reward_granted_at = datetime.utcnow()

            session.commit()

            print(f"[Referral] User {referred_user.id} referred by {code_obj.user_id} - 30 days granted to both")

            return jsonify({
                'success': True,
                'message': 'Referral applied successfully',
                'reward_days': 30
            })

        finally:
            session.close()

    except Exception as e:
        print(f"[Referral] Error applying code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
