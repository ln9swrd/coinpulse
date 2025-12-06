/**
 * CoinPulse - Payment Success Page JavaScript
 * 결제 승인 및 구독 활성화 처리
 */

document.addEventListener('DOMContentLoaded', async () => {
    // URL 파라미터에서 결제 정보 가져오기
    const urlParams = new URLSearchParams(window.location.search);
    const paymentKey = urlParams.get('paymentKey');
    const orderId = urlParams.get('orderId');
    const amount = urlParams.get('amount');
    
    if (!paymentKey || !orderId || !amount) {
        showError('잘못된 접근입니다.');
        return;
    }
    
    // 결제 승인 처리
    await confirmPayment(paymentKey, orderId, amount);
});

/**
 * 결제 승인 처리
 */
async function confirmPayment(paymentKey, orderId, amount) {
    try {
        showLoading('결제를 승인하는 중입니다...');
        
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('로그인이 필요합니다.');
        }
        
        const response = await fetch('/api/payment/confirm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                paymentKey: paymentKey,
                orderId: orderId,
                amount: parseInt(amount)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '결제 승인에 실패했습니다.');
        }
        
        const data = await response.json();
        
        hideLoading();
        showSuccess(data.subscription);
        
    } catch (error) {
        console.error('Payment confirmation error:', error);
        hideLoading();
        showError(error.message);
    }
}

/**
 * 결제 성공 메시지 표시
 */
function showSuccess(subscription) {
    const container = document.getElementById('paymentResult');
    if (!container) return;
    
    const plan = subscription.plan;
    const periodEnd = new Date(subscription.current_period_end).toLocaleDateString('ko-KR');
    
    container.innerHTML = `
        <div class="success-message">
            <div class="success-icon">✓</div>
            <h2>결제가 완료되었습니다!</h2>
            <p>${plan.toUpperCase()} 플랜이 활성화되었습니다.</p>
            <div class="subscription-info">
                <p>구독 만료일: ${periodEnd}</p>
                <p>결제 금액: ${subscription.amount.toLocaleString()}원</p>
            </div>
            <div class="action-buttons">
                <button onclick="goToDashboard()" class="btn-primary">대시보드로 이동</button>
                <button onclick="viewSubscription()" class="btn-secondary">구독 정보 보기</button>
            </div>
        </div>
    `;
}

/**
 * 에러 메시지 표시
 */
function showError(message) {
    const container = document.getElementById('paymentResult');
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-message">
            <div class="error-icon">✗</div>
            <h2>결제 처리 실패</h2>
            <p>${message}</p>
            <div class="action-buttons">
                <button onclick="goToCheckout()" class="btn-primary">다시 시도</button>
                <button onclick="goToSupport()" class="btn-secondary">고객지원</button>
            </div>
        </div>
    `;
}

/**
 * 로딩 표시
 */
function showLoading(message) {
    const container = document.getElementById('paymentResult');
    if (!container) return;
    
    container.innerHTML = `
        <div class="loading-message">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
}

/**
 * 로딩 숨기기
 */
function hideLoading() {
    // showSuccess나 showError가 대체함
}

/**
 * 대시보드로 이동
 */
function goToDashboard() {
    window.location.href = '/dashboard.html';
}

/**
 * 구독 정보 페이지로 이동
 */
function viewSubscription() {
    window.location.href = '/dashboard.html?tab=subscription';
}

/**
 * 결제 페이지로 이동
 */
function goToCheckout() {
    window.location.href = '/checkout.html';
}

/**
 * 고객지원 페이지로 이동
 */
function goToSupport() {
    window.location.href = 'mailto:support@sinsi.ai';
}
