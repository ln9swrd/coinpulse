"""
토스페이먼츠 빌링 결제 API
"""
from flask import Blueprint, request, jsonify, redirect
import requests
import base64
import os
from datetime import datetime

payments_bp = Blueprint('payments', __name__)

# 토스페이먼츠 설정
TOSS_SECRET_KEY = os.getenv('TOSS_SECRET_KEY', 'test_sk_0RnYX2w532w0WB4noyz1VNeyqApQ')
TOSS_API_URL = 'https://api.tosspayments.com/v1/billing'

def get_auth_header():
    """Basic 인증 헤더 생성"""
    credentials = base64.b64encode(f'{TOSS_SECRET_KEY}:'.encode()).decode()
    return {'Authorization': f'Basic {credentials}', 'Content-Type': 'application/json'}


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
            
            # TODO: DB에 빌링키 저장
            # save_billing_key(customer_key, billing_key, billing_data)
            
            return redirect(f'/payment-complete.html?status=success&billingKey={billing_key[:8]}...')
        else:
            error = response.json().get('message', '알 수 없는 오류')
            return redirect(f'/subscribe.html?error={error}')
            
    except Exception as e:
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
