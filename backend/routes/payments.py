"""
토스페이먼츠 빌링 결제 API
"""
from flask import Blueprint, request, jsonify, redirect
import requests
import base64
import os
from datetime import datetime
from backend.database.connection import get_db_session
from backend.database.models import BillingKey, User

payments_bp = Blueprint('payments', __name__)

# 토스페이먼츠 설정
TOSS_SECRET_KEY = os.getenv('TOSS_SECRET_KEY', 'test_sk_0RnYX2w532w0WB4noyz1VNeyqApQ')
TOSS_API_URL = 'https://api.tosspayments.com/v1/billing'

def get_auth_header():
    """Basic 인증 헤더 생성"""
    credentials = base64.b64encode(f'{TOSS_SECRET_KEY}:'.encode()).decode()
    return {'Authorization': f'Basic {credentials}', 'Content-Type': 'application/json'}


def save_billing_key(user_id, customer_key, billing_key, billing_data):
    """
    빌링키를 데이터베이스에 저장

    Args:
        user_id (int): 사용자 ID
        customer_key (str): 토스페이먼츠 customer_key
        billing_key (str): 토스페이먼츠 billing_key
        billing_data (dict): 토스페이먼츠 API 응답 데이터

    Returns:
        BillingKey: 저장된 BillingKey 객체
    """
    session = get_db_session()
    try:
        # Extract card information from billing_data
        card = billing_data.get('card', {})
        card_company = card.get('issuerCode', card.get('company'))
        card_number = card.get('number')  # Already masked by Toss Payments
        card_type = card.get('cardType')  # 신용/체크

        # Check if billing key already exists
        existing_key = session.query(BillingKey).filter_by(customer_key=customer_key).first()

        if existing_key:
            # Update existing billing key
            existing_key.billing_key = billing_key
            existing_key.card_company = card_company
            existing_key.card_number = card_number
            existing_key.card_type = card_type
            existing_key.billing_data = billing_data
            existing_key.status = 'active'
            existing_key.updated_at = datetime.utcnow()
            print(f"[Billing] Updated existing billing key for user_id={user_id}")
        else:
            # Create new billing key
            new_billing_key = BillingKey(
                user_id=user_id,
                customer_key=customer_key,
                billing_key=billing_key,
                card_company=card_company,
                card_number=card_number,
                card_type=card_type,
                billing_data=billing_data,
                status='active'
            )
            session.add(new_billing_key)
            print(f"[Billing] Created new billing key for user_id={user_id}")

        session.commit()
        result = session.query(BillingKey).filter_by(customer_key=customer_key).first()
        return result

    except Exception as e:
        session.rollback()
        print(f"[Billing] Error saving billing key: {e}")
        raise
    finally:
        session.close()


@payments_bp.route('/billing/success', methods=['GET'])
def billing_success():
    """빌링키 발급 성공 콜백"""
    auth_key = request.args.get('authKey')
    customer_key = request.args.get('customerKey')

    if not auth_key or not customer_key:
        return redirect('/subscribe.html?error=missing_params')

    # 빌링키 발급 요청
    try:
        response = requests.post(
            f'{TOSS_API_URL}/authorizations/issue',
            headers=get_auth_header(),
            json={
                'authKey': auth_key,
                'customerKey': customer_key
            }
        )

        if response.status_code == 200:
            billing_data = response.json()
            billing_key = billing_data.get('billingKey')

            # Extract user_id from customer_key
            # Expected format: "user_{user_id}" or just user_id as string
            try:
                if customer_key.startswith('user_'):
                    user_id = int(customer_key.split('_')[1])
                else:
                    user_id = int(customer_key)

                # Save billing key to database
                saved_billing_key = save_billing_key(user_id, customer_key, billing_key, billing_data)
                print(f"[Billing] Successfully saved billing key for user {user_id}")

            except (ValueError, IndexError) as e:
                print(f"[Billing] Warning: Could not extract user_id from customer_key '{customer_key}': {e}")
                # Continue anyway, billing key is still valid

            return redirect(f'/payment-complete.html?status=success&billingKey={billing_key[:8]}...')
        else:
            error = response.json().get('message', '알 수 없는 오류')
            return redirect(f'/subscribe.html?error={error}')

    except Exception as e:
        print(f"[Billing] Error in billing_success: {e}")
        return redirect(f'/subscribe.html?error={str(e)}')


@payments_bp.route('/billing/fail', methods=['GET'])
def billing_fail():
    """빌링키 발급 실패 콜백"""
    error_code = request.args.get('code', 'UNKNOWN')
    error_msg = request.args.get('message', '결제 실패')
    return redirect(f'/subscribe.html?error={error_code}&message={error_msg}')


@payments_bp.route('/billing/execute', methods=['POST'])
def execute_billing():
    """정기결제 실행 (빌링키로 결제)"""
    data = request.json
    billing_key = data.get('billingKey')
    customer_key = data.get('customerKey')
    amount = data.get('amount')
    order_id = data.get('orderId', f'ORDER_{datetime.now().strftime("%Y%m%d%H%M%S")}')
    order_name = data.get('orderName', 'CoinPulse 구독')
    
    if not all([billing_key, customer_key, amount]):
        return jsonify({'success': False, 'error': '필수 파라미터 누락'}), 400
    
    try:
        response = requests.post(
            f'{TOSS_API_URL}/{billing_key}',
            headers=get_auth_header(),
            json={
                'customerKey': customer_key,
                'amount': amount,
                'orderId': order_id,
                'orderName': order_name
            }
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            return jsonify({
                'success': True,
                'paymentKey': payment_data.get('paymentKey'),
                'orderId': payment_data.get('orderId'),
                'status': payment_data.get('status')
            })
        else:
            error = response.json()
            return jsonify({
                'success': False,
                'error': error.get('message', '결제 실패')
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@payments_bp.route('/status', methods=['GET'])
def payment_status():
    """결제 시스템 상태 확인"""
    return jsonify({
        'status': 'active',
        'provider': 'tosspayments',
        'mode': 'test' if 'test_' in TOSS_SECRET_KEY else 'live',
        'timestamp': datetime.now().isoformat()
    })


@payments_bp.route('/billing/keys/<int:user_id>', methods=['GET'])
def get_billing_keys(user_id):
    """
    사용자의 빌링키 조회

    Args:
        user_id (int): 사용자 ID

    Returns:
        JSON: 빌링키 목록
    """
    session = get_db_session()
    try:
        billing_keys = session.query(BillingKey).filter_by(
            user_id=user_id,
            status='active'
        ).order_by(BillingKey.created_at.desc()).all()

        return jsonify({
            'success': True,
            'count': len(billing_keys),
            'billing_keys': [bk.to_dict() for bk in billing_keys]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payments_bp.route('/billing/keys/<int:billing_key_id>/deactivate', methods=['POST'])
def deactivate_billing_key(billing_key_id):
    """
    빌링키 비활성화 (카드 변경 시)

    Args:
        billing_key_id (int): 빌링키 ID

    Returns:
        JSON: 성공 여부
    """
    session = get_db_session()
    try:
        billing_key = session.query(BillingKey).filter_by(id=billing_key_id).first()

        if not billing_key:
            return jsonify({
                'success': False,
                'error': '빌링키를 찾을 수 없습니다'
            }), 404

        billing_key.status = 'inactive'
        billing_key.updated_at = datetime.utcnow()
        session.commit()

        return jsonify({
            'success': True,
            'message': '빌링키가 비활성화되었습니다'
        })

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payments_bp.route('/refund', methods=['POST'])
def refund_payment():
    """
    결제 환불 처리

    Request Body:
        {
            "paymentKey": "결제 키",
            "cancelReason": "환불 사유",
            "refundReceiveAccount": {  # 선택사항
                "bank": "은행 코드",
                "accountNumber": "계좌번호",
                "holderName": "예금주명"
            },
            "cancelAmount": 10000  # 선택사항, 부분 환불 시
        }

    Returns:
        JSON: 환불 결과
    """
    data = request.json
    payment_key = data.get('paymentKey')
    cancel_reason = data.get('cancelReason', '고객 요청')
    cancel_amount = data.get('cancelAmount')  # None이면 전액 환불
    refund_account = data.get('refundReceiveAccount')  # 가상계좌 환불용

    if not payment_key:
        return jsonify({
            'success': False,
            'error': '결제 키가 필요합니다'
        }), 400

    try:
        # Toss Payments 환불 API 호출
        refund_data = {
            'cancelReason': cancel_reason
        }

        # 부분 환불 시 금액 지정
        if cancel_amount:
            refund_data['cancelAmount'] = cancel_amount

        # 가상계좌 환불 계좌 정보
        if refund_account:
            refund_data['refundReceiveAccount'] = refund_account

        response = requests.post(
            f'https://api.tosspayments.com/v1/payments/{payment_key}/cancel',
            headers=get_auth_header(),
            json=refund_data
        )

        if response.status_code == 200:
            refund_result = response.json()

            # TODO: 환불 내역을 데이터베이스에 기록
            # - 환불 금액
            # - 환불 사유
            # - 환불 시간
            # - 사용자 구독 상태 업데이트

            return jsonify({
                'success': True,
                'message': '환불이 완료되었습니다',
                'refund': {
                    'paymentKey': refund_result.get('paymentKey'),
                    'orderId': refund_result.get('orderId'),
                    'status': refund_result.get('status'),
                    'canceledAt': refund_result.get('canceledAt'),
                    'cancelAmount': refund_result.get('cancelAmount'),
                    'cancelReason': refund_result.get('cancelReason')
                }
            })
        else:
            error = response.json()
            return jsonify({
                'success': False,
                'error': error.get('message', '환불 처리 실패'),
                'code': error.get('code')
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'환불 처리 중 오류 발생: {str(e)}'
        }), 500


@payments_bp.route('/refund/status/<payment_key>', methods=['GET'])
def get_refund_status(payment_key):
    """
    결제/환불 상태 조회

    Args:
        payment_key (str): 결제 키

    Returns:
        JSON: 결제 정보 (취소 내역 포함)
    """
    try:
        response = requests.get(
            f'https://api.tosspayments.com/v1/payments/{payment_key}',
            headers=get_auth_header()
        )

        if response.status_code == 200:
            payment_data = response.json()

            return jsonify({
                'success': True,
                'payment': {
                    'paymentKey': payment_data.get('paymentKey'),
                    'orderId': payment_data.get('orderId'),
                    'status': payment_data.get('status'),
                    'totalAmount': payment_data.get('totalAmount'),
                    'balanceAmount': payment_data.get('balanceAmount'),
                    'method': payment_data.get('method'),
                    'approvedAt': payment_data.get('approvedAt'),
                    'cancels': payment_data.get('cancels', [])  # 환불 내역
                }
            })
        else:
            error = response.json()
            return jsonify({
                'success': False,
                'error': error.get('message', '결제 정보 조회 실패')
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payments_bp.route('/subscription/cancel/<int:user_id>', methods=['POST'])
def cancel_subscription(user_id):
    """
    구독 취소 (다음 결제부터 중지)

    Args:
        user_id (int): 사용자 ID

    Request Body:
        {
            "reason": "취소 사유",
            "refund": false  # 즉시 환불 여부 (현재 결제 기간 환불)
        }

    Returns:
        JSON: 취소 결과
    """
    from backend.database.models import UserSubscription

    data = request.json or {}
    cancel_reason = data.get('reason', '사용자 요청')
    immediate_refund = data.get('refund', False)

    session = get_db_session()
    try:
        # 사용자 구독 정보 조회
        subscription = session.query(UserSubscription).filter_by(
            user_id=user_id,
            status='active'
        ).first()

        if not subscription:
            return jsonify({
                'success': False,
                'error': '활성 구독을 찾을 수 없습니다'
            }), 404

        # 구독 상태 업데이트
        subscription.status = 'cancelled'
        subscription.cancel_reason = cancel_reason
        subscription.cancelled_at = datetime.utcnow()

        # 즉시 환불 처리
        if immediate_refund and subscription.last_payment_key:
            # TODO: 일할 계산 후 부분 환불 처리
            # 현재 결제 기간 중 사용한 일수 계산
            # 남은 기간에 대해 환불
            pass

        session.commit()

        return jsonify({
            'success': True,
            'message': '구독이 취소되었습니다',
            'subscription': {
                'user_id': user_id,
                'status': 'cancelled',
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                'cancelled_at': subscription.cancelled_at.isoformat()
            }
        })

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()
