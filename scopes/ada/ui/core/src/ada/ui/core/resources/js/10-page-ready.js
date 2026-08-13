(() => {
    const SCOPE_SELECTOR = '[data-page-ready="true"]';
    const stateByScope = new WeakMap();
    let observer = null;
    let syncQueued = false;

    const parseRequired = (scope) => {
        const raw = scope.getAttribute('data-ready-required') || '';
        return raw.split(',').map((value) => value.trim()).filter(Boolean);
    };

    const getReadyElements = (scope, name) => {
        return Array.from(scope.querySelectorAll('[data-ready-name]')).filter((element) => {
            return element.getAttribute('data-ready-name') === name;
        });
    };

    const pendingNames = (scope) => {
        const required = parseRequired(scope);
        return required.filter((name) => {
            const elements = getReadyElements(scope, name);
            return elements.length === 0 || elements.some((element) => {
                return element.getAttribute('data-ready') !== 'true';
            });
        });
    };

    const setState = (scope, value) => {
        scope.setAttribute('data-ready-state', value);
        scope.classList.toggle('is-loading', value === 'loading');
        scope.classList.toggle('is-ready', value === 'ready');
        scope.classList.toggle('is-failed', value === 'failed');
    };

    const setMessage = (scope, message) => {
        const element = scope.querySelector('[data-page-ready-message="true"]');
        if (element) {
            element.textContent = message;
        }
    };

    const finish = (scope) => {
        const state = stateByScope.get(scope);
        if (state && state.timeoutId) {
            window.clearTimeout(state.timeoutId);
            state.timeoutId = null;
        }
        setState(scope, 'ready');
    };

    const fail = (scope) => {
        const pending = pendingNames(scope);
        if (pending.length === 0) {
            finish(scope);
            return;
        }
        console.warn('[WARN] ADA startup readiness timeout:', pending);
        setMessage(scope, 'No fue posible completar la carga.');
        setState(scope, 'failed');
    };

    const start = (scope) => {
        if (stateByScope.has(scope)) {
            return;
        }
        const rawTimeout = Number(scope.getAttribute('data-ready-timeout-ms'));
        const timeoutMs = Number.isFinite(rawTimeout) && rawTimeout >= 1000 ? rawTimeout : 30000;
        const state = { timeoutId: null };
        state.timeoutId = window.setTimeout(() => fail(scope), timeoutMs);
        stateByScope.set(scope, state);
        setState(scope, 'loading');
    };

    const syncScope = (scope) => {
        start(scope);
        if (pendingNames(scope).length === 0) {
            finish(scope);
        }
    };

    const sync = () => {
        syncQueued = false;
        document.querySelectorAll(SCOPE_SELECTOR).forEach((scope) => {
            try {
                syncScope(scope);
            } catch (error) {
                console.error('[ERROR] ADA startup readiness failed:', error);
            }
        });
    };

    const requestSync = () => {
        if (syncQueued) {
            return;
        }
        syncQueued = true;
        window.setTimeout(sync, 0);
    };

    const boot = () => {
        if (!observer) {
            observer = new MutationObserver(requestSync);
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-ready', 'data-ready-name', 'data-page-ready']
            });
        }
        requestSync();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();
