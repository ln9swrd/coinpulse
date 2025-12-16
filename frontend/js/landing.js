/**
 * CoinPulse Landing Page JavaScript
 * Handles mobile menu, smooth scrolling, scroll animations, and real-time stats
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
        
        document.addEventListener('click', (e) => {
            if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
        
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
            
            if (currentScroll > scrollThreshold) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            lastScroll = currentScroll;
        });
    };

    // ============================================
    // 3. Smooth Scroll
    // ============================================
    const initSmoothScroll = () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    };

    // ============================================
    // 4. Scroll Animations
    // ============================================
    const initScrollAnimations = () => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1
        });
        
        document.querySelectorAll('.feature-card, .pricing-card, .stat-item').forEach(el => {
            observer.observe(el);
        });
    };

    // ============================================
    // 5. Real-time Stats Loading
    // ============================================
    const initStats = () => {
        const loadStats = async () => {
            try {
                const response = await fetch('/api/stats/summary');
                const data = await response.json();
                
                if (data.success) {
                    const stats = data.stats;
                    
                    const totalUsersEl = document.querySelector('[data-stat="total-users"]');
                    if (totalUsersEl) totalUsersEl.textContent = stats.users.total;
                    
                    const activeUsersEl = document.querySelector('[data-stat="active-users"]');
                    if (activeUsersEl) activeUsersEl.textContent = stats.users.active;
                    
                    const tradesEl = document.querySelector('[data-stat="total-trades"]');
                    if (tradesEl) tradesEl.textContent = stats.trading.total_orders;
                }
            } catch (error) {
                console.error('통계 로드 실패:', error);
            }
        };
        
        loadStats();
        setInterval(loadStats, 30000);
    };

    // ============================================
    // Initialize on DOMContentLoaded
    // ============================================
    document.addEventListener('DOMContentLoaded', () => {
        initMobileMenu();
        initNavbarScroll();
        initSmoothScroll();
        initScrollAnimations();
        initStats();
    });

})();
