#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retry Auto-Trade for Pending Surge Alerts
버그로 인해 자동매매가 실행되지 않은 pending 신호를 재처리
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from backend.models.surge_alert_models import SurgeAlert, SurgeAutoTradingSettings
from backend.services.surge_alert_service import SurgeAlertService
from backend.models.plan_features import get_user_features
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_user_plan(session, user_id: int) -> str:
    """Get user's plan"""
    try:
        query = text("SELECT plan FROM user_subscriptions WHERE user_id = :user_id ORDER BY end_date DESC LIMIT 1")
        result = session.execute(query, {"user_id": user_id}).fetchone()

        if result:
            return result[0]
        else:
            # Default to free plan
            return 'free'
    except Exception as e:
        logger.error(f"Error getting plan for user {user_id}: {e}")
        return 'free'


def retry_pending_autotrade(alert_id: int = None, user_id: int = None):
    """
    Retry auto-trade for pending surge alerts

    Args:
        alert_id: Specific alert ID to retry (optional)
        user_id: Retry all pending alerts for specific user (optional)
    """
    session = get_db_session()
    surge_service = SurgeAlertService(session)

    try:
        # Build query
        query = session.query(SurgeAlert).filter(
            SurgeAlert.status == 'pending',
            SurgeAlert.auto_traded == False,
            SurgeAlert.sent_at >= datetime.utcnow() - timedelta(hours=24)  # Only last 24h
        )

        if alert_id:
            query = query.filter(SurgeAlert.id == alert_id)

        if user_id:
            query = query.filter(SurgeAlert.user_id == user_id)

        pending_alerts = query.all()

        logger.info(f"Found {len(pending_alerts)} pending alerts to retry")

        success_count = 0
        failed_count = 0

        for alert in pending_alerts:
            logger.info(f"Processing alert {alert.id}: User {alert.user_id}, {alert.market}, Confidence {alert.confidence}%")

            try:
                # Get user's plan
                plan = get_user_plan(session, alert.user_id)
                logger.info(f"  User {alert.user_id} plan: {plan}")

                # Get user's auto-trading settings
                settings = surge_service.get_user_settings(alert.user_id)

                if not settings:
                    logger.warning(f"  No auto-trading settings for user {alert.user_id}")
                    failed_count += 1
                    continue

                if not settings.enabled:
                    logger.warning(f"  Auto-trading disabled for user {alert.user_id}")
                    failed_count += 1
                    continue

                # Check if can auto-trade (with fixed unlimited check)
                can_trade, reason = surge_service.can_auto_trade(
                    user_id=alert.user_id,
                    plan=plan,
                    settings=settings,
                    confidence=alert.confidence,
                    coin=alert.coin
                )

                if not can_trade:
                    logger.warning(f"  Cannot auto-trade: {reason}")
                    failed_count += 1
                    continue

                # Execute auto-trade
                logger.info(f"  Executing auto-trade for {alert.market}...")
                success, trade_info = surge_service.execute_auto_trade(
                    user_id=alert.user_id,
                    settings=settings,
                    market=alert.market,
                    coin=alert.coin,
                    entry_price=int(alert.entry_price),
                    target_price=int(alert.target_price) if alert.target_price else None,
                    stop_loss_price=int(alert.stop_loss_price) if alert.stop_loss_price else None,
                    use_prediction_prices=True
                )

                if success:
                    # Update alert
                    alert.auto_traded = True
                    alert.trade_amount = trade_info.get('amount')
                    alert.trade_quantity = trade_info.get('quantity')
                    alert.order_id = trade_info.get('order_id')
                    alert.executed_at = datetime.utcnow()
                    alert.status = 'active'

                    session.commit()

                    logger.info(f"  ✅ Success! Order ID: {trade_info.get('order_id')}")
                    logger.info(f"     Amount: {trade_info.get('amount'):,} KRW")
                    logger.info(f"     Quantity: {trade_info.get('quantity'):.8f}")
                    success_count += 1
                else:
                    logger.error(f"  ❌ Failed to execute auto-trade")
                    failed_count += 1

            except Exception as e:
                logger.error(f"  ❌ Error processing alert {alert.id}: {e}")
                failed_count += 1
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Retry completed:")
        logger.info(f"  ✅ Success: {success_count}")
        logger.info(f"  ❌ Failed: {failed_count}")
        logger.info(f"  📊 Total: {len(pending_alerts)}")
        logger.info(f"{'='*60}")

    except Exception as e:
        logger.error(f"Error in retry_pending_autotrade: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Retry auto-trade for pending surge alerts')
    parser.add_argument('--alert-id', type=int, help='Specific alert ID to retry')
    parser.add_argument('--user-id', type=int, help='Retry all pending alerts for specific user')
    parser.add_argument('--all', action='store_true', help='Retry all pending alerts')

    args = parser.parse_args()

    if args.alert_id:
        logger.info(f"Retrying alert ID: {args.alert_id}")
        retry_pending_autotrade(alert_id=args.alert_id)
    elif args.user_id:
        logger.info(f"Retrying all pending alerts for user ID: {args.user_id}")
        retry_pending_autotrade(user_id=args.user_id)
    elif args.all:
        logger.info("Retrying all pending alerts")
        retry_pending_autotrade()
    else:
        parser.print_help()
        sys.exit(1)
