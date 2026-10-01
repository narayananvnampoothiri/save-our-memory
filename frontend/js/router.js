/**
 * SAVE OUR MEMORY - CLIENT HASH ROUTER
 */

const Router = (() => {
  const routes = {
    '': () => Views.renderDashboard(),
    'home': () => Views.renderDashboard(),
    'memories': () => Views.renderTimeline(),
    'photos': () => Views.renderGallery('photo'),
    'videos': () => Views.renderGallery('video'),
    'shared': () => Views.renderShared(),
    'connections': () => Views.renderConnections(),
    'profile': () => Views.renderProfile()
  };

  const getCleanRoute = () => {
    return window.location.hash.replace('#', '').split('?')[0].trim();
  };

  const updateActiveNav = (currentRoute) => {
    const route = currentRoute || 'home';
    document.querySelectorAll('.nav-item').forEach(el => {
      const target = el.dataset.route;
      el.classList.toggle('active', target === route);
    });
    document.querySelectorAll('.mobile-nav-item').forEach(el => {
      const target = el.dataset.route;
      el.classList.toggle('active', target === route);
    });
  };

  const handleRoute = () => {
    const route = getCleanRoute();

    if (!Auth.isAuthenticated()) {
      Views.renderUnauthenticatedState();
      return;
    }

    const handler = routes[route] || routes['home'];
    updateActiveNav(route || 'home');
    handler();
  };

  const init = () => {
    window.addEventListener('hashchange', handleRoute);
    window.addEventListener('som:auth_changed', handleRoute);
    window.addEventListener('som:auth_required', () => {
      Views.openAuthModal('login');
    });
  };

  return {
    init,
    navigate: (route) => {
      window.location.hash = `#${route}`;
    },
    refresh: () => {
      handleRoute();
    }
  };
})();
