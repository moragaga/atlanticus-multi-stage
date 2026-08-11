(() => {
  const rootSelector = '[data-atlanticus-navigation-root="true"]';
  const actionSelector = '[data-atlanticus-navigation-action]';
  const linkSelector = '.atlanticus-navigation__link';

  const getRoot = (node) => node?.closest?.(rootSelector) ?? document.querySelector(rootSelector);

  const setOpen = (root, open) => {
    if (!root) return;
    root.classList.toggle('is-open', open);
    const drawer = root.querySelector('[data-atlanticus-navigation-drawer="true"]');
    const trigger =
      root.querySelector('[data-atlanticus-navigation-action="open"]') ??
      document.querySelector('[data-atlanticus-navigation-action="open"]');
    drawer?.setAttribute('aria-hidden', String(!open));
    trigger?.setAttribute('aria-expanded', String(open));
  };

  const toggleGroup = (button) => {
    const targetId = button.getAttribute('aria-controls');
    const target = targetId ? document.getElementById(targetId) : null;
    if (!target) return;
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    target.classList.toggle('is-open', !expanded);
  };

  const syncActiveLink = () => {
    const current = new URL(window.location.href);
    document.querySelectorAll(linkSelector).forEach((link) => {
      const target = new URL(link.href, current.origin);
      const active = target.origin === current.origin && target.pathname === current.pathname;
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  };

  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const action = target?.closest(actionSelector);
    if (action) {
      const root = getRoot(action);
      const kind = action.dataset.atlanticusNavigationAction;
      if (kind === 'open') setOpen(root, true);
      else if (kind === 'close') setOpen(root, false);
      else if (kind === 'group') toggleGroup(action);
      return;
    }

    const link = target?.closest(linkSelector);
    if (link) {
      setOpen(getRoot(link), false);
      window.requestAnimationFrame(syncActiveLink);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(document.querySelector(rootSelector), false);
  });

  window.addEventListener('popstate', syncActiveLink);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncActiveLink, { once: true });
  } else {
    syncActiveLink();
  }
})();
