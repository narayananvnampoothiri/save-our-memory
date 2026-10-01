/**
 * SAVE OUR MEMORY - AUTHENTICATION STATE MANAGER
 */

const Auth = (() => {
  let currentUser = null;

  const init = () => {
    try {
      const stored = localStorage.getItem('som_user');
      if (stored) {
        currentUser = JSON.parse(stored);
      }
    } catch (e) {
      currentUser = null;
    }
  };

  init();

  return {
    isAuthenticated: () => Boolean(localStorage.getItem('som_token')),
    getUser: () => currentUser,
    setUser: (user) => {
      currentUser = user;
      if (user) {
        localStorage.setItem('som_user', JSON.stringify(user));
      } else {
        localStorage.removeItem('som_user');
      }
      window.dispatchEvent(new CustomEvent('som:auth_changed', { detail: { user } }));
    },
    setSession: (token, user) => {
      localStorage.setItem('som_token', token);
      Auth.setUser(user);
    },
    clearSession: () => {
      localStorage.removeItem('som_token');
      Auth.setUser(null);
    }
  };
})();
