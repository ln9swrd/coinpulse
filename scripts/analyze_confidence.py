# -*- coding: utf-8 -*-
"""
Analyze confidence scores vs actual performance
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

with get_db_session() as session:
    print('=== 신뢰도 vs 수익률 분석 (2025-10-01 이후) ===\n')

    # 1. 손실 건들의 신뢰도 분포
    print('1. 손실 건들의 신뢰도 분포\n')

    loss_query = text("""
        SELECT
            coin,
            confidence * 100 as score,
            entry_price,
            exit_price,
            peak_price,
            ((exit_price::float - entry_price::float) / entry_price::float * 100) as profit_pct,
            ((peak_price::float - entry_price::float) / entry_price::float * 100) as peak_pct,
            close_reason,
            sent_at
        FROM surge_alerts
        WHERE sent_at >= '2025-10-01'
            AND status IN ('lose', 'closed', 'expired')
            AND exit_price <= entry_price
        ORDER BY confidence DESC, sent_at DESC
    """)

    losses = session.execute(loss_query).fetchall()

    print(f'총 손실 건수: {len(losses)}개\n')
    print('신뢰도 | 코인 | 수익률 | 피크 | 종료 사유')
    print('-' * 80)

    high_score_losses = []
    for loss in losses:
        coin = loss[0]
        score = int(float(loss[1])) if loss[1] else 0
        profit_pct = float(loss[5]) if loss[5] else 0
        peak_pct = float(loss[6]) if loss[6] else 0
        reason = loss[7] or 'N/A'

        print(f'{score:3d}점 | {coin:6s} | {profit_pct:+6.2f}% | {peak_pct:+6.2f}% | {reason[:40]}')

        if score >= 70:
            high_score_losses.append({
                'coin': coin,
                'score': score,
                'profit_pct': profit_pct,
                'peak_pct': peak_pct,
                'reason': reason
            })

    # 2. 신뢰도 구간별 승률
    print('\n\n2. 신뢰도 구간별 승률\n')

    bracket_query = text("""
        SELECT
            CASE
                WHEN confidence >= 0.8 THEN '80-100'
                WHEN confidence >= 0.75 THEN '75-79'
                WHEN confidence >= 0.7 THEN '70-74'
                ELSE '60-69'
            END as score_bracket,
            COUNT(*) as total,
            COUNT(CASE WHEN exit_price > entry_price THEN 1 END) as wins,
            COUNT(CASE WHEN exit_price <= entry_price THEN 1 END) as losses,
            AVG(((exit_price - entry_price) / NULLIF(entry_price, 0) * 100)) as avg_return,
            AVG(((peak_price - entry_price) / NULLIF(entry_price, 0) * 100)) as avg_peak
        FROM surge_alerts
        WHERE sent_at >= '2025-10-01'
            AND status IN ('win', 'lose', 'closed', 'expired')
        GROUP BY score_bracket
        ORDER BY score_bracket DESC
    """)

    brackets = session.execute(bracket_query).fetchall()

    print('신뢰도 | 총 건수 | 승 | 패 | 승률 | 평균수익 | 평균피크')
    print('-' * 80)

    for bracket in brackets:
        score_range = bracket[0]
        total = bracket[1]
        wins = bracket[2]
        losses = bracket[3]
        avg_return = float(bracket[4]) if bracket[4] else 0
        avg_peak = float(bracket[5]) if bracket[5] else 0
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        print(f'{score_range:7s} | {total:6d}개 | {wins:2d} | {losses:2d} | {win_rate:5.1f}% | {avg_return:+7.2f}% | {avg_peak:+7.2f}%')

    # 3. 고신뢰도(70+) 손실 케이스 상세 분석
    print('\n\n3. 고신뢰도(70+) 손실 케이스 상세 분석\n')
    print(f'총 {len(high_score_losses)}건\n')

    if high_score_losses:
        # 피크 도달 실패 (피크 < 3%)
        no_peak = [x for x in high_score_losses if x['peak_pct'] < 3]
        # 피크 도달했지만 손실
        peak_but_loss = [x for x in high_score_losses if x['peak_pct'] >= 3]

        print(f'패턴 1: 피크 미도달 (3% 미만) - {len(no_peak)}건')
        for item in no_peak[:10]:
            print(f"  • {item['coin']} ({item['score']}점): 피크 {item['peak_pct']:+.2f}%, 손실 {item['profit_pct']:+.2f}%")

        print(f'\n패턴 2: 피크 도달했지만 손실 - {len(peak_but_loss)}건')
        for item in peak_but_loss[:10]:
            print(f"  • {item['coin']} ({item['score']}점): 피크 {item['peak_pct']:+.2f}%, 손실 {item['profit_pct']:+.2f}%")
            print(f"    이유: {item['reason'][:60]}")

    # 4. 신뢰도와 실제 수익률의 상관관계
    print('\n\n4. 신뢰도와 실제 성과의 상관관계\n')

    correlation_query = text("""
        SELECT
            ROUND(confidence * 100) as score,
            COUNT(*) as count,
            COUNT(CASE WHEN exit_price > entry_price THEN 1 END) as wins,
            AVG(((exit_price - entry_price) / NULLIF(entry_price, 0) * 100)) as avg_return,
            MAX(((peak_price - entry_price) / NULLIF(entry_price, 0) * 100)) as max_peak
        FROM surge_alerts
        WHERE sent_at >= '2025-10-01'
            AND status IN ('win', 'lose', 'closed', 'expired')
        GROUP BY ROUND(confidence * 100)
        HAVING COUNT(*) >= 1
        ORDER BY ROUND(confidence * 100) DESC
    """)

    correlations = session.execute(correlation_query).fetchall()

    print('점수 | 건수 | 승 | 평균수익 | 최대피크 | 실제승률')
    print('-' * 70)

    for corr in correlations:
        score = int(float(corr[0])) if corr[0] else 0
        count = corr[1]
        wins = corr[2]
        avg_return = float(corr[3]) if corr[3] else 0
        max_peak = float(corr[4]) if corr[4] else 0
        actual_win_rate = (wins / count * 100)

        print(f'{score:3d}점 | {count:3d}개 | {wins:2d} | {avg_return:+8.2f}% | {max_peak:+8.2f}% | {actual_win_rate:5.1f}%')

print('\n=== 분석 완료 ===')
