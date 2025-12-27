# 500 Error 디버깅 가이드

## 오류 정보
- **에러 코드**: 500 Internal Server Error
- **발생 위치**: 플랜 변경 API 호출 시
- **콘솔 메시지**: "[Admin] Plan change response: Object"

---

## 오류 원인 추정

### 1. 무제한 플랜 설정 시 NULL 처리 오류 가능성
우리가 방금 수정한 코드에서 `duration_days = null` 전송 시 오류가 발생했을 가능성이 높습니다.

### 2. 가능한 오류 원인
1. **SQL 쿼리 오류**: `expires_at = NULL` 삽입 시 문제
2. **타입 검증 오류**: `duration_days`가 None일 때 처리 누락
3. **데이터베이스 제약 조건**: NOT NULL 제약이 있는 경우

---

## 즉시 확인 방법

### 1. 브라우저 개발자 도구 확인 (F12)

**Network 탭 확인**:
1. F12 키 눌러 개발자 도구 열기
2. "Network" 탭 선택
3. 플랜 변경 다시 시도
4. 실패한 요청 클릭 (빨간색으로 표시)
5. "Response" 탭에서 오류 메시지 확인

**콘솔 탭 확인**:
```javascript
// 콘솔에서 실행하여 마지막 에러 확인
console.log(lastError)
```

### 2. 서버 로그 확인

**로컬 환경**:
```bash
# Python 서버 실행 중인 터미널 확인
# 500 에러 발생 시 traceback이 출력됨
```

**프로덕션 환경**:
```bash
ssh root@158.247.222.216
journalctl -u coinpulse -n 100 -f
# 또는
tail -f /opt/coinpulse/logs/app.log
```

---

## 임시 수정 방안

### 방안 1: 무제한 체크박스 사용하지 않기
- 큰 숫자 입력 (예: 9999일 = 약 27년)
- 체크박스는 나중에 수정 후 사용

### 방안 2: 백엔드 검증 추가
`backend/routes/admin.py` 수정이 필요할 수 있습니다.

---

## 상세 디버깅 단계

### 1단계: 오류 메시지 확인

**브라우저 Network 탭에서 확인할 정보**:
- Request URL: `/api/admin/users/{user_id}/plan`
- Request Method: `POST`
- Status Code: `500`
- Request Payload:
  ```json
  {
    "plan_code": "pro",
    "duration_days": null,  // ← 이 부분이 문제일 수 있음
    "notes": "테스트"
  }
  ```
- Response:
  ```json
  {
    "success": false,
    "error": "..." // ← 실제 오류 메시지
  }
  ```

### 2단계: 백엔드 로그 확인

**예상되는 오류**:
1. **TypeError**: `timedelta(days=None)` 호출 시
2. **SQLAlchemy Error**: NULL 삽입 실패
3. **Validation Error**: None 값 검증 실패

### 3단계: 코드 재검토

**문제가 될 수 있는 코드** (backend/routes/admin.py:261-262):
```python
if duration_days is not None:
    expires_at = datetime.now() + timedelta(days=duration_days)
# else: expires_at stays None (unlimited)
```

**확인 사항**:
- `duration_days`가 정확히 `None`으로 전달되는가?
- SQL 쿼리가 `NULL` 값을 허용하는가?
- `current_period_end` 컬럼이 `NULL` 허용 설정인가?

---

## 긴급 수정 코드

만약 NULL 처리에 문제가 있다면, 아래 코드로 임시 수정:

### backend/routes/admin.py 수정

**현재 코드**:
```python
if duration_days is not None:
    expires_at = datetime.now() + timedelta(days=duration_days)
# else: expires_at stays None (unlimited)
```

**수정 코드** (더 방어적):
```python
# 무제한 플랜 처리
if duration_days is None or duration_days == 0:
    # 무제한: 100년 뒤로 설정 (실질적 무제한)
    expires_at = datetime.now() + timedelta(days=36500)  # 100 years
else:
    expires_at = datetime.now() + timedelta(days=duration_days)
```

**장점**:
- NULL 대신 매우 먼 미래 날짜 사용
- 데이터베이스 제약 조건 회피
- 기존 로직과 호환성 유지

**단점**:
- 진정한 NULL이 아님
- 100년 후 만료됨 (실질적 문제 없음)

---

## 데이터베이스 스키마 확인

### user_subscriptions 테이블 확인

**SQL 쿼리**:
```sql
-- 테이블 구조 확인
\d user_subscriptions

-- 또는
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'user_subscriptions'
  AND column_name = 'current_period_end';
```

**예상 결과**:
```
column_name         | is_nullable | data_type
--------------------|-------------|----------
current_period_end  | YES         | timestamp
```

**만약 `is_nullable = NO`라면**:
- 테이블 ALTER 필요:
  ```sql
  ALTER TABLE user_subscriptions
  ALTER COLUMN current_period_end DROP NOT NULL;
  ```

---

## 수정 우선순위

### 즉시 수정 (긴급)
1. **브라우저에서 오류 메시지 확인**
2. **서버 로그 확인**
3. **데이터베이스 스키마 확인**

### 단기 수정 (오늘 중)
1. NULL 처리 로직 수정
2. 또는 100년 방식으로 변경
3. 오류 처리 개선

### 장기 개선 (다음 작업)
1. 프론트엔드 에러 핸들링 강화
2. 더 명확한 오류 메시지
3. 로그 수준 개선

---

## 체크리스트

**사용자 작업**:
- [ ] F12 → Network 탭 열기
- [ ] 플랜 변경 다시 시도
- [ ] 실패한 요청의 Response 확인
- [ ] 오류 메시지 복사

**개발자 작업**:
- [ ] 오류 메시지 분석
- [ ] 서버 로그 확인
- [ ] 데이터베이스 스키마 확인
- [ ] 코드 수정
- [ ] 테스트

---

## 다음 단계

**오류 메시지를 확인한 후**:
1. 구체적인 오류 내용 공유
2. 적절한 수정 방안 결정
3. 코드 수정 및 재배포

**예시**:
```
"오류 메시지: TypeError: unsupported operand type(s) for +: 'datetime.datetime' and 'NoneType'"
→ timedelta(days=None) 호출 문제
→ 방어적 코드 추가 필요
```

---

**현재 상태**: 🔍 오류 분석 중
**필요한 정보**: Network 탭의 Response 내용
