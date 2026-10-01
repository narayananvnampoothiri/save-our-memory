/**
 * SAVE OUR MEMORY - MAIN APPLICATION BOOTSTRAPPER
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Management
  const initTheme = () => {
    const savedTheme = localStorage.getItem('som_theme') || 'light';
    setTheme(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        setTheme(next);
      });
    }
  };

  const setTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('som_theme', theme);
    const icon = document.getElementById('theme-icon');
    if (icon) {
      icon.innerText = theme === 'light' ? '🌙' : '☀️';
    }
  };

  // User Dropdown Management
  const initUserDropdown = () => {
    const userBtn = document.getElementById('user-menu-btn');
    const dropdown = document.getElementById('user-dropdown');

    if (userBtn && dropdown) {
      userBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
      });

      document.addEventListener('click', () => {
        dropdown.classList.remove('show');
      });
    }
  };

  // Header update on auth change
  const updateAuthUI = () => {
    const isAuth = Auth.isAuthenticated();
    const user = Auth.getUser();

    const authNav = document.getElementById('authenticated-nav');
    const guestNav = document.getElementById('guest-nav');
    const headerActions = document.getElementById('header-auth-actions');
    const mobileNav = document.getElementById('mobile-bottom-nav');

    if (isAuth && user) {
      if (authNav) authNav.style.display = 'flex';
      if (guestNav) guestNav.style.display = 'none';
      if (headerActions) headerActions.style.display = 'flex';
      if (mobileNav) mobileNav.style.display = 'flex';
      Views.updateHeaderUser();
      Views.updateNotificationBadge();
    } else {
      if (authNav) authNav.style.display = 'none';
      if (guestNav) guestNav.style.display = 'flex';
      if (headerActions) headerActions.style.display = 'none';
      if (mobileNav) mobileNav.style.display = 'none';
    }
  };

  window.addEventListener('som:auth_changed', updateAuthUI);

  // Global Logout Action
  window.handleLogout = async () => {
    try {
      await API.auth.logout();
    } catch (e) {}
    Auth.clearSession();
    Views.showToast('You have been logged out.');
    Router.navigate('');
  };

  // Periodic notification check (every 30 seconds)
  setInterval(() => {
    if (Auth.isAuthenticated()) {
      Views.updateNotificationBadge();
    }
  }, 30000);

  // Initialize
  initTheme();
  initUserDropdown();
  updateAuthUI();
  Router.init();
  Router.refresh();

  // Register PWA Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }
});
