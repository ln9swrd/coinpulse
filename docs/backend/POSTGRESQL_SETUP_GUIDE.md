# PostgreSQL 설치 및 설정 가이드

## 1단계: PostgreSQL 설치

### 방법 1: winget 사용 (권장)
```bash
# 관리자 권한으로 PowerShell 실행 후
winget install PostgreSQL.PostgreSQL.16
```

### 방법 2: 공식 웹사이트 다운로드
https://www.postgresql.org/download/windows/

## 2단계: PostgreSQL 서비스 시작 확인

설치 완료 후 자동으로 서비스가 시작됩니다.

확인:
```powershell
Get-Service -Name *postgres*
```

서비스 시작:
```powershell
Start-Service postgresql-x64-16
```

## 3단계: 데이터베이스 및 사용자 생성

### psql 접속
```bash
# 설치 시 설정한 postgres 비밀번호 입력
psql -U postgres
```

### SQL 명령 실행
```sql
-- 1. coinpulse 데이터베이스 생성
CREATE DATABASE coinpulse;

-- 2. coinpulse 사용자 생성 (비밀번호 변경 필수!)
CREATE USER coinpulse_user WITH PASSWORD 'your_secure_password_here';

-- 3. 권한 부여
GRANT ALL PRIVILEGES ON DATABASE coinpulse TO coinpulse_user;

-- 4. 데이터베이스 연결
\c coinpulse

-- 5. 스키마 권한 부여
GRANT ALL ON SCHEMA public TO coinpulse_user;

-- 6. 확인
\l
\q
```

## 4단계: .env 파일 수정

```bash
# 데이터베이스 타입을 postgresql로 변경
DB_TYPE=postgresql

# PostgreSQL 연결 정보 (실제 값으로 변경)
DB_HOST=localhost
DB_PORT=5432
DB_USER=coinpulse_user
DB_PASSWORD=your_secure_password_here
DB_NAME=coinpulse
```

## 5단계: 서버 재시작

```bash
python simple_dual_server.py
```

로그에서 PostgreSQL 연결 확인:
```
[Database] Using PostgreSQL: localhost:5432/coinpulse
```

## 트러블슈팅

### psql 명령어를 찾을 수 없음
PostgreSQL bin 경로를 PATH에 추가:
```
C:\Program Files\PostgreSQL\16\bin
```

### 연결 오류
1. 서비스 상태 확인
2. pg_hba.conf 확인 (localhost 접근 허용)
3. 방화벽 설정 확인

### 비밀번호 초기화
```bash
# postgres 사용자 비밀번호 재설정
psql -U postgres
ALTER USER postgres PASSWORD 'new_password';
```
