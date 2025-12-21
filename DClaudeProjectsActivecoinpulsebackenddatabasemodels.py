
class TelegramLinkCode(Base):
    """
    Telegram Link Code model for account linking.

    Manages temporary codes for linking Telegram accounts to user accounts.
    """
    __tablename__ = 'telegram_link_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    code = Column(String(6), unique=True, nullable=False, index=True, comment='6-digit linking code')
    telegram_chat_id = Column(String(50), nullable=True, comment='Telegram chat ID (set when /link is used)')
    telegram_username = Column(String(100), nullable=True, comment='Telegram username')
    expires_at = Column(DateTime, nullable=False, comment='Code expiration (15 minutes)')
    used = Column(Boolean, default=False, comment='Code usage status')
    used_at = Column(DateTime, nullable=True, comment='Code usage timestamp')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Code creation time')

    def __repr__(self):
        return f"<TelegramLinkCode(id={self.id}, user_id={self.user_id}, code='{self.code}', used={self.used})>"
