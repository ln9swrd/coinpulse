# 코인펄스 아키텍처 리뷰 (2025-12-13)

## 🔍 전체 구조 분석

### ✅ 잘 설계된 부분

#### 1. 모듈화 및 관심사 분리
```
backend/
├── common/          # 공통 모듈 (UpbitAPI, 설정)
├── services/        # 비즈니스 로직 (Chart, Holdings, Trading)
├── routes/          # API 엔드포인트 (Flask Blueprint)
├── models/          # 데이터베이스 모델
└── middleware/      # 인증/인가 미들웨어
```

**장점**:
- 명확한 레이어 분리 (Routes → Services → Models)
- 재사용 가능한 공통 모듈
- Flask Blueprint로 라우팅 모듈화
- 단일 책임 원칙 준수

---

#### 2. 환경별 구성 관리
```python
# app.py:52-94
def load_config():
    # 1. Environment variables (highest priority)
    # 2. config.json file
    # 3. Default values (lowest priority)
```

**장점**:
- 환경 변수 우선순위 시스템
- 개발/프로덕션 설정 분리
- DATABASE_URL 환경 변수로 SQLite/PostgreSQL 자동 전환

---

#### 3. 데이터베이스 추상화
- SQLAlchemy ORM 사용
- 자동 폴백 (PostgreSQL → SQLite)
- 멀티 유저 지원 구조 (`user_id` 기반)

---

#### 4. 백엔드 API 구조
**총 9개 Blueprint**:
- `auth_bp` - 사용자 인증 (JWT)
- `holdings_bp` - 포트폴리오 관리
- `auto_trading_bp` - 자동매매
- `payment_bp` - 결제 (구독)
- `admin_bp` - 베타 테스터 관리
- `users_admin_bp` - 사용자/결제 요청 관리
- `plan_admin_bp` - 플랜 설정
- `stats_bp` - 통계 API
- `health_bp` - 헬스 체크

**장점**: 기능별 명확한 분리

---

## ⚠️ 구조적 문제점

### 🔴 Critical (즉시 수정 필요)

#### 1. 중복된 자동매매 시스템
**문제**: 두 가지 다른 접근 방식이 공존

| 시스템 A | 시스템 B |
|---------|---------|
| `position_tracker.py` | `enhanced_auto_trading_engine.py` |
| `swing_trading_engine.py` | `db_position_tracker.py` |
| JSON 파일 기반 | 데이터베이스 기반 |
| 단일 사용자 | Multi-user 지원 |
| `active_positions.json` | `swing_trading_positions` 테이블 |

**문제점**:
- 두 시스템이 동시 실행 시 충돌 가능
- 데이터 일관성 문제 (JSON vs DB)
- 유지보수 부담 (중복 로직)
- 혼란스러운 아키텍처

**해결 방안**:
```
권장: 시스템 B (Enhanced) 사용
이유:
✅ Multi-user 지원 (확장성)
✅ 데이터베이스 기반 (안정성)
✅ 트랜잭션 보장
✅ 동시성 제어 가능

조치:
1. swing_trading_engine.py → enhanced 버전으로 마이그레이션
2. position_tracker.py를 archives/backups/로 이동
3. 문서 업데이트 (CLAUDE.md)
```

---

#### 2. 보안 취약점

##### A. 하드코딩된 시크릿 키
**파일**: `backend/routes/payments.py:13`
```python
TOSS_SECRET_KEY = os.getenv('TOSS_SECRET_KEY', 'test_sk_0RnYX2w532w0WB4noyz1VNeyqApQ')
```

**문제점**:
- 테스트 키가 기본값으로 설정됨
- Git에 커밋될 위험
- 프로덕션에서 환경 변수 누락 시 테스트 키 사용

**해결 방안**:
```python
TOSS_SECRET_KEY = os.getenv('TOSS_SECRET_KEY')
if not TOSS_SECRET_KEY:
    raise ValueError("TOSS_SECRET_KEY environment variable is required")
```

##### B. 단순 토큰 기반 관리자 인증
**파일**: `backend/middleware/auth.py:14`
```python
admin_token = os.getenv('ADMIN_TOKEN', 'coinpulse_admin_2024')
```

**문제점**:
- 단순 문자열 비교 (암호화 없음)
- 토큰 탈취 시 복구 불가 (만료 없음)
- 감사 로그 부재 (누가 언제 접근했는지 추적 불가)

**해결 방안**:
```python
# 1. JWT 기반 관리자 토큰 사용
# 2. 만료 시간 설정 (예: 1시간)
# 3. 관리자 액션 로그 테이블 생성
# 4. IP 화이트리스트 추가
```

---

#### 3. 미완성 기능 (TODO)

##### A. 빌링키 DB 저장
**파일**: `backend/routes/payments.py:46-47`
```python
# TODO: DB에 빌링키 저장
# save_billing_key(customer_key, billing_key, billing_data)
```

**문제점**:
- 빌링키가 저장되지 않음
- 정기결제 실행 불가 (빌링키 조회 불가)
- 결제 시스템 50% 미완성

**영향**:
- 사용자가 구독 신청해도 자동 결제 안 됨
- 수동으로 빌링키 관리 필요
- 프로덕션 배포 불가능한 상태

---

#### 4. Blueprint 일부 비활성화
**파일**: `app.py:39-40`
```python
# from backend.routes.benefits_admin import benefits_admin_bp  # TEMP DISABLED
# from backend.routes.suspension_admin import suspension_admin_bp  # TEMP DISABLED
```

**문제점**:
- 혜택 관리 기능 사용 불가
- 정지 시스템 사용 불가
- 파일은 존재하지만 라우트 등록 안 됨

**확인 필요**:
- 비활성화 이유?
- 오류가 있었나?
- 언제 활성화할 예정인가?

---

### 🟡 Warning (개선 권장)

#### 5. JSON 파일 기반 상태 관리
**파일들**:
- `swing_trading_config.json`
- `active_positions.json`
- `position_history.json`
- `trading_policies.json`

**문제점**:
- 동시성 문제 (파일 잠금)
- 트랜잭션 미지원
- 백업/복구 어려움
- Multi-user 환경에서 충돌 가능

**권장**:
```
모든 상태를 데이터베이스로 이관
- trading_configs 테이블
- trading_positions 테이블 (이미 존재)
- trading_policies 테이블
```

---

#### 6. 에러 처리 및 로깅

**현재 상태**:
```python
# 대부분의 서비스에서 이런 패턴
try:
    # 로직
except Exception as e:
    print(f"[Service] ERROR: {e}")
    return None
```

**문제점**:
- `print()` 사용 (프로덕션 환경에서 로그 손실)
- 에러 상세 정보 부족 (traceback 없음)
- 에러 모니터링 시스템 부재
- 사용자에게 에러 전달 안 됨

**개선 방안**:
```python
import logging

logger = logging.getLogger(__name__)

try:
    # 로직
except Exception as e:
    logger.exception(f"[Service] ERROR: {e}")
    # Sentry 또는 로그 시스템으로 전송
    raise ServiceError(f"Operation failed: {e}")
```

---

#### 7. 프론트엔드-백엔드 연동 부재

**완성된 백엔드 API**:
- ✅ `surge_predictor.py` - 급등 예측
- ✅ `swing_trading_engine.py` - 스윙 트레이딩
- ✅ `users_admin.py` - 사용자 관리

**프론트엔드 UI**:
- ❌ 급등 예측 모니터링 페이지 없음
- ❌ 스윙 트레이딩 대시보드 없음
- ❌ 사용자 관리 UI 미완성 (admin.html 확인 필요)

**문제점**:
- 강력한 백엔드 기능을 사용자가 접근 불가
- 관리자도 API를 직접 호출해야 함 (불편)

---

#### 8. 백그라운드 작업 스케줄러 부재

**필요한 작업**:
1. **정기결제 스케줄러** (매일 00:00)
   - 만료 3일 전 결제 시도
   - 결제 실패 시 재시도
   - 구독 상태 자동 업데이트

2. **자동매매 스케줄러** (1분마다)
   - 포지션 업데이트
   - 손절/익절 체크
   - 급등 후보 스캔

3. **데이터 동기화** (5분마다)
   - Upbit 주문 내역 동기화
   - 현재가 업데이트

**현재 상태**:
- `background_sync.py` 존재 (주문 동기화만)
- 정기결제 스케줄러 없음
- 자동매매 수동 실행만 가능

**권장 솔루션**:
```python
# APScheduler 사용
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(sync_orders, 'interval', minutes=5)
scheduler.add_job(check_subscriptions, 'cron', hour=0, minute=0)
scheduler.add_job(run_auto_trading, 'interval', minutes=1)
scheduler.start()
```

---

#### 9. 데이터베이스 마이그레이션 관리

**현재 상태**:
- 수동 테이블 생성 스크립트들:
  - `init_auth_db.py`
  - `init_order_sync.py`
  - `init_subscription_db.py`
  - `create_tables.py`

**문제점**:
- 버전 관리 없음
- 롤백 불가
- 프로덕션 스키마 변경 위험
- 어떤 스크립트를 먼저 실행해야 하는지 불명확

**권장**:
```bash
# Alembic 사용 (SQLAlchemy 마이그레이션 도구)
alembic init migrations
alembic revision --autogenerate -m "Add billing_keys table"
alembic upgrade head
```

---

### 🟢 Info (모니터링 필요)

#### 10. 성능 최적화 고려사항

**현재 구조**:
- SimpleCache (메모리 기반, TTL 60초)
- Database-first strategy (주문 내역)
- Connection pooling (SQLAlchemy 기본)

**개선 여지**:
1. **Redis 캐싱**
   - 현재가 정보 (1초 TTL)
   - 차트 데이터 (1분 TTL)
   - 세션 관리

2. **API Rate Limit**
   - Upbit API: 초당 10회 제한
   - 현재: 제한 없음 (429 에러 발생 가능)

3. **쿼리 최적화**
   - N+1 문제 확인 필요
   - 인덱스 최적화
   - EXPLAIN ANALYZE 분석

---

## 📋 구조적 개선 로드맵

### Phase 1: 긴급 수정 (1주)
- [ ] **빌링키 DB 저장** (payments.py:46-47)
- [ ] **자동매매 시스템 통합** (Enhanced 버전 선택)
- [ ] **보안 강화**:
  - TOSS_SECRET_KEY 기본값 제거
  - 관리자 토큰 JWT 전환
  - 환경 변수 필수화

### Phase 2: 기능 완성 (1-2주)
- [ ] **정기결제 스케줄러** 구현
- [ ] **프론트엔드 연동**:
  - 스윙 트레이딩 대시보드
  - 급등 예측 모니터링
  - 사용자 관리 UI
- [ ] **비활성화된 Blueprint** 활성화 (또는 제거)

### Phase 3: 안정화 (2주)
- [ ] **로깅 시스템** (Python logging + 파일 로테이션)
- [ ] **에러 모니터링** (Sentry 통합)
- [ ] **데이터베이스 마이그레이션** (Alembic)
- [ ] **자동 백업** (PostgreSQL pg_dump)

### Phase 4: 최적화 (ongoing)
- [ ] **Redis 캐싱** 도입
- [ ] **API Rate Limit** 구현
- [ ] **쿼리 최적화**
- [ ] **부하 테스트** (100명 동시 접속)

---

## 🎯 결론

### 현재 상태: 70% 완성 ✅

**강점**:
- ✅ 모듈화가 잘 되어 있음
- ✅ 레이어 분리 명확
- ✅ 확장 가능한 구조
- ✅ 멀티 유저 지원 준비됨

**약점**:
- ⚠️ 중복 시스템 (자동매매)
- ⚠️ 미완성 기능 (빌링키 저장)
- ⚠️ 프론트엔드 연동 부족
- ⚠️ 보안 취약점 (하드코딩, 단순 토큰)

### 큰 그림은 건전함 ✅

**아키텍처 자체는 문제 없음**. 다만:
1. **중복 제거** 필요 (자동매매 시스템 통합)
2. **미완성 기능** 완성 (빌링키 저장, 스케줄러)
3. **보안 강화** 필요 (시크릿 키 관리, JWT)
4. **UI 연동** 필요 (백엔드 기능 활용)

### 프로덕션 배포 전 필수 작업

1. ✅ **빌링키 DB 저장** - 결제 시스템 완성
2. ✅ **보안 강화** - 시크릿 키, JWT
3. ✅ **자동매매 통합** - Enhanced 버전으로 일원화
4. ⚠️ **에러 모니터링** - Sentry 또는 로깅
5. ⚠️ **자동 백업** - 데이터 손실 방지

---

**최종 평가**:
구조는 견고하나, **디테일 완성도**가 부족합니다.
백엔드 기능은 강력하지만, **프론트엔드 연동**과 **스케줄러** 부재로 실사용 어려움.

**권장**: Phase 1-2 완료 후 프로덕션 배포 (약 2-3주 소요)
