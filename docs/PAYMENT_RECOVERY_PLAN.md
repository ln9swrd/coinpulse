# 결제 불일치 관리 및 대시보드 요금제 기능 구현 계획

## 📋 구현 개요

### 목표
1. **결제 불일치 처리**: 결제는 성공했지만 플랜 업데이트가 실패한 케이스를 찾고 복구
2. **대시보드 요금제 표시**: 현재 플랜, 남은 이용일, 갱신일 표시
3. **계좌이체 결제 UI**: 사용기간 연장/플랜 변경 기능

---

## 1️⃣ 결제 불일치 관리 (Admin)

### Backend API

#### A. 불일치 케이스 조회
```python
# backend/routes/payment_recovery.py

@admin_bp.route('/payment-recovery/mismatches', methods=['GET'])
@require_admin
def find_payment_mismatches():
    """
    결제 성공 but 플랜 미업데이트 케이스 찾기

    Response:
    {
        "success": true,
        "mismatches": [
            {
                "transaction_id": "TXN_...",
                "user_id": 1,
                "user_email": "user@example.com",
                "amount": 49000,
                "payment_date": "2025-12-24T10:00:00",
                "current_plan": "free",
                "expected_plan": "basic",
                "days_since_payment": 1
            }
        ],
        "count": 5
    }

    로직:
    1. transactions 테이블에서 status=SUCCEEDED 조회
    2. 각 transaction의 user_id로 user_subscriptions 조회
    3. transaction 금액과 구독 플랜 비교
    4. 불일치 케이스 반환
    """

@admin_bp.route('/payment-recovery/<int:transaction_id>/apply', methods=['POST'])
@require_admin
def apply_payment_manually(transaction_id):
    """
    수동으로 플랜 업데이트

    Request:
    {
        "plan": "basic",
        "billing_period": "monthly",
        "admin_notes": "수동 처리 - 결제 확인됨"
    }

    Response:
    {
        "success": true,
        "transaction": {...},
        "subscription": {...},
        "message": "플랜이 성공적으로 업데이트되었습니다"
    }

    로직:
    1. Transaction 존재 및 status=SUCCEEDED 확인
    2. Subscription 생성 또는 업데이트
    3. User 테이블의 plan 컬럼 업데이트 (있다면)
    4. Transaction에 admin_notes 추가
    """
```

#### B. 결제 내역 전체 조회 (Admin)
```python
@admin_bp.route('/transactions', methods=['GET'])
@require_admin
def get_all_transactions():
    """
    모든 거래 내역 조회

    Query params:
    - status: filter by status (succeeded, failed, pending)
    - user_id: filter by user
    - limit: 50 (default)
    - offset: 0 (default)

    Response:
    {
        "success": true,
        "transactions": [...],
        "total": 100,
        "stats": {
            "succeeded": 85,
            "failed": 10,
            "pending": 5
        }
    }
    """
```

### Frontend (Admin Page)

```html
<!-- admin.html에 추가할 섹션 -->

<div class="admin-section" id="payment-recovery-section" style="display: none;">
    <div class="section-header">
        <h2>결제 불일치 관리</h2>
        <button class="btn-primary" onclick="refreshMismatches()">새로고침</button>
    </div>

    <!-- 불일치 케이스 테이블 -->
    <div class="alert alert-warning" id="mismatches-alert" style="display: none;">
        <strong>⚠️ <span id="mismatch-count">0</span>건의 불일치 케이스 발견</strong>
    </div>

    <table class="data-table">
        <thead>
            <tr>
                <th>Transaction ID</th>
                <th>사용자</th>
                <th>결제 금액</th>
                <th>결제일</th>
                <th>현재 플랜</th>
                <th>예상 플랜</th>
                <th>경과 시간</th>
                <th>작업</th>
            </tr>
        </thead>
        <tbody id="mismatches-tbody">
            <!-- 동적 로딩 -->
        </tbody>
    </table>

    <!-- 수동 적용 모달 -->
    <div class="modal" id="apply-payment-modal">
        <div class="modal-content">
            <h3>플랜 수동 업데이트</h3>
            <form id="apply-payment-form">
                <div class="form-group">
                    <label>플랜 선택</label>
                    <select name="plan" required>
                        <option value="basic">Basic (39,000원/월)</option>
                        <option value="pro">Pro (79,000원/월)</option>
                        <option value="expert">Expert (99,000원/월)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>결제 주기</label>
                    <select name="billing_period" required>
                        <option value="monthly">월간</option>
                        <option value="annual">연간</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>관리자 메모</label>
                    <textarea name="admin_notes" rows="3" required></textarea>
                </div>
                <div class="modal-actions">
                    <button type="submit" class="btn-primary">적용</button>
                    <button type="button" class="btn-secondary" onclick="closeModal()">취소</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

---

## 2️⃣ 대시보드 요금제 정보 표시

### Backend API

```python
# backend/routes/subscription_routes.py

@subscription_bp.route('/current', methods=['GET'])
@require_auth
def get_current_subscription():
    """
    현재 구독 정보 조회

    Response:
    {
        "success": true,
        "subscription": {
            "plan": "basic",
            "plan_name_ko": "베이직",
            "billing_period": "monthly",
            "status": "active",
            "amount": 39000,
            "started_at": "2025-12-01T00:00:00",
            "current_period_start": "2025-12-01T00:00:00",
            "current_period_end": "2025-12-31T23:59:59",
            "days_remaining": 7,
            "auto_renew": true,
            "next_billing_date": "2025-12-31T23:59:59"
        },
        "plan_features": {
            "max_advisory_coins": 5,
            "max_surge_alerts": 5,
            "telegram_alerts": true,
            ...
        },
        "usage": {
            "advisory_coins_used": 3,
            "surge_alerts_used": 2
        }
    }
    """

@subscription_bp.route('/history', methods=['GET'])
@require_auth
def get_subscription_history():
    """
    구독 변경 이력 조회

    Response:
    {
        "success": true,
        "history": [
            {
                "plan": "basic",
                "started_at": "2025-12-01",
                "ended_at": "2025-12-31",
                "amount": 39000,
                "status": "active"
            },
            {
                "plan": "free",
                "started_at": "2025-11-01",
                "ended_at": "2025-11-30",
                "status": "expired"
            }
        ]
    }
    """

@subscription_bp.route('/upgrade-options', methods=['GET'])
@require_auth
def get_upgrade_options():
    """
    업그레이드 가능한 플랜 조회

    Response:
    {
        "success": true,
        "current_plan": "basic",
        "upgrade_options": [
            {
                "plan_code": "pro",
                "plan_name_ko": "프로",
                "monthly_price": 79000,
                "annual_price": 790000,
                "price_difference": 40000,  # 현재 플랜 대비
                "features": [...]
            },
            {
                "plan_code": "expert",
                "plan_name_ko": "전문가",
                ...
            }
        ]
    }
    """
```

### Frontend (Dashboard)

```html
<!-- dashboard.html 메인 화면에 추가 -->

<div class="subscription-card">
    <div class="card-header">
        <h3>요금제 정보</h3>
        <span class="plan-badge" id="plan-badge">Basic</span>
    </div>

    <div class="card-body">
        <!-- 현재 플랜 -->
        <div class="plan-info">
            <div class="info-row">
                <span class="label">현재 플랜</span>
                <span class="value" id="current-plan">베이직 (월간)</span>
            </div>
            <div class="info-row">
                <span class="label">결제 금액</span>
                <span class="value" id="plan-amount">39,000원/월</span>
            </div>
            <div class="info-row">
                <span class="label">남은 이용일</span>
                <span class="value highlight" id="days-remaining">7일</span>
            </div>
            <div class="info-row">
                <span class="label">다음 갱신일</span>
                <span class="value" id="next-billing">2025-12-31</span>
            </div>
        </div>

        <!-- 사용량 -->
        <div class="usage-section">
            <h4>사용량</h4>
            <div class="progress-bar">
                <div class="progress-label">
                    <span>투자조언 코인</span>
                    <span id="coins-usage">3/5</span>
                </div>
                <div class="progress">
                    <div class="progress-fill" id="coins-progress" style="width: 60%"></div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-label">
                    <span>급등 알림</span>
                    <span id="alerts-usage">2/5 (이번 주)</span>
                </div>
                <div class="progress">
                    <div class="progress-fill" id="alerts-progress" style="width: 40%"></div>
                </div>
            </div>
        </div>

        <!-- 액션 버튼 -->
        <div class="card-actions">
            <button class="btn-primary" onclick="location.href='#subscription-manage'">
                플랜 변경
            </button>
            <button class="btn-secondary" onclick="location.href='#subscription-extend'">
                사용기간 연장
            </button>
            <button class="btn-outline" onclick="showPaymentHistory()">
                결제 내역
            </button>
        </div>
    </div>
</div>
```

---

## 3️⃣ 계좌이체 결제 UI (플랜 변경/연장)

### 플랜 변경 페이지

```html
<!-- subscription_manage.html (새로 생성) -->

<div class="subscription-manage-container">
    <h1>플랜 변경</h1>

    <!-- 현재 플랜 -->
    <div class="current-plan-section">
        <h2>현재 플랜</h2>
        <div class="plan-card current">
            <div class="plan-name">베이직</div>
            <div class="plan-price">39,000원/월</div>
            <div class="plan-expiry">2025-12-31 만료</div>
        </div>
    </div>

    <!-- 업그레이드 옵션 -->
    <div class="upgrade-options">
        <h2>업그레이드</h2>
        <div class="plans-grid">
            <div class="plan-card" data-plan="pro">
                <div class="plan-badge">추천</div>
                <div class="plan-name">프로</div>
                <div class="plan-price">79,000원/월</div>
                <div class="price-difference">+40,000원</div>
                <ul class="features">
                    <li>10개 코인 모니터링</li>
                    <li>5개 자동매매 전략</li>
                    <li>180일 히스토리</li>
                </ul>
                <button class="btn-upgrade" onclick="selectPlan('pro')">선택</button>
            </div>

            <div class="plan-card" data-plan="expert">
                <div class="plan-name">전문가</div>
                <div class="plan-price">99,000원/월</div>
                <div class="price-difference">+60,000원</div>
                <ul class="features">
                    <li>30개 코인 모니터링</li>
                    <li>10개 자동매매 전략</li>
                    <li>무제한 히스토리</li>
                </ul>
                <button class="btn-upgrade" onclick="selectPlan('expert')">선택</button>
            </div>
        </div>
    </div>

    <!-- 사용기간 연장 (현재 플랜 유지) -->
    <div class="extend-section">
        <h2>사용기간 연장 (현재 플랜 유지)</h2>
        <div class="extend-options">
            <button class="btn-extend" onclick="extendSubscription('monthly')">
                1개월 연장 (39,000원)
            </button>
            <button class="btn-extend" onclick="extendSubscription('annual')">
                1년 연장 (390,000원) - 17% 할인
            </button>
        </div>
    </div>
</div>

<!-- 계좌이체 결제 모달 -->
<div class="modal" id="bank-transfer-modal">
    <div class="modal-content">
        <h3>계좌이체 결제</h3>
        <div class="bank-info">
            <p><strong>입금 계좌</strong></p>
            <p>신한은행 110-123-456789</p>
            <p>예금주: (주)코인펄스</p>
        </div>
        <div class="transfer-amount">
            <p><strong>입금 금액</strong></p>
            <p class="amount" id="transfer-amount">79,000원</p>
        </div>
        <form id="bank-transfer-form">
            <div class="form-group">
                <label>입금자명</label>
                <input type="text" name="depositor_name" required>
            </div>
            <div class="form-group">
                <label>입금 날짜/시간</label>
                <input type="datetime-local" name="transfer_date" required>
            </div>
            <div class="form-group">
                <label>은행명 (선택)</label>
                <input type="text" name="bank_name">
            </div>
            <div class="form-group">
                <label>메모 (선택)</label>
                <textarea name="notes" rows="3"></textarea>
            </div>
            <div class="modal-actions">
                <button type="submit" class="btn-primary">확인 요청 제출</button>
                <button type="button" class="btn-secondary" onclick="closeModal()">취소</button>
            </div>
        </form>
        <div class="info-note">
            💡 입금 확인 후 관리자가 플랜을 활성화합니다 (24시간 이내)
        </div>
    </div>
</div>
```

---

## 4️⃣ 구현 우선순위

### Phase 1: 긴급 (Admin 불일치 관리)
**예상 시간: 2-3시간**

1. ✅ Backend API 구현
   - `/api/admin/payment-recovery/mismatches`
   - `/api/admin/payment-recovery/<id>/apply`
   - `/api/admin/transactions`

2. ✅ Admin 페이지 UI
   - 불일치 케이스 테이블
   - 수동 적용 모달

### Phase 2: 핵심 (대시보드 요금제 정보)
**예상 시간: 3-4시간**

1. ✅ Backend API 구현
   - `/api/subscriptions/current`
   - `/api/subscriptions/history`
   - `/api/subscriptions/upgrade-options`

2. ✅ Dashboard UI
   - 요금제 정보 카드
   - 사용량 progress bar
   - 남은 이용일 표시

### Phase 3: 확장 (플랜 변경/연장)
**예상 시간: 4-5시간**

1. ✅ Frontend 페이지
   - subscription_manage.html (플랜 변경)
   - 계좌이체 결제 모달
   - 사용기간 연장 버튼

2. ✅ 결제 확인 Flow
   - 계좌이체 정보 제출
   - Admin 승인 대기
   - 승인 시 플랜 자동 업데이트

---

## 5️⃣ 데이터베이스 스키마

### 필요한 컬럼 추가 (확인 필요)

```sql
-- transactions 테이블
ALTER TABLE transactions
ADD COLUMN admin_notes TEXT,
ADD COLUMN manually_applied BOOLEAN DEFAULT FALSE,
ADD COLUMN applied_by_admin VARCHAR(255),
ADD COLUMN applied_at TIMESTAMP;

-- user_subscriptions 테이블 (이미 존재하는지 확인)
-- 필요 시 추가:
ALTER TABLE user_subscriptions
ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE,
ADD COLUMN cancel_at_period_end BOOLEAN DEFAULT FALSE;
```

---

## 6️⃣ 보안 고려사항

1. **Admin 권한 확인**
   - 모든 payment-recovery 엔드포인트는 `@require_admin` 데코레이터 필수
   - Admin 이메일 화이트리스트 검증

2. **Transaction 무결성**
   - 동일한 Transaction을 중복 적용 방지
   - `manually_applied` 플래그로 이미 처리된 건 제외

3. **금액 검증**
   - 계좌이체 금액과 플랜 가격 일치 확인
   - 할인/프로모션 코드 처리

4. **로그 기록**
   - Admin이 수동으로 플랜을 변경한 모든 내역 로그
   - 감사 추적(Audit trail) 유지

---

## 7️⃣ 테스트 시나리오

### Test Case 1: 불일치 감지
1. Transaction 생성 (status=SUCCEEDED, amount=39000)
2. User는 여전히 Free 플랜
3. Admin이 `/mismatches` 호출 → 불일치 케이스 1건 발견

### Test Case 2: 수동 복구
1. Admin이 불일치 케이스 선택
2. 플랜 선택 (Basic, monthly)
3. `/apply` 호출
4. User의 Subscription 생성
5. User가 대시보드에서 Basic 플랜 확인

### Test Case 3: 플랜 변경
1. User가 Basic 플랜 사용 중
2. Dashboard에서 "플랜 변경" 클릭
3. Pro 플랜 선택
4. 계좌이체 정보 입력 및 제출
5. Admin이 승인
6. User의 플랜이 Pro로 변경

### Test Case 4: 사용기간 연장
1. User가 Basic 플랜 만료 7일 전
2. "사용기간 연장" 클릭
3. 1개월 연장 선택
4. 계좌이체 후 확인 제출
5. Admin 승인
6. current_period_end가 30일 연장

---

## 8️⃣ 다음 단계

1. ✅ Phase 1 구현 (Admin 불일치 관리)
2. ✅ Phase 2 구현 (Dashboard 요금제 정보)
3. ✅ Phase 3 구현 (플랜 변경/연장)
4. ⏳ Toss Payments Webhook 구현 (자동화)
5. ⏳ 크론잡 모니터링 (매일 불일치 체크)

**구현하시겠습니까?**
