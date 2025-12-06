/* ==============================================
   CoinPulse Payment Result Pages JavaScript
   (Success & Error Pages)
   ============================================== */

(function() {
    'use strict';

    // Plan pricing data (same as checkout)
    const PLAN_PRICING = {
        free: {
            name: 'Free Plan',
            monthly: 0,
            annual: 0
        },
        premium: {
            name: 'Premium Plan',
            monthly: 49000,
            annual: 470400
        },
        enterprise: {
            name: 'Enterprise Plan',
            monthly: null,
            annual: null
        }
    };

    // Payment method labels
    const PAYMENT_METHODS = {
        card: 'Credit Card',
        kakao: 'Kakao Pay',
        toss: 'Toss'
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        console.log('[PaymentResult] Initializing result page');

        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const plan = urlParams.get('plan') || 'premium';
        const billing = urlParams.get('billing') || 'monthly';
        const paymentMethod = urlParams.get('method') || 'card';
        const transactionId = urlParams.get('txn') || 'TXN_' + Date.now();
        const errorCode = urlParams.get('error');
        const errorMessage = urlParams.get('message');

        // Determine page type
        const isSuccessPage = document.body.classList.contains('success-page');
        const isErrorPage = document.body.classList.contains('error-page');

        if (isSuccessPage) {
            console.log('[PaymentResult] Loading success page');
            loadSuccessPage(plan, billing, transactionId);
        } else if (isErrorPage) {
            console.log('[PaymentResult] Loading error page');
            loadErrorPage(plan, billing, paymentMethod, errorCode, errorMessage);
        }

        // Initialize download receipt button (success page)
        if (isSuccessPage) {
            initDownloadReceipt(plan, billing, transactionId);
        }

        // Initialize retry button (error page)
        if (isErrorPage) {
            initRetryButton(plan, billing);
        }

        console.log('[PaymentResult] Initialization complete');
    }

    /* ==============================================
       Success Page Functions
       ============================================== */

    function loadSuccessPage(plan, billing, transactionId) {
        const planData = PLAN_PRICING[plan];
        if (!planData) {
            console.error('[PaymentResult] Invalid plan:', plan);
            return;
        }

        const isAnnual = billing === 'annual';
        const price = isAnnual ? planData.annual : planData.monthly;

        // Update plan name
        const planNameEl = document.getElementById('plan-name');
        if (planNameEl) {
            planNameEl.textContent = planData.name;
        }

        // Update billing period
        const billingPeriodEl = document.getElementById('billing-period');
        if (billingPeriodEl) {
            billingPeriodEl.textContent = isAnnual ? 'Annual' : 'Monthly';
        }

        // Update amount paid
        const amountPaidEl = document.getElementById('amount-paid');
        if (amountPaidEl) {
            amountPaidEl.textContent = `₩${formatNumber(price)}`;
        }

        // Calculate next billing date (30 days or 1 year from now)
        const nextBillingDate = new Date();
        if (isAnnual) {
            nextBillingDate.setFullYear(nextBillingDate.getFullYear() + 1);
        } else {
            nextBillingDate.setDate(nextBillingDate.getDate() + 30);
        }

        const nextBillingEl = document.getElementById('next-billing');
        if (nextBillingEl) {
            nextBillingEl.textContent = formatDate(nextBillingDate);
        }

        // Update transaction ID
        const transactionIdEl = document.getElementById('transaction-id');
        if (transactionIdEl) {
            transactionIdEl.textContent = transactionId;
        }

        // Update user email (get from localStorage or use placeholder)
        const userEmail = localStorage.getItem('user_email') || 'your@email.com';
        const userEmailEl = document.getElementById('user-email');
        if (userEmailEl) {
            userEmailEl.textContent = userEmail;
        }

        // Trigger confetti animation (optional)
        triggerConfetti();
    }

    function initDownloadReceipt(plan, billing, transactionId) {
        const downloadBtn = document.getElementById('download-receipt');
        if (!downloadBtn) return;

        downloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('[PaymentResult] Downloading receipt');

            // TODO: Implement actual receipt download
            // For now, just show alert
            alert('Receipt download will be available soon!\nA copy has been sent to your email.');

            // In real implementation, trigger download:
            // window.location.href = '/api/receipt/download?txn=' + transactionId;
        });
    }

    function triggerConfetti() {
        // Simple confetti animation using CSS
        // In production, use a library like canvas-confetti
        console.log('[PaymentResult] Triggering success animation');

        // Add animation class to body
        document.body.classList.add('celebration');

        // Remove after animation completes
        setTimeout(() => {
            document.body.classList.remove('celebration');
        }, 3000);
    }

    /* ==============================================
       Error Page Functions
       ============================================== */

    function loadErrorPage(plan, billing, paymentMethod, errorCode, errorMessage) {
        const planData = PLAN_PRICING[plan];
        if (!planData) {
            console.error('[PaymentResult] Invalid plan:', plan);
            return;
        }

        const isAnnual = billing === 'annual';
        const price = isAnnual ? planData.annual : planData.monthly;

        // Update plan name
        const planNameEl = document.getElementById('plan-name');
        if (planNameEl) {
            planNameEl.textContent = planData.name;
        }

        // Update amount
        const amountEl = document.getElementById('amount');
        if (amountEl) {
            amountEl.textContent = `₩${formatNumber(price)}`;
        }

        // Update payment method
        const paymentMethodEl = document.getElementById('payment-method');
        if (paymentMethodEl) {
            paymentMethodEl.textContent = PAYMENT_METHODS[paymentMethod] || 'Credit Card';
        }

        // Update attempted time
        const attemptedTimeEl = document.getElementById('attempted-time');
        if (attemptedTimeEl) {
            attemptedTimeEl.textContent = formatDateTime(new Date());
        }

        // Update error message
        if (errorMessage) {
            const errorMessageEl = document.getElementById('error-message');
            if (errorMessageEl) {
                errorMessageEl.textContent = errorMessage;
            }

            const errorReasonEl = document.querySelector('.error-reason p');
            if (errorReasonEl) {
                errorReasonEl.textContent = errorMessage;
            }
        }

        // Show error code if provided
        if (errorCode) {
            const errorCodeContainer = document.getElementById('error-code-container');
            const errorCodeEl = document.getElementById('error-code');

            if (errorCodeContainer && errorCodeEl) {
                errorCodeContainer.style.display = 'flex';
                errorCodeEl.textContent = errorCode;
            }
        }
    }

    function initRetryButton(plan, billing) {
        const retryBtn = document.getElementById('retry-button');
        if (!retryBtn) return;

        // Update retry button URL with plan and billing parameters
        const checkoutUrl = `checkout.html?plan=${plan}&billing=${billing}`;
        retryBtn.href = checkoutUrl;
    }

    /* ==============================================
       Utility Functions
       ============================================== */

    function formatNumber(num) {
        if (num === null || num === undefined) return 'Custom';
        return num.toLocaleString('ko-KR');
    }

    function formatDate(date) {
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return date.toLocaleDateString('en-US', options);
    }

    function formatDateTime(date) {
        const dateOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const timeOptions = {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        };

        const datePart = date.toLocaleDateString('en-US', dateOptions);
        const timePart = date.toLocaleTimeString('en-US', timeOptions);

        return `${datePart} - ${timePart}`;
    }

    /* ==============================================
       Analytics & Tracking (Optional)
       ============================================== */

    function trackPaymentSuccess(plan, billing, amount) {
        console.log('[PaymentResult] Tracking payment success:', {
            plan,
            billing,
            amount
        });

        // TODO: Send to analytics platform
        // Example: Google Analytics, Mixpanel, etc.
        /*
        if (typeof gtag !== 'undefined') {
            gtag('event', 'purchase', {
                transaction_id: transactionId,
                value: amount,
                currency: 'KRW',
                items: [{
                    item_name: plan,
                    item_category: 'subscription',
                    item_variant: billing,
                    price: amount,
                    quantity: 1
                }]
            });
        }
        */
    }

    function trackPaymentError(plan, billing, errorCode, errorMessage) {
        console.log('[PaymentResult] Tracking payment error:', {
            plan,
            billing,
            errorCode,
            errorMessage
        });

        // TODO: Send to analytics platform
        /*
        if (typeof gtag !== 'undefined') {
            gtag('event', 'payment_failed', {
                plan: plan,
                billing: billing,
                error_code: errorCode,
                error_message: errorMessage
            });
        }
        */
    }

})();
