(() => {
    'use strict';

    const ROUTE_SELECTOR = '[data-ada-alarm-route]';
    const SCOPE_SELECTOR = '[data-ada-alarm-geometry-scope="true"]';
    const PRESENTATION_SCOPE_SELECTOR = '[data-ada-alarm-presentation-scope="true"]';
    const BASELINE_SELECTOR = '[data-ada-alarm-baseline]';
    const CARD_SELECTOR = '[data-ada-alarm-event-id]';
    const INTERACTIVE_SELECTOR = 'button, a, input, select, textarea, [role="button"], [data-ada-alarm-card-control]';
    const PLAYER_REFRESH_EVENT = 'ada:alarm-player-refresh';
    // Evento genérico para cambios de geometría externos sin reiniciar la iteración del player.
    const GEOMETRY_REFRESH_EVENT = 'ada:alarm-geometry-refresh';
    const MOTION_SCOPE_WIDTHS_PER_SECOND = 0.2;
    const MIN_MOTION_SPEED_PX_PER_SECOND = 160;
    const MAX_MOTION_SPEED_PX_PER_SECOND = 960;
    const MOTION_SAMPLE_STEP_PX = 2;
    const IMPACT_MIN_DURATION_MS = 1_600;
    const IMPACT_MAX_DURATION_MS = 2_400;
    const DEFAULT_DWELL_MS = 15_000;
    const DEBUG_QUERY_PARAMETER = 'alarmTraceDebug';
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const controllers = new Set();

    class AlarmRoutePlayer {
        constructor(root) {
            this.root = root;
            this.scope = root.closest(SCOPE_SELECTOR);
            this.catalog = new Map();
            this.contextSvg = null;
            this.activeSvg = null;
            this.impactSvg = null;
            this.generation = 0;
            this.autoIndex = 0;
            this.pinnedEventId = null;
            this.timerIds = new Set();
            this.motionFrame = null;
            this.motion = null;
            this.resizeObserver = null;
            this.geometrySizes = new Map();
            this.resizeFrame = null;
            this.geometryDirty = false;
            this.geometryDirtyReason = '';
            this.geometrySyncTimer = null;
            this.pendingPresentationReconcile = false;
            this.started = false;
            this.debugEnabled =
                new URLSearchParams(window.location.search).get(DEBUG_QUERY_PARAMETER) === '1';
            this.debugStartedAt = performance.now();
            this.onClick = (event) => this.handleClick(event);
            this.onRefresh = () => this.handleRefresh();
            // Sólo marca geometría dirty; no reinicia selección, rotación ni dwell.
            this.onGeometryRefresh = () => this.markGeometryDirty('external');
        }

        start() {
            if (!this.scope || this.started) {
                return;
            }
            this.started = true;
            this.scope.addEventListener('click', this.onClick);
            this.scope.addEventListener(PLAYER_REFRESH_EVENT, this.onRefresh);
            this.scope.addEventListener(GEOMETRY_REFRESH_EVENT, this.onGeometryRefresh);
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
                        this.debug('resize.changed', {
                            entries: entries.map((entry) => this.describeElement(entry.target)),
                        });
                        this.markGeometryDirty('resize');
                    }
                });
            }
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    if (!this.root.isConnected) {
                        return;
                    }
                    this.debug('start.ready');
                    this.rebuildCatalog();
                    if (this.isPresentationScope()) {
                        this.startAuto();
                    } else {
                        this.renderSeededStaticRoute();
                    }
                });
            });
        }

        disconnect() {
            this.debug('disconnect');
            this.generation += 1;
            if (this.resizeFrame !== null) {
                cancelAnimationFrame(this.resizeFrame);
                this.resizeFrame = null;
            }
            if (this.geometrySyncTimer !== null) {
                window.clearTimeout(this.geometrySyncTimer);
                this.geometrySyncTimer = null;
            }
            this.clearTimers();
            this.cancelMotion('disconnect');
            this.scope?.removeEventListener('click', this.onClick);
            this.scope?.removeEventListener(PLAYER_REFRESH_EVENT, this.onRefresh);
            this.scope?.removeEventListener(GEOMETRY_REFRESH_EVENT, this.onGeometryRefresh);
            this.resizeObserver?.disconnect();
            this.geometrySizes.clear();
            this.clearActiveVisualState('disconnect');
            this.contextSvg?.remove();
            this.contextSvg = null;
        }

        isPresentationScope() {
            return Boolean(this.root.closest(PRESENTATION_SCOPE_SELECTOR));
        }

        presentationScope() {
            return this.root.closest(PRESENTATION_SCOPE_SELECTOR);
        }

        dwellMs() {
            const value = Number.parseInt(
                this.presentationScope()?.dataset.adaAlarmTraceDwellMs || '',
                10,
            );
            return Number.isFinite(value) && value > 0 ? value : DEFAULT_DWELL_MS;
        }

        interactionEnabled() {
            return this.presentationScope()?.dataset.adaAlarmInteraction === 'interactive';
        }

        handleRefresh() {
            if (this.isPresentationScope()) {
                this.reconcilePresentation('explicit');
                return;
            }
            this.markGeometryDirty('explicit');
        }

        markGeometryDirty(reason) {
            this.geometryDirty = true;
            this.geometryDirtyReason = reason;
            this.debug('geometry.dirty', {
                reason,
                presentation: this.isPresentationScope(),
            });
            if (!this.isPresentationScope()) {
                this.scheduleRefresh();
                return;
            }
            this.schedulePresentationGeometrySync();
        }

        scheduleRefresh() {
            this.debug('refresh.scheduled', { mode: 'static' });
            if (this.resizeFrame !== null) {
                return;
            }
            this.resizeFrame = requestAnimationFrame(() => {
                this.resizeFrame = null;
                this.refreshStaticGeometry();
            });
        }

        refreshStaticGeometry() {
            if (!this.root.isConnected || this.isPresentationScope()) {
                return;
            }
            this.debug('refresh.begin', { mode: 'static' });
            this.generation += 1;
            this.clearTimers();
            this.clearActiveVisualState('refresh.static');
            this.rebuildCatalog();
            this.renderSeededStaticRoute();
        }

        ensureFreshCatalog(boundary) {
            if (!this.geometryDirty) {
                return;
            }
            this.debug('geometry.rebuild.safe', {
                boundary,
                reason: this.geometryDirtyReason,
            });
            this.rebuildCatalog();
        }

        schedulePresentationGeometrySync() {
            if (!this.isPresentationScope() || !this.geometryDirty) {
                return;
            }
            if (this.motion) {
                this.debug('geometry.sync.deferred', {
                    stage: this.motion.step?.stage || '',
                });
                return;
            }
            if (this.geometrySyncTimer !== null) {
                window.clearTimeout(this.geometrySyncTimer);
            }
            this.debug('geometry.sync.scheduled');
            this.geometrySyncTimer = window.setTimeout(() => {
                this.geometrySyncTimer = null;
                if (!this.geometryDirty || !this.root.isConnected || this.motion) {
                    return;
                }
                const eventId = this.pinnedEventId || this.currentEventId();
                if (!eventId) {
                    return;
                }
                this.syncPresentationGeometry(eventId);
            }, 0);
        }

        syncPresentationGeometry(eventId) {
            const card = this.cardByEventId(eventId);
            if (!card) {
                return;
            }
            const snapshot = this.buildCatalogSnapshot();
            const specification = snapshot.catalog.get(eventId);
            if (!specification) {
                return;
            }
            const tone = card.dataset.adaAlarmCardTone;
            const color = this.toneColor(tone);
            const foreground = this.toneForeground(tone);
            if (!color || !foreground) {
                return;
            }
            this.debug('geometry.sync.static', { eventId });
            const nextActiveSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__active-svg',
            );
            const nextImpactSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__impact-svg',
            );
            this.appendStaticRouteVisuals(
                nextActiveSvg,
                nextImpactSvg,
                specification,
                color,
                eventId,
            );
            this.replaceContextCatalog(snapshot);
            if (this.activeSvg?.isConnected) {
                this.activeSvg.replaceWith(nextActiveSvg);
            } else {
                this.root.appendChild(nextActiveSvg);
            }
            if (this.impactSvg?.isConnected) {
                this.impactSvg.replaceWith(nextImpactSvg);
            } else {
                this.root.appendChild(nextImpactSvg);
            }
            this.activeSvg = nextActiveSvg;
            this.impactSvg = nextImpactSvg;
            this.applyStaticNodeStates(specification, color, foreground);
        }

        reconcilePresentation(reason) {
            if (!this.root.isConnected || !this.isPresentationScope()) {
                return;
            }
            const activeEventId = this.pinnedEventId || this.currentEventId();
            const previousSpecification = this.catalog.get(activeEventId);
            const previousIndex = this.autoIndex;
            const snapshot = this.buildCatalogSnapshot();
            const nextSpecification = snapshot.catalog.get(activeEventId);
            const placementChanged = Boolean(
                previousSpecification &&
                    nextSpecification &&
                    previousSpecification.placementKey !== nextSpecification.placementKey,
            );
            const signatureChanged = Boolean(
                previousSpecification &&
                    nextSpecification &&
                    previousSpecification.signature !== nextSpecification.signature,
            );
            this.replaceContextCatalog(snapshot);
            this.debug('presentation.reconcile', {
                reason,
                activeEventId,
                placementChanged,
                signatureChanged,
                catalogSize: this.catalog.size,
            });
            if (this.catalog.size === 0) {
                this.generation += 1;
                this.clearTimers();
                this.pinnedEventId = null;
                this.clearSelections();
                this.clearActiveVisualState('presentation.empty');
                this.clearRouteIdentity();
                return;
            }
            if (
                previousSpecification &&
                nextSpecification &&
                !placementChanged &&
                !signatureChanged &&
                this.motion
            ) {
                this.pendingPresentationReconcile = true;
                return;
            }
            if (
                previousSpecification &&
                nextSpecification &&
                !placementChanged &&
                !signatureChanged
            ) {
                const card = this.cardByEventId(activeEventId);
                if (!card) {
                    return;
                }
                const generation = ++this.generation;
                this.clearTimers();
                this.clearActiveVisualState('presentation.refresh');
                this.playCard(card, generation, false);
                if (!this.pinnedEventId) {
                    const index = this.visibleCards().findIndex(
                        (candidate) => candidate.dataset.adaAlarmEventId === activeEventId,
                    );
                    this.autoIndex = index >= 0 ? index : 0;
                    this.scheduleAutoAdvance(this.autoIndex, generation, activeEventId);
                }
                return;
            }
            this.pendingPresentationReconcile = false;
            this.pinnedEventId = null;
            this.clearSelections();
            const cards = this.visibleCards();
            const activeIndex = cards.findIndex(
                (card) => card.dataset.adaAlarmEventId === activeEventId,
            );
            const replayIndex =
                activeIndex >= 0 ? activeIndex : Math.min(previousIndex, cards.length - 1);
            this.restartAutoAt(replayIndex, 'presentation.replay');
        }

        buildCatalogSnapshot() {
            const catalog = new Map();
            const contextSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__context-svg',
            );
            const baseline = this.scope.querySelector(BASELINE_SELECTOR);
            if (!baseline) {
                return { catalog, contextSvg };
            }
            this.visibleCards().forEach((card) => {
                const specification = this.cardSpecification(card, baseline);
                if (!specification) {
                    return;
                }
                catalog.set(card.dataset.adaAlarmEventId, specification);
                specification.geometry.contextSegments.forEach((segment) => {
                    contextSvg.appendChild(
                        this.createPath(
                            segment,
                            null,
                            'ada-alarm-dashboard-route__context-path',
                        ),
                    );
                });
            });
            return { catalog, contextSvg };
        }

        replaceContextCatalog(snapshot) {
            if (this.contextSvg?.isConnected) {
                this.contextSvg.replaceWith(snapshot.contextSvg);
            } else {
                this.root.prepend(snapshot.contextSvg);
            }
            this.contextSvg = snapshot.contextSvg;
            this.catalog = snapshot.catalog;
            this.observeGeometry([this.scope, this.root]);
            this.geometryDirty = false;
            this.geometryDirtyReason = '';
        }

        rebuildCatalog() {
            this.debug('catalog.rebuild.begin');
            const snapshot = this.buildCatalogSnapshot();
            this.contextSvg?.remove();
            this.contextSvg = snapshot.contextSvg;
            this.catalog = snapshot.catalog;
            this.root.prepend(this.contextSvg);
            this.resetNodes();
            this.observeGeometry([this.scope, this.root]);
            this.geometryDirty = false;
            this.geometryDirtyReason = '';
            this.debug('catalog.rebuild.end', {
                visibleCards: this.visibleCards().length,
                catalogSize: this.catalog.size,
            });
        }

        startAuto() {
            if (!this.isPresentationScope() || this.pinnedEventId) {
                return;
            }
            this.ensureFreshCatalog('auto.start');
            this.generation += 1;
            this.clearTimers();
            const cards = this.visibleCards();
            this.debug('auto.start', {
                generation: this.generation,
                cards: cards.map((card) => card.dataset.adaAlarmEventId),
            });
            if (cards.length === 0) {
                return;
            }
            if (cards.length === 1) {
                this.autoIndex = 0;
                this.playCard(cards[0], this.generation, true);
                return;
            }
            this.presentAutoIndex(this.autoIndex % cards.length, this.generation);
        }

        presentAutoIndex(index, generation) {
            if (!this.isGenerationCurrent(generation) || this.pinnedEventId) {
                return;
            }
            this.ensureFreshCatalog('auto.present');
            const cards = this.visibleCards();
            if (cards.length === 0) {
                return;
            }
            const normalizedIndex = index % cards.length;
            this.autoIndex = normalizedIndex;
            const card = cards[normalizedIndex];
            const eventId = card.dataset.adaAlarmEventId;
            this.debug('auto.present', {
                generation,
                index: normalizedIndex,
                eventId,
            });
            this.playCard(card, generation, true, () => {
                this.scheduleAutoAdvance(normalizedIndex, generation, eventId);
            });
        }

        scheduleAutoAdvance(index, generation, eventId) {
            if (!this.isGenerationCurrent(generation) || this.pinnedEventId) {
                return;
            }
            const cards = this.visibleCards();
            if (cards.length <= 1) {
                return;
            }
            const dwellMs = this.dwellMs();
            this.debug('auto.dwell', { generation, eventId, dwellMs });
            this.scheduleTimer(() => {
                if (!this.isGenerationCurrent(generation) || this.pinnedEventId) {
                    return;
                }
                const nextCards = this.visibleCards();
                if (nextCards.length <= 1) {
                    return;
                }
                const currentIndex = nextCards.findIndex(
                    (candidate) => candidate.dataset.adaAlarmEventId === eventId,
                );
                const nextIndex =
                    currentIndex >= 0
                        ? (currentIndex + 1) % nextCards.length
                        : index % nextCards.length;
                this.debug('auto.next', {
                    generation,
                    fromEventId: eventId,
                    nextIndex,
                });
                this.clearActiveVisualState('auto.next');
                this.presentAutoIndex(nextIndex, generation);
            }, dwellMs, generation, 'auto.next');
        }

        restartAutoAt(index, reason) {
            const cards = this.visibleCards();
            if (cards.length === 0) {
                return;
            }
            const normalizedIndex = Math.max(0, index) % cards.length;
            const generation = ++this.generation;
            this.autoIndex = normalizedIndex;
            this.clearTimers();
            this.clearActiveVisualState(reason);
            if (cards.length === 1) {
                this.playCard(cards[0], generation, true);
                return;
            }
            this.presentAutoIndex(normalizedIndex, generation);
        }

        playPinned(card) {
            this.ensureFreshCatalog('pinned.play');
            const generation = ++this.generation;
            this.debug('pinned.play', {
                generation,
                eventId: card.dataset.adaAlarmEventId,
            });
            this.clearTimers();
            this.playCard(card, generation, true);
        }

        playCard(card, generation, animate, onComplete = null) {
            if (!this.isGenerationCurrent(generation)) {
                return;
            }
            const eventId = card.dataset.adaAlarmEventId;
            const specification = this.catalog.get(eventId);
            if (!specification) {
                return;
            }
            this.clearActiveVisualState('play.begin');
            const tone = card.dataset.adaAlarmCardTone;
            const color = this.toneColor(tone);
            const foreground = this.toneForeground(tone);
            if (!color || !foreground) {
                return;
            }
            this.root.dataset.adaAlarmRouteEventId = eventId;
            this.root.dataset.adaAlarmRouteCardKey = card.dataset.adaAlarmCardKey || '';
            this.root.dataset.adaAlarmRoutePlacementKey = specification.placementKey;
            this.root.dataset.adaAlarmRouteTone = tone || '';
            this.activeSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__active-svg',
            );
            this.impactSvg = this.createSvg(
                'ada-alarm-dashboard-route__svg ada-alarm-dashboard-route__impact-svg',
            );
            this.root.append(this.activeSvg, this.impactSvg);

            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const shouldAnimate = animate && !reducedMotion;
            this.debug('play.begin', {
                generation,
                eventId,
                tone,
                shouldAnimate,
                destinations: specification.destinations.map(
                    (target) => `${target.kind}:${target.key}`,
                ),
                affectedTargets: specification.affectedTargets.map(
                    (target) => `${target.kind}:${target.key}`,
                ),
            });

            if (!shouldAnimate) {
                this.appendStaticRouteVisuals(
                    this.activeSvg,
                    this.impactSvg,
                    specification,
                    color,
                    eventId,
                );
                this.applyStaticNodeStates(specification, color, foreground);
                this.debug('play.timeline', {
                    generation,
                    eventId,
                    mode: 'static',
                });
                onComplete?.();
                return;
            }

            this.startMotion(
                specification,
                color,
                foreground,
                eventId,
                generation,
                onComplete,
            );
        }

        appendStaticRouteVisuals(activeSvg, impactSvg, specification, color, eventId) {
            specification.geometry.contextSegments.forEach((segment, index) => {
                const routePath = this.createPath(segment, color);
                activeSvg.appendChild(routePath);
                this.commitStroke(routePath);
                this.debug('stroke.static', {
                    stage: `route-static:${index}`,
                    eventId,
                });
            });
            specification.affectedElements.forEach((target, index) => {
                const affectedPaths = this.createImpactPaths(target, color);
                affectedPaths.forEach((impactPath, pathIndex) => {
                    impactSvg.appendChild(impactPath);
                    this.commitStroke(impactPath);
                    const side = pathIndex === 0 ? 'left' : 'right';
                    const affected = specification.affectedTargets[index];
                    this.debug('stroke.static', {
                        stage: `affected-${side}:${affected.kind}:${affected.key}`,
                        eventId,
                    });
                });
            });
        }

        applyStaticNodeStates(specification, color, foreground) {
            this.resetNodes();
            const originIsDestination = specification.destinations.some((target) =>
                this.sameTarget(target, specification.origin),
            );
            const originNode = this.findNode(specification.origin);
            if (originNode) {
                this.applyNodeState(
                    originNode,
                    originIsDestination ? 'origin-impact' : 'origin',
                    color,
                    foreground,
                );
            }
            specification.destinations.forEach((target) => {
                if (this.sameTarget(target, specification.origin)) {
                    return;
                }
                const node = this.findNode(target);
                if (node) {
                    this.applyNodeState(node, 'impact', color, foreground);
                }
            });
        }

        renderSeededStaticRoute() {
            const eventId = this.root.dataset.adaAlarmRouteEventId;
            if (!eventId) {
                return;
            }
            const card = this.cardByEventId(eventId);
            if (!card) {
                return;
            }
            const generation = ++this.generation;
            this.clearTimers();
            this.playCard(card, generation, false);
        }

        motionSpeed() {
            const width = this.scope?.getBoundingClientRect().width || 0;
            const normalized = width * MOTION_SCOPE_WIDTHS_PER_SECOND;
            return Math.min(
                MAX_MOTION_SPEED_PX_PER_SECOND,
                Math.max(MIN_MOTION_SPEED_PX_PER_SECOND, normalized),
            );
        }

        startMotion(specification, color, foreground, eventId, generation, onComplete) {
            this.cancelMotion('start');
            this.motion = {
                specification,
                color,
                foreground,
                eventId,
                generation,
                onComplete,
                speed: this.motionSpeed(),
                steps: this.createMotionSteps(specification),
                stepIndex: -1,
                step: null,
                lastTimestamp: null,
                stepElapsedMs: 0,
                stepDurationMs: 0,
                strokes: [],
            };
            this.debug('motion.start', {
                eventId,
                generation,
                speed: this.motion.speed,
            });
            this.beginNextMotionStep();
            this.motionFrame = requestAnimationFrame((timestamp) => this.tickMotion(timestamp));
        }

        createMotionSteps(specification) {
            const steps = [
                {
                    stage: 'shared-trunk',
                    type: 'route',
                    segments: [
                        {
                            data: specification.geometry.sharedTrunk,
                            stage: 'shared-trunk',
                        },
                    ],
                },
                {
                    stage: 'origin-leg',
                    type: 'route',
                    segments: [
                        {
                            data: specification.geometry.originLeg,
                            stage: 'origin-leg',
                        },
                    ],
                    nodeTarget: specification.origin,
                    nodeState: specification.destinations.some((target) =>
                        this.sameTarget(target, specification.origin),
                    )
                        ? 'origin-impact'
                        : 'origin',
                },
            ];
            specification.geometry.destinationSegments.forEach(({ index, data }) => {
                const target = specification.destinations[index];
                steps.push({
                    stage: `destination-leg:${target.kind}:${target.key}`,
                    type: 'route',
                    segments: [
                        {
                            data,
                            stage: `destination-leg:${target.kind}:${target.key}`,
                        },
                    ],
                    nodeTarget: target,
                    nodeState: 'impact',
                });
            });
            specification.affectedTargets.forEach((target, index) => {
                steps.push({
                    stage: `affected:${target.kind}:${target.key}`,
                    type: 'affected',
                    target,
                    targetElement: specification.affectedElements[index],
                });
            });
            return steps;
        }

        beginNextMotionStep() {
            if (!this.motion || !this.isGenerationCurrent(this.motion.generation)) {
                return;
            }
            this.motion.stepIndex += 1;
            if (this.motion.stepIndex >= this.motion.steps.length) {
                this.finishMotion();
                return;
            }
            const step = this.motion.steps[this.motion.stepIndex];
            this.motion.step = step;
            this.motion.stepElapsedMs = 0;
            if (step.type === 'route') {
                this.motion.strokes = this.createRouteMotionStrokes(step.segments);
            } else {
                this.motion.strokes = this.createAffectedMotionStrokes(step);
            }
            this.motion.stepDurationMs = this.motionStepDuration(
                this.motion.strokes,
                step.type,
            );
            this.debug('motion.step.start', {
                stage: step.stage,
                eventId: this.motion.eventId,
                speed: this.motion.speed,
                stepDurationMs: this.motion.stepDurationMs,
                strokes: this.motion.strokes.map(({ stage, length }) => ({ stage, length })),
            });
        }

        createRouteMotionStrokes(segments) {
            if (!this.activeSvg?.isConnected || !this.motion) {
                return [];
            }
            return segments
                .map(({ data, stage }) => {
                    if (!data) {
                        return null;
                    }
                    const path = this.createPath(data, this.motion.color);
                    return this.prepareMotionStroke(path, stage, this.activeSvg);
                })
                .filter(Boolean);
        }

        createAffectedMotionStrokes(step) {
            if (!this.impactSvg?.isConnected || !this.motion) {
                return [];
            }
            return this.createImpactPaths(step.targetElement, this.motion.color)
                .map((path, pathIndex) => {
                    const side = pathIndex === 0 ? 'left' : 'right';
                    const stage = `affected-${side}:${step.target.kind}:${step.target.key}`;
                    return this.prepareMotionStroke(path, stage, this.impactSvg);
                })
                .filter(Boolean);
        }

        prepareMotionStroke(path, stage, container) {
            if (!this.motion || !container?.isConnected) {
                path.remove();
                return null;
            }
            path.style.visibility = 'hidden';
            path.style.opacity = '0';
            path.style.strokeLinecap = 'butt';
            container.appendChild(path);
            const fullData = path.getAttribute('d') || '';
            let length = 0;
            try {
                length = path.getTotalLength();
            } catch (error) {
                path.remove();
                this.debug('stroke.length.error', {
                    stage,
                    eventId: this.motion.eventId,
                    error: String(error),
                });
                return null;
            }
            if (!Number.isFinite(length) || length <= 0) {
                path.remove();
                this.debug('stroke.length.invalid', {
                    stage,
                    eventId: this.motion.eventId,
                    length,
                });
                return null;
            }
            let samples = [];
            try {
                samples = this.createMotionSamples(path, length);
            } catch (error) {
                path.remove();
                this.debug('stroke.samples.error', {
                    stage,
                    eventId: this.motion.eventId,
                    error: String(error),
                });
                return null;
            }
            if (samples.length < 2) {
                path.remove();
                return null;
            }
            const stroke = {
                path,
                stage,
                length,
                fullData,
                samples,
                committed: false,
            };
            path.setAttribute('d', this.motionPrefixData(stroke, 0));
            path.style.visibility = 'visible';
            path.style.opacity = '1';
            return stroke;
        }

        createMotionSamples(path, length) {
            const segmentCount = Math.max(1, Math.ceil(length / MOTION_SAMPLE_STEP_PX));
            const samples = [];
            for (let index = 0; index <= segmentCount; index += 1) {
                const distance = (length * index) / segmentCount;
                const point = path.getPointAtLength(distance);
                samples.push({ distance, x: point.x, y: point.y });
            }
            return samples;
        }

        motionPrefixData(stroke, visibleLength) {
            const clamped = Math.min(stroke.length, Math.max(0, visibleLength));
            const lastIndex = stroke.samples.length - 1;
            const scaledIndex = stroke.length > 0 ? (clamped / stroke.length) * lastIndex : 0;
            const completedIndex = Math.min(lastIndex, Math.floor(scaledIndex));
            const commands = [this.motionPointCommand('M', stroke.samples[0])];
            for (let index = 1; index <= completedIndex; index += 1) {
                commands.push(this.motionPointCommand('L', stroke.samples[index]));
            }
            if (completedIndex < lastIndex) {
                const ratio = scaledIndex - completedIndex;
                if (ratio > 0) {
                    const start = stroke.samples[completedIndex];
                    const end = stroke.samples[completedIndex + 1];
                    commands.push(
                        this.motionPointCommand('L', {
                            x: start.x + (end.x - start.x) * ratio,
                            y: start.y + (end.y - start.y) * ratio,
                        }),
                    );
                }
            }
            return commands.join(' ');
        }

        motionPointCommand(command, point) {
            return `${command} ${this.motionCoordinate(point.x)} ${this.motionCoordinate(point.y)}`;
        }

        motionCoordinate(value) {
            return Number(value.toFixed(3));
        }

        motionStepDuration(strokes, type) {
            if (!this.motion || strokes.length === 0) {
                return 0;
            }
            const longest = Math.max(...strokes.map((stroke) => stroke.length));
            const naturalDuration = (longest / this.motion.speed) * 1000;
            if (type === 'route') {
                return naturalDuration;
            }
            return Math.min(
                IMPACT_MAX_DURATION_MS,
                Math.max(IMPACT_MIN_DURATION_MS, naturalDuration),
            );
        }

        easeAffectedProgress(progress) {
            const clamped = Math.min(1, Math.max(0, progress));
            return 0.5 - Math.cos(Math.PI * clamped) / 2;
        }

        revealMotionStroke(stroke, visibleLength) {
            if (stroke.committed || !stroke.path.isConnected) {
                return;
            }
            stroke.path.setAttribute('d', this.motionPrefixData(stroke, visibleLength));
        }

        completeMotionStep(step) {
            if (!this.motion || !step?.nodeTarget || !step.nodeState) {
                return;
            }
            const node = this.findNode(step.nodeTarget);
            if (node) {
                this.applyNodeState(
                    node,
                    step.nodeState,
                    this.motion.color,
                    this.motion.foreground,
                );
            }
        }

        tickMotion(timestamp) {
            this.motionFrame = null;
            if (!this.motion || !this.isGenerationCurrent(this.motion.generation)) {
                return;
            }
            if (!this.motion.step) {
                return;
            }
            if (this.motion.lastTimestamp === null) {
                this.motion.lastTimestamp = timestamp;
            }
            let remainingMs = Math.max(0, timestamp - this.motion.lastTimestamp);
            this.motion.lastTimestamp = timestamp;
            let completedSteps = 0;
            while (this.motion?.step && completedSteps <= this.motion.steps.length) {
                const motion = this.motion;
                const durationMs = Math.max(0, motion.stepDurationMs);
                const availableMs = Math.max(0, durationMs - motion.stepElapsedMs);
                const consumedMs = Math.min(remainingMs, availableMs);
                motion.stepElapsedMs += consumedMs;
                remainingMs -= consumedMs;
                const rawProgress =
                    durationMs > 0 ? Math.min(1, motion.stepElapsedMs / durationMs) : 1;
                const progress =
                    motion.step.type === 'affected'
                        ? this.easeAffectedProgress(rawProgress)
                        : rawProgress;
                motion.strokes.forEach((stroke) => {
                    if (stroke.committed || !stroke.path.isConnected) {
                        return;
                    }
                    const visibleLength = stroke.length * progress;
                    this.revealMotionStroke(stroke, visibleLength);
                    if (rawProgress >= 1) {
                        this.commitMotionStroke(stroke);
                    }
                });
                if (rawProgress < 1) {
                    break;
                }
                const completedStep = motion.step;
                this.debug('motion.step.end', {
                    stage: completedStep.stage,
                    eventId: motion.eventId,
                    elapsedMs: motion.stepElapsedMs,
                });
                this.completeMotionStep(completedStep);
                this.beginNextMotionStep();
                completedSteps += 1;
                if (remainingMs <= 0) {
                    break;
                }
            }
            if (this.motion) {
                this.motionFrame = requestAnimationFrame((nextTimestamp) =>
                    this.tickMotion(nextTimestamp),
                );
            }
        }

        commitMotionStroke(stroke) {
            if (stroke.committed || !stroke.path.isConnected) {
                return;
            }
            stroke.committed = true;
            stroke.path.setAttribute('d', stroke.fullData);
            stroke.path.style.visibility = 'visible';
            stroke.path.style.opacity = '1';
            stroke.path.style.removeProperty('stroke-linecap');
            this.debug('stroke.committed', {
                stage: stroke.stage,
                eventId: this.motion?.eventId || '',
                length: stroke.length,
            });
        }

        finishMotion() {
            const motion = this.motion;
            if (!motion) {
                return;
            }
            this.motion = null;
            this.motionFrame = null;
            this.debug('motion.complete', {
                eventId: motion.eventId,
                generation: motion.generation,
            });
            if (this.pendingPresentationReconcile) {
                this.pendingPresentationReconcile = false;
                this.reconcilePresentation('motion.complete');
                return;
            }
            if (this.geometryDirty) {
                this.schedulePresentationGeometrySync();
            }
            motion.onComplete?.();
        }

        cancelMotion(reason) {
            if (this.motionFrame !== null) {
                cancelAnimationFrame(this.motionFrame);
                this.motionFrame = null;
            }
            if (this.motion) {
                this.debug('motion.cancel', {
                    reason,
                    stage: this.motion.step?.stage || '',
                    eventId: this.motion.eventId,
                });
            }
            this.motion = null;
            this.pendingPresentationReconcile = false;
        }

        commitStroke(path) {
            if (!path.isConnected) {
                return;
            }
            path.style.opacity = '1';
            path.style.removeProperty('stroke-linecap');
        }

        scheduleTimer(callback, delayMs, generation, label = 'timer') {
            this.debug('timer.scheduled', { label, generation, delayMs });
            const timerId = window.setTimeout(() => {
                this.timerIds.delete(timerId);
                const current = this.isGenerationCurrent(generation);
                this.debug('timer.fired', { label, generation, delayMs, current });
                if (current) {
                    callback();
                }
            }, Math.max(0, delayMs));
            this.timerIds.add(timerId);
            return timerId;
        }

        clearTimers() {
            if (this.timerIds.size > 0) {
                this.debug('timers.clear', { count: this.timerIds.size });
            }
            this.timerIds.forEach((timerId) => window.clearTimeout(timerId));
            this.timerIds.clear();
        }

        handleClick(event) {
            if (!this.interactionEnabled()) {
                return;
            }
            const card = event.target.closest(CARD_SELECTOR);
            if (!card || !this.scope.contains(card)) {
                return;
            }
            if (event.target.closest(INTERACTIVE_SELECTOR)) {
                return;
            }
            const cards = this.visibleCards();
            if (cards.length <= 1) {
                return;
            }
            const eventId = card.dataset.adaAlarmEventId;
            if (this.pinnedEventId === eventId) {
                this.debug('click.unpin', { eventId });
                const index = cards.findIndex(
                    (candidate) => candidate.dataset.adaAlarmEventId === eventId,
                );
                this.pinnedEventId = null;
                this.clearSelections();
                this.generation += 1;
                this.clearTimers();
                this.clearActiveVisualState('click.unpin');
                this.autoIndex = index >= 0 ? (index + 1) % cards.length : 0;
                this.startAuto();
                return;
            }
            this.debug('click.pin', { eventId });
            this.pinnedEventId = eventId;
            this.clearSelections();
            card.dataset.adaAlarmSelected = 'true';
            this.clearActiveVisualState('click.pin');
            this.playPinned(card);
        }

        clearSelections() {
            this.scope.querySelectorAll(CARD_SELECTOR).forEach((card) => {
                card.dataset.adaAlarmSelected = 'false';
            });
        }

        clearRouteIdentity() {
            delete this.root.dataset.adaAlarmRouteEventId;
            delete this.root.dataset.adaAlarmRouteCardKey;
            delete this.root.dataset.adaAlarmRoutePlacementKey;
            delete this.root.dataset.adaAlarmRouteTone;
        }

        clearActiveVisualState(reason = 'unspecified') {
            this.cancelMotion(reason);
            this.debug('visual.clear', {
                reason,
                eventId: this.currentEventId(),
                hasActiveSvg: Boolean(this.activeSvg),
                hasImpactSvg: Boolean(this.impactSvg),
            });
            this.activeSvg?.remove();
            this.impactSvg?.remove();
            this.activeSvg = null;
            this.impactSvg = null;
            this.resetNodes();
        }

        resetNodes() {
            this.scope?.querySelectorAll('[data-ada-alarm-node-state]').forEach((node) => {
                node.dataset.adaAlarmNodeState = 'neutral';
                node.style.removeProperty('--ada-alarm-active-color');
                node.style.removeProperty('--ada-alarm-active-foreground');
            });
        }

        cardSpecification(card, baseline) {
            const origin = this.parseTarget(card.dataset.adaAlarmRouteOrigin);
            const destinations = this.parseTargets(card.dataset.adaAlarmRouteDestinations);
            const affectedTargets = this.parseTargets(card.dataset.adaAlarmAffectedTargets);
            const placementKey = card.dataset.adaAlarmPlacementKey;
            if (
                !origin ||
                !placementKey ||
                destinations.length === 0 ||
                affectedTargets.length === 0
            ) {
                return null;
            }
            const originElement = this.findTarget(origin);
            const destinationElements = destinations.map((target) => this.findTarget(target));
            const resolvedAffectedTargets = this.resolveAffectedTargets(affectedTargets);
            if (
                !originElement ||
                destinationElements.some((target) => !target) ||
                !resolvedAffectedTargets ||
                resolvedAffectedTargets.length === 0
            ) {
                return null;
            }
            const geometry = this.routeGeometry(
                baseline,
                card,
                originElement,
                destinationElements,
            );
            if (!geometry) {
                return null;
            }
            return {
                card,
                origin,
                destinations,
                affectedTargets: resolvedAffectedTargets.map(({ target }) => target),
                originElement,
                destinationElements,
                affectedElements: resolvedAffectedTargets.map(({ element }) => element),
                geometry,
                placementKey,
                signature: this.cardSpecificationSignature(card),
            };
        }

        resolveAffectedTargets(targets) {
            const resolved = [];
            const identities = new Set();
            for (const target of targets) {
                const entries = [];
                if (target.kind === 'component') {
                    const component = this.findTarget(target);
                    if (!component) {
                        return null;
                    }
                    component.querySelectorAll('[data-ada-subcomponent-key]').forEach((element) => {
                        entries.push({
                            target: {
                                kind: 'subcomponent',
                                key: element.dataset.adaSubcomponentKey,
                            },
                            element,
                        });
                    });
                } else {
                    const element = this.findTarget(target);
                    if (!element) {
                        return null;
                    }
                    entries.push({ target, element });
                }
                if (entries.length === 0) {
                    return null;
                }
                entries.forEach((entry) => {
                    const identity = `${entry.target.kind}:${entry.target.key}`;
                    if (!identities.has(identity)) {
                        identities.add(identity);
                        resolved.push(entry);
                    }
                });
            }
            return resolved;
        }

        cardSpecificationSignature(card) {
            return [
                card.dataset.adaAlarmCardKey || '',
                card.dataset.adaAlarmAssignmentKey || '',
                card.dataset.adaAlarmCardTone || '',
                card.dataset.adaAlarmRouteOrigin || '',
                card.dataset.adaAlarmRouteDestinations || '',
                card.dataset.adaAlarmAffectedTargets || '',
                card.dataset.adaAlarmDistributed || '',
            ].join('|');
        }

        routeGeometry(baseline, card, originElement, destinationElements) {
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
            const destinationXs = destinationElements.map((target) =>
                this.targetCenterX(target, rootRect),
            );
            const trackY = Math.max(cardBottom, baselineY - this.readTrackOffset());
            const sharedTrunk = `M ${cardX} ${cardBottom} L ${cardX} ${trackY} L ${originX} ${trackY}`;
            const originLeg = `M ${originX} ${trackY} L ${originX} ${baselineY}`;
            const destinationSegments = this.destinationRouteSegments(
                destinationXs,
                originX,
                trackY,
                baselineY,
            );
            return {
                sharedTrunk,
                originLeg,
                destinationSegments,
                contextSegments: [
                    sharedTrunk,
                    originLeg,
                    ...destinationSegments.map(({ data }) => data),
                ],
            };
        }

        destinationRouteSegments(destinationXs, originX, trackY, baselineY) {
            const candidates = destinationXs
                .map((x, index) => ({ index, x }))
                .filter(({ x }) => Math.abs(x - originX) >= 0.5);
            const groups = [
                candidates.filter(({ x }) => x < originX).sort((left, right) => right.x - left.x),
                candidates.filter(({ x }) => x > originX).sort((left, right) => left.x - right.x),
            ].filter((group) => group.length > 0);
            groups.sort(
                (left, right) =>
                    Math.min(...left.map(({ index }) => index)) -
                    Math.min(...right.map(({ index }) => index)),
            );
            return groups.flatMap((group) => {
                let cursorX = originX;
                return group.map(({ index, x }) => {
                    const data = `M ${cursorX} ${trackY} L ${x} ${trackY} L ${x} ${baselineY}`;
                    cursorX = x;
                    return { index, data };
                });
            });
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

        createImpactPaths(target, color) {
            const rootRect = this.root.getBoundingClientRect();
            const rect = target.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) {
                return [];
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
            const bottomCenterX = centerX;
            const leftPath = document.createElementNS(SVG_NS, 'path');
            leftPath.setAttribute('class', 'ada-alarm-dashboard-route__impact-path');
            leftPath.setAttribute(
                'd',
                [
                    `M ${centerX} ${y}`,
                    `H ${x + radius}`,
                    `Q ${x} ${y} ${x} ${y + radius}`,
                    `V ${bottom - radius}`,
                    `Q ${x} ${bottom} ${x + radius} ${bottom}`,
                    `H ${bottomCenterX}`,
                ].join(' '),
            );
            leftPath.setAttribute('stroke', color);

            const rightPath = document.createElementNS(SVG_NS, 'path');
            rightPath.setAttribute('class', 'ada-alarm-dashboard-route__impact-path');
            rightPath.setAttribute(
                'd',
                [
                    `M ${centerX} ${y}`,
                    `H ${right - radius}`,
                    `Q ${right} ${y} ${right} ${y + radius}`,
                    `V ${bottom - radius}`,
                    `Q ${right} ${bottom} ${right - radius} ${bottom}`,
                    `H ${bottomCenterX}`,
                ].join(' '),
            );
            rightPath.setAttribute('stroke', color);
            return [leftPath, rightPath];
        }

        debug(message, details = {}) {
            if (!this.debugEnabled) {
                return;
            }
            const elapsed = (performance.now() - this.debugStartedAt).toFixed(1);
            console.info(`[ada.alarm.trace +${elapsed}ms] ${message}`, {
                generation: this.generation,
                activeEventId: this.currentEventId(),
                pinnedEventId: this.pinnedEventId,
                ...details,
            });
        }

        describeElement(element) {
            if (!(element instanceof Element)) {
                return String(element);
            }
            return {
                tag: element.tagName.toLowerCase(),
                className: element.className?.baseVal || element.className || '',
                eventId: element.dataset?.adaAlarmEventId || '',
                componentKey: element.dataset?.adaComponentKey || '',
                subcomponentKey: element.dataset?.adaSubcomponentKey || '',
                slotKey: element.dataset?.adaSlotKey || '',
            };
        }


        currentEventId() {
            return this.root.dataset.adaAlarmRouteEventId || '';
        }

        visibleCards() {
            return Array.from(this.scope.querySelectorAll(CARD_SELECTOR)).filter(
                (card) => !card.hidden && card.getClientRects().length > 0,
            );
        }

        cardByEventId(eventId) {
            return this.visibleCards().find(
                (card) => card.dataset.adaAlarmEventId === eventId,
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
            const attribute = {
                component: 'data-ada-component-key',
                subcomponent: 'data-ada-subcomponent-key',
                slot: 'data-ada-slot-key',
            }[target.kind];
            if (!attribute) {
                return null;
            }
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

        applyNodeState(node, state, color, foreground) {
            node.dataset.adaAlarmNodeState = state;
            node.style.setProperty('--ada-alarm-active-color', color);
            node.style.setProperty('--ada-alarm-active-foreground', foreground);
        }

        observeGeometry(elements) {
            if (!this.resizeObserver) {
                return;
            }
            this.resizeObserver.disconnect();
            this.geometrySizes.clear();
            elements.forEach((element) => {
                if (!element) {
                    return;
                }
                this.geometrySizes.set(element, this.elementSize(element));
                this.resizeObserver.observe(element);
            });
        }

        elementSize(element) {
            const rect = element.getBoundingClientRect();
            return { width: rect.width, height: rect.height };
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

        toneColor(tone) {
            if (tone === 'critical') {
                return this.readCssValue('--ada-alarm-route-critical-color');
            }
            if (tone === 'attention') {
                return this.readCssValue('--ada-alarm-route-attention-color');
            }
            return '';
        }

        toneForeground(tone) {
            return tone === 'attention' ? '#212529' : '#FFFFFF';
        }

        readCssValue(name) {
            return getComputedStyle(this.root).getPropertyValue(name).trim();
        }

        isGenerationCurrent(generation) {
            return generation === this.generation && this.root.isConnected;
        }
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = new AlarmRoutePlayer(root);
        controllers.add(controller);
        controller.start();
    }

    function scan(root = document) {
        if (root.matches && root.matches(ROUTE_SELECTOR)) {
            mount(root);
        }
        root.querySelectorAll?.(ROUTE_SELECTOR).forEach(mount);
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
