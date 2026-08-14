/*
Espejo pedagógico del scheduler visual.
Process conserva seis slots horizontales fijos: el scheduler decide qué evento ocupa
cada slot, pero nunca puede crear filas implícitas ni alterar la geometría aprobada.
IO mantiene sus colas internas independientes por posición.
*/
(() => {
    'use strict';

    const SCHEDULER_SELECTOR = '[data-ada-alarm-visibility-strategy]';
    const CARD_SELECTOR = '[data-ada-alarm-event-id]';
    const controllers = new Set();

    class QueueLaneController {
        constructor(root) {
            this.root = root;
            this.index = 0;
            this.timer = null;
            this.observer = null;
        }

        start() {
            this.observer = new MutationObserver(() => this.reconcile());
            this.observer.observe(this.root, { childList: true });
            this.reconcile();
        }

        disconnect() {
            this.clearTimer();
            if (this.observer) {
                this.observer.disconnect();
            }
        }

        reconcile() {
            const cards = this.cards();
            if (cards.length === 0) {
                this.clearTimer();
                return;
            }
            this.index %= cards.length;
            cards.forEach((card, index) => {
                card.hidden = index !== this.index;
            });
            this.schedule(cards.length);
        }

        schedule(count) {
            this.clearTimer();
            if (count <= 1) {
                return;
            }
            const interval = Number.parseInt(this.root.dataset.adaAlarmQueueIntervalMs || '', 10);
            if (!Number.isFinite(interval) || interval <= 0) {
                return;
            }
            this.timer = window.setTimeout(() => {
                this.timer = null;
                const cards = this.cards();
                if (cards.length <= 1) {
                    this.reconcile();
                    return;
                }
                this.index = (this.index + 1) % cards.length;
                this.reconcile();
            }, interval);
        }

        clearTimer() {
            if (this.timer !== null) {
                window.clearTimeout(this.timer);
                this.timer = null;
            }
        }

        cards() {
            return Array.from(this.root.children).filter(
                (child) => child.matches && child.matches(CARD_SELECTOR),
            );
        }
    }

    class QueueInQueueScheduler {
        constructor(root) {
            this.root = root;
            this.lanes = new Map();
            this.observer = null;
        }

        start() {
            this.scan();
            this.observer = new MutationObserver(() => this.scan());
            this.observer.observe(this.root, { childList: true, subtree: true });
        }

        disconnect() {
            this.lanes.forEach((controller) => controller.disconnect());
            this.lanes.clear();
            if (this.observer) {
                this.observer.disconnect();
            }
        }

        scan() {
            const current = new Set(
                this.root.querySelectorAll('[data-ada-alarm-queue-lane]'),
            );
            current.forEach((lane) => {
                if (this.lanes.has(lane)) {
                    return;
                }
                const controller = new QueueLaneController(lane);
                this.lanes.set(lane, controller);
                controller.start();
            });
            this.lanes.forEach((controller, lane) => {
                if (current.has(lane) && lane.isConnected) {
                    return;
                }
                controller.disconnect();
                this.lanes.delete(lane);
            });
        }
    }

    class ProcessScheduler {
        constructor(root) {
            this.root = root;
            this.normalCursor = 0;
            this.distributedCursor = 0;
            this.normalTimer = null;
            this.distributedTimer = null;
            this.observer = null;
        }

        start() {
            this.observer = new MutationObserver(() => this.reconcile());
            this.observer.observe(this.root, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-ada-alarm-distributed'],
            });
            this.reconcile();
        }

        disconnect() {
            this.clearNormalTimer();
            this.clearDistributedTimer();
            if (this.observer) {
                this.observer.disconnect();
            }
        }

        reconcile() {
            const cards = this.cards();
            const distributed = cards.filter(
                (card) => card.dataset.adaAlarmDistributed === 'true',
            );
            const reserved = distributed.length >= 2;
            const normal = reserved
                ? cards.filter((card) => card.dataset.adaAlarmDistributed !== 'true')
                : cards;
            const normalCapacity = reserved ? 5 : 6;
            this.normalCursor = normal.length === 0 ? 0 : this.normalCursor % normal.length;
            this.distributedCursor =
                distributed.length === 0 ? 0 : this.distributedCursor % distributed.length;
            cards.forEach((card) => {
                card.hidden = true;
                card.style.removeProperty('grid-column');
                card.style.removeProperty('grid-row');
            });
            const normalVisible = this.window(normal, this.normalCursor, normalCapacity);
            const normalSlots = this.edgeOrder(normalCapacity);
            normalVisible.forEach((card, index) => {
                this.showAtSlot(card, normalSlots[index]);
            });
            if (reserved && distributed.length > 0) {
                this.showAtSlot(distributed[this.distributedCursor], 5);
            }
            this.scheduleNormal(normal.length, normalCapacity);
            this.scheduleDistributed(distributed.length, reserved);
        }

        scheduleNormal(count, capacity) {
            if (count <= capacity) {
                this.clearNormalTimer();
                return;
            }
            if (this.normalTimer !== null) {
                return;
            }
            const interval = Number.parseInt(
                this.root.dataset.adaAlarmRotationIntervalMs || '',
                10,
            );
            if (!Number.isFinite(interval) || interval <= 0) {
                return;
            }
            this.normalTimer = window.setTimeout(() => {
                this.normalTimer = null;
                this.normalCursor += 1;
                this.reconcile();
            }, interval);
        }

        scheduleDistributed(count, reserved) {
            if (!reserved || count <= 1) {
                this.clearDistributedTimer();
                return;
            }
            if (this.distributedTimer !== null) {
                return;
            }
            const interval = Number.parseInt(
                this.root.dataset.adaAlarmDistributedIntervalMs || '',
                10,
            );
            if (!Number.isFinite(interval) || interval <= 0) {
                return;
            }
            this.distributedTimer = window.setTimeout(() => {
                this.distributedTimer = null;
                this.distributedCursor = (this.distributedCursor + 1) % count;
                this.reconcile();
            }, interval);
        }

        /* La fila 1 se fija explícitamente para impedir el auto-placement vertical. */
        showAtSlot(card, slotIndex) {
            card.hidden = false;
            card.style.gridColumn = String(slotIndex + 1);
            card.style.gridRow = '1';
            card.dataset.adaAlarmAssignmentKey = `process_slot_${slotIndex + 1}`;
        }

        window(items, start, capacity) {
            if (items.length <= capacity) {
                return items.slice();
            }
            return Array.from({ length: capacity }, (_, offset) => {
                return items[(start + offset) % items.length];
            });
        }

        edgeOrder(capacity) {
            const order = [];
            let left = 0;
            let right = capacity - 1;
            while (left <= right) {
                order.push(left);
                if (left !== right) {
                    order.push(right);
                }
                left += 1;
                right -= 1;
            }
            return order;
        }

        clearNormalTimer() {
            if (this.normalTimer !== null) {
                window.clearTimeout(this.normalTimer);
                this.normalTimer = null;
            }
        }

        clearDistributedTimer() {
            if (this.distributedTimer !== null) {
                window.clearTimeout(this.distributedTimer);
                this.distributedTimer = null;
            }
        }

        cards() {
            const frame = this.root.querySelector('[data-ada-alarm-process-queue]');
            return frame ? Array.from(frame.querySelectorAll(CARD_SELECTOR)) : [];
        }
    }

    function createController(root) {
        const strategy = root.dataset.adaAlarmVisibilityStrategy;
        if (strategy === 'queue-in-queue') {
            return new QueueInQueueScheduler(root);
        }
        if (strategy === 'process') {
            return new ProcessScheduler(root);
        }
        return null;
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = createController(root);
        if (!controller) {
            return;
        }
        controllers.add(controller);
        controller.start();
    }

    function scan(root = document) {
        if (root.matches && root.matches(SCHEDULER_SELECTOR)) {
            mount(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll(SCHEDULER_SELECTOR).forEach(mount);
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
