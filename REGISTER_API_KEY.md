# API 키 등록 가이드

## 왜 필요한가?

**자동매매는 각 사용자별 Upbit API 키를 사용해야 합니다.**

현재 글로벌 키를 사용 중이면:
- ❌ 모든 사용자가 동일한 Upbit 계정으로 거래
- ❌ 개인별 포트폴리오 관리 불가
- ❌ 보안 위험

사용자별 API 키를 등록하면:
- ✅ 각자의 Upbit 계정으로 거래
- ✅ 개인별 포트폴리오 관리
- ✅ 안전한 암호화 저장

---

## 등록 프로세스

### Step 1: Upbit에서 API 키 발급

1. **Upbit 로그인** 후 [오픈 API 관리](https://upbit.com/mypage/open_api_management) 접속
2. **"Open API Key 발급받기"** 클릭
3. **권한 설정**:
   - ✅ 자산 조회 (Assets - View)
   - ✅ 주문 조회 (Orders - View)
   - ✅ 주문하기 (Orders - Trade)
4. **IP 주소**: (선택) 158.247.222.216 추가하면 더 안전
5. **Access Key와 Secret Key 복사** (절대 공유하지 말 것!)

### Step 2: CoinPulse에 등록

1. **등록 페이지 접속**: https://coinpulse.sinsi.ai/api_keys.html
2. **폼 작성**:
   - **키 이름** (선택): 예) "자동매매용 키"
   - **Access Key**: Upbit에서 복사한 Access Key
   - **Secret Key**: Upbit에서 복사한 Secret Key
3. **"API 키 등록 및 검증"** 클릭
4. **검증 완료 메시지 확인**: "API 키가 성공적으로 등록되었습니다! ✅"

### Step 3: 등록 확인

SSH로 서버 접속 후:

```bash
cd /opt/coinpulse
./venv/bin/python scripts/test_api_key_flow.py --user-id 1 --real
```

**성공 시 출력**:
```
✅ User 1 has API keys registered
✅ Auto-trading will use user-specific keys
✅ Next surge signal will execute REAL orders
```

---

## 등록 후 동작

### 자동매매 실행 시:

**이전** (글로벌 키):
```python
load_api_keys(user_id=None)  # .env의 글로벌 키 사용
→ 모든 사용자가 동일한 계정으로 거래
```

**이후** (사용자별 키):
```python
load_api_keys(user_id=1)  # user 1의 암호화된 키 사용
→ 각자의 Upbit 계정으로 거래
```

### 보안:

- **암호화 저장**: Fernet 대칭 암호화 (AES-128)
- **데이터베이스**: `upbit_api_keys` 테이블
- **접근 제어**: 본인의 키만 조회 가능
- **자동 비활성화**: 5회 연속 에러 시 자동 비활성화

---

## 트러블슈팅

### Q1: "API key verification failed" 에러

**원인**: API 키가 잘못되었거나 권한이 부족합니다.

**해결**:
1. Upbit에서 키 재확인
2. 권한 설정 확인 (자산 조회, 주문 조회, 주문하기)
3. IP 화이트리스트 설정 시 158.247.222.216 추가

### Q2: 등록 후에도 글로벌 키 사용

**원인**: 캐시 또는 서비스 재시작 필요

**해결**:
```bash
sudo systemctl restart coinpulse
```

### Q3: 키 삭제 방법

등록 페이지에서 **"API 키 삭제"** 버튼 클릭

---

## 다음 단계

API 키 등록 후:

1. **자동매매 설정**: https://coinpulse.sinsi.ai/auto_trading_settings.html
2. **자동매매 활성화**: 최소 신뢰도, 투자 금액, 손절/익절 설정
3. **첫 신호 대기**: 다음 급등 신호부터 자동 거래 실행

**주의**: 실제 자금이 사용되므로 신중히 설정하세요!
