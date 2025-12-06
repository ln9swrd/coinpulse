/**
 * CoinPulse Landing Page JavaScript
 * Handles mobile menu, smooth scrolling, and scroll animations
 */

(function() {
    'use strict';

    // ============================================
    // 1. Mobile Menu Toggle
    // ============================================
    const initMobileMenu = () => {
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (!menuToggle || !navMenu) return;

        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });

        // Close menu when clicking on a link
        const menuLinks = navMenu.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', () => {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    };

    // ============================================
    // 2. Navbar Scroll Effect
    // ============================================
    const initNavbarScroll = () => {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        let lastScroll = 0;
        const scrollThreshold = 100;

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;

            // Add shadow when scrolled
            if (currentScroll > 50) {
                navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.boxShadow = '0 1px 2px 0 rgba(0, 0, 0, 0.05)';
            }

            lastScroll = currentScroll;
        });
    };

    // ============================================
    // 3. Smooth Scrolling for Anchor Links
    // ============================================
    const initSmoothScroll = () => {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');

        anchorLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');

                // Skip if it's just "#"
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();

                    const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                    const targetPosition = target.offsetTop - navbarHeight - 20;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    };

    // ============================================
    // 4. Scroll Animations (Fade In)
    // ============================================
    const initScrollAnimations = () => {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Elements to animate
        const animateElements = [
            '.feature-card',
            '.step',
            '.pricing-card',
            '.testimonial-card'
        ];

        animateElements.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach((el, index) => {
                // Initial state
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = `all 0.6s ease-out ${index * 0.1}s`;

                // Observe
                observer.observe(el);
            });
        });
    };

    // ============================================
    // 5. Animated Counter for Stats
    // ============================================
    const initStatCounters = () => {
        const stats = document.querySelectorAll('.stat-number');
        if (stats.length === 0) return;

        const animateValue = (element, start, end, duration, suffix = '') => {
            const range = end - start;
            const increment = range / (duration / 16); // 60 FPS
            let current = start;

            const timer = setInterval(() => {
                current += increment;
                if (current >= end) {
                    element.textContent = end.toLocaleString() + suffix;
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current).toLocaleString() + suffix;
                }
            }, 16);
        };

        // Observe stats section
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    stats.forEach(stat => {
                        const text = stat.textContent;
                        let endValue = 0;
                        let suffix = '';

                        // Parse value
                        if (text.includes(',')) {
                            endValue = parseInt(text.replace(/,/g, '').replace(/\D/g, ''));
                            if (text.includes('+')) suffix = '+';
                        } else if (text.includes('%')) {
                            endValue = parseFloat(text.replace('%', ''));
                            suffix = '%';
                        } else if (text.includes('$')) {
                            endValue = parseInt(text.replace(/\D/g, ''));
                            suffix = text.includes('M') ? 'M+' : '+';
                            stat.textContent = '$' + stat.textContent.replace('$', '');
                        }

                        if (endValue > 0) {
                            animateValue(stat, 0, endValue, 2000, suffix);
                        }
                    });

                    statsObserver.disconnect();
                }
            });
        }, { threshold: 0.5 });

        const heroStats = document.querySelector('.hero-stats');
        if (heroStats) {
            statsObserver.observe(heroStats);
        }
    };

    // ============================================
    // 6. Form Validation (for future forms)
    // ============================================
    const initFormValidation = () => {
        const forms = document.querySelectorAll('form');

        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const inputs = form.querySelectorAll('input[required], textarea[required]');
                let isValid = true;

                inputs.forEach(input => {
                    if (!input.value.trim()) {
                        isValid = false;
                        input.classList.add('error');

                        // Remove error class on input
                        input.addEventListener('input', () => {
                            input.classList.remove('error');
                        }, { once: true });
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                }
            });
        });
    };

    // ============================================
    // 7. Back to Top Button
    // ============================================
    const initBackToTop = () => {
        // Create button if it doesn't exist
        let backToTopBtn = document.querySelector('.back-to-top');

        if (!backToTopBtn) {
            backToTopBtn = document.createElement('button');
            backToTopBtn.className = 'back-to-top';
            backToTopBtn.innerHTML = '↑';
            backToTopBtn.setAttribute('aria-label', 'Back to top');
            document.body.appendChild(backToTopBtn);

            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .back-to-top {
                    position: fixed;
                    bottom: 2rem;
                    right: 2rem;
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    font-size: 1.5rem;
                    cursor: pointer;
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                    z-index: 999;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                .back-to-top.visible {
                    opacity: 1;
                    visibility: visible;
                }
                .back-to-top:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }
            `;
            document.head.appendChild(style);
        }

        // Show/hide button
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 500) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });

        // Scroll to top
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    };

    // ============================================
    // 8. Initialize All Features
    // ============================================
    const init = () => {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAll);
        } else {
            initAll();
        }
    };

    const initAll = () => {
        try {
            initMobileMenu();
            initNavbarScroll();
            initSmoothScroll();
            initScrollAnimations();
            initStatCounters();
            initFormValidation();
            initBackToTop();

            console.log('[Landing Page] All features initialized successfully');
        } catch (error) {
            console.error('[Landing Page] Initialization error:', error);
        }
    };

    // Start initialization
    init();

})();
