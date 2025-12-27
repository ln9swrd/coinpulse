"""
API Key Management Routes
Handles user's Upbit API key registration, verification, and management
"""

from flask import Blueprint, request, jsonify
from backend.database.connection import get_db_session
from backend.models.user_api_key import UpbitAPIKey
from backend.utils.crypto import encrypt_api_credentials, decrypt_api_credentials
from backend.common import UpbitAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create blueprint
api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/api-keys')


@api_key_bp.route('/', methods=['GET'])
def get_api_keys():
    """
    Get user's API keys (metadata only, no actual keys)

    Query params:
        user_id: User ID (required)

    Returns:
        {
            "success": true,
            "has_key": true,
            "key": {
                "id": 1,
                "key_name": "My Trading Key",
                "is_active": true,
                "is_verified": true,
                "created_at": "2025-12-27T10:00:00"
            }
        }
    """
    try:
        user_id = request.args.get('user_id', type=int)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        session = get_db_session()

        # Query user's API key
        user_key = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id
        ).first()

        if not user_key:
            return jsonify({
                "success": true,
                "has_key": False,
                "key": None
            })

        return jsonify({
            "success": True,
            "has_key": True,
            "key": user_key.to_dict(include_keys=False)
        })

    except Exception as e:
        logger.error(f"[APIKeys] Error getting keys: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@api_key_bp.route('/register', methods=['POST'])
def register_api_keys():
    """
    Register or update user's Upbit API keys

    Request body:
        {
            "user_id": 1,
            "access_key": "Upbit access key",
            "secret_key": "Upbit secret key",
            "key_name": "My Trading Key" (optional),
            "verify": true (optional, default true)
        }

    Returns:
        {
            "success": true,
            "message": "API keys registered successfully",
            "verified": true,
            "key": {... key metadata ...}
        }
    """
    try:
        data = request.json

        user_id = data.get('user_id')
        access_key = data.get('access_key')
        secret_key = data.get('secret_key')
        key_name = data.get('key_name', 'Default Trading Key')
        should_verify = data.get('verify', True)

        # Validation
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if not access_key or not secret_key:
            return jsonify({"error": "access_key and secret_key are required"}), 400

        # Verify keys with Upbit API (if requested)
        is_verified = False
        if should_verify:
            try:
                upbit_api = UpbitAPI(access_key, secret_key)
                accounts = upbit_api.get_accounts()

                if accounts:
                    is_verified = True
                    logger.info(f"[APIKeys] API keys verified for user {user_id}")
                else:
                    return jsonify({
                        "error": "API key verification failed. Please check your keys.",
                        "verified": False
                    }), 400

            except Exception as verify_error:
                logger.error(f"[APIKeys] Verification failed: {verify_error}")
                return jsonify({
                    "error": f"API key verification failed: {str(verify_error)}",
                    "verified": False
                }), 400

        # Encrypt keys
        encrypted_access, encrypted_secret = encrypt_api_credentials(access_key, secret_key)

        session = get_db_session()

        # Check if user already has API keys
        existing_key = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id
        ).first()

        if existing_key:
            # Update existing keys
            existing_key.access_key_encrypted = encrypted_access
            existing_key.secret_key_encrypted = encrypted_secret
            existing_key.key_name = key_name
            existing_key.is_active = True
            existing_key.updated_at = datetime.utcnow()

            if is_verified:
                existing_key.mark_verified()

            session.commit()

            logger.info(f"[APIKeys] Updated API keys for user {user_id}")

            return jsonify({
                "success": True,
                "message": "API keys updated successfully",
                "verified": is_verified,
                "key": existing_key.to_dict(include_keys=False)
            })

        else:
            # Create new record
            new_key = UpbitAPIKey(
                user_id=user_id,
                access_key_encrypted=encrypted_access,
                secret_key_encrypted=encrypted_secret,
                key_name=key_name,
                is_active=True,
                is_verified=is_verified
            )

            if is_verified:
                new_key.mark_verified()

            session.add(new_key)
            session.commit()

            logger.info(f"[APIKeys] Registered new API keys for user {user_id}")

            return jsonify({
                "success": True,
                "message": "API keys registered successfully",
                "verified": is_verified,
                "key": new_key.to_dict(include_keys=False)
            })

    except Exception as e:
        logger.error(f"[APIKeys] Error registering keys: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@api_key_bp.route('/verify', methods=['POST'])
def verify_api_keys():
    """
    Verify user's registered API keys by making test API call

    Request body:
        {
            "user_id": 1
        }

    Returns:
        {
            "success": true,
            "verified": true,
            "accounts": [...] (Upbit accounts)
        }
    """
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        session = get_db_session()

        # Get user's API keys
        user_key = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id,
            UpbitAPIKey.is_active == True
        ).first()

        if not user_key:
            return jsonify({"error": "No API keys found for user"}), 404

        # Decrypt keys
        access_key, secret_key = decrypt_api_credentials(
            user_key.access_key_encrypted,
            user_key.secret_key_encrypted
        )

        # Test API call
        upbit_api = UpbitAPI(access_key, secret_key)
        accounts = upbit_api.get_accounts()

        if accounts:
            # Mark as verified
            user_key.mark_verified()
            session.commit()

            logger.info(f"[APIKeys] Verification successful for user {user_id}")

            return jsonify({
                "success": True,
                "verified": True,
                "accounts": accounts
            })
        else:
            return jsonify({
                "success": False,
                "verified": False,
                "error": "API call failed"
            }), 400

    except Exception as e:
        logger.error(f"[APIKeys] Verification error: {e}")

        # Record error
        if 'user_key' in locals():
            user_key.record_error(str(e))
            session.commit()

        return jsonify({"error": str(e), "verified": False}), 500
    finally:
        session.close()


@api_key_bp.route('/delete', methods=['DELETE'])
def delete_api_keys():
    """
    Delete user's API keys

    Request body:
        {
            "user_id": 1
        }

    Returns:
        {
            "success": true,
            "message": "API keys deleted successfully"
        }
    """
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        session = get_db_session()

        # Delete user's API keys
        deleted_count = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id
        ).delete()

        session.commit()

        if deleted_count > 0:
            logger.info(f"[APIKeys] Deleted API keys for user {user_id}")
            return jsonify({
                "success": True,
                "message": "API keys deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "No API keys found to delete"
            }), 404

    except Exception as e:
        logger.error(f"[APIKeys] Error deleting keys: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
