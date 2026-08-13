(() => {
    // Time Status mantiene un único subscriber y consulta siempre los slots actualmente montados.
    const ROOT_SELECTOR = '[data-ada-time-status="true"]';
    const SOURCE_SELECTOR = '[data-time-status-source="true"]';
    const formatterCache = new Map();
    let observer = null;
    let subscribed = false;

    const formatElapsedTime = (elapsedSeconds) => {
        if (elapsedSeconds < 10) {
            return 'hace menos de 10 segundos';
        }
        if (elapsedSeconds < 60) {
            const bucket = Math.floor(elapsedSeconds / 10) * 10;
            return `hace más de ${bucket} segundos`;
        }
        if (elapsedSeconds < 3600) {
            const minutes = Math.floor(elapsedSeconds / 60);
            return `hace más de ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`;
        }
        if (elapsedSeconds < 86400) {
            const hours = Math.floor(elapsedSeconds / 3600);
            return `hace más de ${hours} ${hours === 1 ? 'hora' : 'horas'}`;
        }
        const days = Math.floor(elapsedSeconds / 86400);
        return `hace más de ${days} ${days === 1 ? 'día' : 'días'}`;
    };

    const getClockFormatter = (timezone) => {
        if (!formatterCache.has(timezone)) {
            formatterCache.set(
                timezone,
                new Intl.DateTimeFormat('es-CL', {
                    timeZone: timezone,
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hourCycle: 'h23'
                })
            );
        }
        return formatterCache.get(timezone);
    };

    const formatClock = (now, timezone) => {
        const parts = Object.fromEntries(
            getClockFormatter(timezone)
                .formatToParts(now)
                .filter((part) => part.type !== 'literal')
                .map((part) => [part.type, part.value])
        );
        return (
            `${parts.day}-${parts.month}-${parts.year} ` +
            `${parts.hour}:${parts.minute}:${parts.second}`
        );
    };

    // Solo una fuente sana puede evolucionar por tiempo; los errores requieren un nuevo snapshot.
    const setTemporalState = (source, now) => {
        if (source.dataset.sourceHealth !== 'healthy') {
            return;
        }

        const timestamp = Date.parse(source.dataset.updatedAtUtc || '');
        const staleAfterSeconds = Number(source.dataset.staleAfterSeconds);
        if (!Number.isFinite(timestamp) || !Number.isFinite(staleAfterSeconds)) {
            return;
        }

        const elapsedSeconds = Math.max(0, Math.floor((now.getTime() - timestamp) / 1000));
        const stale = elapsedSeconds >= staleAfterSeconds;
        const value = source.querySelector('[data-time-status-value="true"]');
        const icon = source.querySelector('[data-time-status-icon="true"]');

        source.dataset.sourceFreshness = stale ? 'stale' : 'fresh';
        source.classList.toggle('is-stale', stale);
        source.classList.toggle('is-fresh', !stale);
        if (value) {
            value.textContent = formatElapsedTime(elapsedSeconds);
        }
        if (icon) {
            const iconClass = stale ? 'bi bi-cloud-slash' : 'bi bi-cloud-check';
            icon.className = `${iconClass} ada-time-status__source-icon`;
        }
    };

    const updateRoot = (root, now) => {
        root.querySelectorAll(SOURCE_SELECTOR).forEach((source) => {
            setTemporalState(source, now);
        });

        const clock = root.querySelector('[data-time-status-clock="true"]');
        if (clock) {
            clock.textContent = formatClock(now, root.dataset.timezone || 'America/Santiago');
        }
    };

    const update = (now) => {
        document.querySelectorAll(ROOT_SELECTOR).forEach((root) => {
            updateRoot(root, now);
        });
    };

    // Dash puede montar el shell después de cargar los assets, por eso esperamos el primer root.
    const subscribe = () => {
        if (subscribed || !document.querySelector(ROOT_SELECTOR)) {
            return subscribed;
        }
        if (!window.AppTicker) {
            console.error('[ERROR] AppTicker is not available for Time Status');
            return false;
        }
        window.AppTicker.subscribe(update);
        subscribed = true;
        if (observer) {
            observer.disconnect();
            observer = null;
        }
        return true;
    };

    const boot = () => {
        if (subscribe()) {
            return;
        }
        observer = new MutationObserver(() => {
            subscribe();
        });
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, {once: true});
    } else {
        boot();
    }
})();
