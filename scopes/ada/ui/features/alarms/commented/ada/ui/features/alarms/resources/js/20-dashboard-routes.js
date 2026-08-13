/* Dibuja una sola ruta activa por scope usando geometría del DOM; no consulta backend. */
(() => {
    'use strict';

    const ROUTE_SELECTOR = '[data-ada-alarm-route]';
    const SCOPE_SELECTOR = '[data-ada-alarm-geometry-scope="true"]';
    const BASELINE_SELECTOR = '[data-ada-alarm-baseline]';
    const controllers = new Set();
    const SVG_NS = 'http://www.w3.org/2000/svg';

    class AlarmDashboardRouteGeometry {
        constructor(root) {
            this.root = root;
            this.scope = root.closest(SCOPE_SELECTOR);
            this.frame = null;
            this.resizeObserver = null;
            this.mutationObserver = null;
            this.onWindowResize = () => this.schedule();
        }

        start() {
            if (!this.scope) {
                return;
            }
            if (typeof ResizeObserver === 'function') {
                this.resizeObserver = new ResizeObserver(() => this.schedule());
                this.resizeObserver.observe(this.scope);
                this.resizeObserver.observe(this.root);
            } else {
                window.addEventListener('resize', this.onWindowResize);
            }
            this.mutationObserver = new MutationObserver((records) => {
                const relevant = records.some((record) => this.isRelevantMutation(record));
                if (relevant) {
                    this.schedule();
                }
            });
            this.mutationObserver.observe(this.scope, {
                attributes: true,
                childList: true,
                subtree: true,
                attributeFilter: [
                    'data-ada-alarm-route-card-key',
                    'data-ada-alarm-route-origin',
                    'data-ada-alarm-route-impacts',
                    'data-ada-alarm-route-tone',
                    'data-ada-slot-key',
                    'data-ada-component-key',
                ],
            });
            this.schedule();
        }

        disconnect() {
            if (this.frame !== null) {
                cancelAnimationFrame(this.frame);
                this.frame = null;
            }
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            }
            if (this.mutationObserver) {
                this.mutationObserver.disconnect();
            }
            window.removeEventListener('resize', this.onWindowResize);
            this.resetVisualState();
        }

        isRelevantMutation(record) {
            if (record.type === 'attributes') {
                return true;
            }
            return [...record.addedNodes, ...record.removedNodes].some(
                (node) =>
                    node.nodeType === Node.ELEMENT_NODE &&
                    !(node.matches && node.matches('.ada-alarm-dashboard-route__svg')),
            );
        }

        schedule() {
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
            this.resetVisualState();
            const baseline = this.scope.querySelector(BASELINE_SELECTOR);
            const card = this.findCard();
            const origin = this.parseTarget(this.root.dataset.adaAlarmRouteOrigin);
            const impacts = this.parseTargets(this.root.dataset.adaAlarmRouteImpacts);
            if (!baseline || !card || !origin || impacts.length === 0) {
                return;
            }
            const originElement = this.findTarget(origin);
            const impactElements = impacts.map((target) => this.findTarget(target));
            if (!originElement || impactElements.some((target) => !target)) {
                return;
            }
            this.observeGeometry([baseline, card, originElement, ...impactElements]);
            const color = this.readCssValue('--ada-alarm-route-color');
            const foreground = this.readCssValue('--ada-alarm-route-foreground');
            if (!color || !foreground) {
                return;
            }
            this.applyActiveCard(card, color, foreground);
            this.applyNodeStates(origin, impacts, color, foreground);
            impacts.forEach((target, index) => {
                this.applyImpact(impactElements[index], color);
            });
            this.drawRoute(baseline, card, originElement, impactElements, color);
        }

        resetVisualState() {
            this.root.querySelectorAll('svg').forEach((svg) => svg.remove());
            if (!this.scope) {
                return;
            }
            this.scope.querySelectorAll('[data-ada-alarm-active="true"]').forEach((element) => {
                element.dataset.adaAlarmActive = 'false';
                element.style.removeProperty('--ada-alarm-active-color');
                element.style.removeProperty('--ada-alarm-active-foreground');
            });
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

        observeGeometry(elements) {
            if (!this.resizeObserver) {
                return;
            }
            elements.forEach((element) => this.resizeObserver.observe(element));
        }

        findCard() {
            const key = this.root.dataset.adaAlarmRouteCardKey;
            return Array.from(this.scope.querySelectorAll('[data-ada-alarm-card-key]')).find(
                (candidate) => candidate.dataset.adaAlarmCardKey === key,
            );
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
            const attribute = target.kind === 'slot' ? 'data-ada-slot-key' : 'data-ada-component-key';
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

        applyActiveCard(card, color, foreground) {
            card.dataset.adaAlarmActive = 'true';
            card.style.setProperty('--ada-alarm-active-color', color);
            card.style.setProperty('--ada-alarm-active-foreground', foreground);
        }

        applyImpact(target, color) {
            target.dataset.adaAlarmImpact = 'active';
            target.style.setProperty('--ada-alarm-active-color', color);
        }

        applyNodeStates(origin, impacts, color, foreground) {
            const originNode = this.findNode(origin);
            if (originNode) {
                const isImpact = impacts.some((target) => this.sameTarget(target, origin));
                this.applyNodeState(originNode, isImpact ? 'origin-impact' : 'origin', color, foreground);
            }
            impacts.forEach((target) => {
                if (this.sameTarget(target, origin)) {
                    return;
                }
                const node = this.findNode(target);
                if (node) {
                    this.applyNodeState(node, 'impact', color, foreground);
                }
            });
        }

        applyNodeState(node, state, color, foreground) {
            node.dataset.adaAlarmNodeState = state;
            node.style.setProperty('--ada-alarm-active-color', color);
            node.style.setProperty('--ada-alarm-active-foreground', foreground);
        }

        sameTarget(left, right) {
            return left.kind === right.kind && left.key === right.key;
        }

        drawRoute(baseline, card, originElement, impactElements, color) {
            const rootRect = this.root.getBoundingClientRect();
            const baselineRect = baseline.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            if (rootRect.width <= 0 || rootRect.height <= 0) {
                return;
            }
            const baselineY = baselineRect.top + baselineRect.height / 2 - rootRect.top;
            const cardX = cardRect.left + cardRect.width / 2 - rootRect.left;
            const cardBottom = cardRect.bottom - rootRect.top;
            const originX = this.targetCenterX(originElement, rootRect);
            const impactXs = impactElements.map((target) => this.targetCenterX(target, rootRect));
            const trackOffset = this.readTrackOffset();
            const trackY = Math.max(cardBottom, baselineY - trackOffset);
            const commands = [
                `M ${cardX} ${cardBottom}`,
                `L ${cardX} ${trackY}`,
                `L ${originX} ${trackY}`,
                `L ${originX} ${baselineY}`,
            ];
            impactXs.forEach((impactX) => {
                if (Math.abs(impactX - originX) < 0.5) {
                    return;
                }
                commands.push(
                    `M ${originX} ${trackY}`,
                    `L ${impactX} ${trackY}`,
                    `L ${impactX} ${baselineY}`,
                );
            });
            const svg = document.createElementNS(SVG_NS, 'svg');
            svg.setAttribute('class', 'ada-alarm-dashboard-route__svg');
            svg.setAttribute('viewBox', `0 0 ${rootRect.width} ${rootRect.height}`);
            svg.setAttribute('preserveAspectRatio', 'none');
            const path = document.createElementNS(SVG_NS, 'path');
            path.setAttribute('class', 'ada-alarm-dashboard-route__path');
            path.setAttribute('d', commands.join(' '));
            path.setAttribute('stroke', color);
            svg.appendChild(path);
            this.root.appendChild(svg);
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
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = new AlarmDashboardRouteGeometry(root);
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
