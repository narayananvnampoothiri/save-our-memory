/**
 * SAVE OUR MEMORY - REST API CLIENT
 */

const API = (() => {
  const getHeaders = (isMultipart = false) => {
    const headers = {};
    const token = localStorage.getItem('som_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  };

  const request = async (url, options = {}) => {
    const isMultipart = options.body instanceof FormData;
    options.headers = {
      ...getHeaders(isMultipart),
      ...(options.headers || {})
    };

    try {
      const res = await fetch(url, options);
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        if (res.status === 401 && !url.includes('/api/auth/login')) {
          // Session expired
          localStorage.removeItem('som_token');
          localStorage.removeItem('som_user');
          window.dispatchEvent(new CustomEvent('som:auth_required'));
        }
        const error = new Error(data.error || 'A system error occurred.');
        error.status = res.status;
        error.data = data;
        throw error;
      }
      return data;
    } catch (err) {
      throw err;
    }
  };

  return {
    auth: {
      register: (data) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),
      login: (data) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }),
      logout: () => request('/api/auth/logout', { method: 'POST' }),
      getMe: () => request('/api/auth/me'),
      forgotPassword: (email) => request('/api/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),
      verifyResetCode: (data) => request('/api/auth/verify-reset-code', { method: 'POST', body: JSON.stringify(data) }),
      resetPassword: (data) => request('/api/auth/reset-password', { method: 'POST', body: JSON.stringify(data) })
    },
    memories: {
      getAll: (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return request(`/api/memories?${q}`);
      },
      create: (formData) => request('/api/memories', { method: 'POST', body: formData }),
      getById: (id) => request(`/api/memories/${id}`),
      update: (id, data) => request(`/api/memories/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
      delete: (id) => request(`/api/memories/${id}`, { method: 'DELETE' })
    },
    shared: {
      getAll: (params = {}) => {
        const q = new URLSearchParams(params).toString();
        return request(`/api/shared?${q}`);
      }
    },
    connections: {
      getAll: () => request('/api/connections'),
      sendRequest: (userId) => request('/api/connections/request', { method: 'POST', body: JSON.stringify({ user_id: userId }) }),
      accept: (connectionId) => request(`/api/connections/${connectionId}/accept`, { method: 'POST' }),
      reject: (connectionId) => request(`/api/connections/${connectionId}/reject`, { method: 'POST' }),
      cancel: (connectionId) => request(`/api/connections/${connectionId}/cancel`, { method: 'DELETE' }),
      remove: (connectionId) => request(`/api/connections/${connectionId}/remove`, { method: 'DELETE' })
    },
    users: {
      search: (query) => request(`/api/users/search?q=${encodeURIComponent(query)}`),
      getProfile: (id) => request(`/api/users/${id}`),
      updateProfile: (formData) => request('/api/users/profile', { method: 'PUT', body: formData })
    },
    notifications: {
      getAll: () => request('/api/notifications'),
      markRead: (id) => request(`/api/notifications/${id}/read`, { method: 'PUT' }),
      markAllRead: () => request('/api/notifications/read-all', { method: 'PUT' })
    },
    dashboard: {
      getStats: () => request('/api/dashboard/stats')
    },
    media: {
      getMediaUrl: (storageKey) => {
        const token = localStorage.getItem('som_token');
        return `/api/media/${storageKey}?token=${encodeURIComponent(token || '')}`;
      },
      getThumbnailUrl: (thumbnailKey) => {
        const token = localStorage.getItem('som_token');
        return `/api/media/thumbnail/${thumbnailKey}?token=${encodeURIComponent(token || '')}`;
      },
      getAvatarUrl: (avatarKey) => {
        if (!avatarKey) return null;
        return `/api/avatar/${avatarKey}`;
      }
    }
  };
})();
