# -*- coding: utf-8 -*-
"""
Signal Generation Service
급등 예측 결과를 자동매매 시그널로 변환
"""

from datetime import datetime, timedelta
import uuid
from sqlalchemy import func
from backend.database.connection import get_db_session
from backend.models.trading_signal import TradingSignal, SignalType, SignalStatus
from backend.services.signal_distribution_service import SignalDistributor


class SignalGenerator:
    """
    시그널 생성 서비스

    급등 예측 분석 결과를 받아서:
    1. 고신뢰도 시그널만 필터링 (score >= 80)
    2. 진입가, 목표가, 손절가 계산
    3. TradingSignal 생성 및 저장
    4. SignalDistributor를 통해 사용자에게 자동 분배
    """

    # 설정
    MIN_CONFIDENCE_SCORE = 80  # 최소 신뢰도 (80% 이상만)
    SIGNAL_VALID_HOURS = 4     # 시그널 유효 시간 (4시간)

    # 가격 계산 비율
    TARGET_PROFIT_RATIO = 0.05     # 목표 수익률: 5%
    STOP_LOSS_RATIO = -0.02        # 손절 비율: -2%

    def __init__(self, telegram_bot=None):
        self.distributor = SignalDistributor(telegram_bot=telegram_bot)

    def generate_signal_from_surge(self, market, surge_analysis, current_price):
        """
        급등 예측 분석 결과를 시그널로 변환

        Args:
            market (str): 마켓 코드 (예: KRW-BTC)
            surge_analysis (dict): SurgePredictor.analyze_coin() 결과
            current_price (float): 현재 가격

        Returns:
            dict: {
                'success': bool,
                'signal': TradingSignal or None,
                'distributed_to': int,
                'message': str
            }
        """
        try:
            # 1. 신뢰도 확인
            score = surge_analysis.get('score', 0)
            if score < self.MIN_CONFIDENCE_SCORE:
                return {
                    'success': False,
                    'signal': None,
                    'distributed_to': 0,
                    'message': f"Low confidence ({score}). Min required: {self.MIN_CONFIDENCE_SCORE}"
                }

            # 2. 가격 계산
            entry_price = int(current_price)
            target_price = int(current_price * (1 + self.TARGET_PROFIT_RATIO))
            stop_loss = int(current_price * (1 + self.STOP_LOSS_RATIO))

            # 3. 시그널 생성 이유 작성
            signals = surge_analysis.get('signals', {})
            reason = self._build_signal_reason(signals, score)

            # 4. 유효 기간 설정
            valid_until = datetime.utcnow() + timedelta(hours=self.SIGNAL_VALID_HOURS)

            # 5. 고유 ID 생성
            signal_id = self._generate_signal_id(market)

            # 6. TradingSignal 생성
            signal = TradingSignal(
                signal_id=signal_id,
                market=market,
                signal_type=SignalType.BUY,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                confidence=score,
                reason=reason,
                signals_data=signals,
                created_at=datetime.utcnow(),
                valid_until=valid_until,
                status=SignalStatus.PENDING
            )

            # 7. 데이터베이스 저장
            session = get_db_session()
            try:
                session.add(signal)
                session.commit()
                signal_db_id = signal.id

                print(f"[SignalGenerator] Signal created: {signal_id}")
                print(f"  Market: {market}")
                print(f"  Score: {score}%")
                print(f"  Entry: KRW {entry_price:,}")
                print(f"  Target: KRW {target_price:,} (+{self.TARGET_PROFIT_RATIO*100:.1f}%)")
                print(f"  Stop Loss: KRW {stop_loss:,} ({self.STOP_LOSS_RATIO*100:.1f}%)")
                print(f"  Valid until: {valid_until.strftime('%Y-%m-%d %H:%M')}")

                # 8. 자동 분배
                distribution_result = self.distributor.distribute_signal(signal_db_id)

                return {
                    'success': True,
                    'signal': signal,
                    'distributed_to': distribution_result['distributed_count'],
                    'message': f"Signal created and distributed to {distribution_result['distributed_count']} users"
                }

            except Exception as e:
                session.rollback()
                return {
                    'success': False,
                    'signal': None,
                    'distributed_to': 0,
                    'message': f"Database error: {str(e)}"
                }
            finally:
                session.close()

        except Exception as e:
            return {
                'success': False,
                'signal': None,
                'distributed_to': 0,
                'message': f"Error: {str(e)}"
            }

    def _build_signal_reason(self, signals, score):
        """
        시그널 발생 이유 텍스트 생성

        Args:
            signals (dict): 시그널 데이터
            score (int): 신뢰도

        Returns:
            str: 이유 텍스트
        """
        reasons = []

        # 거래량 증가
        volume = signals.get('volume', {})
        if volume.get('increased'):
            ratio = volume.get('increase_ratio', 0)
            reasons.append(f"거래량 {ratio:.1f}배 증가")

        # RSI 과매도
        rsi = signals.get('rsi', {})
        if rsi.get('oversold'):
            value = rsi.get('value', 0)
            reasons.append(f"RSI 과매도 ({value:.1f})")

        # 지지선 근접
        support = signals.get('support', {})
        if support.get('near_support'):
            distance = support.get('distance_pct', 0)
            reasons.append(f"지지선 근접 ({distance:.1f}%)")

        # 상승 추세
        trend = signals.get('trend', {})
        if trend.get('uptrend'):
            days = trend.get('consecutive_days', 0)
            reasons.append(f"{days}일 연속 상승")

        # 모멘텀
        momentum = signals.get('momentum', {})
        if momentum.get('positive'):
            strength = momentum.get('strength', 0)
            reasons.append(f"강한 모멘텀 ({strength:.1f}%)")

        if not reasons:
            reasons.append("복합 지표 기반")

        return f"급등 예측 ({score}% 정확도): " + ", ".join(reasons)

    def _generate_signal_id(self, market):
        """
        고유 시그널 ID 생성

        Format: SIGNAL-YYYYMMDD-HHMMSS-MARKET-UUID

        Args:
            market (str): 마켓 코드

        Returns:
            str: 시그널 ID
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        market_short = market.replace('KRW-', '')
        unique_id = str(uuid.uuid4())[:8]

        return f"SIGNAL-{timestamp}-{market_short}-{unique_id}"

    def batch_generate_from_candidates(self, candidates):
        """
        여러 급등 후보에서 일괄 시그널 생성

        Args:
            candidates (list): [{'market': str, 'score': int, 'current_price': float, 'signals': dict}]

        Returns:
            dict: {
                'total': int,
                'generated': int,
                'distributed_total': int,
                'signals': [TradingSignal],
                'errors': [str]
            }
        """
        total = len(candidates)
        generated = 0
        distributed_total = 0
        signals = []
        errors = []

        print(f"\n[SignalGenerator] Batch processing {total} candidates...")

        for candidate in candidates:
            try:
                market = candidate['market']
                current_price = candidate['current_price']
                score = candidate['score']
                signals_data = candidate.get('signals', {})

                # 분석 결과 구성
                surge_analysis = {
                    'score': score,
                    'signals': signals_data,
                    'recommendation': candidate.get('recommendation', 'buy')
                }

                # 시그널 생성
                result = self.generate_signal_from_surge(market, surge_analysis, current_price)

                if result['success']:
                    generated += 1
                    distributed_total += result['distributed_to']
                    signals.append(result['signal'])
                else:
                    errors.append(f"{market}: {result['message']}")

            except Exception as e:
                errors.append(f"{candidate.get('market', 'UNKNOWN')}: {str(e)}")

        print(f"\n[SignalGenerator] Batch complete:")
        print(f"  Total candidates: {total}")
        print(f"  Signals generated: {generated}")
        print(f"  Users notified: {distributed_total}")
        print(f"  Errors: {len(errors)}")

        return {
            'total': total,
            'generated': generated,
            'distributed_total': distributed_total,
            'signals': signals,
            'errors': errors
        }

    def get_active_signals(self, limit=50):
        """
        현재 활성 시그널 조회

        Args:
            limit (int): 최대 조회 개수

        Returns:
            list: [TradingSignal]
        """
        session = get_db_session()

        try:
            signals = session.query(TradingSignal).filter(
                TradingSignal.status == SignalStatus.ACTIVE,
                TradingSignal.valid_until > datetime.utcnow()
            ).order_by(TradingSignal.created_at.desc()).limit(limit).all()

            return signals

        finally:
            session.close()

    def expire_old_signals(self):
        """
        만료된 시그널 상태 업데이트

        Returns:
            int: 만료된 시그널 수
        """
        session = get_db_session()

        try:
            count = session.query(TradingSignal).filter(
                TradingSignal.status.in_([SignalStatus.PENDING, SignalStatus.ACTIVE]),
                TradingSignal.valid_until <= datetime.utcnow()
            ).update({
                'status': SignalStatus.EXPIRED
            })

            session.commit()

            if count > 0:
                print(f"[SignalGenerator] Expired {count} old signals")

            return count

        except Exception as e:
            session.rollback()
            print(f"[SignalGenerator] Error expiring signals: {e}")
            return 0

        finally:
            session.close()


# 전역 인스턴스
signal_generator = SignalGenerator()


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("Signal Generation Service Test")
    print("=" * 60)

    generator = SignalGenerator()

    # Test 1: 시그널 생성 (가상 데이터)
    print("\n[Test 1] Generate signal from surge analysis:")

    test_surge_analysis = {
        'score': 85,
        'signals': {
            'volume': {'increased': True, 'increase_ratio': 2.5},
            'rsi': {'oversold': True, 'value': 32.5},
            'support': {'near_support': True, 'distance_pct': 1.2},
            'trend': {'uptrend': True, 'consecutive_days': 3},
            'momentum': {'positive': True, 'strength': 15.3}
        },
        'recommendation': 'strong_buy'
    }

    result = generator.generate_signal_from_surge(
        market='KRW-XRP',
        surge_analysis=test_surge_analysis,
        current_price=650.0
    )

    print(f"\nResult: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Distributed to: {result['distributed_to']} users")

    # Test 2: 활성 시그널 조회
    print("\n[Test 2] Get active signals:")
    active_signals = generator.get_active_signals(limit=10)
    print(f"Active signals: {len(active_signals)}")

    for signal in active_signals[:3]:
        print(f"\n  {signal.market}:")
        print(f"    ID: {signal.signal_id}")
        print(f"    Confidence: {signal.confidence}%")
        print(f"    Entry: KRW {signal.entry_price:,}")
        print(f"    Target: KRW {signal.target_price:,}")
        print(f"    Distributed to: {signal.distributed_to} users")
