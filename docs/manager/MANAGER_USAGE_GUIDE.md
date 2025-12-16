# CoinPulse Manager 사용 가이드

**Version**: 2.0 (Background Mode)
**Updated**: 2025-11-04

---

## 🚀 빠른 시작

### 관리자 도구 실행

```cmd
# CMD 창 열기
cd D:\Claude\Projects\Active\coinpulse
coinpulse_manager_v2.bat
```

**중요**: 탐색기에서 더블클릭하지 말고 **CMD에서 실행**하세요!

---

## 📋 메뉴 옵션

```
========================================
  CoinPulse Server Manager
========================================

[1] Start All Servers (Background)
[2] Stop All Servers
[3] Check Server Status
[4] Restart Servers
[5] View Logs
[6] Run Diagnostics
[7] Open Browser
[0] Exit

========================================
```

---

## 🔧 각 옵션 설명

### [1] Start All Servers (Background)

**기능**: 차트 서버와 트레이딩 서버를 백그라운드로 시작

**동작**:
1. 포트 8080, 8081 충돌 확인 및 자동 해결
2. Chart Server 백그라운드 실행 → `logs\chart_server.log`
3. Trading Server 백그라운드 실행 → `logs\trading_server.log`
4. 각 서버 시작 확인

**출력 예시**:
```
[1/2] Starting Chart Server (port 8080) in background...
      [OK] Chart Server started successfully
[2/2] Starting Trading Server (port 8081) in background...
      [OK] Trading Server started successfully

========================================
  Servers Running in Background
========================================

Chart Server:   http://localhost:8080
Trading Server: http://localhost:8081

Frontend: http://localhost:8080/frontend/trading_chart.html

Logs:
  - logs\chart_server.log
  - logs\trading_server.log
```

**특징**:
- ✅ 새 창이 안 열림 (백그라운드 실행)
- ✅ 로그가 파일로 저장됨
- ✅ CMD 창을 닫아도 서버 계속 실행
- ✅ 자동으로 포트 충돌 해결

---

### [2] Stop All Servers

**기능**: 실행 중인 모든 서버 중지

**동작**:
1. 포트 8080, 8081을 사용하는 프로세스 찾기
2. 모든 프로세스 강제 종료

**사용 시기**:
- 서버를 완전히 중지할 때
- 설정 파일 수정 후
- 문제 발생 시 재시작 전

---

### [3] Check Server Status

**기능**: 현재 서버 실행 상태 확인

**출력 정보**:
- Chart Server 상태 (RUNNING / STOPPED)
- Trading Server 상태 (RUNNING / STOPPED)
- 포트 및 PID 정보
- 실행 중인 Python 프로세스

**출력 예시**:
```
========================================
  Server Status
========================================

[Chart Server - Port 8080]
Status: RUNNING
  TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING       16364

[Trading Server - Port 8081]
Status: RUNNING
  TCP    0.0.0.0:8081           0.0.0.0:0              LISTENING       948

[Python Processes]
python.exe                   16364 Console                    1     26,840 K
python.exe                     948 Console                    1     53,052 K
```

---

### [4] Restart Servers

**기능**: 서버 재시작 (중지 → 시작)

**동작**:
1. 모든 서버 중지
2. 2초 대기
3. Chart Server 백그라운드 시작
4. Trading Server 백그라운드 시작

**사용 시기**:
- 설정 변경 후 적용
- 서버가 응답하지 않을 때
- 메모리 정리

---

### [5] View Logs

**기능**: 서버 로그 파일 확인

**서브 메뉴**:
```
Select log to view:
[1] Chart Server Log
[2] Trading Server Log
[0] Back to menu
```

**로그 위치**:
- `logs\chart_server.log` - Chart Server 출력
- `logs\trading_server.log` - Trading Server 출력

**팁**: 에러 발생 시 로그를 먼저 확인하세요!

---

### [6] Run Diagnostics

**기능**: 시스템 진단 및 설정 확인

**확인 항목**:
1. **Python 설치**: `python --version`
2. **필수 파일**:
   - `clean_upbit_server.py`
   - `simple_dual_server.py`
3. **설정 파일**:
   - `chart_server_config.json`
   - `trading_server_config.json`
   - `frontend\config.json`
4. **포트 상태**: 8080, 8081
5. **현재 디렉토리**

**출력 예시**:
```
========================================
  System Diagnostics
========================================

[Python Installation]
Python 3.11.5
OK: Python is installed

[Required Files]
OK: clean_upbit_server.py
OK: simple_dual_server.py

[Configuration Files]
OK: chart_server_config.json
OK: trading_server_config.json
OK: frontend\config.json

[Port Status]
All ports are available

[Current Directory]
D:\Claude\Projects\Active\coinpulse
```

---

### [7] Open Browser

**기능**: 기본 브라우저로 프론트엔드 열기

**동작**:
1. Chart Server (포트 8080) 실행 확인
2. 실행 중이 아니면 시작 여부 물어봄
3. 브라우저에서 `http://localhost:8080/frontend/trading_chart.html` 열기

**편의 기능**: 서버가 꺼져있으면 자동으로 시작 가능

---

### [0] Exit

**기능**: 관리자 도구 종료

**주의**: 서버는 **계속 실행**됩니다!
- 서버도 함께 중지하려면 [2] Stop All Servers 먼저 실행

---

## 📁 로그 파일 관리

### 로그 저장 위치

```
D:\Claude\Projects\Active\coinpulse\logs\
├── chart_server.log       # Chart Server 로그
└── trading_server.log     # Trading Server 로그
```

### 로그 확인 방법

#### 방법 1: 관리자 도구에서
```
[5] View Logs → [1] or [2]
```

#### 방법 2: 직접 열기
```cmd
type logs\chart_server.log
type logs\trading_server.log
```

#### 방법 3: 실시간 모니터링 (PowerShell)
```powershell
Get-Content logs\chart_server.log -Wait -Tail 20
```

### 로그 정리

로그 파일이 너무 크면:
```cmd
# 로그 백업
copy logs\chart_server.log logs\chart_server_backup.log

# 로그 삭제 (서버 재시작 시 자동 생성)
del logs\*.log
```

---

## 🐛 문제 해결

### 서버가 시작되지 않을 때

**증상**: `[ERROR] Chart Server failed to start`

**해결 순서**:
1. 로그 확인: `[5] View Logs`
2. Python 확인: `[6] Run Diagnostics`
3. 포트 확인: `netstat -ano | findstr ":8080 :8081"`
4. 기존 프로세스 종료: `[2] Stop All Servers`
5. 재시작: `[1] Start All Servers`

### 포트가 이미 사용 중

**증상**: `Port 8080 is already in use`

**해결**:
- 자동 해결됨 (관리자 도구가 자동으로 프로세스 종료)
- 수동: `[2] Stop All Servers` → `[1] Start All Servers`

### 브라우저에서 연결 안 됨

**증상**: `ERR_CONNECTION_REFUSED`

**해결**:
1. 서버 상태 확인: `[3] Check Server Status`
2. 둘 다 RUNNING이 아니면: `[1] Start All Servers`
3. 브라우저 캐시 삭제: `Ctrl + Shift + Delete`
4. 강력 새로고침: `Ctrl + Shift + R`

### 로그에 에러가 있을 때

**일반적인 에러**:
```
ModuleNotFoundError: No module named 'flask'
→ 해결: pip install flask

Permission denied
→ 해결: 관리자 권한으로 CMD 실행

Port already in use
→ 해결: [2] Stop All Servers
```

---

## 💡 사용 팁

### 1. 빠른 재시작

서버 문제 시 가장 빠른 해결:
```
[4] Restart Servers
```

### 2. 상태 모니터링

서버가 정상 작동하는지 확인:
```
[3] Check Server Status
```

### 3. 에러 디버깅

문제 발생 시:
```
[5] View Logs → 로그 확인
[6] Run Diagnostics → 시스템 진단
```

### 4. 원스텝 시작

프로그램 시작 시:
```
[1] Start All Servers → [7] Open Browser
```

---

## 📊 백그라운드 vs 기존 방식 비교

| 항목 | 기존 (창 열림) | 백그라운드 (신규) |
|------|---------------|------------------|
| 새 창 | ✅ 2개 열림 | ❌ 안 열림 |
| 로그 | 창에 표시 | 파일로 저장 |
| CMD 종료 시 | ❌ 서버 중지 | ✅ 서버 계속 실행 |
| 화면 정리 | 창 2개 관리 필요 | 깔끔함 |
| 로그 확인 | 창 확인 | 파일 확인 |

---

## 🔄 일반적인 워크플로우

### 개발 시작
```
1. coinpulse_manager_v2.bat 실행
2. [1] Start All Servers
3. [7] Open Browser
4. 개발 작업
```

### 개발 중
```
코드 수정
→ [4] Restart Servers (설정 변경 시)
→ 브라우저 새로고침 (Ctrl + Shift + R)
```

### 개발 종료
```
1. [2] Stop All Servers (선택사항)
2. [0] Exit
```

### 문제 발생 시
```
1. [3] Check Server Status
2. [5] View Logs
3. [4] Restart Servers
4. [6] Run Diagnostics (필요시)
```

---

## 🚨 주의사항

### ⚠️ CMD에서만 실행
- ❌ 탐색기 더블클릭: 즉시 종료됨
- ✅ CMD에서 실행: 정상 작동

### ⚠️ 인코딩 문제
- 한글이 깨지면: `chcp 65001` (파일 상단에 자동 포함)

### ⚠️ 서버 중복 실행 방지
- 자동으로 기존 프로세스 종료
- 수동 확인: `[3] Check Server Status`

### ⚠️ 로그 파일 크기
- 장시간 실행 시 로그 파일이 커질 수 있음
- 주기적으로 삭제 권장

---

## 📞 지원

### 문제 보고
- 로그 파일 첨부: `logs\*.log`
- 증상 설명
- 재현 방법

### 추가 명령어

**수동으로 서버 상태 확인**:
```cmd
netstat -ano | findstr ":8080 :8081"
tasklist | findstr "python.exe"
```

**수동으로 프로세스 종료**:
```cmd
taskkill /F /PID [PID번호]
```

**로그 실시간 보기** (PowerShell):
```powershell
Get-Content logs\chart_server.log -Wait
```

---

## 🎯 체크리스트

### 첫 실행 시
- [ ] CMD 창에서 실행 (탐색기 더블클릭 금지)
- [ ] [6] Run Diagnostics로 시스템 확인
- [ ] [1] Start All Servers로 서버 시작
- [ ] [3] Check Server Status로 확인
- [ ] [7] Open Browser로 브라우저 열기

### 일상 사용
- [ ] 개발 시작 시 [1] Start All Servers
- [ ] 코드 수정 후 [4] Restart Servers
- [ ] 문제 발생 시 [5] View Logs 확인
- [ ] 개발 종료 시 [2] Stop All Servers (선택)

---

**가이드 버전**: 2.0
**최종 업데이트**: 2025-11-04
**관련 파일**: `coinpulse_manager_v2.bat`

**이제 편리하게 백그라운드로 서버를 관리할 수 있습니다!** 🎉
