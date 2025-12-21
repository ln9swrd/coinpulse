# -*- coding: utf-8 -*-
"""
Telegram Linking Routes
API endpoints for linking Telegram accounts to user accounts
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.database.models import User, TelegramLinkCode
from backend.utils.auth_utils import require_auth as token_required
import random
import string

telegram_link_bp = Blueprint('telegram_link', __name__)


def generate_link_code():
    """Generate a random 6-digit linking code."""
    return ''.join(random.choices(string.digits, k=6))


@telegram_link_bp.route('/api/telegram/link/generate', methods=['POST'])
@token_required
def generate_linking_code(current_user):
    """
    Generate a new Telegram linking code for the current user.

    Returns:
        {
            "success": true,
            "code": "123456",
            "expires_at": "2025-12-21T12:15:00",
            "expires_in_minutes": 15
        }
    """
    try:
        session = get_db_session()

        # Check if already linked
        if current_user.telegram_chat_id:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Telegram account already linked. Unlink first to generate a new code.'
            }), 400

        # Invalidate any existing unused codes for this user
        existing_codes = session.query(TelegramLinkCode).filter(
            TelegramLinkCode.user_id == current_user.id,
            TelegramLinkCode.used == False
        ).all()

        for code in existing_codes:
            code.used = True
            code.used_at = datetime.utcnow()

        # Generate new code
        new_code = generate_link_code()
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        link_code = TelegramLinkCode(
            user_id=current_user.id,
            code=new_code,
            expires_at=expires_at
        )

        session.add(link_code)
        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'code': new_code,
            'expires_at': expires_at.isoformat(),
            'expires_in_minutes': 15,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@telegram_link_bp.route('/api/telegram/link/verify', methods=['POST'])
def verify_linking_code():
    """
    Verify a linking code from Telegram bot.

    Request body:
        {
            "code": "123456",
            "telegram_chat_id": "123456789",
            "telegram_username": "john_doe"
        }

    Returns:
        {
            "success": true,
            "message": "Telegram account linked successfully",
            "user": {
                "username": "john@example.com",
                "telegram_username": "@john_doe"
            }
        }
    """
    try:
        data = request.json
        code = data.get('code')
        telegram_chat_id = data.get('telegram_chat_id')
        telegram_username = data.get('telegram_username')

        if not code or not telegram_chat_id:
            return jsonify({
                'success': False,
                'error': 'Code and telegram_chat_id are required'
            }), 400

        session = get_db_session()

        # Find the linking code
        link_code = session.query(TelegramLinkCode).filter(
            TelegramLinkCode.code == code,
            TelegramLinkCode.used == False
        ).first()

        if not link_code:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Invalid or expired code'
            }), 404

        # Check expiration
        if link_code.expires_at < datetime.utcnow():
            link_code.used = True
            link_code.used_at = datetime.utcnow()
            session.commit()
            session.close()
            return jsonify({
                'success': False,
                'error': 'Code has expired. Please generate a new one.'
            }), 400

        # Get the user
        user = session.query(User).filter(User.id == link_code.user_id).first()

        if not user:
            session.close()
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Check if this chat_id is already linked to another user
        existing_user = session.query(User).filter(
            User.telegram_chat_id == telegram_chat_id,
            User.id != user.id
        ).first()

        if existing_user:
            session.close()
            return jsonify({
                'success': False,
                'error': 'This Telegram account is already linked to another user'
            }), 400

        # Link the Telegram account
        user.telegram_chat_id = telegram_chat_id
        user.telegram_username = telegram_username
        user.telegram_linked_at = datetime.utcnow()

        # Mark code as used
        link_code.used = True
        link_code.used_at = datetime.utcnow()
        link_code.telegram_chat_id = telegram_chat_id
        link_code.telegram_username = telegram_username

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Telegram account linked successfully',
            'user': {
                'username': user.username,
                'email': user.email,
                'telegram_username': telegram_username
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@telegram_link_bp.route('/api/telegram/link/status', methods=['GET'])
@token_required
def get_link_status(current_user):
    """
    Get the current Telegram linking status for the user.

    Returns:
        {
            "success": true,
            "linked": true,
            "telegram_username": "@john_doe",
            "linked_at": "2025-12-21T10:00:00"
        }
    """
    try:
        return jsonify({
            'success': True,
            'linked': bool(current_user.telegram_chat_id),
            'telegram_chat_id': current_user.telegram_chat_id if current_user.telegram_chat_id else None,
            'telegram_username': current_user.telegram_username,
            'linked_at': current_user.telegram_linked_at.isoformat() if current_user.telegram_linked_at else None,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@telegram_link_bp.route('/api/telegram/link/unlink', methods=['POST'])
@token_required
def unlink_telegram(current_user):
    """
    Unlink the Telegram account from the current user.

    Returns:
        {
            "success": true,
            "message": "Telegram account unlinked successfully"
        }
    """
    try:
        session = get_db_session()

        user = session.query(User).filter(User.id == current_user.id).first()

        if not user.telegram_chat_id:
            session.close()
            return jsonify({
                'success': False,
                'error': 'No Telegram account linked'
            }), 400

        # Unlink
        user.telegram_chat_id = None
        user.telegram_username = None
        user.telegram_linked_at = None

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Telegram account unlinked successfully',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
