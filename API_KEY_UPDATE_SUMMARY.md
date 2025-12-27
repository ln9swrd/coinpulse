# API 키 재등록 기능 업데이트 (2025-12-27)

## 변경 사항 요약

### 문제점
- settings.html에서 사용자가 Upbit API 키를 재등록할 때 기존 키를 삭제하지 않고 덮어쓰는 방식
- users 테이블에 평문으로 저장되던 구식 시스템 사용
- 보안 취약점 (암호화 없음)

### 해결 방법
- `/api/user/api-keys` 엔드포인트를 암호화된 저장소 사용하도록 업데이트
- 재등록 시 기존 키를 **먼저 삭제**한 후 새 키를 등록하도록 변경
- Fernet 암호화 적용 (AES-128)

---

## 기술적 변경 사항

### 수정된 파일
- `backend/routes/user_routes.py` - manage_api_keys() 함수

### 변경 전 (Old System)
```python
# users 테이블에 평문 저장 (보안 취약)
user.upbit_access_key = access_key
user.upbit_secret_key = secret_key
session.commit()
```

**문제점**:
- ❌ 평문 저장 (암호화 없음)
- ❌ 덮어쓰기 방식 (기존 키 삭제 안 함)
- ❌ Upbit API 검증 없음

### 변경 후 (New System)
```python
# 1. Upbit API로 키 검증
upbit_api = UpbitAPI(access_key, secret_key)
accounts = upbit_api.get_accounts()

# 2. Fernet 암호화
encrypted_access, encrypted_secret = encrypt_api_credentials(access_key, secret_key)

# 3. 기존 키 삭제 (중요!)
if existing_key:
    session.delete(existing_key)
    session.flush()

# 4. 새 키 등록 (암호화된 상태로)
new_key = UpbitAPIKey(
    user_id=user_id,
    access_key_encrypted=encrypted_access,
    secret_key_encrypted=encrypted_secret,
    is_verified=True
)
session.add(new_key)
session.commit()
```

**개선 사항**:
- ✅ Fernet 암호화 (AES-128 CBC + HMAC)
- ✅ 기존 키 삭제 후 재등록
- ✅ Upbit API 검증 필수
- ✅ 검증 실패 시 저장 안 함

---

## 엔드포인트 동작

### GET /api/user/api-keys

**요청**:
```http
GET /api/user/api-keys
Authorization: Bearer {JWT_TOKEN}
```

**응답** (키가 있을 때):
```json
{
  "success": true,
  "access_key": "eC7yDWGbeC...",
  "secret_key_masked": "****Uqm1",
  "has_keys": true,
  "is_verified": true,
  "key_name": "Settings Key (2025-12-27)"
}
```

**응답** (키가 없을 때):
```json
{
  "success": true,
  "access_key": null,
  "secret_key_masked": null,
  "has_keys": false
}
```

### POST /api/user/api-keys

**요청**:
```http
POST /api/user/api-keys
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "access_key": "Upbit Access Key",
  "secret_key": "Upbit Secret Key"
}
```

**처리 과정**:
1. JWT 토큰에서 user_id 추출 (@require_auth)
2. Upbit API로 키 유효성 검증
3. 기존 키가 있으면 **삭제** (session.delete)
4. 새 키를 Fernet 암호화하여 저장
5. upbit_api_keys 테이블에 INSERT

**응답** (성공):
```json
{
  "success": true,
  "message": "API keys saved successfully",
  "verified": true
}
```

**응답** (실패 - 검증 실패):
```json
{
  "success": false,
  "error": "API key verification failed: ...",
  "code": "VERIFICATION_FAILED"
}
```

---

## 보안 개선

### Before (Old System)
| 항목 | 상태 |
|------|------|
| 저장 위치 | users 테이블 |
| 암호화 | ❌ 평문 저장 |
| 검증 | ❌ 검증 없음 |
| 재등록 | 덮어쓰기 |

### After (New System)
| 항목 | 상태 |
|------|------|
| 저장 위치 | upbit_api_keys 테이블 |
| 암호화 | ✅ Fernet (AES-128) |
| 검증 | ✅ Upbit API 검증 필수 |
| 재등록 | 삭제 → 등록 |

---

## 사용자 경험 개선

### settings.html에서의 동작
1. **최초 등록**:
   - Access Key, Secret Key 입력
   - "연결 테스트" 클릭 → Upbit API 검증
   - "저장하기" 클릭 → 암호화하여 DB 저장

2. **재등록** (키 변경):
   - 새로운 Access Key, Secret Key 입력
   - "연결 테스트" 클릭 → Upbit API 검증
   - "저장하기" 클릭 → **기존 키 삭제** → 새 키 저장

3. **자동 로딩**:
   - 페이지 로드 시 GET /api/user/api-keys 호출
   - Access Key는 평문으로 표시
   - Secret Key는 마스킹 (****Uqm1)

---

## 배포 정보

- **커밋**: ad6c7dd - "[FIX] Update /api/user/api-keys to use encrypted storage and delete old keys before re-registration"
- **배포 일시**: 2025-12-27 06:34:32 UTC
- **프로덕션 서버**: 158.247.222.216 (coinpulse.sinsi.ai)
- **서비스 상태**: ✅ Active (running)

---

## 테스트 결과

### User 1 (ln9swrd@gmail.com)
```
✅ User 1 has API keys registered
✅ Auto-trading will use user-specific keys
✅ Next surge signal will execute REAL orders
✅ Upbit API connection successful (18 accounts)
```

### User 12 (power240@nate.com)
```
⚠️  IP whitelist issue - 158.247.222.216 not whitelisted
✅ Keys migrated successfully but marked as unverified
```

---

## 마이그레이션 스크립트

### 1. 환경 변수 → 사용자 키 마이그레이션
```bash
./venv/bin/python scripts/migrate_env_keys_to_user.py --user-id 1
```

### 2. users 테이블 → upbit_api_keys 테이블 마이그레이션
```bash
./venv/bin/python scripts/migrate_users_table_keys.py
```

### 3. 테스트 스크립트
```bash
./venv/bin/python scripts/test_api_key_flow.py --user-id 1 --real
```

---

## 참고 문서

- `REGISTER_API_KEY.md` - API 키 등록 가이드
- `backend/models/user_api_key.py` - UpbitAPIKey 모델
- `backend/utils/crypto.py` - 암호화/복호화 함수
- `backend/common/config_loader.py` - load_api_keys() 함수
