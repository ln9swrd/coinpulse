# -*- coding: utf-8 -*-
"""
CoinPulse Telegram Webhook for Bank Transfer Notifications
Automatically processes bank deposit notifications and activates subscriptions
"""

import os
import sys
import re
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.connection import get_db_session
from backend.routes.payment_confirmation import PaymentConfirmation, PaymentConfirmStatus
from backend.models.subscription_models import Subscription, SubscriptionPlan, SubscriptionStatus, BillingPeriod

# Create Blueprint
telegram_webhook_bp = Blueprint('telegram_webhook', __name__, url_prefix='/api/telegram')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')

# Bank account info
BANK_ACCOUNT = "169-176889-01-012"
BANK_NAME = "기업은행"


def send_telegram_message(chat_id, message):
    """Send message to Telegram chat"""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        print(f"[Telegram] Bot token or chat ID not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
        return False


def parse_bank_sms(text):
    """
    Parse bank deposit SMS notification

    Expected formats:
    - "[기업은행] 입금 \\n169176889\\n홍길동\\n99,000원\\n12/20 14:30"
    - "[IBK기업은행] 169-176889-01-012 입금 99,000원 홍길동 12/20 14:30"
    - "기업은행 입금알림\\n계좌:169176889\\n입금자:홍길동\\n금액:99,000원\\n일시:2025-12-20 14:30"

    Returns:
        dict: {
            'depositor_name': str,
            'amount': int,
            'transfer_date': datetime,
            'account_number': str
        } or None if parsing fails
    """

    # Remove all whitespace for easier parsing
    text_clean = text.replace(' ', '').replace('\\n', '\n')

    # Extract depositor name (입금자, 송금인)
    depositor_match = re.search(r'(입금자|송금인)[:\s]*([가-힣a-zA-Z]+)', text_clean)
    if not depositor_match:
        # Try alternative pattern: name followed by amount
        depositor_match = re.search(r'([가-힣]{2,4})\s*[\d,]+원', text)

    if not depositor_match:
        return None

    depositor_name = depositor_match.group(2) if depositor_match.lastindex >= 2 else depositor_match.group(1)

    # Extract amount (금액)
    amount_match = re.search(r'([\d,]+)원', text_clean)
    if not amount_match:
        return None

    amount_str = amount_match.group(1).replace(',', '')
    try:
        amount = int(amount_str)
    except ValueError:
        return None

    # Extract date and time
    # Pattern 1: 12/20 14:30 or 2025-12-20 14:30
    date_match = re.search(r'(\d{2}/\d{2}|\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})', text_clean)

    if date_match:
        date_str = date_match.group(1)
        time_str = date_match.group(2)

        # Parse date
        if '/' in date_str:
            # Format: 12/20 (assume current year)
            month, day = date_str.split('/')
            year = datetime.now().year
            transfer_date = datetime(year, int(month), int(day))
        else:
            # Format: 2025-12-20
            year, month, day = date_str.split('-')
            transfer_date = datetime(int(year), int(month), int(day))

        # Add time
        hour, minute = time_str.split(':')
        transfer_date = transfer_date.replace(hour=int(hour), minute=int(minute))
    else:
        # No date/time found, use current time
        transfer_date = datetime.now()

    # Extract account number (optional)
    account_match = re.search(r'(\d{3}[-\s]?\d{6}[-\s]?\d{2}[-\s]?\d{3})', text_clean)
    account_number = account_match.group(1) if account_match else BANK_ACCOUNT

    return {
        'depositor_name': depositor_name.strip(),
        'amount': amount,
        'transfer_date': transfer_date,
        'account_number': account_number
    }


def auto_match_and_approve(deposit_info):
    """
    Automatically match deposit with pending payment confirmations

    Args:
        deposit_info (dict): Parsed deposit information

    Returns:
        dict: {
            'matched': bool,
            'confirmation_id': int or None,
            'subscription_id': int or None,
            'message': str
        }
    """
    session = get_db_session()

    try:
        # Find pending confirmations with matching amount
        pending_confirmations = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.status == PaymentConfirmStatus.PENDING,
            PaymentConfirmation.amount == deposit_info['amount']
        ).all()

        if not pending_confirmations:
            return {
                'matched': False,
                'confirmation_id': None,
                'subscription_id': None,
                'message': f"매칭되는 pending confirmation이 없습니다 (금액: ₩{deposit_info['amount']:,})"
            }

        # Try to match by depositor name (fuzzy matching)
        best_match = None
        for confirmation in pending_confirmations:
            # Check if depositor name contains user name or vice versa
            if (deposit_info['depositor_name'] in confirmation.user_name or
                confirmation.user_name in deposit_info['depositor_name'] or
                deposit_info['depositor_name'] == confirmation.depositor_name):
                best_match = confirmation
                break

        if not best_match:
            # No name match, but amount matches - return first one for manual review
            best_match = pending_confirmations[0]
            return {
                'matched': False,
                'confirmation_id': best_match.id,
                'subscription_id': None,
                'message': f"⚠️ 금액은 일치하지만 입금자명이 다릅니다\n" +
                          f"입금자: {deposit_info['depositor_name']}\n" +
                          f"등록된 이름: {best_match.user_name}\n" +
                          f"수동 확인이 필요합니다."
            }

        # Perfect match found - auto approve
        best_match.status = PaymentConfirmStatus.APPROVED
        best_match.reviewed_by_admin = 'auto_telegram_bot'
        best_match.reviewed_at = datetime.utcnow()
        best_match.admin_notes = f"자동 승인 (텔레그램 봇)\n입금자: {deposit_info['depositor_name']}\n입금시각: {deposit_info['transfer_date']}"

        # Create or update subscription
        plan_enum = SubscriptionPlan(best_match.plan)
        billing_enum = BillingPeriod(best_match.billing_period)

        subscription = session.query(Subscription).filter(
            Subscription.user_id == best_match.user_id
        ).order_by(Subscription.created_at.desc()).first()

        if subscription:
            # Update existing subscription
            subscription.plan = plan_enum
            subscription.billing_period = billing_enum
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.amount = best_match.amount
            subscription.started_at = datetime.utcnow()
            subscription.current_period_start = datetime.utcnow()

            if billing_enum == BillingPeriod.MONTHLY:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            else:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=365)

            subscription.updated_at = datetime.utcnow()
        else:
            # Create new subscription
            period_end = datetime.utcnow() + timedelta(
                days=30 if billing_enum == BillingPeriod.MONTHLY else 365
            )

            subscription = Subscription(
                user_id=best_match.user_id,
                user_email=best_match.user_email,
                plan=plan_enum,
                billing_period=billing_enum,
                status=SubscriptionStatus.ACTIVE,
                amount=best_match.amount,
                started_at=datetime.utcnow(),
                current_period_start=datetime.utcnow(),
                current_period_end=period_end
            )
            session.add(subscription)

        session.commit()

        return {
            'matched': True,
            'confirmation_id': best_match.id,
            'subscription_id': subscription.id,
            'message': f"✅ 자동 승인 완료!\n" +
                      f"사용자: {best_match.user_name} ({best_match.user_email})\n" +
                      f"플랜: {plan_enum.value}\n" +
                      f"금액: ₩{best_match.amount:,}\n" +
                      f"구독 기간: {subscription.current_period_end.strftime('%Y-%m-%d')}까지"
        }

    except Exception as e:
        session.rollback()
        return {
            'matched': False,
            'confirmation_id': None,
            'subscription_id': None,
            'message': f"❌ 오류 발생: {str(e)}"
        }
    finally:
        session.close()


@telegram_webhook_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """
    Telegram bot webhook endpoint

    Receives messages from Telegram bot and processes bank deposit notifications

    Expected message format (forwarded from bank SMS):
    "[기업은행] 입금 \n169176889\n홍길동\n99,000원\n12/20 14:30"

    Response:
    {
        "success": true,
        "processed": true,
        "matched": true,
        "message": "자동 승인 완료"
    }
    """
    try:
        # Handle UTF-8 encoding explicitly
        if request.content_type and 'charset' not in request.content_type:
            request.environ['CONTENT_TYPE'] = 'application/json; charset=utf-8'

        data = request.get_json(force=True)

        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Invalid webhook data'}), 400

        message = data['message']
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')

        if not text:
            return jsonify({'success': True, 'processed': False, 'message': 'No text in message'}), 200

        # Parse bank SMS
        deposit_info = parse_bank_sms(text)

        if not deposit_info:
            # Not a valid bank deposit SMS
            send_telegram_message(
                chat_id,
                "⚠️ 입금 알림을 파싱할 수 없습니다.\n\n" +
                "올바른 형식:\n" +
                "[기업은행] 입금\n" +
                "169176889\n" +
                "홍길동\n" +
                "99,000원\n" +
                "12/20 14:30"
            )
            return jsonify({'success': True, 'processed': False, 'message': 'Invalid SMS format'}), 200

        # Auto match and approve
        result = auto_match_and_approve(deposit_info)

        # Send notification to admin
        admin_message = f"<b>💰 입금 알림</b>\n\n" + \
                       f"입금자: {deposit_info['depositor_name']}\n" + \
                       f"금액: ₩{deposit_info['amount']:,}\n" + \
                       f"시간: {deposit_info['transfer_date'].strftime('%Y-%m-%d %H:%M')}\n" + \
                       f"계좌: {deposit_info['account_number']}\n\n" + \
                       f"{result['message']}"

        if ADMIN_CHAT_ID:
            send_telegram_message(ADMIN_CHAT_ID, admin_message)

        # Send response to sender
        send_telegram_message(chat_id, result['message'])

        return jsonify({
            'success': True,
            'processed': True,
            'matched': result['matched'],
            'confirmation_id': result['confirmation_id'],
            'subscription_id': result['subscription_id'],
            'message': result['message']
        }), 200

    except Exception as e:
        print(f"[Telegram Webhook] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@telegram_webhook_bp.route('/test-parse', methods=['POST'])
def test_parse():
    """
    Test endpoint for SMS parsing

    Request JSON:
    {
        "text": "[기업은행] 입금 \\n169176889\\n홍길동\\n99,000원\\n12/20 14:30"
    }

    Response:
    {
        "success": true,
        "parsed": {...},
        "original_text": "..."
    }
    """
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({'success': False, 'error': 'text field required'}), 400

        parsed = parse_bank_sms(text)

        if not parsed:
            return jsonify({
                'success': False,
                'error': 'Failed to parse SMS',
                'original_text': text
            }), 400

        return jsonify({
            'success': True,
            'parsed': {
                'depositor_name': parsed['depositor_name'],
                'amount': parsed['amount'],
                'transfer_date': parsed['transfer_date'].isoformat(),
                'account_number': parsed['account_number']
            },
            'original_text': text
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@telegram_webhook_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram_webhook',
        'bot_configured': bool(TELEGRAM_BOT_TOKEN),
        'admin_configured': bool(ADMIN_CHAT_ID),
        'timestamp': datetime.utcnow().isoformat()
    }), 200
