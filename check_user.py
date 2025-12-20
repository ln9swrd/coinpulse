#!/usr/bin/env python
# -*- coding: utf-8 -*-

from backend.database.connection import get_db_session
from backend.database.models import User

session = get_db_session()
user = session.query(User).filter_by(email='test@example.com').first()

if user:
    print(f'User exists: True')
    print(f'Email: {user.email}')
    print(f'Username: {user.username}')
    print(f'Is active: {user.is_active}')
    print(f'Is verified: {user.is_verified}')
    print(f'Has password: {user.password_hash is not None}')
else:
    print('User exists: False')

session.close()
