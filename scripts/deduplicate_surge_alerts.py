#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deduplicate Surge Alerts Script

연속된 급등 알림을 하나로 통합합니다.
- 같은 마켓의 연속된 알림을 24시간 단위로 그룹화
- 가장 최근 알림만 유지하고 나머지 삭제
"""

from backend.database.connection import get_db_session
from sqlalchemy import text
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def deduplicate_alerts(market=None, hours_threshold=24, dry_run=True):
    """
    Deduplicate surge alerts

    Args:
        market: Market to deduplicate (None = all markets)
        hours_threshold: Time window in hours to consider as duplicates
        dry_run: If True, only show what would be deleted without actually deleting
    """
    try:
        with get_db_session() as session:
            # Get all alerts ordered by market and sent_at
            where_clause = f"WHERE market = '{market}'" if market else ""

            query = text(f"""
                SELECT id, market, sent_at, confidence, status, telegram_sent
                FROM surge_alerts
                {where_clause}
                ORDER BY market, sent_at DESC
            """)

            result = session.execute(query)
            alerts = list(result)

            if not alerts:
                logger.info("No alerts found")
                return

            # Group alerts by market and find duplicates
            duplicates_to_delete = []
            current_market = None
            last_kept_alert = None

            for alert in alerts:
                alert_dict = dict(alert._mapping)

                # New market or first alert
                if current_market != alert_dict['market']:
                    current_market = alert_dict['market']
                    last_kept_alert = alert_dict
                    logger.info(f"\n[{current_market}] Keeping alert ID {alert_dict['id']} (most recent)")
                    continue

                # Check if this alert is within threshold of last kept alert
                time_diff = last_kept_alert['sent_at'] - alert_dict['sent_at']

                if time_diff < timedelta(hours=hours_threshold):
                    # This is a duplicate
                    duplicates_to_delete.append(alert_dict['id'])
                    logger.info(f"  → Marking ID {alert_dict['id']} for deletion (sent {time_diff} after kept alert)")
                else:
                    # Keep this alert (it's far enough from the last one)
                    last_kept_alert = alert_dict
                    logger.info(f"\n[{current_market}] Keeping alert ID {alert_dict['id']} (gap: {time_diff})")

            # Summary
            logger.info(f"\n{'='*80}")
            logger.info(f"Summary:")
            logger.info(f"  Total alerts: {len(alerts)}")
            logger.info(f"  Duplicates to delete: {len(duplicates_to_delete)}")
            logger.info(f"  Alerts to keep: {len(alerts) - len(duplicates_to_delete)}")

            if duplicates_to_delete:
                logger.info(f"\nDuplicate IDs: {duplicates_to_delete}")

            # Delete duplicates
            if not dry_run and duplicates_to_delete:
                delete_query = text("""
                    DELETE FROM surge_alerts
                    WHERE id = ANY(:ids)
                """)

                session.execute(delete_query, {'ids': duplicates_to_delete})
                session.commit()
                logger.info(f"\n✅ Deleted {len(duplicates_to_delete)} duplicate alerts")
            elif dry_run and duplicates_to_delete:
                logger.info(f"\n⚠️  DRY RUN: Would delete {len(duplicates_to_delete)} alerts")
                logger.info("Run with dry_run=False to actually delete")
            else:
                logger.info("\n✅ No duplicates to delete")

    except Exception as e:
        logger.error(f"Error deduplicating alerts: {e}")
        raise


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Deduplicate surge alerts')
    parser.add_argument('--market', type=str, help='Market to deduplicate (e.g., KRW-AAVE)')
    parser.add_argument('--hours', type=int, default=24, help='Time threshold in hours (default: 24)')
    parser.add_argument('--execute', action='store_true', help='Actually delete duplicates (default: dry run)')

    args = parser.parse_args()

    logger.info(f"{'='*80}")
    logger.info(f"Surge Alert Deduplication")
    logger.info(f"{'='*80}")
    logger.info(f"Market: {args.market or 'All markets'}")
    logger.info(f"Time threshold: {args.hours} hours")
    logger.info(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    logger.info(f"{'='*80}\n")

    deduplicate_alerts(
        market=args.market,
        hours_threshold=args.hours,
        dry_run=not args.execute
    )
