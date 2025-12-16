# CoinPulse - Quick Start Guide

## 🚀 통합 서버로 빠르게 시작하기

### 1. 환경 설정

#### Step 1: 환경 변수 파일 생성
```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일을 편집하여 Upbit API 키 입력
# UPBIT_ACCESS_KEY=your_actual_access_key
# UPBIT_SECRET_KEY=your_actual_secret_key
```

#### Step 2: 의존성 설치
```bash
# Python 가상 환경 생성 (선택사항)
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

---

### 2. 서버 실행

#### 방법 1: 실행 스크립트 사용 (권장)

**Windows:**
```cmd
start_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh
```

#### 방법 2: 직접 실행
```bash
python app.py
```

---

### 3. 접속 확인

서버가 시작되면 브라우저에서 접속:
- **메인 페이지**: http://localhost:8080
- **로그인**: http://localhost:8080/login.html
- **대시보드**: http://localhost:8080/dashboard.html
- **차트**: http://localhost:8080/trading_chart.html

**API Health Check:**
- http://localhost:8080/health
- http://localhost:8080/api/status

---

## 📋 주요 기능

### 인증 시스템
- `/api/auth/register` - 회원가입
- `/api/auth/login` - 로그인
- `/api/auth/logout` - 로그아웃
- `/api/auth/refresh` - 토큰 갱신
- `/api/auth/me` - 사용자 정보

### 포트폴리오
- `/api/holdings` - 보유 자산 조회
- `/api/orders` - 주문 내역 조회

### 자동매매
- `/api/auto-trading/start` - 자동매매 시작
- `/api/auto-trading/stop` - 자동매매 중지
- `/api/auto-trading/status` - 상태 조회

### 구독 관리
- `/api/subscription/plans` - 구독 플랜 조회
- `/api/payment-requests` - 결제 요청 생성 (계좌이체)
- `/api/subscription/status` - 구독 상태 조회

**💳 결제 방식**: 계좌이체 + 관리자 승인  
**자세한 안내**: `docs/PAYMENT_WORKFLOW_GUIDE.md` 참조

---

## 🔧 설정 파일

### config.json
서버 전반적인 설정을 관리합니다:
- 서버 포트, 호스트
- 데이터베이스 URL
- CORS 설정
- 캐시 설정
- 보안 설정

### .env
민감한 정보를 저장합니다 (절대 커밋하지 마세요!):
- Upbit API 키
- 데이터베이스 비밀번호
- JWT 시크릿 키
- SMTP 설정

---

## 🗄️ 데이터베이스 초기화

### 처음 실행 시 자동 초기화
서버가 처음 시작될 때 자동으로 데이터베이스가 생성됩니다.

### 수동 초기화 (필요시)
```bash
# 인증 데이터베이스 초기화
python init_auth_db.py

# 주문 동기화 초기화
python init_order_sync.py

# 구독 시스템 초기화
python init_subscription_db.py
```

---

## 🐛 문제 해결

### 포트가 이미 사용 중입니다
```bash
# Windows:
netstat -ano | findstr :8080
taskkill /F /PID [프로세스ID]

# Linux/Mac:
lsof -ti:8080 | xargs kill -9
```

### 데이터베이스 오류
```bash
# 데이터베이스 파일 삭제 후 재생성
rm data/coinpulse.db
python init_auth_db.py
```

### 의존성 오류
```bash
# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

---

## 📚 더 알아보기

- **전체 문서**: `docs/` 폴더 참조
- **프로젝트 지침**: `CLAUDE.md`
- **웹 서비스 완성 가이드**: `docs/WEB_SERVICE_COMPLETION_CHECKLIST.md`

---

## 🎯 다음 단계

1. **회원가입**: http://localhost:8080/signup.html
2. **로그인**: http://localhost:8080/login.html
3. **Upbit API 키 등록**: 대시보드에서 설정
4. **자동매매 시작**: 전략 설정 후 실행

---

**문제가 발생하면 `logs/` 폴더의 로그 파일을 확인하세요!**
