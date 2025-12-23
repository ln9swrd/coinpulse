"""
급등예측 상태 자동 업데이트 서비스

발송 시간으로부터 3일 경과 시점에 목표가/손절가 도달 여부를 확인하여
Win/Lose 상태를 자동으로 업데이트합니다.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import text

from backend.common import UpbitAPI, load_api_keys
from backend.database.connection import get_db_session

logging.basicConfig(
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SurgeStatusUpdater:
    """급등예측 상태 자동 업데이트"""

    def __init__(self):
        """Initialize surge status updater"""
        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # 3 days threshold
        self.check_threshold_days = 3

        logger.info("[SurgeStatusUpdater] Initialized")

    def get_pending_alerts_after_3_days(self) -> List[Dict]:
        """
        Get pending alerts that are 3+ days old

        Returns:
            List of alerts that need status check
        """
        try:
            with get_db_session() as session:
                # Calculate cutoff datetime (3 days ago)
                cutoff_datetime = datetime.now() - timedelta(days=self.check_threshold_days)

                query = text("""
                    SELECT
                        id, market, coin, sent_at,
                        entry_price, target_price, stop_loss_price,
                        confidence, expected_return
                    FROM surge_alerts
                    WHERE status = 'pending'
                      AND sent_at <= :cutoff_datetime
                    ORDER BY sent_at ASC
                """)

                result = session.execute(query, {'cutoff_datetime': cutoff_datetime})
                alerts = [dict(row._mapping) for row in result]

                logger.info(f"[SurgeStatusUpdater] Found {len(alerts)} pending alerts after 3 days")
                return alerts

        except Exception as e:
            logger.error(f"[SurgeStatusUpdater] Error getting pending alerts: {e}")
            return []

    def check_and_update_alert(self, alert: Dict) -> bool:
        """
        Check current price and update alert status

        Args:
            alert: Alert data with entry/target/stop prices

        Returns:
            True if updated, False otherwise
        """
        try:
            market = alert['market']
            entry_price = alert['entry_price']
            target_price = alert['target_price']
            stop_loss_price = alert['stop_loss_price']

            # Get current price from Upbit API
            current_price = self.upbit_api.get_current_price(market)
            if not current_price:
                logger.warning(f"[SurgeStatusUpdater] Could not get price for {market}")
                return False

            # Determine status
            new_status = None
            profit_loss = 0
            profit_loss_percent = 0.0

            if current_price >= target_price:
                # Target reached - WIN
                new_status = 'win'
                profit_loss = int(current_price - entry_price)
                profit_loss_percent = ((current_price - entry_price) / entry_price) * 100

            elif current_price <= stop_loss_price:
                # Stop loss hit - LOSE
                new_status = 'lose'
                profit_loss = int(current_price - entry_price)  # Negative value
                profit_loss_percent = ((current_price - entry_price) / entry_price) * 100

            else:
                # Price between stop loss and target - still pending, check again later
                logger.debug(f"[SurgeStatusUpdater] {market} still pending (price: {current_price:,}원)")
                return False

            # Update database
            with get_db_session() as session:
                update_query = text("""
                    UPDATE surge_alerts
                    SET
                        status = :status,
                        profit_loss = :profit_loss,
                        profit_loss_percent = :profit_loss_percent,
                        closed_at = :closed_at
                    WHERE id = :alert_id
                """)

                params = {
                    'alert_id': alert['id'],
                    'status': new_status,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'closed_at': datetime.now()
                }

                session.execute(update_query, params)
                session.commit()

                logger.info(
                    f"[SurgeStatusUpdater] Updated {market} to '{new_status}' "
                    f"(Entry: {entry_price:,}원 → Current: {current_price:,}원, "
                    f"P/L: {profit_loss:+,}원 {profit_loss_percent:+.2f}%)"
                )

                return True

        except Exception as e:
            logger.error(f"[SurgeStatusUpdater] Error checking alert {alert.get('id')}: {e}")
            return False

    def run_update_cycle(self) -> Dict[str, int]:
        """
        Run one update cycle

        Returns:
            Statistics: {total, updated, win, lose}
        """
        logger.info("[SurgeStatusUpdater] Starting update cycle...")

        # Get pending alerts after 3 days
        pending_alerts = self.get_pending_alerts_after_3_days()

        if not pending_alerts:
            logger.info("[SurgeStatusUpdater] No alerts to check")
            return {'total': 0, 'updated': 0, 'win': 0, 'lose': 0}

        # Check and update each alert
        stats = {'total': len(pending_alerts), 'updated': 0, 'win': 0, 'lose': 0}

        for alert in pending_alerts:
            try:
                # Get current status before update
                updated = self.check_and_update_alert(alert)

                if updated:
                    stats['updated'] += 1

                    # Check new status to update stats
                    with get_db_session() as session:
                        status_query = text("SELECT status FROM surge_alerts WHERE id = :alert_id")
                        result = session.execute(status_query, {'alert_id': alert['id']}).scalar()

                        if result == 'win':
                            stats['win'] += 1
                        elif result == 'lose':
                            stats['lose'] += 1

                # Rate limit: avoid Upbit API throttling
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"[SurgeStatusUpdater] Error processing alert {alert['id']}: {e}")
                continue

        logger.info(
            f"[SurgeStatusUpdater] Cycle complete - "
            f"Total: {stats['total']}, Updated: {stats['updated']}, "
            f"Win: {stats['win']}, Lose: {stats['lose']}"
        )

        return stats

    def run_scheduler(self, interval_hours: int = 1):
        """
        Run scheduler loop - checks every N hours

        Args:
            interval_hours: Check interval in hours (default: 1 hour)
        """
        logger.info(f"[SurgeStatusUpdater] Starting scheduler (interval: {interval_hours} hour(s))...")

        while True:
            try:
                # Run update cycle
                self.run_update_cycle()

                # Wait for next cycle
                wait_seconds = interval_hours * 3600
                logger.info(f"[SurgeStatusUpdater] Waiting {interval_hours} hour(s) until next check...")
                time.sleep(wait_seconds)

            except KeyboardInterrupt:
                logger.info("[SurgeStatusUpdater] Stopped by user")
                break
            except Exception as e:
                logger.error(f"[SurgeStatusUpdater] Error in scheduler: {e}")
                # Wait 5 minutes before retry on error
                time.sleep(300)


def main():
    """Main entry point for standalone execution"""
    print("\n" + "="*60)
    print("CoinPulse 급등예측 상태 자동 업데이트 시스템")
    print("="*60 + "\n")
    print("발송 시간으로부터 3일 경과 시점에 자동으로 Win/Lose 판정")
    print("- Win: 목표가 도달")
    print("- Lose: 손절가 도달")
    print("\n" + "="*60 + "\n")

    # Initialize updater
    updater = SurgeStatusUpdater()

    # Run once immediately
    print("[INFO] Running initial update cycle...")
    stats = updater.run_update_cycle()
    print(f"[INFO] Initial cycle complete: {stats}")

    # Ask user if they want to run scheduler
    print("\n스케줄러를 실행하시겠습니까? (1시간마다 자동 체크)")
    print("Enter 'y' to run scheduler, or any other key to exit:")
    choice = input().strip().lower()

    if choice == 'y':
        updater.run_scheduler(interval_hours=1)
    else:
        print("[INFO] Exiting...")


if __name__ == "__main__":
    main()
