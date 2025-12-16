# 🚀 CoinPulse - AI 기반 암호화폐 자동매매 플랫폼

**버전**: 2.0  
**업데이트**: 2025-12-10  
**완성도**: 98%

---

## 📊 프로젝트 개요

CoinPulse는 업비트(Upbit) 거래소를 기반으로 하는 암호화폐 자동매매 및 포트폴리오 관리 플랫폼입니다.

### **핵심 기능**
- ✅ **TradingView 차트 시스템** - 전문 트레이딩 차트
- ✅ **기술적 지표** - MA, RSI, MACD, Bollinger Bands, SuperTrend
- ✅ **그리기 도구** - 추세선, 피보나치, 지지저항선
- ✅ **자동매매 시스템** - RSI/MACD 기반 자동 거래
- ✅ **포트폴리오 추적** - 실시간 보유 자산 관리
- ✅ **구독 시스템** - Free/Premium/Pro 플랜
- ✅ **관리자 대시보드** - 완전한 백오피스 시스템

---

## 🎯 주요 특징

### **1. 로컬 실행 방식**
- 사용자 PC에서 직접 실행 (Desktop App)
- 개인 API 키 사용으로 보안 강화
- 업비트 IP 제한 문제 해결

### **2. 계좌이체 결제 시스템**
- **방식**: 은행 계좌이체 + 관리자 수동 승인
- **이유**: 암호화폐 거래 서비스는 대부분 PG사 승인 제한
- **자세한 안내**: `docs/PAYMENT_WORKFLOW_GUIDE.md`

### **3. 완전한 관리 시스템**
- Admin Dashboard v2.0 (5개 탭)
- 사용자/결제/베타테스터/플랜 관리
- 실시간 통계 및 모니터링

---

## 🚀 빠른 시작

### **1. 환경 설정**

```bash
# 저장소 클론
git clone <repository-url>
cd coinpulse

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집: UPBIT API 키 입력
```

### **2. 의존성 설치**

```bash
# Python 가상환경 (선택)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### **3. 데이터베이스 초기화**

```bash
# PostgreSQL 필요 (기본: localhost:5432)
python create_tables.py
```

### **4. 서버 실행**

```bash
# 통합 서버 (권장)
python app.py

# 또는 스크립트 사용
start_server.bat  # Windows
./start_server.sh  # Linux/Mac
```

### **5. 접속**

- **메인**: http://localhost:8080
- **로그인**: http://localhost:8080/login.html
- **차트**: http://localhost:8080/trading_chart.html
- **Admin**: http://localhost:8080/admin.html

---

## 📁 프로젝트 구조

```
coinpulse/
├── backend/
│   ├── routes/          # API 엔드포인트
│   │   ├── auth.py
│   │   ├── holdings_routes.py
│   │   ├── auto_trading_routes.py
│   │   ├── payment.py
│   │   └── users_admin.py
│   ├── services/        # 비즈니스 로직
│   │   ├── auto_trading_engine.py
│   │   ├── subscription.py
│   │   └── toss_payment.py (deprecated)
│   ├── models/          # 데이터 모델
│   └── database/        # DB 연결 관리
│
├── frontend/
│   ├── *.html           # 웹 페이지
│   ├── css/             # 스타일시트
│   └── js/              # JavaScript
│
├── docs/
│   ├── PAYMENT_WORKFLOW_GUIDE.md  # 결제 시스템 가이드
│   ├── TODO_AND_ROADMAP.md        # 개발 로드맵
│   └── COINPULSE_FEATURE_CHECKLIST.md
│
├── app.py               # 메인 서버
├── create_tables.py     # DB 초기화
├── requirements.txt     # 의존성
└── .env                 # 환경 변수 (Git 제외)
```

---

## 🔑 환경 변수

`.env` 파일 필수 설정:

```bash
# Upbit API (필수)
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key

# 데이터베이스
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coinpulse

# 서버
SERVER_PORT=8080
SECRET_KEY=your_secret_key

# 관리자
ADMIN_TOKEN=coinpulse_admin_2024_secure_token
```

---

## 💳 구독 플랜

### **Free Plan (₩0/월)**
- 기본 차트 조회
- 제한적 기능

### **Premium Plan (₩19,900/월)**
- 실시간 자동매매
- 모든 기술적 지표
- 포트폴리오 추적

### **Pro Plan (₩49,900/월)**
- Premium 모든 기능
- 고급 전략
- 우선 지원

**결제 방법**: 계좌이체 + 관리자 승인  
**상세 안내**: `docs/PAYMENT_WORKFLOW_GUIDE.md`

---

## 🛠️ 기술 스택

### **Backend**
- Python 3.8+
- Flask
- PostgreSQL
- SQLAlchemy
- JWT Authentication

### **Frontend**
- HTML5 / CSS3 / JavaScript
- TradingView Charting Library
- Bootstrap 5

### **Infrastructure**
- Nginx (프록시)
- systemd (서비스 관리)
- Let's Encrypt (SSL)

---

## 📚 주요 문서

### **개발 가이드**
- `QUICKSTART.md` - 빠른 시작 가이드
- `docs/TODO_AND_ROADMAP.md` - 개발 로드맵
- `docs/COINPULSE_FEATURE_CHECKLIST.md` - 기능 체크리스트

### **운영 가이드**
- `docs/PAYMENT_WORKFLOW_GUIDE.md` - 결제 시스템
- `COMPLETE_ADMIN_SUMMARY.txt` - 관리자 시스템
- `BETA_TESTER_GUIDE.txt` - 베타 테스터 관리

---

## 🔐 보안

### **API 키 관리**
- `.env` 파일에만 저장 (Git 제외)
- 절대 하드코딩 금지
- 정기적 키 교체 권장

### **관리자 인증**
- Admin Token 기반 인증
- Bearer Token 방식
- HTTPS 필수

### **데이터베이스**
- 비밀번호 bcrypt 해싱
- JWT 토큰 기반 세션
- SQL Injection 방지

---

## 🚨 문제 해결

### **포트 충돌**
```bash
# 프로세스 확인
netstat -ano | findstr :8080

# 프로세스 종료
taskkill /F /PID <PID>
```

### **데이터베이스 오류**
```bash
# DB 재생성
rm data/coinpulse.db  # SQLite (deprecated)
python create_tables.py
```

### **API 키 오류**
```bash
# .env 파일 확인
cat .env | grep UPBIT

# 키 재발급
# Upbit 웹사이트 → API 관리 → 새 키 발급
```

---

## 📈 개발 현황

### **완성된 기능** (98%)
- [x] TradingView 차트 시스템
- [x] 기술적 지표 (5종)
- [x] 그리기 도구
- [x] 자동매매 엔진
- [x] 포트폴리오 관리
- [x] 인증 시스템
- [x] 구독 시스템
- [x] 관리자 대시보드
- [x] 결제 시스템 (계좌이체)

### **진행 중** (2%)
- [ ] 이메일 알림 시스템
- [ ] 실시간 통계 API
- [ ] 모바일 최적화

---

## 🤝 기여

현재 비공개 프로젝트입니다.

---

## 📄 라이선스

Proprietary - All Rights Reserved

---

## 📞 문의

**프로젝트**: CoinPulse  
**회사**: (주)신시AI  
**웹사이트**: https://coinpulse.sinsi.ai  
**관리자**: root@158.247.222.216

---

**최종 업데이트**: 2025-12-10  
**문서 버전**: 2.0