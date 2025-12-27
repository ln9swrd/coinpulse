# -*- coding: utf-8 -*-
"""
Surge System Settings Model
관리자가 관리하는 급등 감지 시스템 설정
"""
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from backend.database.models import Base
import json


class SurgeSystemSettings(Base):
    """
    급등 감지 시스템 설정 (관리자 전용)

    단일 레코드로 관리 (id=1)
    """
    __tablename__ = 'surge_system_settings'

    id = Column(Integer, primary_key=True, default=1)

    # ===== 신호 감지 기준 =====
    base_min_score = Column(Integer, default=60, nullable=False)
    """시스템 최소 점수 (Worker가 스캔할 최소 점수)"""

    telegram_min_score = Column(Integer, default=70, nullable=False)
    """텔레그램 알림 최소 점수 (고품질 신호만 알림)"""

    db_save_threshold = Column(Integer, default=60, nullable=False)
    """DB 저장 기준 점수 (이 점수 이상만 surge_alerts에 저장)"""

    # ===== 워커 설정 =====
    check_interval = Column(Integer, default=300, nullable=False)
    """체크 주기 (초) - 기본 5분"""

    monitor_coins_count = Column(Integer, default=50, nullable=False)
    """모니터링할 코인 수"""

    duplicate_alert_hours = Column(Integer, default=24, nullable=False)
    """중복 알림 방지 시간 (시간)"""

    # ===== 분석 파라미터 (JSON) =====
    analysis_config = Column(Text, nullable=False, default='{}')
    """
    분석 파라미터 (JSON):
    {
        "volume_increase_threshold": 1.5,
        "rsi_oversold_level": 35,
        "rsi_buy_zone_max": 50,
        "support_level_proximity": 0.02,
        "uptrend_confirmation_days": 3
    }
    """

    # ===== 활성화 플래그 =====
    worker_enabled = Column(Boolean, default=True, nullable=False)
    """Worker 활성화 여부"""

    scheduler_enabled = Column(Boolean, default=True, nullable=False)
    """Scheduler (텔레그램 알림) 활성화 여부"""

    # ===== 메타 정보 =====
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(100), nullable=True)
    """마지막 수정자 (관리자 이메일)"""

    notes = Column(Text, nullable=True)
    """관리자 메모"""

    def get_analysis_config(self):
        """분석 설정을 dict로 반환"""
        try:
            return json.loads(self.analysis_config) if self.analysis_config else {}
        except:
            return {}

    def set_analysis_config(self, config_dict):
        """분석 설정을 JSON으로 저장"""
        self.analysis_config = json.dumps(config_dict, ensure_ascii=False)

    def to_dict(self):
        """Dict 변환"""
        return {
            'id': self.id,
            'base_min_score': self.base_min_score,
            'telegram_min_score': self.telegram_min_score,
            'db_save_threshold': self.db_save_threshold,
            'check_interval': self.check_interval,
            'monitor_coins_count': self.monitor_coins_count,
            'duplicate_alert_hours': self.duplicate_alert_hours,
            'analysis_config': self.get_analysis_config(),
            'worker_enabled': self.worker_enabled,
            'scheduler_enabled': self.scheduler_enabled,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'notes': self.notes
        }

    @staticmethod
    def get_default_analysis_config():
        """기본 분석 설정"""
        return {
            "volume_increase_threshold": 1.5,
            "rsi_oversold_level": 35,
            "rsi_buy_zone_max": 50,
            "support_level_proximity": 0.02,
            "uptrend_confirmation_days": 3,
            "min_surge_probability_score": 60
        }


# 초기 데이터 생성 스크립트
if __name__ == "__main__":
    from backend.database.connection import get_db_session

    print("Creating surge_system_settings table and default record...")

    with get_db_session() as session:
        # Check if record exists
        existing = session.query(SurgeSystemSettings).filter_by(id=1).first()

        if existing:
            print("✓ Settings already exist")
            print(f"  Base min score: {existing.base_min_score}")
            print(f"  Telegram min score: {existing.telegram_min_score}")
        else:
            # Create default settings
            settings = SurgeSystemSettings(
                id=1,
                base_min_score=60,
                telegram_min_score=70,
                db_save_threshold=60,
                check_interval=300,
                monitor_coins_count=50,
                duplicate_alert_hours=24,
                worker_enabled=True,
                scheduler_enabled=True,
                updated_by='system',
                notes='Initial system settings'
            )
            settings.set_analysis_config(SurgeSystemSettings.get_default_analysis_config())

            session.add(settings)
            session.commit()

            print("✓ Default settings created")
            print(f"  Base min score: {settings.base_min_score}")
            print(f"  Telegram min score: {settings.telegram_min_score}")
            print(f"  Analysis config: {settings.get_analysis_config()}")
