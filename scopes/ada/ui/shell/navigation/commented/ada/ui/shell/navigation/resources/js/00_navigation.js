/* Espejo comentado: sincronización visual con la ruta de Dash Pages. */
(() => {
    'use strict';

    const normalizePath = (value) => {
        if (!value || value === '/') {
            return '/';
        }
        return value.replace(/\/+$/, '') || '/';
    };

    const groupButtonFor = (collapse) =>
        collapse.closest('.app-navigation-group')?.querySelector('.app-navigation-group-button');

    const syncGroupButton = (collapse) => {
        const button = groupButtonFor(collapse);
        if (!button) {
            return;
        }
        button.classList.toggle(
            'app-navigation-group-button-open',
            collapse.classList.contains('show'),
        );
    };

    const syncActiveNavigation = (alignGroups = false) => {
        const currentPath = normalizePath(window.location.pathname);
        const links = document.querySelectorAll('.app-navigation-link-wrapper[href]');
        let activeLink = null;

        links.forEach((link) => {
            const path = link.getAttribute('href') || '';
            const active = path.startsWith('/') && normalizePath(path) === currentPath;
            const button = link.querySelector('.app-navigation-link');

            button?.classList.toggle('active-nav-link', active);
            if (active) {
                activeLink = link;
            }
        });

        document.querySelectorAll('.app-navigation-group .collapse').forEach((collapse) => {
            if (alignGroups) {
                const shouldOpen = activeLink !== null && collapse.contains(activeLink);
                const isOpen = collapse.classList.contains('show');
                if (shouldOpen !== isOpen) {
                    groupButtonFor(collapse)?.click();
                }
            }
            syncGroupButton(collapse);
        });
    };

    const dispatchLocationChange = () => window.dispatchEvent(new Event('ada:locationchange'));
    const patchHistory = (method) => {
        const original = history[method];
        history[method] = function patchedHistory(...args) {
            const result = original.apply(this, args);
            dispatchLocationChange();
            return result;
        };
    };

    if (!window.__ADA_NAVIGATION_HISTORY_PATCHED__) {
        patchHistory('pushState');
        patchHistory('replaceState');
        window.__ADA_NAVIGATION_HISTORY_PATCHED__ = true;
    }

    window.addEventListener('popstate', () => syncActiveNavigation(true));
    window.addEventListener('ada:locationchange', () => syncActiveNavigation(true));
    document.addEventListener('DOMContentLoaded', () => syncActiveNavigation(true));

    new MutationObserver(() => syncActiveNavigation(false)).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class'],
        childList: true,
        subtree: true,
    });
})();
