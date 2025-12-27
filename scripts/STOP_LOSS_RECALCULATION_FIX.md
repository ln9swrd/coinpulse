# 손절가 재계산 기능 구현 완료

## 📋 개요

급등 알림 시스템의 손절가 계산 방식을 개선하여, 사용자가 알림 수신 후 늦게 매수할 경우에도 적절한 손절가가 설정되도록 수정했습니다.

## ⚠️ 문제점

### 기존 방식의 문제
- **손절가 계산 시점**: 알림 생성 시점의 가격 기준
- **문제 상황**: 사용자가 늦게 매수할 경우 손절가가 부적절하게 설정됨

### 예시
```
알림 시점:
- 가격: 100원
- 손절가: 95원 (-5%)
- 목표가: 110원 (+10%)

실제 매수 시점 (늦은 매수):
- 매수가: 110원
- 손절가: 95원 (그대로 유지)
- 실제 손절률: -13.6% ❌ (너무 공격적!)
```

## ✅ 해결 방법

### 선택한 방식: Option 1 (실제 매수가 기준 재계산)

사용자가 수동으로 코인을 매수할 때, 해당 코인에 활성화된 급등 알림이 있으면 자동으로 손절가와 목표가를 재계산합니다.

### 구현 내용

#### 1. `update_surge_alert_prices()` 함수 생성
**파일**: `backend/routes/holdings_routes.py` (53-136줄)

**기능**:
- 실제 매수가 기준으로 손절가/목표가 재계산
- 사용자의 자동매매 설정(stop_loss_percent, take_profit_percent) 로드
- SurgePredictor 서비스 사용하여 가격 계산
- surge_alerts 테이블 업데이트

**매개변수**:
```python
def update_surge_alert_prices(alert_id, actual_entry_price, user_id):
    """
    Args:
        alert_id: 급등 알림 ID
        actual_entry_price: 실제 매수가 (주문 가격)
        user_id: 사용자 ID
    """
```

#### 2. `place_buy_order()` 엔드포인트 통합
**파일**: `backend/routes/holdings_routes.py` (688-746줄)

**동작 흐름**:
1. 매수 주문 성공 후 실행
2. surge_alerts 테이블에서 해당 마켓의 활성 알림 조회
   - 조건: `status = 'pending'` AND `market = 주문마켓` AND `user_id = 사용자ID`
3. 활성 알림이 있으면:
   - `update_surge_alert_prices()` 호출하여 가격 재계산
   - `user_action = 'bought'` 설정
   - `order_id` 저장
   - `action_timestamp` 기록

**에러 처리**:
- 알림 업데이트 실패 시에도 주문은 정상 처리
- 로그에 경고 메시지 출력

## 📊 개선 효과

### Before (수정 전)
```
알림: 100원
↓
사용자 매수: 110원
↓
손절가: 95원 (-13.6% 실제 손실!)
목표가: 110원 (0% 수익)
```

### After (수정 후)
```
알림: 100원
↓
사용자 매수: 110원
↓
자동 재계산:
- 손절가: 104.5원 (-5% 정확)
- 목표가: 121원 (+10% 정확)
```

## 🔍 작동 시나리오

### 시나리오 1: 자동매매 알림 후 수동 매수
1. 시스템이 급등 감지 → 알림 생성 (entry_price=100원, stop_loss=95원)
2. 사용자가 차트 확인 후 늦게 매수 (110원)
3. **시스템이 자동으로 가격 재계산**:
   - entry_price: 100원 → 110원
   - stop_loss_price: 95원 → 104.5원
   - target_price: 110원 → 121원
4. user_action='bought', order_id 저장

### 시나리오 2: 알림 없이 일반 매수
1. 사용자가 일반 매수 (활성 알림 없음)
2. 시스템이 알림 조회 → 결과 없음
3. 주문만 정상 처리 (알림 업데이트 없음)

### 시나리오 3: 알림 업데이트 실패
1. 사용자 매수 성공
2. 알림 업데이트 중 에러 발생
3. 경고 로그 출력하지만 주문은 정상 완료

## 📝 데이터베이스 변경사항

### surge_alerts 테이블 업데이트 필드
```sql
UPDATE surge_alerts
SET
    entry_price = :actual_entry_price,      -- 실제 매수가
    target_price = :new_target_price,       -- 재계산된 목표가
    stop_loss_price = :new_stop_loss_price, -- 재계산된 손절가
    current_price = :actual_entry_price,    -- 현재가 업데이트
    user_action = 'bought',                  -- 사용자 행동 기록
    action_timestamp = CURRENT_TIMESTAMP,    -- 행동 시각
    order_id = :order_uuid                   -- 주문 UUID
WHERE id = :alert_id
```

## 🚀 배포 정보

- **커밋**: db82a66
- **배포 일시**: 2025-12-27 07:43 UTC
- **배포 환경**: Production (coinpulse.sinsi.ai)
- **서비스 상태**: ✅ 정상 운영 중

### 배포 확인
```bash
# 프로덕션 서버
ssh root@158.247.222.216

# Git 상태
cd /opt/coinpulse
git log --oneline -1
# db82a66 [FIX] Update surge alert prices based on actual buy order price

# 서비스 상태
sudo systemctl status coinpulse
# Active: active (running)
```

## 🧪 테스트 방법

### 수동 테스트 시나리오
1. **준비**:
   - 급등 알림 활성화 (status='pending')
   - 해당 코인의 알림 가격 확인

2. **실행**:
   ```bash
   # API 엔드포인트 호출
   POST /api/trading/buy
   {
     "market": "KRW-DOGE",
     "price": "110",
     "volume": "100"
   }
   ```

3. **검증**:
   ```sql
   -- 알림 가격 확인
   SELECT
       id,
       market,
       entry_price,
       target_price,
       stop_loss_price,
       user_action,
       order_id
   FROM surge_alerts
   WHERE user_id = 1 AND market = 'KRW-DOGE'
   ORDER BY sent_at DESC
   LIMIT 1;
   ```

4. **기대 결과**:
   - entry_price가 실제 매수가로 업데이트
   - stop_loss_price가 -5% 정확히 재계산
   - target_price가 +10% 정확히 재계산
   - user_action='bought'
   - order_id 저장됨

## 📚 관련 파일

- `backend/routes/holdings_routes.py` - 주문 API 및 가격 재계산 로직
- `backend/services/surge_predictor.py` - 목표가/손절가 계산 서비스
- `backend/models/surge_alert_models.py` - 알림 데이터 모델
- `backend/services/surge_auto_trading_worker.py` - 자동매매 워커 (참고)

## 🔗 참고 문서

- [SURGE_ALERT_SYSTEM.md](../docs/features/SURGE_ALERT_SYSTEM.md) - 급등 알림 시스템 전체 사양
- [PLAN_FEATURES.md](../backend/models/plan_features.py) - 요금제별 기능

## 📞 문의

- 이슈 발생 시: GitHub Issues
- 긴급 문의: 시스템 관리자

---

**작성일**: 2025-12-27
**작성자**: Claude Code
**버전**: 1.0
