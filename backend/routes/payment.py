"""
CoinPulse - Payment API Routes
결제 및 구독 관리 API 엔드포인트
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
import logging
from datetime import datetime

from backend.database.connection import get_db
from backend.services.subscription import get_subscription_service
from backend.services.toss_payment import get_toss_payment_service

logger = logging.getLogger(__name__)

# Blueprint 생성
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Services
subscription_service = get_subscription_service()
toss_service = get_toss_payment_service()


def token_required(f):
    """JWT 토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 헤더에서 토큰 추출
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # 토큰 검증
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            request.user_id = data['user_id']
            request.user_email = data.get('email')
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


@payment_bp.route('/plans', methods=['GET'])
def get_plans():
    """
    구독 플랜 목록 조회
    
    Returns:
        JSON: 구독 플랜 정보
    """
    plans = {
        'free': {
            'name': 'Free',
            'price': {'monthly': 0, 'annual': 0},
            'features': [
                '실시간 차트',
                '기본 기술적 지표',
                '수동 매매만 가능'
            ]
        },
        'premium': {
            'name': 'Premium',
            'price': {'monthly': 29000, 'annual': 290000},
            'features': [
                'Free 플랜 모든 기능',
                '자동매매 (최대 3개 전략)',
                '고급 기술적 지표',
                '그리기 도구',
                '우선 고객지원'
            ]
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': {'monthly': 99000, 'annual': 990000},
            'features': [
                'Premium 플랜 모든 기능',
                '무제한 자동매매 전략',
                '백테스팅 시스템',
                'API 액세스',
                '전담 고객지원',
                '맞춤형 전략 개발 지원'
            ]
        }
    }
    
    return jsonify(plans), 200


@payment_bp.route('/checkout', methods=['POST'])
@token_required
def create_checkout():
    """
    결제 세션 생성
    
    Request Body:
        plan: 구독 플랜 (premium/enterprise)
        billing_period: 결제 주기 (monthly/annual)
        
    Returns:
        JSON: 결제 정보
    """
    try:
        data = request.get_json()
        plan = data.get('plan')
        billing_period = data.get('billing_period', 'monthly')
        
        if not plan or plan not in ['premium', 'enterprise']:
            return jsonify({'error': 'Invalid plan'}), 400
        
        # DB 세션 가져오기
        db = next(get_db())
        
        # 구독 생성
        subscription = subscription_service.create_subscription(
            db=db,
            user_id=request.user_id,
            user_email=request.user_email,
            plan=plan,
            billing_period=billing_period
        )
        
        # 주문 정보 생성
        order_id = f"SUB-{subscription.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        order_name = f"{plan.title()} Plan ({billing_period})"
        
        # 성공/실패 URL
        base_url = request.url_root.rstrip('/')
        success_url = f"{base_url}/payment-success?orderId={order_id}"
        fail_url = f"{base_url}/payment-error"
        
        # 토스페이먼츠 결제 데이터 생성
        payment_data = toss_service.create_payment(
            amount=subscription.amount,
            order_id=order_id,
            order_name=order_name,
            customer_email=request.user_email,
            customer_name=f"User {request.user_id}",
            success_url=success_url,
            fail_url=fail_url
        )
        
        response = {
            'subscription_id': subscription.id,
            'payment': payment_data,
            'client_key': toss_service.client_key
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"[Payment] Checkout failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/confirm', methods=['POST'])
@token_required
def confirm_payment():
    """
    결제 승인
    
    Request Body:
        payment_key: 토스페이먼츠 결제 키
        order_id: 주문 ID
        amount: 결제 금액
        
    Returns:
        JSON: 승인 결과
    """
    try:
        data = request.get_json()
        payment_key = data.get('paymentKey')
        order_id = data.get('orderId')
        amount = data.get('amount')
        
        if not all([payment_key, order_id, amount]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 토스페이먼츠 결제 승인
        result = toss_service.confirm_payment(
            payment_key=payment_key,
            order_id=order_id,
            amount=amount
        )
        
        # 구독 ID 추출
        subscription_id = int(order_id.split('-')[1])
        
        # DB 세션 가져오기
        db = next(get_db())
        
        # 구독 활성화
        subscription = subscription_service.activate_subscription(
            db=db,
            subscription_id=subscription_id,
            payment_key=payment_key,
            transaction_id=result.get('orderId')
        )
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"[Payment] Confirmation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/subscription', methods=['GET'])
@token_required
def get_subscription():
    """
    사용자의 현재 구독 조회
    
    Returns:
        JSON: 구독 정보
    """
    try:
        db = next(get_db())
        
        subscription = subscription_service.get_user_subscription(
            db=db,
            user_id=request.user_id
        )
        
        if subscription:
            return jsonify(subscription.to_dict()), 200
        else:
            return jsonify({'subscription': None}), 200
            
    except Exception as e:
        logger.error(f"[Payment] Get subscription failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/subscription/cancel', methods=['POST'])
@token_required
def cancel_subscription():
    """
    구독 취소
    
    Returns:
        JSON: 취소 결과
    """
    try:
        db = next(get_db())
        
        # 현재 구독 조회
        subscription = subscription_service.get_user_subscription(
            db=db,
            user_id=request.user_id
        )
        
        if not subscription:
            return jsonify({'error': 'No active subscription'}), 404
        
        # 구독 취소
        subscription = subscription_service.cancel_subscription(
            db=db,
            subscription_id=subscription.id,
            reason='User requested'
        )
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"[Payment] Cancel subscription failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    """
    사용자의 결제 내역 조회
    
    Returns:
        JSON: 트랜잭션 목록
    """
    try:
        db = next(get_db())
        
        # 현재 구독 조회
        subscription = subscription_service.get_user_subscription(
            db=db,
            user_id=request.user_id
        )
        
        if not subscription:
            return jsonify({'transactions': []}), 200
        
        # 트랜잭션 조회
        transactions = subscription_service.get_subscription_transactions(
            db=db,
            subscription_id=subscription.id
        )
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions]
        }), 200
        
    except Exception as e:
        logger.error(f"[Payment] Get transactions failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Blueprint 등록 함수
def register_payment_routes(app):
    """Register payment routes to Flask app"""
    app.register_blueprint(payment_bp)
    logger.info("[Payment] Routes registered")
