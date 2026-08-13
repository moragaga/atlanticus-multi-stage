(() => {
    'use strict';

    const ROOT_SELECTOR = '[data-ada-alarm-baseline]';
    const SCOPE_SELECTOR = '[data-ada-alarm-geometry-scope="true"]';
    const controllers = new Set();

    class AlarmBaselineGeometry {
        constructor(root) {
            this.root = root;
            this.scope = root.closest(SCOPE_SELECTOR);
            this.frame = null;
            this.resizeObserver = null;
            this.targetObserver = null;
            this.mutationObserver = null;
            this.onWindowResize = () => this.schedule();
        }

        start() {
            if (!this.scope) {
                return;
            }
            if (typeof ResizeObserver === 'function') {
                this.resizeObserver = new ResizeObserver(() => this.schedule());
                this.targetObserver = new ResizeObserver(() => this.schedule());
                this.resizeObserver.observe(this.scope);
                this.resizeObserver.observe(this.root);
            } else {
                window.addEventListener('resize', this.onWindowResize);
            }
            this.mutationObserver = new MutationObserver(() => this.schedule());
            this.mutationObserver.observe(this.scope, {
                attributes: true,
                childList: true,
                subtree: true,
                attributeFilter: ['data-ada-slot-key', 'data-ada-component-key'],
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
            if (this.targetObserver) {
                this.targetObserver.disconnect();
            }
            if (this.mutationObserver) {
                this.mutationObserver.disconnect();
            }
            window.removeEventListener('resize', this.onWindowResize);
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
            const rootRect = this.root.getBoundingClientRect();
            const nodes = this.root.querySelectorAll('[data-ada-alarm-target-kind]');
            const nodeSize = this.readNodeSize();
            if (this.targetObserver) {
                this.targetObserver.disconnect();
            }
            nodes.forEach((node) => {
                const target = this.findTarget(node);
                if (!target || rootRect.width <= 0) {
                    node.dataset.adaAlarmPositioned = 'false';
                    return;
                }
                if (this.targetObserver) {
                    this.targetObserver.observe(target);
                }
                const targetRect = target.getBoundingClientRect();
                const rawX = targetRect.left + targetRect.width / 2 - rootRect.left;
                const halfNode = nodeSize / 2;
                const x = Math.min(
                    Math.max(rawX, halfNode),
                    Math.max(halfNode, rootRect.width - halfNode),
                );
                node.style.left = `${x}px`;
                node.dataset.adaAlarmPositioned = 'true';
            });
        }

        readNodeSize() {
            const node = this.root.querySelector('[data-ada-alarm-target-kind]');
            return node ? node.getBoundingClientRect().width || 12 : 12;
        }

        findTarget(node) {
            const kind = node.dataset.adaAlarmTargetKind;
            const key = node.dataset.adaAlarmTargetKey;
            const attribute = kind === 'slot' ? 'data-ada-slot-key' : 'data-ada-component-key';
            return Array.from(this.scope.querySelectorAll(`[${attribute}]`)).find(
                (candidate) => candidate.getAttribute(attribute) === key,
            );
        }
    }

    function mount(root) {
        if (Array.from(controllers).some((controller) => controller.root === root)) {
            return;
        }
        const controller = new AlarmBaselineGeometry(root);
        controllers.add(controller);
        controller.start();
    }

    function scan(root = document) {
        if (root.matches && root.matches(ROOT_SELECTOR)) {
            mount(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll(ROOT_SELECTOR).forEach(mount);
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
