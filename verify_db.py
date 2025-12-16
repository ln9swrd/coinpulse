"""
Quick database verification script
"""
from backend.database import get_db_session, Order, SyncStatus
from sqlalchemy import func

db = get_db_session()

# Count total orders
total_orders = db.query(func.count(Order.uuid)).scalar()
print(f"\n[DB] Total orders in database: {total_orders}")

# Get first 5 orders
orders = db.query(Order).order_by(Order.executed_at.desc()).limit(5).all()
print(f"\n[DB] Latest 5 orders:")
for order in orders:
    print(f"  - {order.market} {order.side} {order.executed_volume} @ {order.avg_price} ({order.executed_at})")

# Check sync status
sync_status = db.query(SyncStatus).all()
print(f"\n[DB] Sync status records: {len(sync_status)}")
for status in sync_status:
    print(f"  - {status.market}: {status.total_orders} orders, last sync: {status.last_sync}")

# Check by market
market_counts = db.query(Order.market, func.count(Order.uuid)).group_by(Order.market).all()
print(f"\n[DB] Orders by market:")
for market, count in sorted(market_counts, key=lambda x: x[1], reverse=True)[:10]:
    print(f"  - {market}: {count} orders")

db.close()
print("\n[DB] Verification complete!")
