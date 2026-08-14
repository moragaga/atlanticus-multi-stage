(() => {
    'use strict';

    // Player de rutas de alarmas. La capa blanca permanece completa y esta clase solo controla el color activo.

    const ROUTE_SELECTOR = '[data-ada-alarm-route]';
    const SCOPE_SELECTOR = '[data-ada-alarm-geometry-scope="true"]';
    const PRESENTATION_SCOPE_SELECTOR = '[data-ada-alarm-presentation-scope="true"]';
    const BASELINE_SELECTOR = '[data-ada-alarm-baseline]';
    const CARD_SELECTOR = '[data-ada-alarm-event-id]';
    const INTERACTIVE_SELECTOR = 'button, a, input, select, textarea, [role="button"], [data-ada-alarm-card-control]';
    const PLAYER_REFRESH_EVENT = 'ada:alarm-player-refresh';
    // Las rutas conservan una velocidad espacial normalizada por el ancho del dashboard.
    const MOTION_SCOPE_WIDTHS_PER_SECOND = 0.2;
    const MIN_MOTION_SPEED_PX_PER_SECOND = 160;
    const MAX_MOTION_SPEED_PX_PER_SECOND = 960;
    // El trazado activo usa un único prefijo visible seguido por un gap mayor que el path. Así no existe un segundo dash que pueda aparecer como línea fantasma.
    const PREFIX_GAP_PX = 24;
    const PREFIX_GAP_RATIO = 0.08;
    // Los bordes de impacto se coordinan como una sola fase. El mayor borde fija una duración acotada para evitar cierres demasiado rápidos o eternos.
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
            this.started = false;
            this.debugEnabled =
                new URLSearchParams(window.location.search).get(DEBUG_QUERY_PARAMETER) === '1';
            this.debugStartedAt = performance.now();
            this.onClick = (event) => this.handleClick(event);
            this.onRefresh = () => this.markGeometryDirty('explicit');
        }

        start() {
            if (!this.scope || this.started) {
                return;
            }
            this.started = true;
            this.scope.addEventListener('click', this.onClick);
            this.scope.addEventListener(PLAYER_REFRESH_EVENT, this.onRefresh);
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
                this.debug('geometry.sync.deferred', { phase: this.motion.phase });
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
                if (!this.isGenerationCurrent(generation) || this.pinnedEventId) {
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
                    this.debug('auto.next', {
                        generation,
                        fromEventId: eventId,
                        nextIndex: (normalizedIndex + 1) % nextCards.length,
                    });
                    this.clearActiveVisualState('auto.next');
                    this.presentAutoIndex(
                        (normalizedIndex + 1) % nextCards.length,
                        generation,
                    );
                }, dwellMs, generation, 'auto.next');
            });
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
                impacts: specification.impacts.map((target) => `${target.kind}:${target.key}`),
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
            specification.impactElements.forEach((target, index) => {
                const impactPaths = this.createImpactPaths(target, color);
                impactPaths.forEach((impactPath, pathIndex) => {
                    impactSvg.appendChild(impactPath);
                    this.commitStroke(impactPath);
                    const side = pathIndex === 0 ? 'left' : 'right';
                    const impact = specification.impacts[index];
                    this.debug('stroke.static', {
                        stage: `impact-${side}:${impact.kind}:${impact.key}`,
                        eventId,
                    });
                });
            });
        }

        applyStaticNodeStates(specification, color, foreground) {
            this.resetNodes();
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
            specification.impacts.forEach((target) => {
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

        // Devuelve una velocidad comparable entre tablet, desktop y videowall usando la escala del scope, no una cifra absoluta para todas las pantallas.
        motionSpeed() {
            const width = this.scope?.getBoundingClientRect().width || 0;
            const normalized = width * MOTION_SCOPE_WIDTHS_PER_SECOND;
            return Math.min(
                MAX_MOTION_SPEED_PX_PER_SECOND,
                Math.max(MIN_MOTION_SPEED_PX_PER_SECOND, normalized),
            );
        }

        // Toda la presentación activa usa un único reloj requestAnimationFrame.
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
                phase: 'shared-trunk',
                phaseStartedAt: null,
                phaseDurationMs: null,
                strokes: [],
            };
            this.beginMotionPhase('shared-trunk');
            this.debug('motion.start', {
                eventId,
                generation,
                speed: this.motion.speed,
            });
            this.motionFrame = requestAnimationFrame((timestamp) => this.tickMotion(timestamp));
        }

        // Las fases siguen siendo trunk -> fan-out -> impactos, pero ninguna crea color futuro antes de que corresponda.
        beginMotionPhase(phase) {
            if (!this.motion || !this.isGenerationCurrent(this.motion.generation)) {
                return;
            }
            this.motion.phase = phase;
            this.motion.phaseStartedAt = null;
            this.motion.phaseDurationMs = null;
            if (phase === 'shared-trunk') {
                this.motion.strokes = this.createRouteMotionStrokes([
                    {
                        data: this.motion.specification.geometry.sharedTrunk,
                        stage: 'shared-trunk',
                    },
                ]);
            } else if (phase === 'fan-out') {
                const segments = [
                    {
                        data: this.motion.specification.geometry.originLeg,
                        stage: 'origin-leg',
                    },
                ];
                this.motion.specification.impacts.forEach((target, index) => {
                    if (this.sameTarget(target, this.motion.specification.origin)) {
                        return;
                    }
                    const data = this.motion.specification.geometry.impactLegs[index];
                    if (data) {
                        segments.push({
                            data,
                            stage: `impact-leg:${target.kind}:${target.key}`,
                        });
                    }
                });
                this.motion.strokes = this.createRouteMotionStrokes(segments);
            } else if (phase === 'impact') {
                this.applyStaticNodeStates(
                    this.motion.specification,
                    this.motion.color,
                    this.motion.foreground,
                );
                this.motion.strokes = this.createImpactMotionStrokes();
                this.motion.phaseDurationMs = this.impactPhaseDuration(this.motion.strokes);
            }
            this.debug('motion.phase.start', {
                phase,
                eventId: this.motion.eventId,
                speed: this.motion.speed,
                phaseDurationMs: this.motion.phaseDurationMs,
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

        createImpactMotionStrokes() {
            if (!this.impactSvg?.isConnected || !this.motion) {
                return [];
            }
            const strokes = [];
            this.motion.specification.impactElements.forEach((target, index) => {
                const impact = this.motion.specification.impacts[index];
                this.createImpactPaths(target, this.motion.color).forEach((path, pathIndex) => {
                    const side = pathIndex === 0 ? 'left' : 'right';
                    const stage = `impact-${side}:${impact.kind}:${impact.key}`;
                    const stroke = this.prepareMotionStroke(path, stage, this.impactSvg);
                    if (stroke) {
                        strokes.push(stroke);
                    }
                });
            });
            return strokes;
        }

        // Oculta el path ANTES de insertarlo en el SVG. Después de medirlo se prepara un patrón 'prefijo visible + gap largo' sin animar dashoffset.
        prepareMotionStroke(path, stage, container) {
            if (!this.motion || !container?.isConnected) {
                path.remove();
                return null;
            }
            path.style.visibility = 'hidden';
            path.style.opacity = '0';
            path.style.strokeLinecap = 'butt';
            path.style.strokeDashoffset = '0';
            container.appendChild(path);
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
            const guard = Math.max(PREFIX_GAP_PX, length * PREFIX_GAP_RATIO);
            const gapLength = length + guard;
            path.style.strokeDasharray = `0 ${gapLength}`;
            return {
                path,
                stage,
                length,
                gapLength,
                committed: false,
            };
        }

        // Todos los bordes impactados comienzan y terminan coordinados. La duración depende suavemente del mayor recorrido y queda acotada.
        impactPhaseDuration(strokes) {
            if (!this.motion || strokes.length === 0) {
                return 0;
            }
            const longest = Math.max(...strokes.map((stroke) => stroke.length));
            const naturalDuration = (longest / this.motion.speed) * 1000;
            return Math.min(
                IMPACT_MAX_DURATION_MS,
                Math.max(IMPACT_MIN_DURATION_MS, naturalDuration),
            );
        }

        // Ease-in-out senoidal: evita que el borde arranque o cierre de golpe al encontrarse abajo.
        easeImpactProgress(progress) {
            const clamped = Math.min(1, Math.max(0, progress));
            return 0.5 - Math.cos(Math.PI * clamped) / 2;
        }

        // Solo el primer tramo del path puede ser visible. El gap posterior es más largo que el path completo, por lo que no hay repetición al extremo opuesto.
        revealMotionStroke(stroke, visibleLength) {
            if (stroke.committed || !stroke.path.isConnected || visibleLength <= 0) {
                return;
            }
            const clamped = Math.min(stroke.length, visibleLength);
            stroke.path.style.strokeDasharray = `${clamped} ${stroke.gapLength}`;
            stroke.path.style.visibility = 'visible';
            stroke.path.style.opacity = '1';
        }

        // En rutas el avance se mide por distancia. En impactos todas las mitades comparten el mismo progreso normalizado para cerrar juntas.
        tickMotion(timestamp) {
            this.motionFrame = null;
            const motion = this.motion;
            if (!motion || !this.isGenerationCurrent(motion.generation)) {
                return;
            }
            if (motion.phaseStartedAt === null) {
                motion.phaseStartedAt = timestamp;
            }
            const elapsedMs = Math.max(0, timestamp - motion.phaseStartedAt);
            const elapsedSeconds = elapsedMs / 1000;
            const distance = elapsedSeconds * motion.speed;
            const impactProgress =
                motion.phase === 'impact' && motion.phaseDurationMs > 0
                    ? this.easeImpactProgress(elapsedMs / motion.phaseDurationMs)
                    : null;
            let complete = true;
            motion.strokes.forEach((stroke) => {
                if (stroke.committed || !stroke.path.isConnected) {
                    return;
                }
                const visibleLength =
                    impactProgress === null
                        ? Math.min(stroke.length, distance)
                        : stroke.length * impactProgress;
                this.revealMotionStroke(stroke, visibleLength);
                if (visibleLength >= stroke.length) {
                    this.commitMotionStroke(stroke);
                } else {
                    complete = false;
                }
            });
            if (motion.strokes.length === 0) {
                complete = true;
            }
            if (complete) {
                this.debug('motion.phase.end', {
                    phase: motion.phase,
                    eventId: motion.eventId,
                    elapsedMs,
                });
                if (motion.phase === 'shared-trunk') {
                    this.beginMotionPhase('fan-out');
                } else if (motion.phase === 'fan-out') {
                    this.beginMotionPhase('impact');
                } else {
                    this.finishMotion();
                    return;
                }
            }
            if (this.motion) {
                this.motionFrame = requestAnimationFrame((nextTimestamp) =>
                    this.tickMotion(nextTimestamp),
                );
            }
        }

        // Al terminar se elimina el patrón dash y queda una línea sólida permanente durante FULL/dwell.
        commitMotionStroke(stroke) {
            if (stroke.committed || !stroke.path.isConnected) {
                return;
            }
            stroke.committed = true;
            stroke.path.style.visibility = 'visible';
            stroke.path.style.opacity = '1';
            stroke.path.style.strokeDasharray = 'none';
            stroke.path.style.strokeDashoffset = '0';
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
                    phase: this.motion.phase,
                    eventId: this.motion.eventId,
                });
            }
            this.motion = null;
        }

        commitStroke(path) {
            if (!path.isConnected) {
                return;
            }
            path.style.opacity = '1';
            path.style.strokeDasharray = 'none';
            path.style.strokeDashoffset = '0';
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
            const impacts = this.parseTargets(card.dataset.adaAlarmRouteImpacts);
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
            const sharedTrunk = `M ${cardX} ${cardBottom} L ${cardX} ${trackY} L ${originX} ${trackY}`;
            const originLeg = `M ${originX} ${trackY} L ${originX} ${baselineY}`;
            const impactLegs = impactXs.map((impactX) => {
                if (Math.abs(impactX - originX) < 0.5) {
                    return null;
                }
                return `M ${originX} ${trackY} L ${impactX} ${trackY} L ${impactX} ${baselineY}`;
            });
            return {
                sharedTrunk,
                originLeg,
                impactLegs,
                contextSegments: [
                    sharedTrunk,
                    originLeg,
                    ...impactLegs.filter(Boolean),
                ],
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

        // Cada card usa dos paths abiertos que parten del centro superior y se encuentran en el centro inferior.
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
