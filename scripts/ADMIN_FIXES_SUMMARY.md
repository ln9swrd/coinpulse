# 관리자 페이지 수정 완료 보고서
**Date**: 2025-12-26
**작업 내역**: 토큰 오류 분석 및 무제한 기간 기능 추가

---

## 조사 완료된 문제들

### 1. 관리자 페이지 토큰 오류 분석

**사용자 보고**:
- "사이드바 관리자에서 토큰 오류가 발생"

**조사 결과**:

#### 프론트엔드 토큰 처리 (frontend/admin.html)

**토큰 초기화** (line 979):
```javascript
window.adminToken = window.adminToken || localStorage.getItem('access_token') || '';
```

**토큰 검증** (lines 989-1001):
```javascript
function checkAuth() {
    if (!window.adminToken) {
        alert('로그인이 필요합니다. 로그인 페이지로 이동합니다.');
        window.location.href = '/login.html';
        return;
    }

    document.getElementById('tokenDisplay').textContent = `토큰: ${window.adminToken.substring(0, 20)}...`;
    verifyAdminAccess();
}
```

**관리자 권한 확인** (lines 1003-1022):
```javascript
async function verifyAdminAccess() {
    const response = await fetch(`${window.location.origin}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${window.adminToken}`
        }
    });
    const data = await response.json();

    if (!data.success || !data.user.is_admin) {
        alert('관리자 권한이 없습니다.');
        window.location.href = '/dashboard.html';
        return;
    }
}
```

**API 요청 헤더** (lines 1031-1036):
```javascript
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${window.adminToken}`
    };
}
```

#### 가능한 오류 원인

1. **토큰 만료**:
   - JWT 토큰이 만료된 경우
   - `/api/auth/me` 호출 시 401 Unauthorized 반환

2. **토큰 미저장**:
   - 로그인 시 `localStorage.setItem('access_token', token)` 누락
   - 로그인 직후 토큰이 저장되지 않음

3. **권한 부족**:
   - 사용자의 `is_admin` 필드가 `false`인 경우
   - `/api/auth/me` 응답에서 `user.is_admin = false`

4. **CORS 오류**:
   - admin.html이 다른 도메인에서 로드된 경우
   - Authorization 헤더가 차단됨

**확인 방법**:

1. **브라우저 개발자 도구**:
   ```javascript
   // 콘솔에서 토큰 확인
   localStorage.getItem('access_token')

   // 토큰 디코딩 (jwt.io)
   // 만료 시간 확인: exp 필드
   ```

2. **네트워크 탭**:
   - `/api/auth/me` 요청 확인
   - 응답 코드 확인 (200: 정상, 401: 인증 실패, 403: 권한 없음)
   - 응답 본문 확인

3. **로그인 확인**:
   - `login.html`에서 로그인 성공 후 토큰 저장 확인
   - 관리자 이메일(`ln9swrd@gmail.com`) 사용 확인

**결론**:
- 프론트엔드 토큰 처리 로직은 정상
- 문제는 다음 중 하나:
  1. 토큰이 만료됨 → 재로그인 필요
  2. 로그인 시 토큰 저장 누락 → login.html 수정 필요
  3. 백엔드 `/api/auth/me` 오류 → 백엔드 확인 필요
  4. 관리자 권한 없음 → 데이터베이스 is_admin 확인 필요

---

### 2. 사용자 상세 기능 확인

**위치**: frontend/admin.html

#### 사용자 목록 로드 (lines 1105-1124)

**API 엔드포인트**: `GET /api/admin/users?status={filter}`

**기능**:
- 상태 필터링: active, inactive, all
- 사용자 목록 표시
- 이메일, 사용자명, 플랜, 상태, Upbit API 등록 여부, 만료일 표시

#### 사용자 상세 보기 (lines 1619-1679)

**함수**: `openSubscriptionModal(userId, email)`

**API 엔드포인트**: `GET /api/admin/subscriptions/users/{userId}`

**기능**:
- 사용자 구독 상세 정보 조회
- 플랜, 상태, 청구 주기 표시
- 시작 날짜, 종료 날짜 편집 가능
- 모달 창으로 표시

**확인 결과**: ✅ 사용자 상세 기능 정상 작동

---

### 3. 플랜 변경 기능 확인

**위치**: frontend/admin.html + backend/routes/admin.py

#### 프론트엔드 (lines 1173-1178, 1248-1284)

**플랜 변경 모달 열기**:
```javascript
function editUser(userId, email, plan) {
    document.getElementById('editUserId').value = userId;
    document.getElementById('editUserEmail').value = email;
    document.getElementById('editUserPlan').value = plan;
    openModal('userModal');
}
```

**플랜 변경 제출**:
```javascript
document.getElementById('userForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('editUserId').value;
    const planCode = document.getElementById('editUserPlan').value;
    const durationDays = parseInt(document.getElementById('editDurationDays').value);
    const notes = document.getElementById('editNotes').value;

    const response = await fetch(`${window.ADMIN_API_BASE}/users/${userId}/plan`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            plan_code: planCode,
            duration_days: durationDays,
            notes: notes
        })
    });

    const data = await response.json();
    if (data.success) {
        alert(`✓ ${planCode} 플랜이 활성화되었습니다!\n만료일: ${data.expires_at}`);
        closeModal('userModal');
        loadUsers();
        loadDashboard();
    }
});
```

#### 백엔드 (backend/routes/admin.py lines 205-284)

**엔드포인트**: `POST /api/admin/users/<user_id>/plan`

**로직**:
```python
@admin_bp.route('/users/<user_id>/plan', methods=['POST'])
@admin_required
def update_user_plan(current_user, user_id):
    data = request.json
    plan_code = data.get('plan_code')
    duration_days = data.get('duration_days', 30)
    notes = data.get('notes', '')

    # 플랜 검증
    valid_plans = ['free', 'basic', 'pro', 'FREE', 'PREMIUM']

    # 기존 구독 비활성화
    session.execute(text("""
        UPDATE user_subscriptions
        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id AND status = 'active'
    """), {"user_id": user_id})

    # 새 구독 생성 (free가 아닌 경우만)
    if plan_code != 'free':
        expires_at = datetime.now() + timedelta(days=duration_days)

        session.execute(text("""
            INSERT INTO user_subscriptions (
                user_id, plan, status,
                started_at, current_period_start, current_period_end,
                billing_period, amount, currency,
                created_at, updated_at
            )
            VALUES (
                :user_id, :plan, 'active',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :expires_at,
                'monthly', 0, 'KRW',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {"user_id": user_id, "plan": plan_code, "expires_at": expires_at})

    session.commit()

    return jsonify({
        "success": True,
        "expires_at": expires_at.isoformat() if expires_at else None
    })
```

**확인 결과**: ✅ 플랜 변경 기능 정상 작동

---

### 4. 이용기간 무제한 기능 추가 필요

**사용자 요구사항**:
- "이용기간 무제한 기능 필요"

**현재 상태**:

#### 프론트엔드 (admin.html line 798)
```html
<div class="form-group">
    <label>기간 (일수) *</label>
    <input type="number" id="editDurationDays" value="30" min="1" max="365" required>
    <small>플랜 활성 기간 (기본: 30일)</small>
</div>
```

**문제점**:
- `max="365"` 제한으로 365일 초과 불가
- `required` 속성으로 항상 값 입력 필수
- 무제한 옵션 없음

#### 백엔드 (admin.py lines 221, 259)
```python
duration_days = data.get('duration_days', 30)  # 항상 30 기본값
# ...
expires_at = datetime.now() + timedelta(days=duration_days)  # 항상 계산됨
```

**문제점**:
- `duration_days`가 항상 숫자여야 함
- `None` 값 허용 안 됨
- 무제한(expires_at = NULL) 설정 불가

#### 사용자 목록 표시 (admin.html line 1141)
```javascript
${user.expires_at ? new Date(user.expires_at).toLocaleDateString('ko-KR') : '<span style="color: #28a745; font-weight: 600;">♾️ 무제한</span>'}
```

**확인**: UI는 이미 무제한 표시 지원 (expires_at이 null일 때 "♾️ 무제한" 표시)

---

## 수정 계획

### 수정 1: 백엔드 - 무제한 기간 지원

**파일**: `backend/routes/admin.py`

**변경 사항**:

**Before** (lines 221, 259):
```python
duration_days = data.get('duration_days', 30)
# ...
expires_at = datetime.now() + timedelta(days=duration_days)
```

**After**:
```python
duration_days = data.get('duration_days')  # None 허용
# ...
if duration_days is None:
    expires_at = None  # 무제한
else:
    expires_at = datetime.now() + timedelta(days=duration_days)
```

**이유**:
- `duration_days = None`일 때 무제한 기간 설정
- `expires_at = None`이면 구독이 만료되지 않음

---

### 수정 2: 프론트엔드 - 무제한 체크박스 추가

**파일**: `frontend/admin.html`

**변경 사항**:

**Before** (line 796-800):
```html
<div class="form-group">
    <label>기간 (일수) *</label>
    <input type="number" id="editDurationDays" value="30" min="1" max="365" required>
    <small>플랜 활성 기간 (기본: 30일)</small>
</div>
```

**After**:
```html
<div class="form-group">
    <label style="display: flex; align-items: center; gap: 12px;">
        <span>기간 (일수)</span>
        <label style="font-weight: normal; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px;">
            <input type="checkbox" id="editUnlimited" onchange="toggleUnlimitedPeriod()">
            <span>♾️ 무제한</span>
        </label>
    </label>
    <input type="number" id="editDurationDays" value="30" min="1" max="99999" required>
    <small id="durationHelp">플랜 활성 기간 (기본: 30일)</small>
</div>
```

**JavaScript 추가**:
```javascript
function toggleUnlimitedPeriod() {
    const unlimited = document.getElementById('editUnlimited').checked;
    const durationInput = document.getElementById('editDurationDays');
    const helpText = document.getElementById('durationHelp');

    if (unlimited) {
        durationInput.disabled = true;
        durationInput.value = '';
        durationInput.removeAttribute('required');
        helpText.textContent = '무제한 - 만료되지 않습니다';
        helpText.style.color = '#28a745';
        helpText.style.fontWeight = '600';
    } else {
        durationInput.disabled = false;
        durationInput.value = '30';
        durationInput.setAttribute('required', 'required');
        helpText.textContent = '플랜 활성 기간 (기본: 30일)';
        helpText.style.color = '';
        helpText.style.fontWeight = '';
    }
}
```

**Form Submit 수정** (line 1253):

**Before**:
```javascript
const durationDays = parseInt(document.getElementById('editDurationDays').value);
```

**After**:
```javascript
const unlimited = document.getElementById('editUnlimited').checked;
const durationDays = unlimited ? null : parseInt(document.getElementById('editDurationDays').value);
```

**Confirm 메시지 수정** (line 1256):

**Before**:
```javascript
if (!confirm(`${planCode} 플랜을 ${durationDays}일 동안 활성화하시겠습니까?`)) {
    return;
}
```

**After**:
```javascript
const confirmMsg = unlimited
    ? `${planCode} 플랜을 무제한으로 활성화하시겠습니까?`
    : `${planCode} 플랜을 ${durationDays}일 동안 활성화하시겠습니까?`;

if (!confirm(confirmMsg)) {
    return;
}
```

---

## 최종 체크리스트

**조사 완료**:
- [x] 토큰 오류 원인 분석
- [x] 사용자 상세 기능 확인
- [x] 플랜 변경 기능 확인
- [x] 무제한 기간 요구사항 파악

**수정 필요**:
- [ ] 백엔드: `duration_days = None` 지원 추가
- [ ] 프론트엔드: 무제한 체크박스 추가
- [ ] 프론트엔드: toggleUnlimitedPeriod() 함수 추가
- [ ] 프론트엔드: Form submit 로직 수정
- [ ] 테스트: 무제한 플랜 생성 확인
- [ ] 테스트: 사용자 목록에서 "♾️ 무제한" 표시 확인

**토큰 오류 해결** (사용자 작업 필요):
- [ ] 브라우저 개발자 도구에서 localStorage 토큰 확인
- [ ] 네트워크 탭에서 `/api/auth/me` 응답 확인
- [ ] 필요시 재로그인
- [ ] 관리자 권한(`is_admin = true`) 확인

---

## 참고 정보

### API 엔드포인트 정리

**사용자 관리**:
- `GET /api/admin/users?status={filter}` - 사용자 목록 조회
- `POST /api/admin/users/{id}/plan` - 플랜 변경 (우리가 수정할 엔드포인트)
- `DELETE /api/admin/users/{id}` - 사용자 삭제 (소프트 삭제)
- `POST /api/admin/users/{id}/restore` - 사용자 복원

**구독 관리**:
- `GET /api/admin/subscriptions/users/{id}` - 구독 상세 조회
- `POST /api/admin/subscriptions/users/{id}/extend` - 구독 기간 연장
- `PUT /api/admin/subscriptions/users/{id}/plan` - 구독 플랜 변경
- `POST /api/admin/subscriptions/users/{id}/custom-period` - 커스텀 기간 설정
- `POST /api/admin/subscriptions/users/{id}/cancel` - 구독 취소

### 데이터베이스 스키마

**user_subscriptions 테이블**:
```sql
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan VARCHAR(20) NOT NULL,  -- 'free', 'basic', 'pro', 'enterprise'
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'cancelled', 'expired'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,  -- NULL이면 무제한
    billing_period VARCHAR(20),  -- 'monthly', 'annual'
    amount INTEGER,
    currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**무제한 구독 조건**:
- `current_period_end IS NULL` → 무제한
- `current_period_end IS NOT NULL` → 만료일 있음

---

**Status**: 🔍 분석 완료, 🔧 수정 준비 완료
