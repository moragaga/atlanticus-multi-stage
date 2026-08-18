(() => {
    'use strict';

    // El controlador no crea un segundo estado de negocio: sólo cambia la ventana de presentación.
    const TOOL_SELECTOR = '[data-ada-integrated-operations-tool]';
    const TARGET_SELECTOR = '[data-ada-io-presentation-target]';
    const VALID_PRESENTATIONS = new Set(['overview', 'mine', 'plant']);
    const ALARM_GEOMETRY_REFRESH_EVENT = 'ada:alarm-geometry-refresh';

    function applyPresentation(tool, presentation) {
        if (!VALID_PRESENTATIONS.has(presentation)) {
            return;
        }
        if (tool.dataset.adaIoPresentation === presentation) {
            return;
        }
        tool.dataset.adaIoPresentation = presentation;
        // Esperamos dos frames para que CSS termine de proyectar Mina/Planta antes de recalcular rutas.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                if (!tool.isConnected) {
                    return;
                }
                // El engine de alarmas conserva evento, rotación y dwell; sólo sincroniza geometría.
                tool.dispatchEvent(new CustomEvent(ALARM_GEOMETRY_REFRESH_EVENT));
            });
        });
    }

    function handleClick(event) {
        const trigger = event.target.closest(TARGET_SELECTOR);
        if (!trigger) {
            return;
        }
        const tool = trigger.closest(TOOL_SELECTOR);
        if (!tool) {
            return;
        }
        applyPresentation(tool, trigger.dataset.adaIoPresentationTarget || '');
    }

    document.addEventListener('click', handleClick);
})();
