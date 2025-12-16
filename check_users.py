"""
Check users in PostgreSQL database
"""
from dotenv import load_dotenv
load_dotenv()

from backend.database.connection import get_db_session
from backend.database.models import User

print("="*60)
print("CHECKING USERS IN DATABASE")
print("="*60)

session = get_db_session()
try:
    users = session.query(User).all()

    if users:
        print(f"\n[FOUND] {len(users)} users in database:\n")
        for i, user in enumerate(users, 1):
            print(f"{i}. ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Created: {user.created_at}")
            print()
    else:
        print("\n[EMPTY] No users found in database")

finally:
    session.close()

print("="*60)
