# -*- coding: utf-8 -*-
"""
Backtest Results Models
백테스트 검증 결과 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, Index
from datetime import datetime
from backend.database.connection import Base


class BacktestResult(Base):
    """
    백테스트 거래 결과

    급등 예측 알고리즘의 백테스트 검증 결과를 저장
    """
    __tablename__ = 'backtest_results'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Trade info
    market = Column(String(20), nullable=False, index=True)  # 'KRW-BTC'
    coin = Column(String(10), nullable=False)  # 'BTC'
    trade_date = Column(Date, nullable=False, index=True)  # 거래 일자

    # Prediction info
    confidence_score = Column(Integer, nullable=False)  # 예측 신뢰도 (0-100)
    prediction_signals = Column(Text, nullable=True)  # JSON string of signals

    # Price info
    entry_price = Column(Float, nullable=False)  # 진입가
    target_price = Column(Float, nullable=True)  # 목표가
    stop_loss_price = Column(Float, nullable=True)  # 손절가

    # Actual results
    actual_high = Column(Float, nullable=True)  # 실제 최고가
    actual_low = Column(Float, nullable=True)  # 실제 최저가
    exit_price = Column(Float, nullable=True)  # 실제 청산가

    # Performance
    return_pct = Column(Float, nullable=False)  # 수익률 (%)
    hold_days = Column(Integer, nullable=True)  # 보유 기간 (일)
    success = Column(Boolean, nullable=False)  # 성공 여부 (목표 달성)

    # Analysis
    reason = Column(Text, nullable=True)  # 예측 근거
    notes = Column(Text, nullable=True)  # 추가 메모

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_backtest_market_date', 'market', 'trade_date'),
        Index('idx_backtest_success', 'success'),
        Index('idx_backtest_score', 'confidence_score'),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'market': self.market,
            'coin': self.coin,
            'date': self.trade_date.isoformat() if self.trade_date else None,
            'confidence_score': self.confidence_score,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss_price': self.stop_loss_price,
            'actual_high': self.actual_high,
            'actual_low': self.actual_low,
            'exit_price': self.exit_price,
            'return_pct': self.return_pct,
            'hold_days': self.hold_days,
            'success': self.success,
            'reason': self.reason,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<BacktestResult(market={self.market}, date={self.trade_date}, return={self.return_pct}%, success={self.success})>"


class BacktestSummary(Base):
    """
    백테스트 요약 통계

    전체 백테스트 기간의 통계 요약
    """
    __tablename__ = 'backtest_summaries'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Summary stats
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)

    win_rate = Column(Float, nullable=False)  # % (0-100)
    avg_return = Column(Float, nullable=False)  # Average return %
    avg_win = Column(Float, nullable=False)  # Average winning trade %
    avg_loss = Column(Float, nullable=False)  # Average losing trade %

    best_trade = Column(Float, nullable=True)  # Best return %
    worst_trade = Column(Float, nullable=True)  # Worst return %

    # Metadata
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)  # Algorithm version
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'period': f"{self.start_date.isoformat()} ~ {self.end_date.isoformat()}" if self.start_date and self.end_date else None,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_return': self.avg_return,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<BacktestSummary(period={self.start_date}~{self.end_date}, win_rate={self.win_rate}%)>"


# 초기화 함수
def init_db(engine):
    """Create database tables"""
    # Only create backtest tables
    BacktestResult.__table__.create(engine, checkfirst=True)
    BacktestSummary.__table__.create(engine, checkfirst=True)
    print("[Backtest] Database tables created: backtest_results, backtest_summaries")


if __name__ == "__main__":
    print("Backtest Results Models")
    print("=" * 60)

    # Example
    result = BacktestResult(
        market='KRW-DOGE',
        coin='DOGE',
        trade_date=datetime(2024, 12, 7).date(),
        confidence_score=85,
        entry_price=180,
        target_price=198,
        stop_loss_price=171,
        actual_high=214,
        return_pct=18.89,
        hold_days=1,
        success=True,
        reason='Strong volume surge + RSI oversold'
    )

    print(f"Market: {result.market}")
    print(f"Date: {result.trade_date}")
    print(f"Score: {result.confidence_score}")
    print(f"Return: {result.return_pct}%")
    print(f"Success: {result.success}")

    print("\n✅ Models defined successfully")
