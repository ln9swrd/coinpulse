/**
 * CoinPulse - Checkout Page JavaScript
 * 토스페이먼츠 결제 처리
 */

// 전역 변수
let selectedPlan = 'premium';
let selectedPeriod = 'monthly';
let clientKey = null;
let tossPayments = null;

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    // URL 파라미터에서 플랜 정보 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('plan')) {
        selectedPlan = urlParams.get('plan');
    }
    if (urlParams.has('period')) {
        selectedPeriod = urlParams.get('period');
    }
    
    // 플랜 정보 로드
    loadPlans();
    
    // 이벤트 리스너 등록
    document.querySelectorAll('.plan-card').forEach(card => {
        card.addEventListener('click', () => selectPlan(card.dataset.plan));
    });
    
    document.querySelectorAll('input[name="period"]').forEach(radio => {
        radio.addEventListener('change', (e) => selectPeriod(e.target.value));
    });
    
    document.getElementById('payButton').addEventListener('click', processPayment);
});

/**
 * 구독 플랜 로드
 */
async function loadPlans() {
    try {
        const response = await fetch('/api/payment/plans');
        const plans = await response.json();
        
        // 플랜 정보 표시
        updatePlanDisplay(plans);
        
        // 선택된 플랜 표시
        selectPlan(selectedPlan);
        selectPeriod(selectedPeriod);
        
    } catch (error) {
        console.error('Failed to load plans:', error);
        showError('플랜 정보를 불러오는데 실패했습니다.');
    }
}

/**
 * 플랜 정보 화면에 표시
 */
function updatePlanDisplay(plans) {
    Object.keys(plans).forEach(planKey => {
        const plan = plans[planKey];
        const card = document.querySelector(`[data-plan="${planKey}"]`);
        if (card) {
            // 가격 업데이트
            const priceEl = card.querySelector('.plan-price-monthly');
            const annualPriceEl = card.querySelector('.plan-price-annual');
            
            if (priceEl) priceEl.textContent = plan.price.monthly.toLocaleString();
            if (annualPriceEl) annualPriceEl.textContent = plan.price.annual.toLocaleString();
            
            // 기능 목록 업데이트
            const featuresEl = card.querySelector('.plan-features');
            if (featuresEl && plan.features) {
                featuresEl.innerHTML = plan.features
                    .map(f => `<li>✓ ${f}</li>`)
                    .join('');
            }
        }
    });
}

/**
 * 플랜 선택
 */
function selectPlan(plan) {
    selectedPlan = plan;
    
    // 모든 카드 선택 해제
    document.querySelectorAll('.plan-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // 선택된 카드 강조
    const selectedCard = document.querySelector(`[data-plan="${plan}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // 요약 정보 업데이트
    updateSummary();
}

/**
 * 결제 주기 선택
 */
function selectPeriod(period) {
    selectedPeriod = period;
    updateSummary();
}

/**
 * 결제 요약 정보 업데이트
 */
function updateSummary() {
    const summaryEl = document.getElementById('paymentSummary');
    if (!summaryEl) return;
    
    // 플랜 정보 가져오기
    fetch('/api/payment/plans')
        .then(res => res.json())
        .then(plans => {
            const plan = plans[selectedPlan];
            if (plan) {
                const amount = plan.price[selectedPeriod];
                const periodText = selectedPeriod === 'monthly' ? '월간' : '연간';
                
                summaryEl.innerHTML = `
                    <h3>${plan.name} 플랜</h3>
                    <p>결제 주기: ${periodText}</p>
                    <p class="total-amount">${amount.toLocaleString()}원</p>
                `;
            }
        });
}

/**
 * 결제 처리
 */
async function processPayment() {
    // 로그인 확인
    const token = localStorage.getItem('token');
    if (!token) {
        alert('로그인이 필요합니다.');
        window.location.href = '/login.html';
        return;
    }
    
    // 플랜 선택 확인
    if (selectedPlan === 'free') {
        alert('무료 플랜은 결제가 필요하지 않습니다.');
        return;
    }
    
    try {
        // 로딩 표시
        showLoading('결제 준비 중...');
        
        // 결제 세션 생성
        const response = await fetch('/api/payment/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                plan: selectedPlan,
                billing_period: selectedPeriod
            })
        });
        
        if (!response.ok) {
            throw new Error('결제 세션 생성 실패');
        }
        
        const data = await response.json();
        
        // 토스페이먼츠 SDK 초기화
        if (!tossPayments) {
            clientKey = data.client_key;
            tossPayments = TossPayments(clientKey);
        }
        
        // 결제 위젯 실행
        await tossPayments.requestPayment('카드', {
            amount: data.payment.amount,
            orderId: data.payment.orderId,
            orderName: data.payment.orderName,
            customerName: data.payment.customerName,
            customerEmail: data.payment.customerEmail,
            successUrl: window.location.origin + data.payment.successUrl,
            failUrl: window.location.origin + data.payment.failUrl
        });
        
    } catch (error) {
        console.error('Payment error:', error);
        hideLoading();
        showError('결제 처리 중 오류가 발생했습니다.');
    }
}

/**
 * 로딩 표시
 */
function showLoading(message) {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner"></div>
        <p>${message}</p>
    `;
    document.body.appendChild(overlay);
}

/**
 * 로딩 숨기기
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * 에러 표시
 */
function showError(message) {
    alert(message);
}
