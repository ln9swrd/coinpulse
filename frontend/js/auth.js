/**
 * CoinPulse Authentication JavaScript
 * Handles login, signup, password reset
 */

(function() {
    'use strict';

    // ============================================
    // 1. Configuration
    // ============================================
    const CONFIG = {
        apiUrl: `${window.location.origin}/api`,  // 환경 자동 감지 (localhost or production)
        endpoints: {
            login: '/auth/login',
            signup: '/auth/signup',
            logout: '/auth/logout',
            verifyToken: '/auth/verify',
            resetPassword: '/auth/reset-password'
        }
    };

    // ============================================
    // 2. Authentication Class
    // ============================================
    class AuthManager {
        constructor() {
            this.token = localStorage.getItem('auth_token') || null;
            this.user = JSON.parse(localStorage.getItem('user_data') || 'null');
            this.init();
        }

        init() {
            // Load configuration
            this.loadConfig();

            // Initialize page-specific functionality
            const currentPage = window.location.pathname;

            if (currentPage.includes('login.html')) {
                this.initLoginPage();
            } else if (currentPage.includes('signup.html')) {
                this.initSignupPage();
            } else if (currentPage.includes('forgot-password.html')) {
                this.initForgotPasswordPage();
            }
        }

        /**
         * Load API configuration
         */
        async loadConfig() {
            try {
                const response = await fetch('config.json');
                const config = await response.json();
                CONFIG.apiUrl = config.api?.tradingServerUrl || CONFIG.apiUrl;
                console.log('[Auth] Configuration loaded:', CONFIG.apiUrl);
            } catch (error) {
                console.warn('[Auth] Failed to load config, using defaults:', error);
            }
        }

        // ============================================
        // LOGIN PAGE
        // ============================================
        initLoginPage() {
            const loginForm = document.getElementById('login-form');
            const togglePassword = document.querySelector('.toggle-password');

            if (loginForm) {
                loginForm.addEventListener('submit', (e) => this.handleLogin(e));
            }

            if (togglePassword) {
                togglePassword.addEventListener('click', () => this.togglePasswordVisibility('password'));
            }

            console.log('[Auth] Login page initialized');
        }

        async handleLogin(e) {
            e.preventDefault();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('remember-me').checked;

            // Clear previous errors
            this.clearFormErrors();

            // Validate inputs
            if (!this.validateEmail(email)) {
                this.showError('email-error', 'Please enter a valid email address');
                return;
            }

            if (password.length < 6) {
                this.showError('password-error', 'Password must be at least 6 characters');
                return;
            }

            // Show loading state
            this.setButtonLoading('login-btn', true);

            try {
                // API call (to be implemented on backend)
                const response = await this.apiCall('POST', CONFIG.endpoints.login, {
                    email,
                    password,
                    remember: rememberMe
                });

                if (response.success) {
                    // Store token and user data
                    this.token = response.token;
                    this.user = response.user;

                    localStorage.setItem('auth_token', this.token);
                    localStorage.setItem('user_data', JSON.stringify(this.user));

                    if (rememberMe) {
                        localStorage.setItem('remember_me', 'true');
                    }

                    // Show success message
                    this.showFormMessage('success', 'Login successful! Redirecting...');

                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = 'trading_chart.html';
                    }, 1500);
                } else {
                    throw new Error(response.message || 'Login failed');
                }
            } catch (error) {
                console.error('[Auth] Login error:', error);
                this.showFormMessage('error', error.message || 'Invalid email or password');
            } finally {
                this.setButtonLoading('login-btn', false);
            }
        }

        // ============================================
        // SIGNUP PAGE
        // ============================================
        initSignupPage() {
            const signupForm = document.getElementById('signup-form');
            const togglePassword = document.querySelector('.toggle-password');
            const toggleConfirmPassword = document.querySelector('.toggle-confirm-password');

            if (signupForm) {
                signupForm.addEventListener('submit', (e) => this.handleSignup(e));
            }

            if (togglePassword) {
                togglePassword.addEventListener('click', () => this.togglePasswordVisibility('password'));
            }

            if (toggleConfirmPassword) {
                toggleConfirmPassword.addEventListener('click', () => this.togglePasswordVisibility('confirm-password'));
            }

            console.log('[Auth] Signup page initialized');
        }

        async handleSignup(e) {
            e.preventDefault();

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const agreeTerms = document.getElementById('agree-terms').checked;

            // Clear previous errors
            this.clearFormErrors();

            // Validate inputs
            if (name.length < 2) {
                this.showError('name-error', 'Name must be at least 2 characters');
                return;
            }

            if (!this.validateEmail(email)) {
                this.showError('email-error', 'Please enter a valid email address');
                return;
            }

            if (password.length < 8) {
                this.showError('password-error', 'Password must be at least 8 characters');
                return;
            }

            if (password !== confirmPassword) {
                this.showError('confirm-password-error', 'Passwords do not match');
                return;
            }

            if (!agreeTerms) {
                this.showFormMessage('error', 'You must agree to the terms and conditions');
                return;
            }

            // Show loading state
            this.setButtonLoading('signup-btn', true);

            try {
                // API call (to be implemented on backend)
                const response = await this.apiCall('POST', CONFIG.endpoints.signup, {
                    name,
                    email,
                    password
                });

                if (response.success) {
                    // Show success message
                    this.showFormMessage('success', 'Account created! Redirecting to login...');

                    // Redirect to login
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 2000);
                } else {
                    throw new Error(response.message || 'Signup failed');
                }
            } catch (error) {
                console.error('[Auth] Signup error:', error);
                this.showFormMessage('error', error.message || 'Failed to create account');
            } finally {
                this.setButtonLoading('signup-btn', false);
            }
        }

        // ============================================
        // FORGOT PASSWORD PAGE
        // ============================================
        initForgotPasswordPage() {
            const resetForm = document.getElementById('reset-form');

            if (resetForm) {
                resetForm.addEventListener('submit', (e) => this.handlePasswordReset(e));
            }

            console.log('[Auth] Forgot password page initialized');
        }

        async handlePasswordReset(e) {
            e.preventDefault();

            const email = document.getElementById('email').value.trim();

            // Clear previous errors
            this.clearFormErrors();

            // Validate email
            if (!this.validateEmail(email)) {
                this.showError('email-error', 'Please enter a valid email address');
                return;
            }

            // Show loading state
            this.setButtonLoading('reset-btn', true);

            try {
                // API call (to be implemented on backend)
                const response = await this.apiCall('POST', CONFIG.endpoints.resetPassword, {
                    email
                });

                if (response.success) {
                    this.showFormMessage('success', 'Password reset link sent to your email');
                } else {
                    throw new Error(response.message || 'Password reset failed');
                }
            } catch (error) {
                console.error('[Auth] Password reset error:', error);
                this.showFormMessage('error', error.message || 'Failed to send reset link');
            } finally {
                this.setButtonLoading('reset-btn', false);
            }
        }

        // ============================================
        // UTILITY METHODS
        // ============================================

        /**
         * API call wrapper
         */
        async apiCall(method, endpoint, data = null) {
            const url = `${CONFIG.apiUrl}${endpoint}`;
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (this.token) {
                options.headers['Authorization'] = `Bearer ${this.token}`;
            }

            if (data && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(data);
            }

            try {
                const response = await fetch(url, options);
                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.message || `HTTP ${response.status}`);
                }

                return result;
            } catch (error) {
                // For development: simulate successful responses
                if (error.message.includes('fetch')) {
                    console.warn('[Auth] API not available, using mock data');
                    return this.getMockResponse(endpoint, data);
                }
                throw error;
            }
        }

        /**
         * Mock responses for development
         */
        getMockResponse(endpoint, data) {
            if (endpoint === CONFIG.endpoints.login) {
                return {
                    success: true,
                    token: 'mock_token_' + Date.now(),
                    user: {
                        id: 1,
                        name: 'Test User',
                        email: data.email
                    }
                };
            }

            if (endpoint === CONFIG.endpoints.signup) {
                return {
                    success: true,
                    message: 'Account created successfully'
                };
            }

            if (endpoint === CONFIG.endpoints.resetPassword) {
                return {
                    success: true,
                    message: 'Password reset link sent'
                };
            }

            return { success: false, message: 'Unknown endpoint' };
        }

        /**
         * Validate email format
         */
        validateEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }

        /**
         * Toggle password visibility
         */
        togglePasswordVisibility(inputId) {
            const input = document.getElementById(inputId);
            if (!input) return;

            if (input.type === 'password') {
                input.type = 'text';
            } else {
                input.type = 'password';
            }
        }

        /**
         * Show field error
         */
        showError(errorId, message) {
            const errorElement = document.getElementById(errorId);
            const inputElement = errorElement?.previousElementSibling;

            if (errorElement) {
                errorElement.textContent = message;
            }

            if (inputElement && inputElement.tagName === 'INPUT') {
                inputElement.classList.add('error');
            } else if (inputElement && inputElement.classList.contains('password-input-wrapper')) {
                inputElement.querySelector('input')?.classList.add('error');
            }
        }

        /**
         * Clear all form errors
         */
        clearFormErrors() {
            const errorMessages = document.querySelectorAll('.error-message');
            const errorInputs = document.querySelectorAll('input.error');

            errorMessages.forEach(el => el.textContent = '');
            errorInputs.forEach(el => el.classList.remove('error'));
        }

        /**
         * Show form message (success/error)
         */
        showFormMessage(type, message) {
            const formMessage = document.getElementById('form-message');
            if (!formMessage) return;

            formMessage.className = `form-message ${type}`;
            formMessage.textContent = message;
        }

        /**
         * Set button loading state
         */
        setButtonLoading(buttonId, isLoading) {
            const button = document.getElementById(buttonId);
            if (!button) return;

            const btnText = button.querySelector('.btn-text');
            const btnLoader = button.querySelector('.btn-loader');

            if (isLoading) {
                button.disabled = true;
                if (btnText) btnText.style.display = 'none';
                if (btnLoader) btnLoader.style.display = 'inline-flex';
            } else {
                button.disabled = false;
                if (btnText) btnText.style.display = 'inline';
                if (btnLoader) btnLoader.style.display = 'none';
            }
        }

        /**
         * Logout
         */
        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_data');
            localStorage.removeItem('remember_me');
            window.location.href = 'index.html';
        }

        /**
         * Check if user is authenticated
         */
        isAuthenticated() {
            return this.token !== null;
        }

        /**
         * Get current user
         */
        getUser() {
            return this.user;
        }
    }

    // ============================================
    // 3. Initialize Authentication
    // ============================================
    const authManager = new AuthManager();

    // Expose to window for use in other scripts
    window.authManager = authManager;

    console.log('[Auth] Authentication system initialized');

})();
