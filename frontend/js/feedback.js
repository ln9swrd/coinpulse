/**
 * Feedback System
 * 사용자 피드백 제출 시스템
 */

(function() {
    'use strict';

    // DOM Elements
    const floatingBtn = document.getElementById('feedback-floating-btn');
    const modal = document.getElementById('feedback-modal');
    const modalOverlay = document.getElementById('feedback-modal-overlay');
    const modalClose = document.getElementById('feedback-modal-close');
    const cancelBtn = document.getElementById('feedback-cancel-btn');
    const form = document.getElementById('feedback-form');
    const submitBtn = document.getElementById('feedback-submit-btn');
    const submitText = document.getElementById('feedback-submit-text');
    const submitSpinner = document.getElementById('feedback-submit-spinner');

    // Open modal
    function openModal() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Close modal
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        form.reset();
    }

    // Event Listeners
    floatingBtn.addEventListener('click', openModal);
    modalClose.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', closeModal);

    // Close modal on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get form data
        const formData = new FormData(form);
        const data = {
            type: formData.get('type'),
            priority: formData.get('priority'),
            subject: formData.get('subject'),
            content: formData.get('content'),
            screenshot_url: formData.get('screenshot_url') || null
        };

        // Validate required fields
        if (!data.type || !data.subject || !data.content) {
            showNotification('모든 필수 항목을 입력해주세요.', 'error');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitText.style.display = 'none';
        submitSpinner.style.display = 'inline-block';

        try {
            // Get JWT token
            const token = localStorage.getItem('jwt_token');
            if (!token) {
                showNotification('로그인이 필요합니다.', 'error');
                window.location.href = '/login.html';
                return;
            }

            // Submit feedback
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                showNotification('피드백이 성공적으로 제출되었습니다. 소중한 의견 감사합니다!', 'success');
                closeModal();

                // Log success
                console.log('[Feedback] Submitted successfully:', result.feedback_id);
            } else {
                const errorMsg = result.error || '피드백 제출에 실패했습니다.';
                showNotification(errorMsg, 'error');
                console.error('[Feedback] Submission failed:', result);
            }
        } catch (error) {
            console.error('[Feedback] Network error:', error);
            showNotification('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'error');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitText.style.display = 'inline';
            submitSpinner.style.display = 'none';
        }
    });

    // Show notification (toast)
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelectorAll('.feedback-notification');
        existing.forEach(el => el.remove());

        // Create notification
        const notification = document.createElement('div');
        notification.className = `feedback-notification feedback-notification-${type}`;
        notification.textContent = message;

        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '16px 24px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            fontSize: '14px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
            zIndex: '9999',
            animation: 'slideInRight 0.3s ease',
            maxWidth: '400px',
            wordWrap: 'break-word'
        });

        // Set background color based on type
        if (type === 'success') {
            notification.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        } else if (type === 'error') {
            notification.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        } else {
            notification.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }

        // Add animation keyframes
        if (!document.getElementById('feedback-notification-style')) {
            const style = document.createElement('style');
            style.id = 'feedback-notification-style';
            style.textContent = `
                @keyframes slideInRight {
                    from {
                        opacity: 0;
                        transform: translateX(100px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                @keyframes slideOutRight {
                    from {
                        opacity: 1;
                        transform: translateX(0);
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100px);
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // Add to DOM
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    console.log('[Feedback] System initialized');
})();
