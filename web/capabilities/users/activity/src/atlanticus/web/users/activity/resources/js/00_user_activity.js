(() => {
    const ENDPOINT = '/api/user-activity';
    const HEARTBEAT_MS = 5 * 60 * 1000;
    const STORAGE_NAMESPACE = 'atlanticus:user-activity:v2';
    const STORAGE_KEYS = {
        clientSessionId: `${STORAGE_NAMESPACE}:client-session-id`,
        sequence: `${STORAGE_NAMESPACE}:sequence`,
        lastPathname: `${STORAGE_NAMESPACE}:last-pathname`
    };
    const state = {
        started: false,
        heartbeatIntervalId: null,
        currentPathname: window.location.pathname || '/'
    };

    const createId = () => {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return window.crypto.randomUUID();
        }
        return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    };

    const getOrCreateClientSessionId = () => {
        const existing = window.sessionStorage.getItem(STORAGE_KEYS.clientSessionId);
        if (existing) {
            return existing;
        }
        const created = createId();
        window.sessionStorage.setItem(STORAGE_KEYS.clientSessionId, created);
        return created;
    };

    const nextSequence = () => {
        const previous = Number.parseInt(
            window.sessionStorage.getItem(STORAGE_KEYS.sequence) || '0',
            10
        );
        const next = Number.isFinite(previous) ? previous + 1 : 1;
        window.sessionStorage.setItem(STORAGE_KEYS.sequence, String(next));
        return next;
    };

    const getViewport = () => ({
        width: window.innerWidth,
        height: window.innerHeight
    });

    const getScreen = () => ({
        width: window.screen?.width || 0,
        height: window.screen?.height || 0,
        pixel_ratio: window.devicePixelRatio || 1
    });

    const normalizePathname = (value) => {
        const path = value || '/';
        if (path === '/') {
            return '/';
        }
        return path.replace(/\/+$/, '') || '/';
    };

    const buildPayload = (eventType, previousPathname = null) => ({
        event_id: createId(),
        client_session_id: getOrCreateClientSessionId(),
        sequence: nextSequence(),
        event_type: eventType,
        pathname: normalizePathname(window.location.pathname),
        previous_pathname: previousPathname,
        visibility_state: document.visibilityState === 'hidden' ? 'hidden' : 'visible',
        viewport: getViewport(),
        screen: getScreen(),
        client_timestamp_utc: new Date().toISOString()
    });

    const sendBeacon = (payload) => {
        if (typeof navigator.sendBeacon !== 'function') {
            return false;
        }
        const body = new Blob([JSON.stringify(payload)], {type: 'application/json'});
        return navigator.sendBeacon(ENDPOINT, body);
    };

    const post = async (payload, keepalive = false) => {
        const response = await fetch(ENDPOINT, {
            method: 'POST',
            credentials: 'same-origin',
            keepalive,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        return response.ok;
    };

    const sendEvent = async (eventType, options = {}) => {
        const payload = buildPayload(eventType, options.previousPathname || null);
        if (options.beacon === true && sendBeacon(payload)) {
            return true;
        }
        try {
            return await post(payload, options.keepalive === true);
        } catch {
            return false;
        }
    };

    const stopHeartbeat = () => {
        if (state.heartbeatIntervalId === null) {
            return;
        }
        window.clearInterval(state.heartbeatIntervalId);
        state.heartbeatIntervalId = null;
    };

    const startHeartbeat = () => {
        if (state.heartbeatIntervalId !== null || document.visibilityState !== 'visible') {
            return;
        }
        state.heartbeatIntervalId = window.setInterval(() => {
            if (document.visibilityState === 'visible') {
                sendEvent('heartbeat').catch(() => undefined);
            }
        }, HEARTBEAT_MS);
    };

    const handleVisibilityChange = () => {
        if (document.visibilityState === 'hidden') {
            stopHeartbeat();
            sendEvent('hidden', {beacon: true, keepalive: true}).catch(() => undefined);
            return;
        }
        sendEvent('visible').catch(() => undefined);
        startHeartbeat();
    };

    const handleRouteChange = () => {
        const nextPathname = normalizePathname(window.location.pathname);
        const previousPathname = normalizePathname(state.currentPathname);
        if (nextPathname === previousPathname) {
            return;
        }
        state.currentPathname = nextPathname;
        window.sessionStorage.setItem(STORAGE_KEYS.lastPathname, nextPathname);
        sendEvent('route_changed', {previousPathname}).catch(() => undefined);
    };

    const wrapHistory = (methodName) => {
        const original = window.history[methodName];
        window.history[methodName] = function (...args) {
            const result = original.apply(this, args);
            handleRouteChange();
            return result;
        };
    };

    const handlePageHide = () => {
        stopHeartbeat();
        sendEvent('pagehide', {beacon: true, keepalive: true}).catch(() => undefined);
    };

    const start = () => {
        if (state.started) {
            return;
        }
        state.started = true;
        state.currentPathname = normalizePathname(window.location.pathname);
        const previousPathname = window.sessionStorage.getItem(STORAGE_KEYS.lastPathname);
        window.sessionStorage.setItem(STORAGE_KEYS.lastPathname, state.currentPathname);
        wrapHistory('pushState');
        wrapHistory('replaceState');
        window.addEventListener('popstate', handleRouteChange);
        window.addEventListener('pagehide', handlePageHide);
        document.addEventListener('visibilitychange', handleVisibilityChange);
        sendEvent('register', {previousPathname}).catch(() => undefined);
        startHeartbeat();
    };

    window.AtlanticusUserActivity = {
        heartbeat: () => sendEvent('heartbeat'),
        sessionId: () => getOrCreateClientSessionId()
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start, {once: true});
    } else {
        start();
    }
})();
