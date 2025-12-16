# CoinPulse 프로덕션 배포 가이드

**작성일**: 2025-12-14
**버전**: 1.0
**대상**: Linux 서버 (Ubuntu 20.04+, CentOS 7+)

---

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [사전 준비](#사전-준비)
3. [서버 설정](#서버-설정)
4. [애플리케이션 배포](#애플리케이션-배포)
5. [systemd 서비스 설정](#systemd-서비스-설정)
6. [Nginx 리버스 프록시](#nginx-리버스-프록시)
7. [SSL 인증서 설정](#ssl-인증서-설정)
8. [모니터링 및 로깅](#모니터링-및-로깅)
9. [백업 자동화](#백업-자동화)
10. [보안 강화](#보안-강화)
11. [트러블슈팅](#트러블슈팅)

---

## 시스템 요구사항

### 최소 사양
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 7+
- **Python**: 3.9+
- **PostgreSQL**: 13+
- **Nginx**: 1.18+

### 권장 사양 (100+ 동시 사용자)
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 50GB SSD
- **Bandwidth**: 100 Mbps

---

## 사전 준비

### 1. 서버 준비

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib
```

### 2. 사용자 생성

```bash
# 애플리케이션 전용 사용자 생성
sudo useradd -m -s /bin/bash coinpulse
sudo usermod -aG sudo coinpulse

# 사용자 전환
sudo su - coinpulse
```

### 3. PostgreSQL 설정

```bash
# PostgreSQL 사용자 생성
sudo -u postgres createuser coinpulse

# 데이터베이스 생성
sudo -u postgres createdb coinpulse -O coinpulse

# 비밀번호 설정
sudo -u postgres psql
postgres=# ALTER USER coinpulse WITH PASSWORD 'your_secure_password';
postgres=# \q
```

---

## 서버 설정

### 1. 방화벽 설정

```bash
# UFW 방화벽 활성화
sudo ufw enable

# SSH 허용 (포트 변경 권장)
sudo ufw allow 22/tcp

# HTTP/HTTPS 허용
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 상태 확인
sudo ufw status
```

### 2. SSH 보안 강화

```bash
# SSH 키 생성 (로컬 머신에서)
ssh-keygen -t ed25519 -C "your_email@example.com"

# 공개키 복사 (로컬 머신에서)
ssh-copy-id coinpulse@your_server_ip

# SSH 설정 수정 (서버에서)
sudo nano /etc/ssh/sshd_config

# 다음 설정 적용:
# Port 2222  # 기본 포트 변경
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

# SSH 재시작
sudo systemctl restart sshd
```

---

## 애플리케이션 배포

### 1. 코드 클론

```bash
# 애플리케이션 디렉토리로 이동
cd /opt
sudo mkdir coinpulse
sudo chown coinpulse:coinpulse coinpulse
cd coinpulse

# Git 클론
git clone https://github.com/your-username/coinpulse.git .
```

### 2. 가상 환경 설정

```bash
# Python 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
nano .env
```

**.env 파일 내용**:
```bash
# 환경 설정
ENV=production
DEBUG_MODE=False

# 데이터베이스
DATABASE_URL=postgresql://coinpulse:your_secure_password@localhost:5432/coinpulse

# 보안
SECRET_KEY=your_secret_key_here  # openssl rand -hex 32
JWT_SECRET_KEY=your_jwt_secret_key_here

# Upbit API
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key

# Toss Payments
TOSS_SECRET_KEY=your_toss_secret_key
TOSS_CLIENT_KEY=your_toss_client_key

# 서버 설정
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# 백업 설정
BACKUP_DIR=/opt/coinpulse/backups/database_backups
BACKUP_RETENTION_DAYS=30
BACKUP_TIME=02:00  # 새벽 2시 자동 백업
```

### 4. 데이터베이스 마이그레이션

```bash
# 데이터베이스 스키마 생성
python init_postgres_schema.py

# 주문 동기화 (초기 데이터 로드)
python init_order_sync.py
```

---

## systemd 서비스 설정

### 1. systemd 서비스 파일 생성

```bash
sudo nano /etc/systemd/system/coinpulse.service
```

**coinpulse.service 내용**:
```ini
[Unit]
Description=CoinPulse Web Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=coinpulse
Group=coinpulse
WorkingDirectory=/opt/coinpulse
Environment="PATH=/opt/coinpulse/venv/bin"
EnvironmentFile=/opt/coinpulse/.env
ExecStart=/opt/coinpulse/venv/bin/python app.py

# 재시작 정책
Restart=always
RestartSec=10

# 보안 설정
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/coinpulse/logs /opt/coinpulse/backups /opt/coinpulse/data

# 리소스 제한
LimitNOFILE=65536
LimitNPROC=4096

# 로깅
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinpulse

[Install]
WantedBy=multi-user.target
```

### 2. 서비스 활성화 및 시작

```bash
# systemd 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable coinpulse

# 서비스 시작
sudo systemctl start coinpulse

# 상태 확인
sudo systemctl status coinpulse

# 로그 확인
sudo journalctl -u coinpulse -f
```

---

## Nginx 리버스 프록시

### 1. Nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/coinpulse
```

**Nginx 설정 내용**:
```nginx
# Upstream 정의
upstream coinpulse_app {
    server 127.0.0.1:8080;
    keepalive 32;
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    listen [::]:80;
    server_name coinpulse.yourdomain.com;

    # Let's Encrypt 인증용
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 나머지 요청은 HTTPS로 리다이렉트
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name coinpulse.yourdomain.com;

    # SSL 인증서 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/coinpulse.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/coinpulse.yourdomain.com/privkey.pem;

    # SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 보안 헤더
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 로그
    access_log /var/log/nginx/coinpulse-access.log;
    error_log /var/log/nginx/coinpulse-error.log;

    # 정적 파일
    location /static/ {
        alias /opt/coinpulse/frontend/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket 지원
    location /socket.io/ {
        proxy_pass http://coinpulse_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    # API 요청
    location / {
        proxy_pass http://coinpulse_app;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 버퍼 설정
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # Keepalive
        proxy_set_header Connection "";
    }

    # Rate limiting (선택사항)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=20 nodelay;

    # 파일 업로드 크기 제한
    client_max_body_size 10M;
}
```

### 2. Nginx 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/coinpulse /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

---

## SSL 인증서 설정

### Let's Encrypt 사용 (무료, 권장)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d coinpulse.yourdomain.com

# 자동 갱신 설정 (crontab)
sudo crontab -e

# 다음 줄 추가 (매일 새벽 3시 갱신 확인)
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 모니터링 및 로깅

### 1. 로그 확인

```bash
# 애플리케이션 로그
tail -f /opt/coinpulse/logs/app.log

# 에러 로그
tail -f /opt/coinpulse/logs/error.log

# Nginx 로그
tail -f /var/log/nginx/coinpulse-access.log
tail -f /var/log/nginx/coinpulse-error.log

# systemd 로그
sudo journalctl -u coinpulse -f
```

### 2. 헬스 체크

```bash
# 기본 헬스 체크
curl https://coinpulse.yourdomain.com/health

# 상세 헬스 체크
curl https://coinpulse.yourdomain.com/api/health/detailed

# 데이터베이스 체크
curl https://coinpulse.yourdomain.com/api/health/db
```

### 3. 서버 모니터링

```bash
# CPU, 메모리, 디스크 사용량
htop

# 서비스 상태
systemctl status coinpulse
systemctl status nginx
systemctl status postgresql

# 디스크 사용량
df -h

# 네트워크 연결
netstat -tuln | grep 8080
```

---

## 백업 자동화

### 1. 데이터베이스 백업 cron 설정

```bash
# crontab 편집
crontab -e

# 매일 새벽 2시 자동 백업
0 2 * * * /opt/coinpulse/venv/bin/python /opt/coinpulse/backup_database.py >> /opt/coinpulse/logs/backup.log 2>&1
```

### 2. 백업 검증

```bash
# 백업 목록 확인
python backup_database.py --list

# 수동 백업 실행
python backup_database.py

# 오래된 백업 정리
python backup_database.py --clean
```

---

## 보안 강화

### 1. PostgreSQL 보안

```bash
# PostgreSQL 설정 수정
sudo nano /etc/postgresql/13/main/pg_hba.conf

# 로컬 연결만 허용
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     peer
host    coinpulse       coinpulse       127.0.0.1/32            md5

# PostgreSQL 재시작
sudo systemctl restart postgresql
```

### 2. fail2ban 설정 (SSH 보호)

```bash
# fail2ban 설치
sudo apt install fail2ban

# 설정 파일 생성
sudo nano /etc/fail2ban/jail.local
```

**jail.local 내용**:
```ini
[sshd]
enabled = true
port = 2222  # SSH 포트에 맞게 수정
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/coinpulse-error.log
maxretry = 5
bantime = 600
```

```bash
# fail2ban 시작
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 트러블슈팅

### 서비스가 시작되지 않는 경우

```bash
# 로그 확인
sudo journalctl -u coinpulse -n 50

# 설정 파일 확인
cat /etc/systemd/system/coinpulse.service

# 환경 변수 확인
cat /opt/coinpulse/.env

# 수동 실행 (디버깅)
cd /opt/coinpulse
source venv/bin/activate
python app.py
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -U coinpulse -d coinpulse -h localhost

# 데이터베이스 URL 확인
echo $DATABASE_URL
```

### Nginx 502 Bad Gateway

```bash
# 애플리케이션 상태 확인
systemctl status coinpulse

# 포트 리스닝 확인
netstat -tuln | grep 8080

# Nginx 에러 로그
tail -f /var/log/nginx/coinpulse-error.log
```

---

## 유지보수

### 애플리케이션 업데이트

```bash
# 1. 코드 업데이트
cd /opt/coinpulse
git pull origin main

# 2. 의존성 업데이트
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 3. 데이터베이스 마이그레이션 (필요 시)
python migrate_database.py

# 4. 서비스 재시작
sudo systemctl restart coinpulse

# 5. 상태 확인
sudo systemctl status coinpulse
curl https://coinpulse.yourdomain.com/health
```

### 로그 로테이션

애플리케이션 로깅 시스템이 자동으로 로그를 로테이션합니다:
- `app.log`: 30일 보관
- `error.log`: 10개 파일 (각 10MB)
- `access.log`: 30일 보관
- `security.log`: 90일 보관

---

## 체크리스트

배포 전 확인사항:

- [ ] PostgreSQL 설치 및 설정
- [ ] 환경 변수 (.env) 설정
- [ ] 데이터베이스 마이그레이션 완료
- [ ] systemd 서비스 등록
- [ ] Nginx 리버스 프록시 설정
- [ ] SSL 인증서 발급
- [ ] 방화벽 설정
- [ ] 백업 자동화 설정
- [ ] 모니터링 설정
- [ ] 보안 강화 (fail2ban, SSH 키)
- [ ] 헬스 체크 확인
- [ ] 로그 확인

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-14
**작성자**: CoinPulse Team
