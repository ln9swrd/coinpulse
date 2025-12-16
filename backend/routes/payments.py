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
