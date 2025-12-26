/**
 * Page Header Component Loader
 * Dynamically loads and initializes the page header
 */

(function() {
    'use strict';

    console.log('[HeaderLoader] Starting header loader...');

    async function loadHeader() {
        const headerContainer = document.getElementById('header-container');

        if (!headerContainer) {
            console.error('[HeaderLoader] Header container not found');
            return;
        }

        try {
            console.log('[HeaderLoader] Fetching page-header.html...');

            const response = await fetch('/components/page-header.html?v=' + Date.now());

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const html = await response.text();
            console.log('[HeaderLoader] Header HTML loaded, length:', html.length);

            // Insert header HTML
            headerContainer.innerHTML = html;

            // Extract and execute scripts
            const scripts = headerContainer.querySelectorAll('script');
            console.log('[HeaderLoader] Found', scripts.length, 'scripts to execute');

            scripts.forEach((oldScript, index) => {
                const newScript = document.createElement('script');

                // Copy attributes
                Array.from(oldScript.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });

                // Copy content
                newScript.textContent = oldScript.textContent;

                // Replace old script with new one to trigger execution
                oldScript.parentNode.replaceChild(newScript, oldScript);

                console.log(`[HeaderLoader] Script ${index + 1} executed`);
            });

            console.log('[HeaderLoader] Header loaded and initialized successfully');

            // Fire custom event
            window.dispatchEvent(new CustomEvent('headerLoaded', {
                detail: { timestamp: Date.now() }
            }));

        } catch (error) {
            console.error('[HeaderLoader] Failed to load header:', error);
            headerContainer.innerHTML = `
                <div style="padding: 20px; background: #fee; color: #c00; border-radius: 8px; margin: 10px;">
                    <strong>Error loading header:</strong> ${error.message}
                </div>
            `;
        }
    }

    // Load header immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadHeader);
    } else {
        loadHeader();
    }

    console.log('[HeaderLoader] Header loader script initialized');
})();
