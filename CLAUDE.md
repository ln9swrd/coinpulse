# 코인펄스 (CoinPulse) 프로젝트 지침

## 🤝 협업 원칙 (2025.12.13 추가)

### 핵심 원칙
1. **다각도 검토 + 단계적 실행**: 기술적/비즈니스적/사용자 관점 분석 → 2-3단계 점진 진행
2. **솔직한 소통**: 불확실하면 "모른다"고 인정, 과장 금지
3. **과거 경험 활용**: 작업 전 대화 기록 검색, 성공 패턴 우선 적용
4. **실용성 우선**: 80% 확실한 빠른 해결책 > 100% 완벽한 느린 해결책
5. **하드코딩 절대 금지**: 모든 데이터는 파일/데이터베이스/API에서 참조 (상세: "코드 작성 규칙" 섹션 참조)

### 작업 분류
- **Type A** (5분): 간단한 질문/확인, 파일 읽기, 명령어 실행 → 즉시 처리
- **Type B** (10분-1시간): 버그 수정, 기능 추가, 문서 작성 → Phase 1(검토) → Phase 2(실행) → Phase 3(완료)
- **Type C** (1시간+): 대규모 작업, 아키텍처 변경 → Type B 단위로 분할 실행

### 금지사항
- ❌ 과장된 표현 ("완벽하게 해결")
- ❌ 한 파일에 모든 기능 몰아넣기
- ❌ 문법 에러가 있는 코드 제공
- ✅ 전체 구조 설계 → 파일별 모듈 개발 → 통합 테스트

---

## 🗣️ 대화 언어 및 인코딩 규칙 (2025.11.30 추가, 2025.12.18 업데이트)

### 핵심 원칙 (반드시 준수)
1. ✅ **모든 파일은 UTF-8 BOM 인코딩**: HTML, JS, CSS, Python, JSON 모두 UTF-8 BOM 사용 (필수)
2. ✅ **프론트엔드는 한글 우선**: 사용자 대면 텍스트는 100% 한글 작성 (영어 금지)
3. ✅ **백엔드는 영어 허용**: 로그, 에러 메시지, 코드 주석은 영어 사용 가능

---

### 인코딩 규칙 (강제 사항)

#### UTF-8 BOM 인코딩 필수
**모든 텍스트 파일은 UTF-8 BOM(Byte Order Mark)으로 저장해야 합니다.**

| 파일 종류 | 인코딩 | 필수 여부 |
|----------|--------|-----------|
| HTML     | UTF-8 BOM | ✅ 필수 |
| JavaScript | UTF-8 BOM | ✅ 필수 |
| CSS      | UTF-8 BOM | ✅ 필수 |
| Python   | UTF-8 BOM | ✅ 필수 |
| JSON     | UTF-8 BOM | ✅ 필수 |
| Markdown | UTF-8 BOM | ✅ 필수 |

**UTF-8 BOM 사용 이유:**
- Windows 환경에서 한글 인코딩 오류 100% 방지
- CMD/PowerShell 출력 깨짐 방지
- 파일 읽기/쓰기 시 자동 인코딩 감지
- 국제 표준 호환성 유지

#### 파일별 인코딩 선언

**HTML 파일:**
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">  <!-- 필수 -->
    ...
</head>
```

**Python 파일:**
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-  <!-- 필수 -->

import os
...
```

**JSON 파일:**
```python
# JSON 저장 시 반드시 ensure_ascii=False 사용
with open('data.json', 'w', encoding='utf-8-sig') as f:  # utf-8-sig = UTF-8 BOM
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**에디터 설정:**
- VS Code: `"files.encoding": "utf8bom"`
- PyCharm: Settings → Editor → File Encodings → UTF-8 with BOM

---

### 언어 사용 규칙

#### 프론트엔드 (HTML/JS/CSS)
**사용자 대면 텍스트는 100% 한글 작성 (영어 금지)**

```html
<!-- ✅ 올바른 예시 (한글) -->
<button>로그인</button>
<h1>결제 완료</h1>
<p>회원가입이 성공적으로 완료되었습니다.</p>
<label>이메일</label>
<input placeholder="이메일을 입력하세요">
<div class="error">비밀번호가 일치하지 않습니다</div>

<!-- ❌ 잘못된 예시 (영어) -->
<button>Login</button>
<h1>Payment Complete</h1>
<p>Registration successful.</p>
<label>Email</label>
<input placeholder="Enter your email">
<div class="error">Passwords do not match</div>
```

**JavaScript 사용자 메시지:**
```javascript
// ✅ 올바른 예시 (한글)
alert('로그인에 성공했습니다');
console.log('[로그인] 사용자 인증 완료');
throw new Error('이메일 형식이 올바르지 않습니다');

// ❌ 잘못된 예시 (영어)
alert('Login successful');
console.log('[Login] User authenticated');
throw new Error('Invalid email format');
```

#### 백엔드 (Python)
**로그, 에러 메시지, 코드 주석은 영어 허용**

```python
# ✅ 영어 사용 가능
logger.info("User login successful")
raise ValueError("Invalid email format")

# 변수명, 함수명, 클래스명은 반드시 영어
def get_user_profile(user_id):
    pass
```

#### 문서 (Markdown)
**사용자 대면 문서는 한글, 기술 문서는 영어 허용**

```markdown
<!-- ✅ 사용자 가이드 (한글) -->
# CoinPulse 사용자 가이드
## 시작하기
1. 회원가입을 진행하세요
2. 이메일 인증을 완료하세요

<!-- ✅ 기술 문서 (영어) -->
# API Documentation
## Authentication
- Use JWT tokens for authentication
```

---

### 예외 사항

다음 경우에만 영어 사용 허용:

| 항목 | 언어 | 이유 |
|------|------|------|
| 변수명, 함수명, 클래스명 | 영어 | 코드 가독성 |
| Git 커밋 메시지 | 영어 | 국제 협업 |
| API 엔드포인트 | 영어 | RESTful 표준 |
| 로그 메시지 | 영어 | 디버깅 편의성 |
| 에러 코드 | 영어 | 표준화 |

**국제 서비스 대비:**
- 다국어 지원이 필요한 경우 i18n 시스템 사용
- 텍스트는 별도 언어 파일로 분리
- 기본 언어는 한글로 설정

---

### 검증 체크리스트

**파일 생성/수정 시 반드시 확인:**

- [ ] 파일이 UTF-8 BOM 인코딩으로 저장되었는가?
- [ ] HTML 파일에 `<meta charset="UTF-8">` 선언이 있는가?
- [ ] 사용자 대면 텍스트가 모두 한글인가?
- [ ] 버튼, 라벨, 메시지가 한글로 작성되었는가?
- [ ] 코드 주석은 영어로 작성되었는가? (선택)
- [ ] 변수명/함수명이 영어로 작성되었는가?

**위반 시 조치:**
- 즉시 파일 인코딩을 UTF-8 BOM으로 변경
- 영어 UI 텍스트를 한글로 번역
- 커밋 전 검증 필수

---

## 개발/배포 환경 구분 (2025.10.22 추가)

### 개발 환경: Windows
- **OS**: Windows 10/11
- **Python**: Windows용 Python 3.x
- **서버 관리**: 배치 파일 (.bat)
  - `QUICK_START.bat` - 빠른 시작 (권장)
  - `coinpulse_manager_v2.bat` - 관리 메뉴 (CMD에서 실행)
  - `stop_coinpulse.bat` - 서버 중지
- **명령어**: Windows CMD/PowerShell
  - 포트 확인: `netstat -ano | findstr ":8080"`
  - 프로세스 종료: `taskkill /F /PID [PID]`
- **경로 구분자**: 백슬래시 (`\`)
- **개발 도구**: Visual Studio Code, PyCharm

### 배포 환경: Linux
- **OS**: Ubuntu 20.04+ / CentOS 7+ (권장)
- **Python**: Linux용 Python 3.x
- **서버 관리**: Shell 스크립트 (.sh) + systemd
  - `start_server.sh` - 서버 시작 스크립트
  - `systemd` service files - 자동 시작/재시작
- **프로세스 관리**: systemd, supervisor, PM2
- **명령어**: Linux bash
  - 포트 확인: `netstat -tuln | grep 8080` 또는 `ss -tuln | grep 8080`
  - 프로세스 확인: `ps aux | grep python`
  - 프로세스 종료: `kill -9 [PID]`
- **경로 구분자**: 슬래시 (`/`)
- **배포 도구**: Docker, Nginx, Gunicorn, uWSGI

### 플랫폼 독립적 코드 작성 규칙
1. **경로 처리**:
   - ✅ `os.path.join()` 또는 `pathlib.Path` 사용
   - ❌ 하드코딩된 `\` 또는 `/` 사용 금지

2. **설정 파일**:
   - 환경별 설정 파일 분리
   - `config.dev.json` (Windows 개발)
   - `config.prod.json` (Linux 배포)
   - 환경 변수로 전환: `ENV=production`

3. **포트 바인딩**:
   - 개발: `127.0.0.1` (localhost only)
   - 배포: `0.0.0.0` (all interfaces)

4. **로그 파일**:
   - 개발: `logs/` 디렉토리 (상대 경로)
   - 배포: `/var/log/coinpulse/` (절대 경로)

5. **프로세스 관리**:
   - 개발: 수동 시작/중지
   - 배포: systemd 자동 관리

### 배포 준비 체크리스트
- [ ] 모든 경로가 `os.path.join()` 사용
- [ ] 설정 파일이 환경별로 분리됨
- [ ] 포트가 `0.0.0.0`으로 바인딩 설정됨
- [ ] 환경 변수로 민감 정보 관리 (.env 파일)
- [ ] requirements.txt 업데이트
- [ ] systemd service file 작성
- [ ] Nginx reverse proxy 설정 준비
- [ ] 방화벽 규칙 설정 (포트 8080, 8081)
- [ ] SSL 인증서 준비 (Let's Encrypt 권장)
- [ ] 로그 로테이션 설정

### 로컬/프로덕션 동기화 워크플로우 (2025.12.13 추가)

#### 기본 원칙
- **개발**: 로컬 환경 (Windows, D:\Claude\Projects\Active\coinpulse)
- **배포**: 프로덕션 환경 (Linux, root@158.247.222.216:/opt/coinpulse)
- **버전 관리**: 항상 두 환경을 동기화하여 버전 일치 유지

#### 표준 워크플로우 (로컬 → 프로덕션)

**1. 로컬에서 개발**
```bash
# 로컬 환경에서 코드 수정 및 테스트
python app.py  # 로컬 테스트
```

**2. Git 커밋**
```bash
git add .
git commit -m "[TYPE] 변경 내용"
git push origin main
```

**3. 프로덕션 배포**
```bash
# SSH 접속
ssh root@158.247.222.216

# 프로덕션 서버에서 pull
cd /opt/coinpulse
git pull origin main

# 서비스 재시작
sudo systemctl restart coinpulse
sudo systemctl status coinpulse

# 로그 확인
journalctl -u coinpulse -f
```

#### 역방향 워크플로우 (프로덕션 → 로컬)

**상황**: 프로덕션에서 직접 수정한 경우 (긴급 패치 등)

**1. 프로덕션 변경사항 커밋**
```bash
# SSH 접속
ssh root@158.247.222.216

# 변경사항 커밋
cd /opt/coinpulse
git add .
git commit -m "[HOTFIX] 프로덕션 긴급 수정"
git push origin main
```

**2. 로컬에 반영**
```bash
# 로컬 환경
cd D:\Claude\Projects\Active\coinpulse
git pull origin main
```

**3. 로컬에서 테스트**
```bash
python app.py  # 변경사항 확인
```

#### 동기화 체크리스트

**배포 전 체크**:
- [ ] 로컬에서 충분히 테스트 완료
- [ ] requirements.txt 업데이트 (새 패키지 추가 시)
- [ ] .env 파일 변경사항 확인 (수동 반영 필요)
- [ ] 데이터베이스 마이그레이션 스크립트 준비
- [ ] Git에 커밋 및 푸시 완료

**배포 후 체크**:
- [ ] 프로덕션 서비스 정상 작동 확인
- [ ] 로그에 에러 없는지 확인
- [ ] API 엔드포인트 테스트
- [ ] 데이터베이스 연결 확인

**긴급 프로덕션 수정 시**:
- [ ] 수정 사유 문서화
- [ ] 즉시 Git 커밋
- [ ] 로컬에 즉시 반영
- [ ] 로컬에서 재테스트

#### 파일별 동기화 규칙

**Git으로 동기화**:
- 모든 `.py` 파일
- 모든 `.html`, `.js`, `.css` 파일
- `requirements.txt`
- 설정 파일 (단, .env 제외)

**수동 동기화** (Git 제외):
- `.env` (환경별로 다름)
- `data/` (데이터베이스 파일)
- `logs/` (로그 파일)
- `*.pyc`, `__pycache__/`

#### 주의사항
⚠️ **절대 금지**:
- 프로덕션에서 직접 코드 수정 후 커밋 안 하기
- 로컬과 프로덕션 버전 불일치 상태 유지
- .env 파일을 Git에 커밋하기

✅ **반드시 할 것**:
- 매일 시작 전 `git pull`로 최신 상태 확인
- 프로덕션 수정 시 즉시 로컬 반영
- 중요 변경 전 백업 생성

---

## 시스템 아키텍처 및 성능 목표 (2025.11.19 추가)

### 동시 사용자 목표
- **목표 동시 접속자**: 100명
- **아키텍처**: Multi-user support with user isolation
- **인증 방식**: API key-based authentication (Swing Trading)
- **세션 관리**: Stateless architecture for horizontal scaling

### 데이터베이스 전략

#### 개발 환경 (Development)
- **DB**: SQLite
- **위치**: `data/coinpulse.db`
- **용도**: 로컬 개발 및 테스트
- **설정**: 자동 폴백 (DATABASE_URL 없을 때)

#### 프로덕션 환경 (Production)
- **DB**: PostgreSQL
- **설정**: `DATABASE_URL` 환경 변수
- **연결 풀**: SQLAlchemy connection pooling
- **동시성**: 100+ concurrent connections 지원
- **트랜잭션**: ACID 보장

#### 데이터베이스 설정 예시

**개발 환경** (자동):
```python
# DATABASE_URL 없음 → SQLite 자동 사용
# 위치: data/coinpulse.db
```

**프로덕션 환경**:
```bash
# .env 파일 또는 환경 변수
DATABASE_URL=postgresql://username:password@localhost:5432/coinpulse

# 또는 Heroku/Railway 스타일
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

#### 데이터베이스 마이그레이션

**초기 설정**:
```bash
# 개발 환경 (SQLite)
python init_order_sync.py

# 프로덕션 환경 (PostgreSQL)
export DATABASE_URL=postgresql://user:pass@host:5432/coinpulse
python init_order_sync.py
```

**백업 전략**:
- 개발: `data/` 폴더 백업
- 프로덕션: PostgreSQL pg_dump 자동화
- 주기: 매일 00:00 KST

### 성능 최적화 전략

#### API 호출 최적화
- **Before**: 모든 요청 → Upbit API (느림, rate limit)
- **After**: Database-first strategy
  - 1차: 로컬 DB 조회 (95% faster)
  - 2차: API fallback (DB 없을 때만)
  - 3차: Background sync (5분마다 자동 갱신)

#### 데이터베이스 인덱싱
```sql
-- 주요 인덱스 (자동 생성)
CREATE INDEX idx_orders_market ON orders(market);
CREATE INDEX idx_orders_executed_at ON orders(executed_at);
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

#### 캐싱 전략
- **메모리 캐시**: SimpleCache (TTL: 60초)
- **DB 캐시**: Order history (갱신: 5분)
- **가격 캐시**: Current price (TTL: 1초)

### 확장성 고려사항

#### Horizontal Scaling (수평 확장)
- **로드 밸런서**: Nginx/HAProxy
- **App 서버**: Multiple instances (Gunicorn workers)
- **DB 연결**: Connection pooling (max 100 connections)
- **세션**: Stateless (JWT or API key)

#### Vertical Scaling (수직 확장)
- **CPU**: 4+ cores (Python multiprocessing)
- **RAM**: 8GB+ (캐시 및 연결 풀)
- **Disk**: SSD 권장 (DB I/O 성능)

#### 모니터링
- **서버 상태**: `/api/health` endpoint
- **DB 연결**: Connection pool monitoring
- **API 제한**: Rate limit tracking
- **에러 로그**: Centralized logging (ELK Stack)

---

## 백엔드 모듈 구조 (2025.11.06 추가)

### backend/ 폴더 구조
```
backend/
├── common/                    # 공통 모듈
│   ├── __init__.py
│   ├── upbit_api.py          # 통합 Upbit API 클라이언트 (545줄)
│   ├── config_loader.py      # 설정 및 CORS 관리 (246줄)
│   └── cache.py              # 스레드 안전 캐시 (88줄)
└── README.md
```

### 백엔드 공통 모듈 사용 규칙

1. **UpbitAPI 클래스**:
   ```python
   from backend.common import UpbitAPI, load_api_keys

   access_key, secret_key = load_api_keys()
   api = UpbitAPI(access_key, secret_key)

   # 사용 예시
   accounts = api.get_accounts()
   price = api.get_current_price('KRW-BTC')
   ```

2. **설정 로더**:
   ```python
   from backend.common import setup_cors, load_api_keys

   # CORS 설정
   setup_cors(app, 'config_file.json')

   # API 키 로드
   access_key, secret_key = load_api_keys()
   ```

3. **캐시 시스템**:
   ```python
   from backend.common import SimpleCache

   cache = SimpleCache(default_ttl=60)
   cache.set('key', value)
   data = cache.get('key')
   ```

### 중복 코드 방지 규칙

- ❌ **금지**: UpbitAPI 클래스를 서버 파일에 직접 작성
- ❌ **금지**: SimpleCache 클래스 중복 구현
- ❌ **금지**: setup_cors 함수 중복 작성
- ✅ **권장**: backend.common 모듈 import 사용

### Phase 1 완료 (2025.11.06)

- ✅ backend/common 모듈 생성 완료
- ✅ clean_upbit_server.py 마이그레이션 완료 (783 → 568줄, 27.5% 감소)
- ✅ simple_dual_server.py 마이그레이션 완료 (1710 → 1368줄, 20% 감소)
- ✅ 총 557줄의 중복 코드 제거

---

## 포트 및 설정 관리 규칙

### 절대 금지사항
- **포트 번호 하드코딩 금지**: 모든 포트는 설정 파일에서 불러와야 함
- **URL 하드코딩 금지**: API 엔드포인트는 `config.json`에서 불러와야 함

### 포트 분리 구성
- **포트 8080**: 차트 API 서버 (clean_upbit_server.py)
- **포트 8081**: 거래 API 서버 (simple_dual_server.py)
- **포트 8082**: 프론트엔드 정적 서버 (향후 추가)
- **설정 파일 기반**: 각 서버별 전용 설정 파일 사용

### 프로젝트 디렉토리
- `backend/`: 백엔드 모듈 (common, services, routes, models)
- `frontend/`: 프론트엔드 (HTML/CSS/JS 모듈화 완료)
- `docs/`: 문서 20개 (backend, features, frontend, guides, manager)
- `tests/`, `scripts/`, `logs/`, `backups/`
- `clean_upbit_server.py` (8080), `simple_dual_server.py` (8081)

### 코드 작성 규칙
1. **하드코딩 절대 금지 원칙** (2025.12.22 강화):
   - **모든 데이터는 외부 소스에서 참조**: 파일, 데이터베이스, API
   - **설정값**: JSON 설정 파일에서 로드 (포트, URL, API 키, 타임아웃 등)
   - **비즈니스 로직**: 데이터베이스에서 조회 (요금제 기능, 가격, 제한사항)
   - **UI 텍스트**: 다국어 파일 또는 CMS (향후 i18n 대응)
   - **정책/규칙**: 설정 파일 또는 DB 테이블 (변경 시 코드 수정 없이 적용)

   **❌ 금지 사례:**
   ```python
   # 하드코딩 (금지)
   if plan == 'pro':
       max_alerts = 999
       has_telegram = True
   ```

   **✅ 권장 사례:**
   ```python
   # 데이터베이스/파일 참조 (권장)
   features = get_plan_features(plan)  # PLAN_FEATURES dict에서 조회
   max_alerts = features['max_auto_trading_alerts']
   has_telegram = features['telegram_alerts']
   ```

   **적용 대상:**
   - 요금제 기능 목록 → `PLAN_FEATURES` (backend/models/plan_features.py)
   - 가격 정보 → `PLAN_PRICING` (backend/models/subscription_models.py)
   - 서버 설정 → `config.json` 파일
   - API 엔드포인트 → 환경 변수 또는 설정 파일
   - HTML 내 요금제 UI → API로 동적 로드 (하드코딩 시 DB와 불일치 위험)
2. **포트 관리 전략**:
   - 포트가 선점된 경우 포트 번호 변경 금지
   - 점유하고 있는 프로세스를 강제 중지 후 해당 포트 사용
   - `tasklist`, `netstat` 명령어로 점유 프로세스 확인 후 `taskkill` 사용
   - 중복 프로세스 실행 방지 (성능 저하 원인)
3. **인코딩 오류 방지 강화** (2025.12.17 업데이트):
   - 한글, 이모지, 특수문자로 인한 작업 중단 방지
   - **✅ 모든 파일은 UTF-8 BOM 인코딩으로 저장** (필수)
   - **✅ Windows 환경에서 한글 호환성 보장**
   - 개발 환경에서 인코딩 설정 통일
   - **✅ HTML UI 텍스트는 한글 우선** (사용자 대면)
   - **✅ 코드 내부는 영어** (변수명, 함수명, 로그)
   - **VS Code 설정**: `"files.encoding": "utf8bom"`
   - **PyCharm 설정**: File Encodings → UTF-8 with BOM
4. **기존 파일 편집 우선**: 새 파일 생성보다 기존 파일 수정
5. **중복 변수 선언 금지**: JavaScript에서 변수 중복 선언 방지
6. **캐시 무효화**: 파일 수정 시 `?v=날짜` 파라미터 사용
7. **모듈화 핵심 원칙** (2025.10.18 추가):
   - **파일 크기 제한**: 단일 파일 500줄 초과 시 모듈 분리 필수
   - **단일 책임 원칙**: 하나의 모듈은 하나의 기능만 담당
   - **명확한 인터페이스**: 모듈 간 의존성은 명시적으로 정의
   - **독립성 유지**: 각 모듈은 독립적으로 테스트 가능해야 함
   - **순환 참조 금지**: 모듈 간 순환 의존성 절대 금지

### 오류 방지 규칙
1. **문자 인코딩 규칙** (2025.12.17 업데이트):
   - **코드 내부**: 변수명, 함수명, 클래스명은 영어만 사용
   - **코드 주석**: 영어 권장 (한글 사용 시 UTF-8 BOM 필수)
   - **로그 출력**: 영어 권장 (디버깅 편의성)
   - **HTML UI**: 한글 우선 (사용자 대면 텍스트)
   - **모든 파일**: UTF-8 BOM 인코딩 필수
2. **스크립트 작성 규칙**:
   - `&&`, `||` 등 연산자 사용 시 공백으로 분리
   - 복잡한 명령어 체이닝 금지
   - 각 명령어는 별도 줄로 작성
3. **파일 구조화 규칙**:
   - **큰 구조 우선**: 메인 로직과 세부 기능 분리
   - **CSS 통합**: 모든 스타일은 `integrated.css` 하나로 통합 관리
   - **JavaScript 모듈화**: 기능별 파일 분리 (api_handler, chart_utils, trading_chart)
   - **HTML 최소화**: HTML은 구조만, 스타일과 로직은 외부 파일
4. **레이아웃 구조 규칙**:
   - **3줄 구조**: 헤더+가격정보+차트설정으로 고정
   - **반응형 디자인**: 모바일/태블릿 지원 필수
   - **테마 지원**: 라이트/다크 테마 토글 기능

### 인코딩 설정 예시 (2025.12.17 추가)

#### Python 파일
```python
# -*- coding: utf-8 -*-
"""
파일 설명
"""

# 파일 읽기/쓰기 시 인코딩 명시
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# JSON 저장 시 ensure_ascii=False 사용
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

#### HTML 파일
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>코인펄스</title>
</head>
<body>
    <h1>환영합니다</h1>
    <button>로그인</button>
</body>
</html>
```

#### VS Code 설정 (.vscode/settings.json)
```json
{
  "files.encoding": "utf8bom",
  "files.autoGuessEncoding": false,
  "[python]": {
    "files.encoding": "utf8bom"
  },
  "[html]": {
    "files.encoding": "utf8bom"
  },
  "[javascript]": {
    "files.encoding": "utf8bom"
  }
}
```

#### PyCharm 설정
1. **File → Settings → Editor → File Encodings**
2. **Global Encoding**: UTF-8
3. **Project Encoding**: UTF-8
4. **Default encoding for properties files**: UTF-8
5. ✅ **Create UTF-8 files with BOM** 체크

### 확장된 설정 파일 예시 (2025.11.06)

#### chart_server_config.json (확장)
```json
{
  "server": {
    "name": "Chart API Server",
    "host": "0.0.0.0",
    "port": 8080,
    "debug": true,
    "description": "Upbit 차트 데이터 API 서버"
  },
  "api": {
    "upbit_base_url": "https://api.upbit.com",
    "request_timeout": 5,
    "max_retries": 3
  },
  "cache": {
    "default_ttl": 60,
    "enabled": true
  },
  "cors": {
    "origins": [
      "http://localhost:8080",
      "http://127.0.0.1:8080",
      "http://localhost:8081",
      "http://127.0.0.1:8081",
      "*"
    ]
  }
}
```

#### trading_server_config.json (확장)
```json
{
  "server": {
    "name": "Trading API Server",
    "host": "0.0.0.0",
    "port": 8081,
    "debug": true,
    "description": "포트폴리오 및 거래 데이터 API 서버"
  },
  "api": {
    "upbit_base_url": "https://api.upbit.com",
    "request_timeout": 5,
    "max_retries": 3,
    "default_count": 200,
    "max_count": 200
  },
  "cors": {
    "origins": [
      "http://localhost:8080",
      "http://127.0.0.1:8080",
      "http://localhost:8081",
      "http://127.0.0.1:8081",
      "http://localhost:8082",
      "http://127.0.0.1:8082",
      "*"
    ]
  },
  "network": {
    "port_check_timeout": 1
  },
  "paths": {
    "frontend": "frontend",
    "policies": "policies"
  }
}
```

### 설정 파일 사용 규칙

1. **서버에서 설정 로드**:
   ```python
   # 설정 파일 로드
   with open('chart_server_config.json', 'r', encoding='utf-8') as f:
       CONFIG = json.load(f)

   # 설정 값 사용
   cache_ttl = CONFIG.get('cache', {}).get('default_ttl', 60)
   request_timeout = CONFIG.get('api', {}).get('request_timeout', 5)
   ```

2. **클래스에서 설정 사용**:
   ```python
   class CleanUpbitAPI:
       def __init__(self, config=None):
           self.config = config or CONFIG
           self.base_url = self.config.get('api', {}).get('upbit_base_url')
           self.request_timeout = self.config.get('api', {}).get('request_timeout', 5)
   ```

3. **CORS 설정**:
   ```python
   cors_origins = CONFIG.get('cors', {}).get('origins', ['*'])
   CORS(app, origins=cors_origins, supports_credentials=True)
   ```
```

### 코드 작성 예시
- **설정 파일**: `config.json`에 모든 URL, 포트 정의 → JavaScript에서 `fetch('config.json')` 동적 로드
- **포트 관리**: 점유 시 프로세스 종료 (`taskkill /F /PID`) 후 재시작
- **파일 구조**: HTML(구조) + CSS(통합) + JS(모듈화) 분리
- **네이밍**: 영어 변수명, 한글/이모지 금지

### 인코딩 설정 예시 (2025.12.16 업데이트)

#### Python 파일 인코딩
```python
# ✅ UTF-8 BOM 권장 (파일 저장 시 에디터에서 UTF-8 BOM 선택)
# BOM이 있으면 # -*- coding: utf-8 -*- 불필요

# 파일 읽기/쓰기 시 인코딩 명시
with open('config.json', 'r', encoding='utf-8-sig') as f:  # BOM 자동 제거
    config = json.load(f)

# JSON 파일 저장 시 ensure_ascii=False 사용
with open('data.json', 'w', encoding='utf-8-sig') as f:  # BOM 포함
    json.dump(data, f, ensure_ascii=False, indent=2)
```

#### VS Code 설정 (.vscode/settings.json)
```json
{
  "files.encoding": "utf8bom",
  "files.autoGuessEncoding": false,
  "[python]": {
    "files.encoding": "utf8bom"
  },
  "[javascript]": {
    "files.encoding": "utf8bom"
  },
  "[markdown]": {
    "files.encoding": "utf8bom"
  }
}
```

#### Git 설정 (.gitattributes)
```
# UTF-8 BOM을 유지하도록 Git 설정
*.py text eol=crlf encoding=utf-8-bom
*.js text eol=crlf encoding=utf-8-bom
*.md text eol=crlf encoding=utf-8-bom
*.json text eol=crlf encoding=utf-8-bom
```

---

## 배치 파일 작성 규칙 (2025.11.06 추가)

### Windows 배치 파일 (.bat) 규칙

#### 1. 인코딩 설정
```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
```

**규칙**:
- 파일 첫 줄: `@echo off`
- 두 번째 줄: `chcp 65001 >nul` (UTF-8 인코딩)
- 세 번째 줄: `setlocal enabledelayedexpansion` (변수 지연 확장)

#### 2. 파이프 명령 규칙

❌ **잘못된 방법** (여러 줄로 분리):
```batch
netstat -ano | findstr "LISTENING" |
findstr ":8080" >nul 2>&1
```

✅ **올바른 방법** (한 줄로 작성):
```batch
netstat -ano | findstr "LISTENING" | findstr ":8080" >nul 2>&1
```

**규칙**:
- 파이프(`|`) 명령은 반드시 한 줄로 작성
- 줄바꿈 시 명령이 분리되어 오류 발생
- 복잡한 경우 변수에 저장 후 사용

#### 3. 주석 규칙

❌ **잘못된 방법** (여러 줄 주석):
```batch
REM === 이 주석은
여러 줄로 작성됨 ===
```

✅ **올바른 방법** (각 줄에 REM):
```batch
REM === 이 주석은 ===
REM === 여러 줄로 작성됨 ===
```

**규칙**:
- 각 주석 줄은 `REM`으로 시작
- 두 번째 줄 이후 텍스트는 명령으로 인식됨
- 긴 주석은 여러 REM 줄로 분리

#### 4. 명령어 체이닝

✅ **순차 실행** (`&&`):
```batch
echo Step 1 && echo Step 2 && echo Step 3
```

✅ **별도 실행** (줄바꿈):
```batch
echo Step 1
echo Step 2
echo Step 3
```

❌ **복잡한 체이닝** (가독성 저하):
```batch
echo A && echo B || echo C && echo D || echo E
```

**규칙**:
- 간단한 명령은 `&&`로 연결 가능
- 복잡한 로직은 별도 줄로 작성
- 가독성 우선

#### 5. 백그라운드 실행

```batch
REM 백그라운드로 서버 시작
start /B "" python clean_upbit_server.py > logs\chart_server.log 2>&1

REM 대기 후 다음 서버 시작
timeout /t 3 >nul
start /B "" python simple_dual_server.py > logs\trading_server.log 2>&1
```

**규칙**:
- `/B`: 백그라운드 실행 (창 없음)
- `""`(빈 제목): 제목 없음
- `>`: 표준 출력 리다이렉트
- `2>&1`: 에러도 같은 파일로

#### 6. 오류 처리

```batch
python script.py
if %errorlevel% neq 0 (
    echo ERROR: Script failed!
    pause
    exit /b 1
)
echo Success!
```

**규칙**:
- `%errorlevel%`: 마지막 명령 종료 코드
- `0`: 성공
- `0 이외`: 실패
- `exit /b`: 배치 파일 종료 (코드 반환)

---

## 현재 상태 (2025.12.14 업데이트)

### 완료된 작업 ✅

#### Phase 6: Real-time Dashboard (WebSocket 통합 완료 - 2025.12.14)
- ✅ **WebSocket Service 구현**: backend/services/websocket_service.py (334줄)
  - Flask-SocketIO 기반 실시간 통신
  - 1초 주기 가격 업데이트 루프
  - Market 구독 시스템 (room 기반)
  - 사용자별 알림 (주문, 포지션 변경)
  - Event handlers: connect, disconnect, subscribe_market, authenticate
- ✅ **app.py WebSocket 통합**:
  - SocketIO 초기화 (line 182)
  - WebSocket 서비스 시작 (line 355)
  - Background price update loop 자동 시작
- ✅ **Real-time Dashboard UI**: frontend/realtime_dashboard.html
  - Socket.IO 클라이언트 통합
  - 연결 상태 표시 (실시간 pulse 애니메이션)
  - 8개 코인 실시간 모니터링 (BTC, ETH, XRP, ADA, SOL, DOGE, DOT, MATIC)
  - 가격 변동률 실시간 표시 (색상 코딩)
  - 포트폴리오 상태 (5초 주기 갱신)
  - 알림 피드 (최근 10개)
  - 모바일 반응형 디자인 (<768px breakpoint)
- ✅ **프로덕션 배포 완료**:
  - URL: https://coinpulse.sinsi.ai/realtime_dashboard.html
  - WebSocket 서비스 정상 작동 확인
  - 로그 검증: "[WebSocket] Service started", "Price update loop started"

#### Phase 7: Performance Optimization (완료 - 2025.12.14)
- ✅ **Performance Middleware 구현**: backend/middleware/performance.py (152줄)
  - **gzip 압축**: 500바이트 이상 JSON 응답 자동 압축 (30-70% 크기 감소)
  - **차등 캐시 전략**:
    - Holdings/Orders: 5초 캐시
    - Surge predictions: 60초 캐시
    - User/Plan: 300초 캐시
    - 기타 엔드포인트: 30초 캐시
  - **응답 시간 로깅**: 500ms 이상 소요 시 경고 로그
  - **X-Response-Time 헤더**: 모든 응답에 처리 시간 추가
  - **Cache-Control 헤더**: POST/PUT/DELETE는 no-cache
- ✅ **app.py 통합** (line 173-175):
  - CORS 설정 후 performance middleware 초기화
  - before_request/after_request hooks 자동 적용
- ✅ **성능 검증**:
  - 테스트 엔드포인트: /api/auto-trading/status/1
  - 응답 헤더 확인: `Cache-Control: public, max-age=30`
  - 응답 시간: X-Response-Time: 0.070s
  - 로그: "[Performance] Middleware configured - gzip compression + cache headers enabled"

#### Phase 8: 급등 알림 시스템 정리 (완료 - 2025.12.22)
- ✅ **시스템 사양 문서 작성**: docs/features/SURGE_ALERT_SYSTEM.md
  - 용어 정의 (급등 모니터링, 급등 신호, 급등 알림, 관심 코인)
  - 시스템 동작 흐름 (스캔 → 필터링 → 알림 전송)
  - 요금제별 기능 (Free: view only, Basic: 주 3회, Pro: 주 10회)
  - 시나리오별 동작 (5가지 시나리오 정의)
  - 데이터베이스 스키마 (surge_alerts, user_favorite_coins)

- ✅ **plan_features.py 용어 통일**:
  - `max_auto_trading_alerts` → `max_surge_alerts`
  - `favorite_coins` 필드 추가
  - 상세 주석 추가 (시스템 개요, 요금제별 제공량)
  - 참고 문서 링크 추가

- ✅ **프론트엔드 UI 개선**:
  - "거래 탭" → "관심 코인" 탭으로 명칭 변경
  - 설정 설명 추가: "급등 알림을 우선적으로 받을 코인 선택"
  - "자동 거래 활성화" → "급등 알림 받기" 체크박스로 변경
  - 별 아이콘으로 탭 아이콘 변경

- ✅ **주요 개선사항**:
  - 용어 혼란 해소 (자동매매 알림 vs 급등 알림 명확히 구분)
  - 관심 코인 개념 도입 (최대 5개 선택)
  - 요금제별 알림 횟수 제한 명확화
  - 이미 보유 중인 코인 처리 정책 정의

**참고 문서**: [SURGE_ALERT_SYSTEM.md](docs/features/SURGE_ALERT_SYSTEM.md)

#### 데이터베이스 통합 (Priority 1 완료 - 2025.11.19)
- ✅ **OrderSyncService 구현**: backend/services/order_sync_service.py (270줄)
  - Initial full sync: 최대 10,000개 주문 동기화
  - Incremental sync: 마지막 동기화 이후 신규 주문만 조회
  - Native upsert: SQLite/PostgreSQL 모두 지원
- ✅ **초기 주문 동기화**: 3,070개 거래 이력 DB 저장 완료
- ✅ **Database-first API 전략**: backend/routes/holdings_routes.py
  - `/api/orders` 엔드포인트 수정
  - 1차: DB 조회 (95% faster, no rate limit)
  - 2차: API fallback (DB 없을 때만)
  - Response에 `"source": "database"` 필드 추가
- ✅ **백그라운드 동기화 스케줄러**: backend/services/background_sync.py
  - 5분마다 자동 incremental sync
  - 별도 스레드로 실행 (daemon=True)
  - 서버 시작 시 자동 시작
- ✅ **성능 개선 확인**:
  - Before: 매 요청마다 Upbit API 호출 (느림, rate limit)
  - After: DB 조회 (instant, unlimited)
  - 예상 API 호출 감소: 95%

#### 관리 시스템 개발 (2025.12.07)
- ✅ **Beta Tester System**: backend/routes/admin.py
  - 베타 테스터 관리 API 엔드포인트 (/api/admin/beta-testers)
  - backend/models/beta_tester.py 모델 정의
  - 가입일(joined_at), 이메일, 상태 관리

- ✅ **User Benefits System**: backend/routes/benefits_admin.py
  - 사용자 혜택 관리 시스템 (/api/admin/benefits)
  - backend/models/user_benefit.py 모델 정의
  - 만료일 기반 혜택 관리

- ✅ **Plan Config System**: backend/routes/plan_admin.py
  - 구독 플랜 설정 관리 (/api/admin/plans)
  - backend/models/plan_config.py 모델 정의
  - 동적 플랜 구성 기능

- ✅ **Suspension System**: backend/routes/suspension_admin.py
  - 사용자 정지 관리 시스템 (/api/admin/suspensions)
  - backend/models/user_suspension.py 모델 정의
  - 정지 기간 및 사유 관리

#### 프로덕션 배포 및 수정 (2025.12.13)
- ✅ **프로덕션 서버 배포**: Vultr (158.247.222.216)
  - PostgreSQL 데이터베이스 (23개 테이블)
  - Nginx reverse proxy + SSL (coinpulse.sinsi.ai)
  - systemd 서비스 관리 (자동 재시작)
  - SSH 키 기반 인증

- ✅ **Beta Tester API 수정**: backend/routes/admin.py
  - 컬럼명 수정: created_at → joined_at
  - 데이터베이스 스키마 정합성 확보
  - API 500 에러 해결

- ✅ **Upbit API 통합**: 외부 API 연동
  - IP 화이트리스트 업데이트 (158.247.222.216)
  - query_hash 구현 (SHA512 해싱)
  - Accounts, Orders, API Keys 엔드포인트 검증
  - JWT 인증 토큰 생성

- ✅ **Subscription 모델 수정**: backend/models/subscription_models.py
  - 테이블명 수정: subscriptions → user_subscriptions
  - ForeignKey 참조 수정
  - 중복 인덱스 오류 해결 (ix_subscriptions_user_id)
  - 임시로 구독 라우트 비활성화

#### 프론트엔드 모듈화 Phase 2 완료 (2025.11.13)
- ✅ **DataLoader 모듈 추출**: 985줄 - 모든 데이터 로딩 작업
- ✅ **RealtimeUpdates 모듈 추출**: 364줄 - 실시간 UI 업데이트
- ✅ **AutoTradingController 모듈 추출**: 235줄 - 자동거래 컨트롤
- ✅ **메인 파일 축소**: trading_chart_working.js 3,819 → 2,321줄 (39.2% 감소)
- ✅ **브라우저 테스트 통과**: Phase 2 관련 에러 없음

#### 프론트엔드 모듈화 Phase 3 완료 (2025.11.13)
- ✅ **ChartManager 모듈**: 408줄 - 차트 생성 및 관리
- ✅ **IndicatorCalculator 모듈**: 379줄 - 기술적 지표 계산
- ✅ **IndicatorRenderer 모듈**: 479줄 - 지표 렌더링
- ✅ **ChartUtilities 모듈**: 322줄 - 유틸리티 함수
- ✅ **chart_utils.js 축소**: 1,547 → 282줄 (81.8% 감소)
- ✅ **모든 파일 < 500줄**: 100% 준수
- ✅ **하위 호환성 유지**: breaking change 0개

#### 백엔드 모듈화 (Phase 1 완료 - 2025.11.06)
- ✅ **backend/common 모듈 생성**: UpbitAPI, SimpleCache, config_loader
- ✅ **simple_dual_server.py 마이그레이션**: 1710 → 1368줄 (20% 감소)
- ✅ **clean_upbit_server.py 마이그레이션**: 783 → 568줄 (27.5% 감소)
- ✅ **중복 코드 제거**: 총 557줄 제거 (22.3% 전체 감소)
- ✅ **단일 소스 원칙**: 모든 API 로직을 backend.common에 통합

#### 프로젝트 구조 정리 (2025.11.06)
- ✅ **문서 정리**: 88개 MD 파일을 docs/ 폴더로 체계화
- ✅ **테스트 파일 정리**: tests/backend, tests/frontend 구조 생성
- ✅ **백업 파일 정리**: backups/server_backups, backups/database_backups
- ✅ **스크립트 정리**: scripts/analysis 폴더로 이동
- ✅ **루트 디렉토리 정리**: 필수 파일만 유지

#### 설정 파일 기반 구성 (2025.11.06)
- ✅ **하드코딩 제거**: URL, 포트, 타임아웃 등 모든 값을 설정 파일로
- ✅ **설정 파일 확장**: cache, cors, network 섹션 추가
- ✅ **환경별 설정**: development/production 구분 가능 구조

#### 기존 완료 항목 (2025.10.18)
- ✅ **포트 분리 구성**: 차트(8080), 거래(8081)
- ✅ **3줄 구조 레이아웃**: 헤더+가격정보+차트설정
- ✅ **CSS 통합**: integrated.css 하나로 통합 관리
- ✅ **JavaScript 모듈화**: 6개 모듈 추출 (3,114줄)
- ✅ **반응형 디자인**: 모바일/태블릿 지원
- ✅ **테마 지원**: 라이트/다크 테마 토글
- ✅ **지지저항선 개선**: ATR 기반, 클러스터링, 시간가중

### 전체 모듈화 성과 📊

| Phase | 완료일 | 모듈 수 | 감소 줄 수 | 상태 |
|-------|--------|---------|-----------|------|
| **Phase 1** | 2025-10-18 | 6개 | 3,114줄 | ✅ 완료 |
| **Phase 2** | 2025-11-13 | 3개 | 1,498줄 | ✅ 완료 |
| **Phase 3** | 2025-11-13 | 4개 | 1,265줄 | ✅ 완료 |
| **총계** | - | **13개** | **5,877줄** | ✅ 완료 |

**메인 차트 파일 크기 변화:**
- 시작: 3,819줄 (거대한 단일 파일)
- 현재: 282줄 (모듈화된 래퍼)
- **감소율: 92.6%** 🎯

### 프로덕션 준비 완료 상태 🎉

**Phase 1~7 모두 완료**: CoinPulse는 이제 프로덕션 환경에서 운영 가능한 상태입니다.

| Phase | 상태 | 완료일 | 핵심 기능 |
|-------|------|--------|----------|
| Phase 1 | ✅ 완료 | 2025.11.19 | Database Integration (Order Sync) |
| Phase 2 | ✅ 완료 | 2025.11.20 | Surge Prediction (81.25% accuracy) |
| Phase 3 | ✅ 완료 | 2025.11.21 | Subscription System (Premium/Enterprise) |
| Phase 4 | ✅ 완료 | 2025.12.10 | Telegram Bot (Surge Alerts) |
| Phase 5 | ✅ 완료 | 2025.12.11 | Auto-Trading System |
| Phase 6 | ✅ 완료 | 2025.12.14 | Real-time Dashboard (WebSocket) |
| Phase 7 | ✅ 완료 | 2025.12.14 | Performance Optimization |

### 다음 단계 🎯 (선택사항)

#### 운영 및 성장 단계
- 🔲 **사용자 확보 전략**:
  - Beta tester 모집 캠페인
  - 사용자 가이드 및 튜토리얼 제작
  - 커뮤니티 구축 (Discord, Telegram)

- 🔲 **결제 시스템 완성**:
  - Stripe/PayPal 통합 (Toss Payments 대체)
  - 구독 자동 갱신 로직
  - 환불 정책 구현

- 🔲 **모니터링 및 분석**:
  - 사용자 행동 분석 (Google Analytics)
  - 에러 트래킹 (Sentry)
  - 성능 모니터링 대시보드

- 🔲 **추가 기능 개발**:
  - 이메일/SMS 알림
  - 모바일 앱 (React Native)
  - 다중 거래소 지원 (Binance, Bybit)
  - AI 기반 포트폴리오 추천

## 모듈화 규칙 (2025.10.18 신규)

> 📘 **상세 문서**: [`docs/guides/MODULARIZATION_RULES.md`](docs/guides/MODULARIZATION_RULES.md)

### 핵심 원칙
- **파일 크기 제한**: 500줄 초과 시 반드시 분리
- **단일 책임 원칙**: 하나의 모듈은 하나의 기능만
- **명시적 의존성**: 전역 변수 접근 금지, 생성자 주입 사용
- **3단계 테스트**: 단위 → 통합 → 시각 테스트 필수

### 모듈 작성 패턴
```javascript
class ModuleName {
    constructor(chartInstance) {
        this.chart = chartInstance;
    }
    publicMethod() { /* 구현 */ }
}
```

### 체크리스트
- [ ] 파일 크기 500줄 이하
- [ ] 순환 참조 없음
- [ ] 독립적으로 테스트 가능
- [ ] JSDoc 주석 완비

## 새로운 규칙 추가 (2025.10.04-10.18)
- ✅ **3줄 구조 고정**: 레이아웃 변경 시 3줄 구조 유지
- ✅ **CSS 통합 관리**: 여러 CSS 파일 대신 integrated.css 하나만 사용
- ✅ **JavaScript 비동기 로드**: 설정 파일을 비동기로 로드하여 성능 향상
- ✅ **프로젝트 정리 규칙**: 중복 파일 정기적 정리, 구조 단순화
- ✅ **성능 최적화**: 중복 프로세스 방지, 포트 충돌 해결
- 🆕 **모듈화 우선**: 2936줄 파일을 8개 모듈로 분리 (진행 중)
- 🆕 **알고리즘 개선**: 업계 표준 방식 적용 (ATR, 클러스터링 등)
- 🆕 **에러 처리 패턴**: 모든 모듈 일관된 에러 처리 적용
- 🆕 **3단계 테스트**: 단위/통합/시각 테스트 필수
- 🆕 **성능 기준**: 로딩 2초, 토글 500ms 목표
- 🆕 **Git 규칙**: [TYPE] 형식의 커밋 메시지 사용

## 프로젝트 구조

### 핵심 디렉토리
- `backend/`: 백엔드 모듈 (common, services, routes, models)
- `frontend/`: 프론트엔드 (HTML/CSS/JS, 모듈화 완료)
- `docs/`: 문서 (backend, features, frontend, guides, manager - 총 20개)
- `tests/`: 테스트 파일 (backend, frontend)
- `logs/`: 서버 로그
- `archives/`: 백업 및 임시 파일

### 파일 관리 규칙
- **백업**: `archives/backups/` (30일 자동 삭제)
- **문서**: `docs/[category]/` (루트에는 README.md, CLAUDE.md만)
- **로그**: `logs/` (7일 압축/삭제)
- **모듈화**: 500줄 초과 시 분리 필수

---

## 💎 요금제 구조 (2025.12.22 업데이트)

### 핵심 원칙
- **3가지 플랜만**: Free, Basic, Pro
- **명확한 용어**: "봇" → "자동매매 알림"
- **핵심 기능만**: 사용자가 실제 사용하는 기능만 포함

### 요금제별 기능

| 기능 | Free | Basic | Pro | 설명 |
|------|------|-------|-----|------|
| **manual_trading** | ❌ | ✅ | ✅ | 수동 거래 가능 여부 |
| **max_auto_trading_alerts** | 0 | 1 | 무제한 | 자동매매 알림 개수 |
| **telegram_alerts** | ❌ | ❌ | ✅ | 텔레그램 실시간 알림 |
| **surge_monitoring** | ✅ | ✅ | ✅ | 급등 모니터링 (기본) |
| **advanced_indicators** | ❌ | ❌ | ✅ | 고급 기술적 지표 |
| **backtesting** | ❌ | ❌ | ✅ | 전략 백테스팅 |
| **priority_support** | ❌ | ❌ | ✅ | 우선 고객 지원 |

### 플랜 상세 설명

#### Free (무료)
- 급등 모니터링만 가능
- 자동매매 알림 사용 불가
- 기본 기능 체험

#### Basic (베이직)
- 수동 거래 가능
- **1개의 자동매매 알림** 설정 가능
- 급등 모니터링 + 기본 지표

#### Pro (프로)
- 수동 거래 가능
- **무제한 자동매매 알림**
- 텔레그램 실시간 알림
- 고급 지표 + 백테스팅
- 우선 고객 지원

### 제거된 기능 (2025.12.22)
- ~~email_alerts~~ (이메일 알림 제거)
- ~~indicators~~ (advanced_indicators로 통합)
- ~~api_access~~ (현재 미사용)
- ~~webhook_access~~ (현재 미사용)
- ~~data_export~~ (현재 미사용)
- ~~advanced_strategies~~ (기본 기능으로 통합)
- ~~enterprise 플랜~~ (사용 안함)

### 코드 참조
- **정의**: `backend/models/plan_features.py` - PLAN_FEATURES 딕셔너리
- **API**: `app.py` - `/api/user/plan` 엔드포인트
- **UI**: `frontend/auto_trading_settings.html` - 요금제별 접근 제어

---

## 참고 문서

### 관리자 가이드 (docs/admin/) - 2025.12.13 신규
- `BETA_TESTER_GUIDE.md` - 베타 테스터 관리 가이드
- `BENEFITS_SYSTEM.md` - 사용자 혜택 시스템
- `ADMIN_SUMMARY.md` - 관리자 시스템 요약
- `SYSTEM_SUMMARY.md` - 전체 시스템 요약
- `PLAN_MANAGEMENT.md` - 구독 플랜 관리
- `SUSPENSION_SYSTEM.md` - 사용자 정지 시스템
- `USER_BENEFITS.md` - 사용자 혜택 가이드
- `VULTR_SERVER_INFO.md` - Vultr 서버 정보
- `UPLOAD_GUIDE.md` - WinSCP 업로드 가이드

### 백엔드 문서 (docs/backend/)
- `BACKEND_COMPLETION_SUMMARY.md` - 백엔드 모듈 요약
- `BACKEND_MODULARIZATION_PLAN.md` - 백엔드 모듈화 계획
- `POSTGRESQL_SETUP_GUIDE.md` - PostgreSQL 설정 가이드

### 기능 문서 (docs/features/)
- `TRADE_MARKERS_DOCUMENTATION.md` - 거래 마커 기능
- `UNDO_REDO_FEATURE.md` - 실행 취소/다시 실행
- `VERTICAL_LINE_IMPLEMENTATION.md` - 수직선 구현

### 프론트엔드 문서 (docs/frontend/)
- `FEATURE_CHECKLIST.md` - 기능 체크리스트
- `VERIFICATION_GUIDE.md` - 검증 가이드

### 가이드 (docs/guides/)
- `AUTO_TRADING_GUIDE.md` - 자동 거래 가이드
- `CODING_GUIDELINES.md` - 코딩 가이드라인
- `GIT_SETUP_GUIDE.md` - Git 설정 가이드
- `MODULARIZATION_RULES.md` - 모듈화 규칙 (상세)
- `QUICK_FIX_GUIDE.md` - 빠른 수정 가이드
- `TESTING_GUIDE.md` - 테스트 가이드

### 서버 관리 (docs/manager/)
- `MANAGER_README.md` - 서버 관리자 가이드
- `MANAGER_USAGE_GUIDE.md` - 사용 방법
- `SERVICE_MANAGER_README.md` - 서비스 관리자 README

### 프로젝트 문서 (docs/)
- `COINPULSE_FEATURE_CHECKLIST.md` - 기능 체크리스트
- `FEATURE_REGISTRY.md` - 기능 레지스트리
- `PAYMENT_WORKFLOW_GUIDE.md` - 결제 워크플로우
- `TODO_AND_ROADMAP.md` - TODO 및 로드맵