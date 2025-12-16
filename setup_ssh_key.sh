#!/bin/bash
# SSH 키를 서버에 복사하는 스크립트

echo "공개 키를 확인 중..."
cat ~/.ssh/id_rsa.pub

echo ""
echo "위 공개 키를 서버에 복사합니다."
echo "비밀번호: ehrrh#9rja"
echo ""

# SSH로 접속하여 키 복사
ssh-copy-id -i ~/.ssh/id_rsa.pub root@158.247.222.216
