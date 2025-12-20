"""
CoinPulse - Statistics API Routes
실시간 통계 조회 API

주요 기능:
- 사용자 통계
- 거래 통계  
- 활성 봇 통계
- 종합 통계
"""

from flask import Blueprint, jsonify
from sqlalchemy import func, and_, text
from datetime import datetime, timedelta
import logging

from backend.database.connection import get_db_session

logger = logging.getLogger(__name__)

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@stats_bp.route('/summary', methods=['GET'])
def get_stats_summary():
    """
    모든 통계를 한 번에 조회
    
    Returns:
        JSON: 전체 통계 요약
    """
    try:
        with get_db_session() as session:
            # 1. 사용자 통계
            try:
                total_users = session.execute(
                    text("SELECT COUNT(*) FROM users")
                ).scalar()
            except Exception:
                total_users = 0

            try:
                active_users = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE is_active = true")
                ).scalar()
            except Exception:
                active_users = 0

            try:
                verified_users = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE is_verified = true")
                ).scalar()
            except Exception:
                verified_users = 0

            # 2. 거래 통계
            try:
                total_orders = session.execute(
                    text("SELECT COUNT(*) FROM orders")
                ).scalar()
            except Exception:
                total_orders = 0

            try:
                completed_orders = session.execute(
                    text("SELECT COUNT(*) FROM orders WHERE state = 'done'")
                ).scalar()
            except Exception:
                completed_orders = 0

            # 오늘 거래
            try:
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_orders = session.execute(
                    text("SELECT COUNT(*) FROM orders WHERE executed_at >= :today"),
                    {"today": today_start}
                ).scalar()
            except Exception:
                today_orders = 0

            # 3. 자동매매 활동
            try:
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_activities = session.execute(
                    text("SELECT COUNT(*) FROM swing_trading_logs WHERE created_at > :one_hour_ago"),
                    {"one_hour_ago": one_hour_ago}
                ).scalar()
            except Exception:
                recent_activities = 0

            # 활성 사용자 (최근 1시간 활동)
            try:
                one_hour_ago = datetime.now() - timedelta(hours=1)
                active_traders = session.execute(
                    text("SELECT COUNT(DISTINCT user_id) FROM swing_trading_logs WHERE created_at > :one_hour_ago"),
                    {"one_hour_ago": one_hour_ago}
                ).scalar()
            except Exception:
                active_traders = 0

            # 4. 구독 통계
            try:
                active_subscriptions = session.execute(
                    text("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
                ).scalar()
            except Exception:
                # Table doesn't exist yet - return 0
                active_subscriptions = 0

            # 5. 베타 테스터
            try:
                beta_testers = session.execute(
                    text("SELECT COUNT(*) FROM beta_testers WHERE is_active = true")
                ).scalar()
            except Exception:
                beta_testers = 0

            # 6. 거래량 통계 (executed_funds 합계)
            try:
                total_volume = session.execute(
                    text("SELECT COALESCE(SUM(executed_funds), 0) FROM orders WHERE state = 'done'")
                ).scalar()
            except Exception:
                total_volume = 0
            
            return jsonify({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "users": {
                        "total": total_users or 0,
                        "active": active_users or 0,
                        "verified": verified_users or 0
                    },
                    "trading": {
                        "total_orders": total_orders or 0,
                        "completed_orders": completed_orders or 0,
                        "today_orders": today_orders or 0,
                        "total_volume_krw": float(total_volume or 0)
                    },
                    "activity": {
                        "recent_actions": recent_activities or 0,
                        "active_traders": active_traders or 0
                    },
                    "subscriptions": {
                        "active": active_subscriptions or 0
                    },
                    "beta": {
                        "testers": beta_testers or 0
                    }
                }
            }), 200
            
    except Exception as e:
        logger.error(f"[Stats] Summary error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch statistics"
        }), 500


@stats_bp.route('/users', methods=['GET'])
def get_user_stats():
    """사용자 통계"""
    try:
        with get_db_session() as session:
            total = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            active = session.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar()
            verified = session.execute(text("SELECT COUNT(*) FROM users WHERE is_verified = true")).scalar()
            
            # 오늘 가입
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_signups = session.execute(
                text("SELECT COUNT(*) FROM users WHERE created_at >= :today"),
                {"today": today_start}
            ).scalar()
            
            return jsonify({
                "success": True,
                "users": {
                    "total": total or 0,
                    "active": active or 0,
                    "verified": verified or 0,
                    "today_signups": today_signups or 0
                }
            }), 200
            
    except Exception as e:
        logger.error(f"[Stats] User stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@stats_bp.route('/trades', methods=['GET'])
def get_trade_stats():
    """거래 통계"""
    try:
        with get_db_session() as session:
            total = session.execute(text("SELECT COUNT(*) FROM orders")).scalar()
            completed = session.execute(text("SELECT COUNT(*) FROM orders WHERE state = 'done'")).scalar()
            
            # 오늘 거래
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today = session.execute(
                text("SELECT COUNT(*) FROM orders WHERE executed_at >= :today"),
                {"today": today_start}
            ).scalar()
            
            # 거래량
            total_volume = session.execute(
                text("SELECT COALESCE(SUM(executed_funds), 0) FROM orders WHERE state = 'done'")
            ).scalar()
            
            return jsonify({
                "success": True,
                "trades": {
                    "total": total or 0,
                    "completed": completed or 0,
                    "today": today or 0,
                    "volume_krw": float(total_volume or 0)
                }
            }), 200
            
    except Exception as e:
        logger.error(f"[Stats] Trade stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@stats_bp.route('/active', methods=['GET'])
def get_active_stats():
    """활성 통계 (최근 1시간)"""
    try:
        with get_db_session() as session:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            # 최근 활동
            recent_actions = session.execute(
                text("SELECT COUNT(*) FROM swing_trading_logs WHERE created_at > :one_hour_ago"),
                {"one_hour_ago": one_hour_ago}
            ).scalar()
            
            # 활성 트레이더
            active_traders = session.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM swing_trading_logs WHERE created_at > :one_hour_ago"),
                {"one_hour_ago": one_hour_ago}
            ).scalar()
            
            # 활성 구독
            try:
                active_subs = session.execute(
                    text("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
                ).scalar()
            except Exception:
                # Table doesn't exist yet - return 0
                active_subs = 0
            
            return jsonify({
                "success": True,
                "active": {
                    "recent_actions": recent_actions or 0,
                    "active_traders": active_traders or 0,
                    "active_subscriptions": active_subs or 0
                }
            }), 200
            
    except Exception as e:
        logger.error(f"[Stats] Active stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@stats_bp.route('/beta', methods=['GET'])
def get_beta_stats():
    """베타 테스터 통계"""
    try:
        with get_db_session() as session:
            total = session.execute(text("SELECT COUNT(*) FROM beta_testers")).scalar()
            active = session.execute(text("SELECT COUNT(*) FROM beta_testers WHERE is_active = true")).scalar()
            
            return jsonify({
                "success": True,
                "beta": {
                    "total": total or 0,
                    "active": active or 0
                }
            }), 200
            
    except Exception as e:
        logger.error(f"[Stats] Beta stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
