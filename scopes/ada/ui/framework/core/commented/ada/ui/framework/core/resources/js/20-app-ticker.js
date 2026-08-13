(() => {
    // El ticker vive una sola vez por documento y comparte el mismo temporizador.
    if (window.AppTicker) {
        return;
    }

    const subscribers = new Set();
    let timeoutId = null;

    const currentSecond = () => {
        const timestamp = Date.now();
        return new Date(timestamp - (timestamp % 1000));
    };

    const emit = () => {
        const now = currentSecond();
        Array.from(subscribers).forEach((callback) => {
            try {
                callback(now);
            } catch (error) {
                // Un consumidor defectuoso no puede detener a los demás.
                console.error('[ERROR] AppTicker subscriber failed:', error);
            }
        });
    };

    const schedule = () => {
        if (subscribers.size === 0 || timeoutId !== null) {
            return;
        }
        // Se alinea al próximo cambio real de segundo para evitar deriva acumulativa.
        const delay = 1000 - (Date.now() % 1000);
        timeoutId = setTimeout(() => {
            timeoutId = null;
            emit();
            schedule();
        }, delay);
    };

    const stopIfUnused = () => {
        if (subscribers.size !== 0 || timeoutId === null) {
            return;
        }
        clearTimeout(timeoutId);
        timeoutId = null;
    };

    window.AppTicker = Object.freeze({
        subscribe(callback) {
            if (typeof callback !== 'function') {
                throw new TypeError('AppTicker subscriber must be a function');
            }
            subscribers.add(callback);
            try {
                // El primer frame se actualiza sin esperar al próximo segundo.
                callback(currentSecond());
            } catch (error) {
                console.error('[ERROR] AppTicker initial subscriber failed:', error);
            }
            schedule();

            let active = true;
            return () => {
                if (!active) {
                    return;
                }
                active = false;
                subscribers.delete(callback);
                stopIfUnused();
            };
        }
    });
})();
