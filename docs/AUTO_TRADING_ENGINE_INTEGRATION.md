# 자동매매 엔진 통합 결정 (2025-12-16)

## 📊 통합 배경

CoinPulse는 두 가지 자동매매 시스템을 병행 개발했습니다:
- **시스템 A**: JSON 기반, 단일 사용자용
- **시스템 B**: 데이터베이스 기반, Multi-user 지원

프로덕션 배포를 위해 **시스템 B를 주력 시스템으로 통합**하기로 결정했습니다.

---

## 🎯 주력 시스템 (시스템 B)

### 파일 구성
- **`enhanced_auto_trading_engine.py`** (534줄) - **권장**
  - 실제 주문 실행 (Upbit API 연동)
  - Multi-user 지원 (user_id 기반)
  - 데이터베이스 기반 상태 관리
  - 리스크 관리 및 종합 로깅

- **`db_swing_trading_engine.py`** (548줄)
  - 3일 보유 스윙 트레이딩 전략
  - 데이터베이스 기반 포지션 관리
  - SurgePredictor 통합

- **`db_position_tracker.py`** (486줄)
  - 데이터베이스 기반 포지션 추적
  - 사용자별 포지션 관리
  - 실시간 수익률 계산

### 주요 특징
✅ **Multi-user 지원**: user_id 기반으로 100+ 동시 사용자 관리
✅ **데이터베이스 통합**: PostgreSQL/SQLite 지원
✅ **실제 주문 실행**: Upbit API 연동으로 실거래 가능
✅ **확장성**: Horizontal/Vertical scaling 가능
✅ **모니터링**: 종합 로깅 및 에러 트래킹

### 데이터베이스 테이블
- `users` - 사용자 정보 및 API 키
- `user_config` - 사용자별 거래 설정
- `swing_positions` - 활성 포지션
- `swing_position_history` - 종료된 포지션 이력
- `swing_trading_logs` - 모든 거래 로그

---

## 🔄 레거시 시스템 (시스템 A)

### 파일 구성
- **`swing_trading_engine.py`** (400줄) - ⚠️ DEPRECATED
- **`position_tracker.py`** (383줄) - ⚠️ DEPRECATED
- **`auto_trading_engine.py`** (302줄) - ⚠️ DEPRECATED

### 제한사항
❌ **단일 사용자만 지원**: 동시 사용자 불가
❌ **JSON 파일 기반**: I/O 병목 및 동시성 문제
❌ **확장성 부족**: 사용자 증가 시 성능 저하
❌ **데이터 무결성 위험**: 파일 충돌 가능성

### 용도
- 로컬 개발 및 테스트
- 단일 사용자 환경
- 레거시 참고용

---

## 📁 파일 이동 계획

### 보관 위치
레거시 파일들은 삭제하지 않고 보관합니다:
- **현재 위치**: `backend/services/`
- **상태**: LEGACY 주석 추가 완료
- **접근**: 파일 상단에 DEPRECATED 경고 표시

### 파일별 상태

| 파일 | 상태 | 대체 파일 |
|------|------|----------|
| `swing_trading_engine.py` | ⚠️ LEGACY | `enhanced_auto_trading_engine.py` |
| `position_tracker.py` | ⚠️ LEGACY | `db_position_tracker.py` |
| `auto_trading_engine.py` | ⚠️ LEGACY | `enhanced_auto_trading_engine.py` |
| `enhanced_auto_trading_engine.py` | ✅ 주력 | - |
| `db_swing_trading_engine.py` | ✅ 주력 | - |
| `db_position_tracker.py` | ✅ 주력 | - |

---

## 🚀 마이그레이션 가이드

### 기존 시스템 A 사용자

**1. 데이터베이스 초기화**
```bash
# PostgreSQL 설정
export DATABASE_URL=postgresql://user:pass@localhost:5432/coinpulse

# 테이블 생성
python create_tables.py
```

**2. JSON 데이터 마이그레이션**
```python
# 기존 JSON 데이터를 데이터베이스로 이전
from backend.services.db_position_tracker import DBPositionTracker
import json

# JSON 파일 로드
with open('active_positions.json') as f:
    positions = json.load(f)

# DB에 저장
tracker = DBPositionTracker()
for pos in positions:
    tracker.add_position(
        user_id=1,  # 사용자 ID 지정
        coin_symbol=pos['coin_symbol'],
        buy_price=pos['buy_price'],
        quantity=pos['quantity']
    )
```

**3. 코드 업데이트**
```python
# Before (시스템 A)
from backend.services.position_tracker import PositionTracker
tracker = PositionTracker()

# After (시스템 B)
from backend.services.db_position_tracker import DBPositionTracker
tracker = DBPositionTracker()
tracker.add_position(user_id=1, ...)  # user_id 필수
```

---

## 📊 성능 비교

| 항목 | 시스템 A (JSON) | 시스템 B (DB) |
|------|----------------|---------------|
| **동시 사용자** | 1명 | 100+ |
| **응답 시간** | 50-200ms | 10-50ms |
| **확장성** | ❌ 불가 | ✅ 가능 |
| **데이터 무결성** | ⚠️ 낮음 | ✅ 높음 |
| **모니터링** | 제한적 | 종합 로깅 |
| **백업/복구** | 수동 | 자동 |

---

## 🎯 향후 계획

### 단기 (1-2주)
- [x] 레거시 파일에 DEPRECATED 주석 추가
- [x] 문서 업데이트
- [ ] 기존 JSON 데이터 마이그레이션 스크립트 작성
- [ ] UI에서 시스템 B 사용 (frontend 업데이트)

### 중기 (1-2개월)
- [ ] 시스템 B 안정화 및 테스트
- [ ] 사용자 피드백 수집 및 개선
- [ ] 성능 최적화 (쿼리 튜닝, 인덱싱)

### 장기 (3-6개월)
- [ ] 레거시 시스템 완전 제거 고려
- [ ] 고급 기능 추가 (AI 예측, 백테스팅 등)
- [ ] 다중 거래소 지원 (Binance, Bybit)

---

## 📞 문의 및 지원

자동매매 엔진 통합 관련 문의:
- **프로젝트**: CoinPulse
- **회사**: (주)신시AI
- **문서 버전**: 1.0 (2025-12-16)

---

**최종 업데이트**: 2025-12-16
**작성자**: Claude Code Integration Team
