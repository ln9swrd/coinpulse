/**
 * Sidebar Loader
 * Dynamically loads sidebar component into dashboard
 */

(async function loadSidebar() {
    'use strict';

    const sidebarContainer = document.getElementById('sidebar-container');

    if (!sidebarContainer) {
        console.error('[Sidebar] Container not found');
        return;
    }

    try {
        console.log('[Sidebar] Loading sidebar component...');

        // Fetch sidebar HTML (cache-busting parameter to force reload)
        const response = await fetch('components/sidebar.html?v=20251224_dom_fix');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const sidebarHTML = await response.text();

        // Inject sidebar HTML
        sidebarContainer.innerHTML = sidebarHTML;

        console.log('[Sidebar] Sidebar loaded successfully');

        // Dispatch custom event to notify sidebar is ready
        window.dispatchEvent(new CustomEvent('sidebarLoaded'));

    } catch (error) {
        console.error('[Sidebar] Failed to load sidebar:', error);

        // Show error state
        sidebarContainer.innerHTML = `
            <aside class="sidebar" style="padding: 20px; text-align: center; color: #dc3545;">
                <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                <h3 style="margin: 0 0 12px 0; font-size: 16px;">사이드바 로드 실패</h3>
                <p style="margin: 0; font-size: 14px; opacity: 0.8;">페이지를 새로고침 해주세요</p>
                <button onclick="location.reload()" style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                ">새로고침</button>
            </aside>
        `;
    }
})();
