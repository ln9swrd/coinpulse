# -*- coding: utf-8 -*-
"""
Trading Signal Models
자동매매 시그널 및 사용자 시그널 히스토리 모델
"""

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import enum

Base = declarative_base()


class SignalType(enum.Enum):
    """시그널 타입"""
    BUY = "buy"
    SELL = "sell"


class SignalStatus(enum.Enum):
    """시그널 상태"""
    PENDING = "pending"      # 대기 중
    ACTIVE = "active"        # 활성 (유효 기간 내)
    EXPIRED = "expired"      # 만료됨
    CANCELLED = "cancelled"  # 취소됨


class ExecutionStatus(enum.Enum):
    """실행 상태"""
    NOT_EXECUTED = "not_executed"  # 미실행
    EXECUTED = "executed"          # 실행됨
    FAILED = "failed"              # 실행 실패
    PENDING = "pending"            # 대기 중


class TradingSignal(Base):
    """
    자동매매 시그널 (중앙에서 생성, 사용자에게 배포)
    """
    __tablename__ = 'auto_trading_signals'

    id = Column(Integer, primary_key=True)
    signal_id = Column(String(50), unique=True, nullable=False)  # 고유 ID

    # 마켓 정보
    market = Column(String(20), nullable=False)  # 예: KRW-BTC
    signal_type = Column(SQLEnum(SignalType), nullable=False)  # BUY or SELL

    # 가격 정보 (핵심!)
    entry_price = Column(BigInteger, nullable=False)   # 진입가 (원)
    target_price = Column(BigInteger, nullable=False)  # 목표가 (원)
    stop_loss = Column(BigInteger, nullable=False)     # 손절가 (원)

    # 메타 정보
    confidence = Column(Integer, nullable=False)  # 신뢰도 (0-100)
    reason = Column(Text, nullable=True)          # 시그널 발생 이유
    signals_data = Column(JSON, nullable=True)    # 추가 시그널 데이터

    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=False)  # 유효 기간
    status = Column(SQLEnum(SignalStatus), default=SignalStatus.PENDING)

    # 통계
    distributed_to = Column(Integer, default=0)   # 몇 명에게 배포되었는지
    executed_count = Column(Integer, default=0)   # 몇 명이 실행했는지

    # 인덱스
    __table_args__ = (
        Index('idx_auto_trading_signals_market', 'market'),
        Index('idx_auto_trading_signals_created_at', 'created_at'),
        Index('idx_auto_trading_signals_status', 'status'),
    )

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'signal_id': self.signal_id,
            'market': self.market,
            'signal_type': self.signal_type.value if self.signal_type else None,

            # 가격 정보
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'expected_return': self.get_expected_return(),

            # 메타 정보
            'confidence': self.confidence,
            'reason': self.reason,
            'signals_data': self.signals_data,

            # 시간 정보
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status.value if self.status else None,
            'is_expired': self.is_expired(),

            # 통계
            'distributed_to': self.distributed_to,
            'executed_count': self.executed_count,
            'execution_rate': self.get_execution_rate()
        }

    def get_expected_return(self):
        """예상 수익률 계산 (%)"""
        if not self.entry_price or not self.target_price:
            return 0
        return ((self.target_price - self.entry_price) / self.entry_price) * 100

    def get_stop_loss_ratio(self):
        """손절 비율 계산 (%)"""
        if not self.entry_price or not self.stop_loss:
            return 0
        return ((self.stop_loss - self.entry_price) / self.entry_price) * 100

    def is_expired(self):
        """만료되었는지 확인"""
        if not self.valid_until:
            return True
        return datetime.utcnow() > self.valid_until

    def get_execution_rate(self):
        """실행률 계산 (%)"""
        if self.distributed_to == 0:
            return 0
        return (self.executed_count / self.distributed_to) * 100


class UserSignalHistory(Base):
    """
    사용자 시그널 히스토리
    """
    __tablename__ = 'user_signal_history'

    id = Column(Integer, primary_key=True)

    # 외래 키
    user_id = Column(Integer, nullable=False)
    signal_id = Column(Integer, ForeignKey('auto_trading_signals.id'), nullable=False)

    # 수신 정보
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_bonus = Column(Boolean, default=False)  # 보너스 알림인지

    # 실행 정보
    execution_status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.NOT_EXECUTED)
    executed_at = Column(DateTime, nullable=True)
    order_id = Column(String(50), nullable=True)  # Upbit 주문 ID
    execution_price = Column(BigInteger, nullable=True)  # 실제 체결 가격

    # 결과 정보
    result_status = Column(String(20), nullable=True)  # 'profit', 'loss', 'pending', 'cancelled'
    profit_loss = Column(BigInteger, nullable=True)    # 수익/손실 금액 (원)
    profit_loss_ratio = Column(Integer, nullable=True)  # 수익/손실률 (%)

    # 메모
    notes = Column(Text, nullable=True)

    # 인덱스
    __table_args__ = (
        Index('idx_user_signal_history_user_id', 'user_id'),
        Index('idx_user_signal_history_signal_id', 'signal_id'),
        Index('idx_user_signal_history_received_at', 'received_at'),
        Index('idx_user_signal_history_execution', 'execution_status'),
    )

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'signal_id': self.signal_id,

            # 수신 정보
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'is_bonus': self.is_bonus,

            # 실행 정보
            'execution_status': self.execution_status.value if self.execution_status else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'order_id': self.order_id,
            'execution_price': self.execution_price,

            # 결과 정보
            'result_status': self.result_status,
            'profit_loss': self.profit_loss,
            'profit_loss_ratio': self.profit_loss_ratio,

            # 메모
            'notes': self.notes
        }


# 초기화 함수
def init_db(engine):
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(engine)
    print("[TradingSignal] Database tables created")


if __name__ == "__main__":
    print("Trading Signal Models")
    print("=" * 60)

    # 예시 데이터
    signal = TradingSignal(
        signal_id="SIGNAL-20251220-001",
        market="KRW-BTC",
        signal_type=SignalType.BUY,
        entry_price=52000000,
        target_price=54000000,
        stop_loss=50000000,
        confidence=81,
        reason="급등 예측 (81.25% 정확도)",
        valid_until=datetime.utcnow() + timedelta(minutes=5)
    )

    print("\nExample Signal:")
    print(f"  Market: {signal.market}")
    print(f"  Entry: ₩{signal.entry_price:,}")
    print(f"  Target: ₩{signal.target_price:,} (+{signal.get_expected_return():.2f}%)")
    print(f"  Stop Loss: ₩{signal.stop_loss:,} ({signal.get_stop_loss_ratio():.2f}%)")
    print(f"  Confidence: {signal.confidence}%")
