(() => {
    'use strict';

    /*
     * El presenter decide qué alarma visible se explica. AUTO y selección manual
     * comparten exactamente el mismo reproductor: ambos disparan un replay de la
     * ruta. El temporizador de permanencia empieza solo después de recibir el
     * evento de término de la animación.
     */

    const SCOPE_SELECTOR = '[data-ada-alarm-presentation-scope="true"]';
    const CARD_SELECTOR = '[data-ada-alarm-event-id]';
    const ROUTE_SELECTOR = '[data-ada-alarm-route="active"]';
    const COMPLETE_EVENT = 'ada:alarm-route-complete';
    const INTERACTIVE_SELECTOR =
        'button,a,input,select,textarea,[role="button"],[data-ada-alarm-interactive="true"]';
    const EXIT_DURATION_MS = 180;
    const controllers = new Set();

    class AlarmPresentationController {
        constructor(root) {
            this.root = root;
            this.activeEventId = null;
            this.activeAssignmentKey = null;
            this.pinnedEventId = null;
            this.pinnedAssignmentKey = null;
            this.cursor = -1;
            this.timer = null;
            this.transitionToken = 0;
            this.replayCounter = 0;
            this.observer = null;
            this.onClick = (event) => this.handleClick(event);
            this.onRouteComplete = (event) => this.handleRouteComplete(event);
        }

        start() {
            this.root.addEventListener('click', this.onClick);
            this.root.addEventListener(COMPLETE_EVENT, this.onRouteComplete);
            this.observer = new MutationObserver((records) => this.handleMutations(records));
            this.observer.observe(this.root, {
                attributes: true,
                childList: true,
                subtree: true,
                attributeFilter: [
                    'hidden',
                    'data-ada-alarm-event-id',
                    'data-ada-alarm-assignment-key',
                    'data-ada-alarm-card-tone',
                ],
            });
            this.reconcile(true);
        }

        disconnect() {
            this.clearTimer();
            this.transitionToken += 1;
            this.root.removeEventListener('click', this.onClick);
            this.root.removeEventListener(COMPLETE_EVENT, this.onRouteComplete);
            if (this.observer) {
                this.observer.disconnect();
            }
            const route = this.route();
            if (route) {
                route.dataset.adaAlarmRouteState = 'idle';
            }
        }

        handleMutations(records) {
            const toneChanged = records.some(
                (record) =>
                    record.type === 'attributes' &&
                    record.attributeName === 'data-ada-alarm-card-tone',
            );
            if (toneChanged) {
                this.syncActiveTone();
            }
            this.reconcile(false);
        }

        /*
         * La permanencia configurada es un dwell posterior al trazado completo,
         * no un intervalo contado en paralelo con la animación.
         */
        handleRouteComplete(event) {
            const detail = event.detail || {};
            if (
                detail.eventId !== this.activeEventId ||
                detail.assignmentKey !== this.activeAssignmentKey
            ) {
                return;
            }
            if (this.pinnedEventId || this.effectiveEventCount() <= 1) {
                this.clearTimer();
                return;
            }
            this.scheduleDwell(true);
        }

        /*
         * Los controles internos de la card no alteran el foco. Un click en la
         * superficie de la alarma sí fija el event_id concreto y reproduce su
         * trazado desde el comienzo.
         */
        handleClick(event) {
            if (this.root.dataset.adaAlarmInteraction !== 'interactive') {
                return;
            }
            const target = event.target;
            if (!(target instanceof Element) || target.closest(INTERACTIVE_SELECTOR)) {
                return;
            }
            const card = target.closest(CARD_SELECTOR);
            if (!card || !this.root.contains(card) || !this.isVisible(card)) {
                return;
            }
            if (this.effectiveEventCount() === 1) {
                return;
            }
            const eventId = card.dataset.adaAlarmEventId;
            const assignmentKey = card.dataset.adaAlarmAssignmentKey;
            if (!eventId || !assignmentKey) {
                return;
            }
            if (this.pinnedEventId === eventId) {
                this.clearPinnedState();
                this.advanceFrom(eventId);
                return;
            }
            this.pinnedEventId = eventId;
            this.pinnedAssignmentKey = assignmentKey;
            this.clearTimer();
            this.updateSelectedCards();
            this.activateCard(card, true);
        }

        reconcile(initial) {
            const visible = this.visibleCards();
            if (visible.length === 0) {
                this.clearPinnedState();
                this.clearActiveRoute();
                return;
            }
            if (this.effectiveEventCount() === 1) {
                this.clearPinnedState();
                const only = visible[0];
                const changed =
                    this.activeEventId !== only.dataset.adaAlarmEventId ||
                    this.activeAssignmentKey !== only.dataset.adaAlarmAssignmentKey;
                this.activateCard(only, initial || changed);
                this.clearTimer();
                return;
            }
            if (this.pinnedEventId) {
                const pinned = visible.find(
                    (card) => card.dataset.adaAlarmEventId === this.pinnedEventId,
                );
                if (
                    !pinned ||
                    pinned.dataset.adaAlarmAssignmentKey !== this.pinnedAssignmentKey
                ) {
                    const previous = this.pinnedEventId;
                    this.clearPinnedState();
                    this.advanceFrom(previous);
                    return;
                }
                this.activateCard(pinned, false);
                this.clearTimer();
                return;
            }
            const active = visible.find(
                (card) => card.dataset.adaAlarmEventId === this.activeEventId,
            );
            if (
                active &&
                active.dataset.adaAlarmAssignmentKey === this.activeAssignmentKey
            ) {
                return;
            }
            this.advanceFrom(this.activeEventId, initial);
        }

        advanceFrom(eventId, initial = false) {
            const visible = this.visibleCards();
            if (visible.length === 0) {
                this.clearActiveRoute();
                return;
            }
            let index = visible.findIndex(
                (card) => card.dataset.adaAlarmEventId === eventId,
            );
            if (index < 0) {
                index = this.cursor;
            }
            const nextIndex = initial ? 0 : (index + 1 + visible.length) % visible.length;
            this.cursor = nextIndex;
            this.activateCard(visible[nextIndex], true);
        }

        /*
         * El dwell mantiene una ventana de observación estable. En el harness
         * se usa 15 s; producción podrá inyectar otro valor sin cambiar el player.
         */
        scheduleDwell(reset = false) {
            if (reset) {
                this.clearTimer();
            } else if (this.timer !== null) {
                return;
            }
            if (this.pinnedEventId || this.effectiveEventCount() <= 1) {
                return;
            }
            const dwell = Number.parseInt(
                this.root.dataset.adaAlarmTraceDwellMs || '',
                10,
            );
            if (!Number.isFinite(dwell) || dwell <= 0) {
                return;
            }
            this.timer = window.setTimeout(() => {
                this.timer = null;
                this.advanceFrom(this.activeEventId);
            }, dwell);
        }

        clearTimer() {
            if (this.timer !== null) {
                window.clearTimeout(this.timer);
                this.timer = null;
            }
        }

        activateCard(card, replay) {
            const eventId = card.dataset.adaAlarmEventId;
            const assignmentKey = card.dataset.adaAlarmAssignmentKey;
            if (!eventId || !assignmentKey) {
                return;
            }
            const route = this.route();
            if (!route) {
                return;
            }
            const current = this.activeRoute();
            const sameEvent =
                current === route && route.dataset.adaAlarmRouteEventId === eventId;
            this.activeEventId = eventId;
            this.activeAssignmentKey = assignmentKey;
            this.cursor = this.visibleCards().indexOf(card);
            if (replay) {
                this.clearTimer();
            }
            if (sameEvent) {
                this.applyCardToRoute(route, card);
                if (replay) {
                    this.replayCounter += 1;
                    route.dataset.adaAlarmRouteReplay = String(this.replayCounter);
                }
                return;
            }
            const token = ++this.transitionToken;
            this.clearTimer();
            if (current) {
                current.dataset.adaAlarmRouteState = 'exiting';
            }
            window.setTimeout(() => {
                if (token !== this.transitionToken || !this.root.isConnected) {
                    return;
                }
                this.applyCardToRoute(route, card);
                this.replayCounter += 1;
                route.dataset.adaAlarmRouteReplay = String(this.replayCounter);
                route.dataset.adaAlarmRouteState = 'active';
            }, current ? EXIT_DURATION_MS : 0);
        }

        applyCardToRoute(route, card) {
            route.dataset.adaAlarmRouteEventId = card.dataset.adaAlarmEventId || '';
            route.dataset.adaAlarmRouteCardKey = card.dataset.adaAlarmCardKey || '';
            route.dataset.adaAlarmRouteAssignmentKey =
                card.dataset.adaAlarmAssignmentKey || '';
            route.dataset.adaAlarmRouteTone = card.dataset.adaAlarmCardTone || 'attention';
            route.dataset.adaAlarmRouteOrigin = card.dataset.adaAlarmRouteOrigin || '';
            route.dataset.adaAlarmRouteImpacts = card.dataset.adaAlarmRouteImpacts || '';
        }

        clearActiveRoute() {
            this.clearTimer();
            this.transitionToken += 1;
            const route = this.route();
            if (route) {
                route.dataset.adaAlarmRouteState = 'idle';
            }
            this.activeEventId = null;
            this.activeAssignmentKey = null;
        }

        clearPinnedState() {
            this.pinnedEventId = null;
            this.pinnedAssignmentKey = null;
            this.updateSelectedCards();
        }

        updateSelectedCards() {
            this.cards().forEach((card) => {
                card.dataset.adaAlarmSelected = String(
                    Boolean(this.pinnedEventId) &&
                        card.dataset.adaAlarmEventId === this.pinnedEventId,
                );
            });
        }

        syncActiveTone() {
            if (!this.activeEventId) {
                return;
            }
            const card = this.cards().find(
                (candidate) => candidate.dataset.adaAlarmEventId === this.activeEventId,
            );
            const route = this.route();
            if (card && route && card.dataset.adaAlarmCardTone) {
                route.dataset.adaAlarmRouteTone = card.dataset.adaAlarmCardTone;
            }
        }

        effectiveEventCount() {
            return new Set(
                this.cards()
                    .map((card) => card.dataset.adaAlarmEventId)
                    .filter(Boolean),
            ).size;
        }

        visibleCards() {
            return this.cards().filter((card) => this.isVisible(card));
        }

        cards() {
            return Array.from(this.root.querySelectorAll(CARD_SELECTOR));
        }

        route() {
            return this.root.querySelector(ROUTE_SELECTOR);
        }

        activeRoute() {
            const route = this.route();
            return route && route.dataset.adaAlarmRouteState === 'active' ? route : null;
        }

        isVisible(card) {
            return !card.hidden && card.getClientRects().length > 0;
        }
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = new AlarmPresentationController(root);
        controllers.add(controller);
        controller.start();
    }

    function scan(root = document) {
        if (root.matches && root.matches(SCOPE_SELECTOR)) {
            mount(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll(SCOPE_SELECTOR).forEach(mount);
        }
    }

    function sweep() {
        controllers.forEach((controller) => {
            if (controller.root.isConnected) {
                return;
            }
            controller.disconnect();
            controllers.delete(controller);
        });
    }

    function start() {
        scan();
        const observer = new MutationObserver((records) => {
            records.forEach((record) => {
                record.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        scan(node);
                    }
                });
            });
            sweep();
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
        start();
    }
})();
