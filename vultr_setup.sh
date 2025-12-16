#!/bin/bash
# Vultr 서버 초기 설정 및 코인펄스 배포 스크립트

echo "========================================="
echo "CoinPulse Vultr 배포 스크립트 v1.0"
echo "========================================="
echo ""

# Step 1: 시스템 업데이트
echo "[1/7] 시스템 업데이트 중..."
apt update && apt upgrade -y

# Step 2: 필수 패키지 설치
echo "[2/7] 필수 패키지 설치 중..."
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx postgresql postgresql-contrib

# Step 3: PostgreSQL 설정
echo "[3/7] PostgreSQL 설정 중..."
sudo -u postgres psql -c "CREATE DATABASE coinpulse;"
sudo -u postgres psql -c "CREATE USER coinpulse_user WITH PASSWORD 'coinpulse2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE coinpulse TO coinpulse_user;"

# Step 4: 코인펄스 다운로드
echo "[4/7] 코인펄스 소스코드 다운로드 중..."
cd /opt
git clone https://github.com/ln9swrd/coinpulse.git
cd coinpulse

# Step 5: Python 가상환경 및 의존성 설치
echo "[5/7] Python 패키지 설치 중..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 6: 환경 변수 설정
echo "[6/7] 환경 변수 파일 생성 중..."
cat > .env << EOF
# Upbit API Keys (나중에 수정 필요)
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here

# Database
DATABASE_URL=postgresql://coinpulse_user:coinpulse2024@localhost:5432/coinpulse

# Server
PORT=8080
DEBUG_MODE=false

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF

echo "[7/7] 기본 설정 완료!"
echo ""
echo "========================================="
echo "다음 단계:"
echo "1. .env 파일에 실제 Upbit API 키 입력"
echo "2. Nginx 설정"
echo "3. SSL 인증서 발급"
echo "4. 서비스 시작"
echo "========================================="
