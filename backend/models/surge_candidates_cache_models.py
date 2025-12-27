# -*- coding: utf-8 -*-
"""
Surge Candidates Cache Models
급등 후보 캐시 모델

Background scheduler가 분석한 결과를 저장하여
프론트엔드 API에서 즉시 조회 가능하도록 함 (API 호출 0회)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index, Numeric
from datetime import datetime
from backend.database.connection import Base


class SurgeCandidatesCache(Base):
    """
    Surge Candidates Cache
    급등 후보 캐시

    surge_alert_scheduler가 5분마다 분석한 결과를 저장
    /api/surge-candidates에서 이 테이블을 조회하여 응답 (API 호출 0회)
    """
    __tablename__ = 'surge_candidates_cache'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Market info
    market = Column(String(20), nullable=False, unique=True, index=True)  # e.g., 'KRW-BTC'
    coin = Column(String(10), nullable=False)  # e.g., 'BTC'

    # Analysis results
    score = Column(Integer, nullable=False)  # 0-100
    current_price = Column(Numeric(20, 10), nullable=False)  # in KRW (supports decimals for low-price coins)
    recommendation = Column(String(20), nullable=False)  # 'strong_buy', 'buy', 'hold', 'pass'

    # Detailed signals (JSON)
    signals = Column(JSON, nullable=True)  # { volume: {...}, rsi: {...}, support: {...}, ... }

    # Full analysis result for target price calculation
    analysis_result = Column(JSON, nullable=True)  # Complete analysis data

    # Timestamps
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)  # When analyzed
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_surge_cache_market', 'market'),
        Index('idx_surge_cache_score', 'score'),
        Index('idx_surge_cache_analyzed_at', 'analyzed_at'),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'market': self.market,
            'coin': self.coin,
            'score': self.score,
            'current_price': self.current_price,
            'recommendation': self.recommendation,
            'signals': self.signals,
            'analysis_result': self.analysis_result,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<SurgeCandidatesCache(market={self.market}, score={self.score}, analyzed_at={self.analyzed_at})>"


def init_db(engine):
    """Create database tables"""
    Base.metadata.create_all(engine)
    print("[SurgeCandidatesCache] Database table created: surge_candidates_cache")


if __name__ == "__main__":
    print("Surge Candidates Cache Models v1.0")
    print("=" * 60)

    print("\n1. Table: surge_candidates_cache")
    print("   - Stores latest analysis results from scheduler")
    print("   - Updated every 5 minutes")
    print("   - Used by /api/surge-candidates (0 API calls)")

    print("\n2. Key Features:")
    print("   - Unique market constraint (no duplicates)")
    print("   - JSON fields for detailed signals")
    print("   - Fast indexed queries")
    print("   - Cache-first architecture")

    print("\n✅ Model defined successfully (v1.0)")
