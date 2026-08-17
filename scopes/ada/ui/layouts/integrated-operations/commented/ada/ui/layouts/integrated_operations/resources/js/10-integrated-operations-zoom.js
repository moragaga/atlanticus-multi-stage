/* Espejo comentado: solo cambia el atributo de presentación de la vista IO; no reconstruye el árbol ni ejecuta callbacks. */
(() => {
    const ROOT_SELECTOR = '[data-ada-io-view-root="integrated-operations"]';
    const CONTROL_SELECTOR = '[data-ada-io-target-view]';
    const VALID_VIEWS = new Set(['overview', 'mine', 'plant']);

    document.addEventListener('click', (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        const control = event.target.closest(CONTROL_SELECTOR);
        if (!control) {
            return;
        }
        const root = control.closest(ROOT_SELECTOR);
        if (!root) {
            return;
        }
        const targetView = control.getAttribute('data-ada-io-target-view');
        if (!VALID_VIEWS.has(targetView)) {
            return;
        }
        root.setAttribute('data-ada-io-view', targetView);
    });
})();
