(() => {
    'use strict';

    /*
     * Este controlador separa dos capas visuales. La capa de contexto mantiene
     * siempre visibles, en tono neutro, las rutas de todas las alarmas que
     * actualmente ocupan un slot. La capa activa dibuja encima únicamente la
     * alarma que el presenter está explicando, usando rojo o amarillo.
     *
     * Esta separación evita que las líneas aparezcan y desaparezcan en cada
     * turno: la geometría queda estable y solo viaja el color semántico.
     */

    const ROUTE_SELECTOR = '[data-ada-alarm-route]';
    const SCOPE_SELECTOR = '[data-ada-alarm-geometry-scope="true"]';
    const BASELINE_SELECTOR = '[data-ada-alarm-baseline]';
    const CARD_SELECTOR = '[data-ada-alarm-event-id]';
    const FLOW_SPEED_PX_PER_SECOND = 520;
    const MIN_FLOW_DURATION_MS = 250;
    const COMPLETE_EVENT = 'ada:alarm-route-complete';
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const controllers = new Set();

    class AlarmDashboardRouteController {
        constructor(root) {
            this.root = root;
            this.scope = root.closest(SCOPE_SELECTOR);
            this.frame = null;
            this.resizeObserver = null;
            this.geometrySizes = new Map();
            this.mutationObserver = null;
            this.animationGeneration = 0;
            this.lastReplay = null;
            this.lastCompletedReplay = null;
            this.onWindowResize = () => this.schedule(false);
        }

        start() {
            if (!this.scope) {
                return;
            }
            window.addEventListener('resize', this.onWindowResize);
            if (typeof ResizeObserver === 'function') {
                this.resizeObserver = new ResizeObserver((entries) => {
                    let changed = false;
                    entries.forEach((entry) => {
                        const next = this.elementSize(entry.target);
                        const previous = this.geometrySizes.get(entry.target);
                        this.geometrySizes.set(entry.target, next);
                        if (
                            previous &&
                            (Math.abs(previous.width - next.width) > 0.5 ||
                                Math.abs(previous.height - next.height) > 0.5)
                        ) {
                            changed = true;
                        }
                    });
                    if (changed) {
                        this.schedule(false);
                    }
                });
                this.observeResizeElement(this.scope);
                this.observeResizeElement(this.root);
            }
            this.mutationObserver = new MutationObserver((records) => {
                const replay = records.some(
                    (record) =>
                        record.type === 'attributes' &&
                        record.attributeName === 'data-ada-alarm-route-replay',
                );
                if (records.some((record) => this.isRelevantMutation(record))) {
                    this.schedule(replay);
                }
            });
            this.mutationObserver.observe(this.scope, {
                attributes: true,
                childList: true,
                subtree: true,
                attributeFilter: [
                    'hidden',
                    'style',
                    'data-ada-alarm-route-state',
                    'data-ada-alarm-route-replay',
                    'data-ada-alarm-route-card-key',
                    'data-ada-alarm-route-origin',
                    'data-ada-alarm-route-impacts',
                    'data-ada-alarm-route-tone',
                    'data-ada-alarm-card-key',
                    'data-ada-alarm-card-tone',
                    'data-ada-alarm-event-id',
                    'data-ada-alarm-assignment-key',
                    'data-ada-slot-key',
                    'data-ada-component-key',
                ],
            });
            this.schedule(false);
        }

        disconnect() {
            if (this.frame !== null) {
                cancelAnimationFrame(this.frame);
                this.frame = null;
            }
            window.removeEventListener('resize', this.onWindowResize);
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            }
            this.geometrySizes.clear();
            if (this.mutationObserver) {
                this.mutationObserver.disconnect();
            }
            this.clearAllVisualState();
        }

        isRelevantMutation(record) {
            if (record.type === 'attributes') {
                return true;
            }
            if (
                record.target instanceof Element &&
                record.target.closest('.ada-alarm-dashboard-route__svg')
            ) {
                return false;
            }
            return [...record.addedNodes, ...record.removedNodes].some((node) => {
                if (node.nodeType !== Node.ELEMENT_NODE) {
                    return false;
                }
                return !(node.matches && node.matches('.ada-alarm-dashboard-route__svg'));
            });
        }

        schedule(replay) {
            if (replay) {
                this.lastReplay = null;
            }
            if (this.frame !== null) {
                return;
            }
            this.frame = requestAnimationFrame(() => {
                this.frame = null;
                this.refresh();
            });
        }

        refresh() {
            if (!this.scope || !this.root.isConnected) {
                return;
            }
            this.renderContextRoutes();
            const state = this.root.dataset.adaAlarmRouteState || 'idle';
            if (state === 'idle') {
                this.clearActiveVisualState();
                return;
            }
            if (state === 'exiting') {
                return;
            }
            if (state !== 'active') {
                return;
            }
            const replay = this.root.dataset.adaAlarmRouteReplay || '0';
            const animate = replay !== this.lastReplay;
            this.lastReplay = replay;
            this.renderActiveRoute(animate, replay);
        }

        /*
         * Reconstruye las rutas de contexto sin animación. Cada card visible
         * conserva su conexión completa, pero atenuada. No toca nodos ni bordes.
         */
        renderContextRoutes() {
            this.root
                .querySelectorAll('.ada-alarm-dashboard-route__context-svg')
                .forEach((svg) => svg.remove());
            const baseline = this.scope.querySelector(BASELINE_SELECTOR);
            if (!baseline) {
                return;
            }
            const svg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__context-svg',
            );
            const observed = [baseline];
            this.visibleCards().forEach((card) => {
                const specification = this.cardSpecification(card, baseline);
                if (!specification) {
                    return;
                }
                observed.push(
                    card,
                    specification.originElement,
                    ...specification.impactElements,
                );
                this.appendContextGeometry(svg, specification.geometry);
            });
            this.root.prepend(svg);
            this.observeGeometry(observed);
        }

        appendContextGeometry(svg, geometry) {
            [geometry.entry, geometry.connector, ...geometry.branches.filter(Boolean)].forEach(
                (data) => {
                    const path = this.createPath(
                        data,
                        null,
                        'ada-alarm-dashboard-route__context-path',
                    );
                    svg.appendChild(path);
                },
            );
        }

        /*
         * Superpone la ruta activa sobre la ruta neutra existente. El replay
         * controla si debe recorrerse de nuevo o solo recalcularse por resize.
         */
        renderActiveRoute(animate, replay) {
            const baseline = this.scope.querySelector(BASELINE_SELECTOR);
            const card = this.findActiveCard();
            if (!baseline || !card) {
                this.clearActiveVisualState();
                return;
            }
            const specification = this.cardSpecification(card, baseline, true);
            if (!specification) {
                this.clearActiveVisualState();
                return;
            }
            const color = this.readCssValue('--ada-alarm-route-color');
            const foreground = this.readCssValue('--ada-alarm-route-foreground');
            if (!color || !foreground) {
                this.clearActiveVisualState();
                return;
            }
            this.clearActiveVisualState();
            const routeSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__active-svg',
            );
            const impactSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__impact-svg',
            );
            this.root.append(routeSvg, impactSvg);
            const entry = this.createPath(specification.geometry.entry, color);
            routeSvg.appendChild(entry);
            const generation = this.animationGeneration;
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (!animate || reducedMotion) {
                this.finishAll(
                    routeSvg,
                    impactSvg,
                    specification,
                    color,
                    foreground,
                );
                if (animate) {
                    this.notifyComplete(replay);
                }
                return;
            }
            void this.animateSequence(
                generation,
                replay,
                routeSvg,
                impactSvg,
                entry,
                specification,
                color,
                foreground,
            );
        }

        /*
         * Coreografía: card -> connector -> nodo -> impacto. El borde del body
         * empieza a dibujarse únicamente cuando la ruta alcanzó su target.
         */
        async animateSequence(
            generation,
            replay,
            routeSvg,
            impactSvg,
            entry,
            specification,
            color,
            foreground,
        ) {
            await this.animateStroke(entry, generation);
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            const connector = this.createPath(specification.geometry.connector, color);
            routeSvg.appendChild(connector);
            await this.animateStroke(connector, generation);
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            const originIsImpact = specification.impacts.some((target) =>
                this.sameTarget(target, specification.origin),
            );
            const originNode = this.findNode(specification.origin);
            if (originNode) {
                this.applyNodeState(
                    originNode,
                    originIsImpact ? 'origin-impact' : 'origin',
                    color,
                    foreground,
                );
            }
            const tasks = [];
            specification.impacts.forEach((target, index) => {
                if (this.sameTarget(target, specification.origin)) {
                    tasks.push(
                        this.animateImpactBorder(
                            impactSvg,
                            specification.impactElements[index],
                            color,
                            generation,
                        ),
                    );
                    return;
                }
                const pathData = specification.geometry.branches[index];
                if (!pathData) {
                    return;
                }
                const branch = this.createPath(pathData, color);
                routeSvg.appendChild(branch);
                tasks.push(
                    this.animateBranch(
                        branch,
                        impactSvg,
                        target,
                        specification.impactElements[index],
                        color,
                        foreground,
                        generation,
                    ),
                );
            });
            await Promise.all(tasks);
            if (this.isAnimationCurrent(generation)) {
                this.notifyComplete(replay);
            }
        }

        async animateBranch(
            path,
            impactSvg,
            target,
            targetElement,
            color,
            foreground,
            generation,
        ) {
            await this.animateStroke(path, generation);
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            const node = this.findNode(target);
            if (node) {
                this.applyNodeState(node, 'impact', color, foreground);
            }
            await this.animateImpactBorder(impactSvg, targetElement, color, generation);
        }

        async animateImpactBorder(svg, target, color, generation) {
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            this.applyImpact(target, color);
            const path = this.createImpactPath(target, color);
            if (!path) {
                return;
            }
            svg.appendChild(path);
            await this.animateStroke(path, generation);
        }

        finishAll(routeSvg, impactSvg, specification, color, foreground) {
            routeSvg.appendChild(this.createPath(specification.geometry.connector, color));
            const originIsImpact = specification.impacts.some((target) =>
                this.sameTarget(target, specification.origin),
            );
            const originNode = this.findNode(specification.origin);
            if (originNode) {
                this.applyNodeState(
                    originNode,
                    originIsImpact ? 'origin-impact' : 'origin',
                    color,
                    foreground,
                );
            }
            specification.impacts.forEach((target, index) => {
                if (!this.sameTarget(target, specification.origin)) {
                    const pathData = specification.geometry.branches[index];
                    if (pathData) {
                        routeSvg.appendChild(this.createPath(pathData, color));
                    }
                    const node = this.findNode(target);
                    if (node) {
                        this.applyNodeState(node, 'impact', color, foreground);
                    }
                }
                this.applyImpact(specification.impactElements[index], color);
                const path = this.createImpactPath(specification.impactElements[index], color);
                if (path) {
                    impactSvg.appendChild(path);
                }
            });
        }

        cardSpecification(card, baseline, useActiveRouteData = false) {
            if (!this.isVisible(card)) {
                return null;
            }
            const origin = this.parseTarget(
                useActiveRouteData
                    ? this.root.dataset.adaAlarmRouteOrigin
                    : card.dataset.adaAlarmRouteOrigin,
            );
            const impacts = this.parseTargets(
                useActiveRouteData
                    ? this.root.dataset.adaAlarmRouteImpacts
                    : card.dataset.adaAlarmRouteImpacts,
            );
            if (!origin || impacts.length === 0) {
                return null;
            }
            const originElement = this.findTarget(origin);
            const impactElements = impacts.map((target) => this.findTarget(target));
            if (!originElement || impactElements.some((target) => !target)) {
                return null;
            }
            const geometry = this.routeGeometry(
                baseline,
                card,
                originElement,
                impactElements,
            );
            if (!geometry) {
                return null;
            }
            return {
                card,
                origin,
                impacts,
                originElement,
                impactElements,
                geometry,
            };
        }

        routeGeometry(baseline, card, originElement, impactElements) {
            const rootRect = this.root.getBoundingClientRect();
            const baselineRect = baseline.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            if (rootRect.width <= 0 || rootRect.height <= 0 || cardRect.width <= 0) {
                return null;
            }
            const baselineY = baselineRect.top + baselineRect.height / 2 - rootRect.top;
            const cardX = cardRect.left + cardRect.width / 2 - rootRect.left;
            const cardBottom = cardRect.bottom - rootRect.top;
            const originX = this.targetCenterX(originElement, rootRect);
            const impactXs = impactElements.map((target) =>
                this.targetCenterX(target, rootRect),
            );
            const trackY = Math.max(cardBottom, baselineY - this.readTrackOffset());
            return {
                entry: `M ${cardX} ${cardBottom} L ${cardX} ${trackY}`,
                connector: `M ${cardX} ${trackY} L ${originX} ${trackY} L ${originX} ${baselineY}`,
                branches: impactXs.map((impactX) => {
                    if (Math.abs(impactX - originX) < 0.5) {
                        return null;
                    }
                    return `M ${originX} ${trackY} L ${impactX} ${trackY} L ${impactX} ${baselineY}`;
                }),
            };
        }

        createSvg(className) {
            const rect = this.root.getBoundingClientRect();
            const svg = document.createElementNS(SVG_NS, 'svg');
            svg.setAttribute('class', className);
            svg.setAttribute('viewBox', `0 0 ${rect.width} ${rect.height}`);
            svg.setAttribute('preserveAspectRatio', 'none');
            return svg;
        }

        createPath(data, color, className = 'ada-alarm-dashboard-route__path') {
            const path = document.createElementNS(SVG_NS, 'path');
            path.setAttribute('class', className);
            path.setAttribute('d', data);
            if (color) {
                path.setAttribute('stroke', color);
            }
            return path;
        }

        createImpactPath(target, color) {
            const rootRect = this.root.getBoundingClientRect();
            const rect = target.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) {
                return null;
            }
            const x = rect.left - rootRect.left;
            const y = rect.top - rootRect.top;
            const width = rect.width;
            const height = rect.height;
            const radiusValue = Number.parseFloat(
                getComputedStyle(target).borderTopLeftRadius,
            );
            const radius = Math.min(
                Number.isFinite(radiusValue) ? radiusValue : 0,
                width / 2,
                height / 2,
            );
            const centerX = x + width / 2;
            const right = x + width;
            const bottom = y + height;
            const path = document.createElementNS(SVG_NS, 'path');
            path.setAttribute('class', 'ada-alarm-dashboard-route__impact-path');
            path.setAttribute(
                'd',
                [
                    `M ${centerX} ${y}`,
                    `H ${x + radius}`,
                    `Q ${x} ${y} ${x} ${y + radius}`,
                    `V ${bottom - radius}`,
                    `Q ${x} ${bottom} ${x + radius} ${bottom}`,
                    `H ${right - radius}`,
                    `Q ${right} ${bottom} ${right} ${bottom - radius}`,
                    `V ${y + radius}`,
                    `Q ${right} ${y} ${right - radius} ${y}`,
                    `H ${centerX}`,
                ].join(' '),
            );
            path.setAttribute('stroke', color);
            return path;
        }

        async animateStroke(element, generation) {
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            let length;
            try {
                length = element.getTotalLength();
            } catch (_) {
                return;
            }
            if (!Number.isFinite(length) || length <= 0) {
                return;
            }
            const duration = Math.max(
                MIN_FLOW_DURATION_MS,
                (length / FLOW_SPEED_PX_PER_SECOND) * 1000,
            );
            element.style.strokeDasharray = String(length);
            element.style.strokeDashoffset = String(length);
            element.style.animation = 'none';
            await this.nextAnimationFrame(generation);
            if (!this.isAnimationCurrent(generation)) {
                return;
            }
            await new Promise((resolve) => {
                let settled = false;
                const finish = () => {
                    if (settled) {
                        return;
                    }
                    settled = true;
                    window.clearTimeout(fallback);
                    element.removeEventListener('animationend', finish);
                    resolve();
                };
                const fallback = window.setTimeout(finish, duration + 120);
                element.addEventListener('animationend', finish, { once: true });
                element.style.animation = `adaAlarmFlow ${duration.toFixed(0)}ms linear forwards`;
            });
            if (this.isAnimationCurrent(generation)) {
                element.style.strokeDashoffset = '0';
                element.style.animation = 'none';
            }
        }

        nextAnimationFrame(generation) {
            return new Promise((resolve) => {
                requestAnimationFrame(() => {
                    if (!this.isAnimationCurrent(generation)) {
                        resolve();
                        return;
                    }
                    requestAnimationFrame(resolve);
                });
            });
        }

        /*
         * El dwell no comienza al iniciar la animación. Se notifica al presenter
         * cuando toda la ruta y los impactos terminaron de pintarse.
         */
        notifyComplete(replay) {
            if (this.lastCompletedReplay === replay) {
                return;
            }
            this.lastCompletedReplay = replay;
            this.root.dispatchEvent(
                new CustomEvent(COMPLETE_EVENT, {
                    bubbles: true,
                    detail: {
                        eventId: this.root.dataset.adaAlarmRouteEventId || '',
                        assignmentKey:
                            this.root.dataset.adaAlarmRouteAssignmentKey || '',
                        replay,
                    },
                }),
            );
        }

        clearActiveVisualState() {
            this.animationGeneration += 1;
            this.root
                .querySelectorAll(
                    '.ada-alarm-dashboard-route__active-svg, .ada-alarm-dashboard-route__impact-svg',
                )
                .forEach((svg) => svg.remove());
            if (!this.scope) {
                return;
            }
            this.scope.querySelectorAll('[data-ada-alarm-impact="active"]').forEach((element) => {
                element.dataset.adaAlarmImpact = 'none';
                element.style.removeProperty('--ada-alarm-active-color');
            });
            this.scope.querySelectorAll('[data-ada-alarm-node-state]').forEach((node) => {
                node.dataset.adaAlarmNodeState = 'neutral';
                node.style.removeProperty('--ada-alarm-active-color');
                node.style.removeProperty('--ada-alarm-active-foreground');
            });
        }

        clearAllVisualState() {
            this.clearActiveVisualState();
            this.root.querySelectorAll('.ada-alarm-dashboard-route__context-svg').forEach((svg) =>
                svg.remove(),
            );
        }

        observeGeometry(elements) {
            if (!this.resizeObserver) {
                return;
            }
            elements.forEach((element) => this.observeResizeElement(element));
        }

        observeResizeElement(element) {
            if (!this.resizeObserver || this.geometrySizes.has(element)) {
                return;
            }
            this.geometrySizes.set(element, this.elementSize(element));
            this.resizeObserver.observe(element);
        }

        elementSize(element) {
            const rect = element.getBoundingClientRect();
            return { width: rect.width, height: rect.height };
        }

        findActiveCard() {
            const key = this.root.dataset.adaAlarmRouteCardKey;
            return Array.from(this.scope.querySelectorAll('[data-ada-alarm-card-key]')).find(
                (candidate) => candidate.dataset.adaAlarmCardKey === key,
            );
        }

        visibleCards() {
            return Array.from(this.scope.querySelectorAll(CARD_SELECTOR)).filter((card) =>
                this.isVisible(card),
            );
        }

        isVisible(card) {
            return !card.hidden && card.getClientRects().length > 0;
        }

        parseTargets(value) {
            return (value || '')
                .split('|')
                .filter(Boolean)
                .map((item) => this.parseTarget(item))
                .filter(Boolean);
        }

        parseTarget(value) {
            const [kind, key, ...rest] = (value || '').split(':');
            if (!kind || !key || rest.length > 0) {
                return null;
            }
            return { kind, key };
        }

        findTarget(target) {
            const attribute =
                target.kind === 'slot' ? 'data-ada-slot-key' : 'data-ada-component-key';
            return Array.from(this.scope.querySelectorAll(`[${attribute}]`)).find(
                (candidate) => candidate.getAttribute(attribute) === target.key,
            );
        }

        findNode(target) {
            return Array.from(
                this.scope.querySelectorAll('[data-ada-alarm-target-kind]'),
            ).find(
                (candidate) =>
                    candidate.dataset.adaAlarmTargetKind === target.kind &&
                    candidate.dataset.adaAlarmTargetKey === target.key,
            );
        }

        applyImpact(target, color) {
            target.dataset.adaAlarmImpact = 'active';
            target.style.setProperty('--ada-alarm-active-color', color);
        }

        applyNodeState(node, state, color, foreground) {
            node.dataset.adaAlarmNodeState = state;
            node.style.setProperty('--ada-alarm-active-color', color);
            node.style.setProperty('--ada-alarm-active-foreground', foreground);
        }

        sameTarget(left, right) {
            return left.kind === right.kind && left.key === right.key;
        }

        targetCenterX(target, rootRect) {
            const rect = target.getBoundingClientRect();
            return rect.left + rect.width / 2 - rootRect.left;
        }

        readTrackOffset() {
            const measure = this.root.querySelector('.ada-alarm-dashboard-route__measure');
            return measure ? measure.getBoundingClientRect().width || 20 : 20;
        }

        readCssValue(name) {
            return getComputedStyle(this.root).getPropertyValue(name).trim();
        }

        isAnimationCurrent(generation) {
            return generation === this.animationGeneration && this.root.isConnected;
        }
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = new AlarmDashboardRouteController(root);
        controllers.add(controller);
        controller.start();
    }

    function scan(root = document) {
        if (root.matches && root.matches(ROUTE_SELECTOR)) {
            mount(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll(ROUTE_SELECTOR).forEach(mount);
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
