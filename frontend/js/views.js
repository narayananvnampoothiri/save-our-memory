/**
 * SAVE OUR MEMORY - VIEW RENDERING ENGINE
 */

const Views = (() => {
  const appEl = () => document.getElementById('app');

  // Friendly Toast Notification
  const showToast = (message, type = 'success') => {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <span style="font-size: 1.2rem;">${type === 'success' ? '❤️' : '⚠️'}</span>
      <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  // Helper for safe HTML insertion
  const escapeHtml = (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  };

  // 1. Unauthenticated Landing State
  const renderUnauthenticatedState = () => {
    appEl().innerHTML = `
      <div class="app-container" style="max-width: 900px; padding-top: 2rem;">
        <div class="dashboard-hero text-center" style="padding: 4rem 2rem;">
          <div class="hero-tagline">Private • Emotional • Timeless</div>
          <h1 class="hero-title" style="font-size: 2.8rem; margin: 0.5rem 0 1rem;">Save Our Memory</h1>
          <p class="hero-subtitle" style="margin: 0 auto 2rem; font-size: 1.15rem; max-width: 620px;">
            A sanctuary designed for couples, families, and close friends to privately preserve their most precious photos and videos.
            Not a public social network — a secure, intimate digital memory vault.
          </p>
          <div class="flex items-center justify-center gap-4" style="flex-wrap: wrap;">
            <button class="btn btn-primary btn-lg" onclick="Views.openAuthModal('register')">
              <span>❤️ Create Your Memory Vault</span>
            </button>
            <button class="btn btn-secondary btn-lg" onclick="Views.openAuthModal('login')">
              <span>Sign In</span>
            </button>
          </div>

          <div class="demo-accounts-bar" style="margin-top: 3.5rem;">
            <p style="font-size: 0.85rem; font-weight: 600; color: var(--accent-gold);">
              ⚡ Quick Demo Mode: Click to explore pre-seeded memory vaults
            </p>
            <div class="demo-accounts-buttons">
              <button class="demo-btn" onclick="Views.quickLogin('narayanan', 'LoveStory2026!')">
                👨 Narayanan (Owner of private & shared memories)
              </button>
              <button class="demo-btn" onclick="Views.quickLogin('anumaria', 'LoveStory2026!')">
                👩 Anu Maria (Connected partner)
              </button>
              <button class="demo-btn" onclick="Views.quickLogin('sid', 'LoveStory2026!')">
                📷 Siddharth (Pending connection)
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  };

  // 2. Dashboard View
  const renderDashboard = async () => {
    const user = Auth.getUser();
    appEl().innerHTML = `
      <div class="app-container">
        <div style="text-align: center; padding: 4rem 0;">
          <div class="brand-heart" style="font-size: 2.5rem; margin-bottom: 1rem;">❤️</div>
          <p>Opening your memory vault...</p>
        </div>
      </div>
    `;

    try {
      const stats = await API.dashboard.getStats();
      appEl().innerHTML = `
        <div class="app-container">
          <!-- Hero Banner -->
          <div class="dashboard-hero">
            <div class="hero-tagline">Private Digital Sanctuary</div>
            <h1 class="hero-title">Welcome back, ${escapeHtml(user.name)} ❤️</h1>
            <p class="hero-subtitle">
              Your memories, safely kept. Every milestone, sunrise, and quiet glance preserved exactly as you felt it.
            </p>
            <div class="hero-actions">
              <button class="btn btn-primary" onclick="Views.openAddMemoryModal()">
                <span>➕ Add Memory</span>
              </button>
              <button class="btn btn-secondary" onclick="Router.navigate('memories')">
                <span>❤️ Browse Timeline</span>
              </button>
              <button class="btn btn-secondary" onclick="Views.openSearchModal()">
                <span>🔍 Search People</span>
              </button>
            </div>
          </div>

          <!-- Quick Stats Grid -->
          <div class="stats-grid">
            <div class="stat-card" onclick="Router.navigate('photos')" style="cursor: pointer;">
              <div class="stat-icon photos">📷</div>
              <div>
                <div class="stat-number">${stats.photo_count}</div>
                <div class="stat-label">Photos Safely Kept</div>
              </div>
            </div>
            <div class="stat-card" onclick="Router.navigate('videos')" style="cursor: pointer;">
              <div class="stat-icon videos">🎥</div>
              <div>
                <div class="stat-number">${stats.video_count}</div>
                <div class="stat-label">Video Moments</div>
              </div>
            </div>
            <div class="stat-card" onclick="Router.navigate('connections')" style="cursor: pointer;">
              <div class="stat-icon connections">👥</div>
              <div>
                <div class="stat-number">${stats.connection_count}</div>
                <div class="stat-label">Connected Loved Ones</div>
              </div>
            </div>
          </div>

          <!-- Connected Hearts Row -->
          ${stats.connected_people.length > 0 ? `
            <div style="margin-bottom: 2rem;">
              <div class="section-header">
                <h3 class="section-title"><span>👥</span> Connected People</h3>
                <a href="#connections" class="section-link">Manage Connections &rarr;</a>
              </div>
              <div class="connected-hearts-list">
                ${stats.connected_people.map(p => `
                  <div class="connected-heart-chip" onclick="Views.viewUserProfile(${p.id})">
                    <div class="user-avatar" style="width: 28px; height: 28px; font-size: 0.75rem;">
                      ${p.profile_picture ? `<img src="${API.media.getAvatarUrl(p.profile_picture)}" class="user-avatar" style="width:28px;height:28px;">` : escapeHtml(p.name[0])}
                    </div>
                    <span style="font-size: 0.85rem; font-weight: 600;">${escapeHtml(p.name)}</span>
                    <span class="text-xs text-muted">@${escapeHtml(p.username)}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Recent Memories Shelf -->
          <div style="margin-bottom: 3rem;">
            <div class="section-header">
              <h3 class="section-title"><span>❤️</span> Recent Memories</h3>
              <a href="#memories" class="section-link">View Full Timeline &rarr;</a>
            </div>
            ${stats.recent_memories.length === 0 ? `
              <div style="text-align: center; padding: 3rem 1rem; background: var(--bg-surface); border: 1px dashed var(--border-strong); border-radius: var(--radius-lg);">
                <p style="margin-bottom: 1rem;">No memories added yet. Start your story today.</p>
                <button class="btn btn-primary" onclick="Views.openAddMemoryModal()">➕ Add Your First Memory</button>
              </div>
            ` : `
              <div class="memory-grid">
                ${stats.recent_memories.map(m => renderMemoryCard(m, true)).join('')}
              </div>
            `}
          </div>

          <!-- Recently Uploaded Shelf -->
          ${stats.recently_uploaded.length > 0 ? `
            <div style="margin-bottom: 3rem;">
              <div class="section-header">
                <h3 class="section-title"><span>⏳</span> Recently Uploaded</h3>
              </div>
              <div class="memory-grid">
                ${stats.recently_uploaded.map(m => renderMemoryCard(m, true)).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 3. Render Memory Card HTML
  const renderMemoryCard = (memory, isOwner = true) => {
    const isVideo = memory.media_type === 'video';
    const thumbUrl = memory.thumbnail_key 
      ? API.media.getThumbnailUrl(memory.thumbnail_key)
      : API.media.getMediaUrl(memory.storage_key);

    const privacyBadge = () => {
      if (!isOwner) return '';
      if (memory.privacy === 'private') {
        return `<span class="privacy-badge private">🔒 Private</span>`;
      } else if (memory.privacy === 'connections') {
        return `<span class="privacy-badge connections">👥 Connections</span>`;
      } else if (memory.privacy === 'selected') {
        const count = memory.permitted_users ? memory.permitted_users.length : 1;
        return `<span class="privacy-badge selected">👤 ${count} Selected</span>`;
      }
      return '';
    };

    return `
      <div class="memory-card" onclick="Views.openMemoryDetailModal(${memory.id})">
        <div class="memory-media-wrap">
          <img src="${thumbUrl}" alt="${escapeHtml(memory.title || 'Memory')}" class="memory-thumb" loading="lazy">
          ${isVideo ? `
            <div class="video-play-overlay">
              <div class="play-icon-circle">▶</div>
            </div>
          ` : ''}
          <div class="memory-badges-overlay">
            <span class="media-type-tag">${isVideo ? '🎥 Video' : '📷 Photo'}</span>
            ${privacyBadge()}
          </div>
        </div>

        <div class="memory-content">
          <div class="memory-meta">
            <span class="memory-meta-item">📅 ${formatDate(memory.memory_date)}</span>
            ${memory.location ? `<span class="memory-meta-item">📍 ${escapeHtml(memory.location)}</span>` : ''}
          </div>

          <h4 class="memory-title">${escapeHtml(memory.title || 'Untitled Memory')}</h4>
          ${memory.description ? `<p class="memory-desc">${escapeHtml(memory.description)}</p>` : ''}

          <div class="memory-footer">
            ${!isOwner && memory.owner ? `
              <div class="shared-owner-badge">
                <span>Shared by @${escapeHtml(memory.owner.username)}</span>
              </div>
            ` : `
              <span>Uploaded ${formatDate(memory.uploaded_at ? memory.uploaded_at.split(' ')[0] : '')}</span>
            `}
            <span style="font-weight: 600; color: var(--primary);">View Details &rarr;</span>
          </div>
        </div>
      </div>
    `;
  };

  // 4. Filter Bar Builder
  const renderFilterBar = (currentFilters, onApply) => {
    return `
      <div class="filter-bar">
        <div class="filter-controls">
          <!-- Type Filter -->
          <select id="filter-type" class="filter-select" onchange="${onApply}">
            <option value="all" ${currentFilters.type === 'all' ? 'selected' : ''}>All Media</option>
            <option value="photo" ${currentFilters.type === 'photo' ? 'selected' : ''}>📷 Photos Only</option>
            <option value="video" ${currentFilters.type === 'video' ? 'selected' : ''}>🎥 Videos Only</option>
          </select>

          <!-- Year Filter -->
          <input type="number" id="filter-year" class="filter-input" placeholder="Year (e.g. 2026)" 
                 value="${currentFilters.year || ''}" min="1900" max="2100" style="width: 130px;" onchange="${onApply}">

          <!-- Month Filter -->
          <select id="filter-month" class="filter-select" onchange="${onApply}">
            <option value="">Any Month</option>
            <option value="01" ${currentFilters.month === '01' ? 'selected' : ''}>January</option>
            <option value="02" ${currentFilters.month === '02' ? 'selected' : ''}>February</option>
            <option value="03" ${currentFilters.month === '03' ? 'selected' : ''}>March</option>
            <option value="04" ${currentFilters.month === '04' ? 'selected' : ''}>April</option>
            <option value="05" ${currentFilters.month === '05' ? 'selected' : ''}>May</option>
            <option value="06" ${currentFilters.month === '06' ? 'selected' : ''}>June</option>
            <option value="07" ${currentFilters.month === '07' ? 'selected' : ''}>July</option>
            <option value="08" ${currentFilters.month === '08' ? 'selected' : ''}>August</option>
            <option value="09" ${currentFilters.month === '09' ? 'selected' : ''}>September</option>
            <option value="10" ${currentFilters.month === '10' ? 'selected' : ''}>October</option>
            <option value="11" ${currentFilters.month === '11' ? 'selected' : ''}>November</option>
            <option value="12" ${currentFilters.month === '12' ? 'selected' : ''}>December</option>
          </select>

          <!-- Location Filter -->
          <input type="text" id="filter-location" class="filter-input" placeholder="📍 Location..." 
                 value="${escapeHtml(currentFilters.location || '')}" style="width: 140px;" onkeyup="if(event.key==='Enter')${onApply}">
        </div>

        <div class="flex items-center gap-2">
          <!-- Sorting -->
          <select id="filter-sort" class="filter-select" onchange="${onApply}">
            <option value="memory_desc" ${currentFilters.sort === 'memory_desc' ? 'selected' : ''}>📅 Memory Date (Newest)</option>
            <option value="memory_asc" ${currentFilters.sort === 'memory_asc' ? 'selected' : ''}>📅 Memory Date (Oldest)</option>
            <option value="uploaded_desc" ${currentFilters.sort === 'uploaded_desc' ? 'selected' : ''}>⏳ Uploaded Date (Recent)</option>
            <option value="uploaded_asc" ${currentFilters.sort === 'uploaded_asc' ? 'selected' : ''}>⏳ Uploaded Date (Oldest)</option>
          </select>

          <button class="btn btn-secondary text-sm" onclick="Views.resetFilters()" title="Reset Filters">
            ↺ Reset
          </button>
        </div>
      </div>
    `;
  };

  let activeFilters = { type: 'all', year: '', month: '', location: '', sort: 'memory_desc' };

  window.applyTimelineFilters = () => {
    activeFilters.type = document.getElementById('filter-type').value;
    activeFilters.year = document.getElementById('filter-year').value.trim();
    activeFilters.month = document.getElementById('filter-month').value;
    activeFilters.location = document.getElementById('filter-location').value.trim();
    activeFilters.sort = document.getElementById('filter-sort').value;
    Views.renderTimeline();
  };

  window.applyGalleryFilters = () => {
    activeFilters.year = document.getElementById('filter-year').value.trim();
    activeFilters.month = document.getElementById('filter-month').value;
    activeFilters.location = document.getElementById('filter-location').value.trim();
    activeFilters.sort = document.getElementById('filter-sort').value;
    const type = document.getElementById('filter-type') ? document.getElementById('filter-type').value : 'all';
    Views.renderGallery(type);
  };

  const resetFilters = () => {
    activeFilters = { type: 'all', year: '', month: '', location: '', sort: 'memory_desc' };
    const route = window.location.hash.replace('#', '');
    if (route === 'photos') Views.renderGallery('photo');
    else if (route === 'videos') Views.renderGallery('video');
    else Views.renderTimeline();
  };

  // 5. Render Chronological Timeline View
  const renderTimeline = async () => {
    appEl().innerHTML = `
      <div class="app-container">
        <div style="margin-bottom: 2rem;">
          <h1 class="font-serif">Memories Timeline</h1>
          <p>Chronological journey of your moments together across years and seasons.</p>
        </div>
        ${renderFilterBar(activeFilters, 'applyTimelineFilters()')}
        <div id="timeline-content" style="text-align: center; padding: 3rem 0;">
          <div class="brand-heart" style="font-size: 2rem;">❤️</div>
          <p>Loading timeline...</p>
        </div>
      </div>
    `;

    try {
      const res = await API.memories.getAll(activeFilters);
      const memories = res.memories || [];
      const contentEl = document.getElementById('timeline-content');

      if (memories.length === 0) {
        contentEl.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); border: 1px dashed var(--border-strong);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🍃</div>
            <h3 style="margin-bottom: 0.5rem;">No memories match your filter</h3>
            <p style="margin-bottom: 1.5rem;">Try adjusting the filter criteria or upload a new memory.</p>
            <button class="btn btn-primary" onclick="Views.openAddMemoryModal()">➕ Add Memory</button>
          </div>
        `;
        return;
      }

      // Group memories by Year
      const groupedByYear = {};
      memories.forEach(m => {
        const year = m.memory_date ? m.memory_date.split('-')[0] : 'Unknown';
        if (!groupedByYear[year]) groupedByYear[year] = [];
        groupedByYear[year].push(m);
      });

      const sortedYears = Object.keys(groupedByYear).sort((a, b) => {
        return activeFilters.sort === 'memory_asc' ? a.localeCompare(b) : b.localeCompare(a);
      });

      let timelineHtml = '<div class="timeline-wrapper">';
      sortedYears.forEach(year => {
        timelineHtml += `
          <div class="timeline-year-group">
            <div class="timeline-year-header">
              <span class="year-pill">${year}</span>
            </div>
        `;

        groupedByYear[year].forEach((m, idx) => {
          const side = idx % 2 === 0 ? 'left' : 'right';
          const thumbUrl = m.thumbnail_key ? API.media.getThumbnailUrl(m.thumbnail_key) : API.media.getMediaUrl(m.storage_key);

          timelineHtml += `
            <div class="timeline-entry ${side}">
              <div class="timeline-dot"></div>
              <div class="timeline-card" onclick="Views.openMemoryDetailModal(${m.id})">
                <div class="timeline-card-media">
                  <img src="${thumbUrl}" alt="${escapeHtml(m.title)}" loading="lazy">
                </div>
                <div class="flex items-center gap-2" style="font-size: 0.8rem; color: var(--text-soft); margin-bottom: 0.35rem;">
                  <span>📅 ${formatDate(m.memory_date)}</span>
                  ${m.location ? `<span>📍 ${escapeHtml(m.location)}</span>` : ''}
                </div>
                <h4 style="margin-bottom: 0.35rem;">${escapeHtml(m.title || 'Untitled Memory')}</h4>
                ${m.description ? `<p class="text-sm text-muted" style="margin-bottom: 0.5rem;">${escapeHtml(m.description)}</p>` : ''}
                <div class="flex items-center justify-between text-xs text-muted" style="border-top: 1px solid var(--border-subtle); padding-top: 0.5rem;">
                  <span>${m.media_type === 'video' ? '🎥 Video' : '📷 Photo'}</span>
                  <span style="color: var(--primary); font-weight: 600;">View &rarr;</span>
                </div>
              </div>
            </div>
          `;
        });

        timelineHtml += '</div>';
      });
      timelineHtml += '</div>';

      contentEl.outerHTML = timelineHtml;
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 6. Dedicated Gallery View ('photo' or 'video')
  const renderGallery = async (type = 'photo') => {
    activeFilters.type = type;
    const title = type === 'photo' ? 'My Photos' : 'My Videos';
    const subtitle = type === 'photo' 
      ? 'A private visual gallery of preserved photographs and treasured moments.' 
      : 'Moving memories, voices, and laughter kept safe in your vault.';

    appEl().innerHTML = `
      <div class="app-container">
        <div style="margin-bottom: 2rem;">
          <h1 class="font-serif">${title}</h1>
          <p>${subtitle}</p>
        </div>
        ${renderFilterBar(activeFilters, 'applyGalleryFilters()')}
        <div id="gallery-content" style="text-align: center; padding: 3rem 0;">
          <div class="brand-heart" style="font-size: 2rem;">❤️</div>
          <p>Loading your ${type}s...</p>
        </div>
      </div>
    `;

    try {
      const res = await API.memories.getAll(activeFilters);
      const memories = res.memories || [];
      const contentEl = document.getElementById('gallery-content');

      if (memories.length === 0) {
        contentEl.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); border: 1px dashed var(--border-strong);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">${type === 'photo' ? '📷' : '🎥'}</div>
            <h3 style="margin-bottom: 0.5rem;">No ${type}s found</h3>
            <p style="margin-bottom: 1.5rem;">Upload your first ${type} to start preserving your moments.</p>
            <button class="btn btn-primary" onclick="Views.openAddMemoryModal('${type}')">➕ Upload ${type === 'photo' ? 'Photo' : 'Video'}</button>
          </div>
        `;
        return;
      }

      contentEl.outerHTML = `
        <div class="memory-grid">
          ${memories.map(m => renderMemoryCard(m, true)).join('')}
        </div>
      `;
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 7. Shared With Me View
  const renderShared = async () => {
    appEl().innerHTML = `
      <div class="app-container">
        <div style="margin-bottom: 2rem;">
          <h1 class="font-serif">Shared With Me</h1>
          <p>Memories lovingly shared with you by your connected partner, friends, and family.</p>
        </div>
        <div id="shared-content" style="text-align: center; padding: 3rem 0;">
          <div class="brand-heart" style="font-size: 2rem;">❤️</div>
          <p>Loading shared memories...</p>
        </div>
      </div>
    `;

    try {
      const res = await API.shared.getAll();
      const memories = res.memories || [];
      const contentEl = document.getElementById('shared-content');

      if (memories.length === 0) {
        contentEl.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); border: 1px dashed var(--border-strong);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💌</div>
            <h3 style="margin-bottom: 0.5rem;">No shared memories yet</h3>
            <p style="margin-bottom: 1.5rem;">When connected loved ones choose to share a memory with you, it will appear here safely.</p>
            <button class="btn btn-secondary" onclick="Router.navigate('connections')">👥 Check Connections</button>
          </div>
        `;
        return;
      }

      contentEl.outerHTML = `
        <div class="memory-grid">
          ${memories.map(m => renderMemoryCard(m, false)).join('')}
        </div>
      `;
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 8. Connection Management View
  const renderConnections = async () => {
    appEl().innerHTML = `
      <div class="app-container">
        <div class="flex items-center justify-between" style="margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;">
          <div>
            <h1 class="font-serif">Connections & Loved Ones</h1>
            <p>Connect with your partner, family, or close friends. Connection does not automatically reveal all memories.</p>
          </div>
          <button class="btn btn-primary" onclick="Views.openSearchModal()">
            <span>🔍 Find Someone to Connect</span>
          </button>
        </div>

        <div class="tabs-container">
          <button class="tab-btn active" id="tab-btn-accepted" onclick="Views.switchConnTab('accepted')">Accepted Connections</button>
          <button class="tab-btn" id="tab-btn-received" onclick="Views.switchConnTab('received')">Requests Received</button>
          <button class="tab-btn" id="tab-btn-sent" onclick="Views.switchConnTab('sent')">Sent Requests</button>
        </div>

        <div id="conn-tab-content">
          <div style="text-align: center; padding: 3rem;">
            <div class="brand-heart" style="font-size: 2rem;">❤️</div>
            <p>Loading connections...</p>
          </div>
        </div>
      </div>
    `;

    Views.loadConnectionsData('accepted');
  };

  let cachedConnections = null;
  const loadConnectionsData = async (activeTab = 'accepted') => {
    try {
      cachedConnections = await API.connections.getAll();
      switchConnTab(activeTab);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const switchConnTab = (tab) => {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById(`tab-btn-${tab}`);
    if (btn) btn.classList.add('active');

    const content = document.getElementById('conn-tab-content');
    if (!cachedConnections) return;

    if (tab === 'accepted') {
      const list = cachedConnections.accepted || [];
      if (list.length === 0) {
        content.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); text-align: center; border: 1px dashed var(--border-strong);">
            <p style="margin-bottom: 1.5rem;">You haven't connected with anyone yet.</p>
            <button class="btn btn-primary" onclick="Views.openSearchModal()">🔍 Search for Loved Ones</button>
          </div>
        `;
        return;
      }
      content.innerHTML = `
        <div class="connection-list">
          ${list.map(c => `
            <div class="connection-card">
              <div class="connection-info">
                <div class="user-avatar" style="width: 44px; height: 44px; font-size: 1.2rem;">
                  ${c.user.profile_picture ? `<img src="${API.media.getAvatarUrl(c.user.profile_picture)}" class="user-avatar" style="width:44px;height:44px;">` : escapeHtml(c.user.name[0])}
                </div>
                <div class="connection-meta">
                  <h4>${escapeHtml(c.user.name)}</h4>
                  <p class="text-muted">@${escapeHtml(c.user.username)}</p>
                  <p class="text-xs text-soft">Connected ${formatDate(c.connected_at.split(' ')[0])}</p>
                </div>
              </div>
              <button class="btn btn-danger text-sm" onclick="Views.removeConnection(${c.connection_id}, '${escapeHtml(c.user.name)}')">
                Remove
              </button>
            </div>
          `).join('')}
        </div>
      `;
    } else if (tab === 'received') {
      const list = cachedConnections.received || [];
      if (list.length === 0) {
        content.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); text-align: center; border: 1px dashed var(--border-strong);">
            <p>No pending connection requests received.</p>
          </div>
        `;
        return;
      }
      content.innerHTML = `
        <div class="connection-list">
          ${list.map(c => `
            <div class="connection-card">
              <div class="connection-info">
                <div class="user-avatar" style="width: 44px; height: 44px; font-size: 1.2rem;">
                  ${c.requester.profile_picture ? `<img src="${API.media.getAvatarUrl(c.requester.profile_picture)}" class="user-avatar" style="width:44px;height:44px;">` : escapeHtml(c.requester.name[0])}
                </div>
                <div class="connection-meta">
                  <h4>${escapeHtml(c.requester.name)}</h4>
                  <p class="text-muted">@${escapeHtml(c.requester.username)}</p>
                  <p class="text-xs text-soft">Wants to connect with you ❤️</p>
                </div>
              </div>
              <div class="flex gap-2">
                <button class="btn btn-primary text-sm" onclick="Views.acceptConnection(${c.connection_id})">Accept</button>
                <button class="btn btn-secondary text-sm" onclick="Views.rejectConnection(${c.connection_id})">Decline</button>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } else if (tab === 'sent') {
      const list = cachedConnections.sent || [];
      if (list.length === 0) {
        content.innerHTML = `
          <div style="background: var(--bg-surface); padding: 3rem; border-radius: var(--radius-lg); text-align: center; border: 1px dashed var(--border-strong);">
            <p>No outgoing requests waiting for approval.</p>
          </div>
        `;
        return;
      }
      content.innerHTML = `
        <div class="connection-list">
          ${list.map(c => `
            <div class="connection-card">
              <div class="connection-info">
                <div class="user-avatar" style="width: 44px; height: 44px; font-size: 1.2rem;">
                  ${c.receiver.profile_picture ? `<img src="${API.media.getAvatarUrl(c.receiver.profile_picture)}" class="user-avatar" style="width:44px;height:44px;">` : escapeHtml(c.receiver.name[0])}
                </div>
                <div class="connection-meta">
                  <h4>${escapeHtml(c.receiver.name)}</h4>
                  <p class="text-muted">@${escapeHtml(c.receiver.username)}</p>
                  <p class="text-xs text-soft">Pending acceptance</p>
                </div>
              </div>
              <button class="btn btn-secondary text-sm" onclick="Views.cancelRequest(${c.connection_id})">Cancel Request</button>
            </div>
          `).join('')}
        </div>
      `;
    }
  };

  const acceptConnection = async (id) => {
    try {
      const res = await API.connections.accept(id);
      showToast(res.message);
      loadConnectionsData('accepted');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const rejectConnection = async (id) => {
    try {
      const res = await API.connections.reject(id);
      showToast(res.message);
      loadConnectionsData('received');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const cancelRequest = async (id) => {
    try {
      const res = await API.connections.cancel(id);
      showToast(res.message);
      loadConnectionsData('sent');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const removeConnection = async (id, name) => {
    if (!confirm(`Are you sure you want to remove connection with ${name}? They will immediately lose access to shared memories.`)) {
      return;
    }
    try {
      const res = await API.connections.remove(id);
      showToast(res.message);
      loadConnectionsData('accepted');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 9. Profile View
  const renderProfile = async () => {
    const user = Auth.getUser();
    appEl().innerHTML = `
      <div class="app-container" style="max-width: 680px;">
        <div style="margin-bottom: 2rem;">
          <h1 class="font-serif">My Profile</h1>
          <p>Personal profile details and memory statistics.</p>
        </div>

        <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); padding: 2rem; box-shadow: var(--shadow-sm); margin-bottom: 2rem;">
          <div class="flex items-center gap-4" style="margin-bottom: 2rem; flex-wrap: wrap;">
            <div class="user-avatar-lg">
              ${user.profile_picture ? `<img src="${API.media.getAvatarUrl(user.profile_picture)}" class="user-avatar-lg">` : escapeHtml(user.name[0])}
            </div>
            <div>
              <h2 style="margin-bottom: 0.25rem;">${escapeHtml(user.name)}</h2>
              <p class="text-muted" style="margin-bottom: 0.25rem;">@${escapeHtml(user.username)}</p>
              <p class="text-xs text-soft">Member since ${formatDate(user.created_at ? user.created_at.split(' ')[0] : '')}</p>
            </div>
          </div>

          <form id="profile-edit-form" onsubmit="Views.handleProfileUpdate(event)">
            <div class="form-group">
              <label class="form-label">Full Name</label>
              <input type="text" id="edit-name" class="form-input" value="${escapeHtml(user.name)}" required>
            </div>

            <div class="form-group">
              <label class="form-label">Username</label>
              <input type="text" id="edit-username" class="form-input" value="${escapeHtml(user.username)}" required>
            </div>

            <div class="form-group">
              <label class="form-label">Email Address (Private)</label>
              <input type="email" class="form-input" value="${escapeHtml(user.email || '')}" disabled style="background: var(--bg-surface-soft); cursor: not-allowed;">
              <small class="text-soft">Your email address is never exposed publicly to other users.</small>
            </div>

            <div class="form-group">
              <label class="form-label">About / Bio</label>
              <textarea id="edit-bio" class="form-textarea" placeholder="A line about yourself or what you cherish...">${escapeHtml(user.bio || '')}</textarea>
            </div>

            <div class="form-group">
              <label class="form-label">Update Profile Picture</label>
              <input type="file" id="edit-avatar" class="form-input" accept="image/*">
            </div>

            <button type="submit" class="btn btn-primary w-full" style="margin-top: 1rem;">
              <span>Save Profile Changes ❤️</span>
            </button>
          </form>
        </div>
      </div>
    `;
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    const name = document.getElementById('edit-name').value.trim();
    const username = document.getElementById('edit-username').value.trim();
    const bio = document.getElementById('edit-bio').value.trim();
    const avatarFile = document.getElementById('edit-avatar').files[0];

    const formData = new FormData();
    formData.append('name', name);
    formData.append('username', username);
    formData.append('bio', bio);
    if (avatarFile) {
      formData.append('profile_picture', avatarFile);
    }

    try {
      const res = await API.users.updateProfile(formData);
      Auth.setUser(res.user);
      showToast(res.message);
      renderProfile();
      updateHeaderUser();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 10. Add Memory Modal (5-Step Intuitive Workflow)
  let addMemorySelectedUsers = [];
  const openAddMemoryModal = async (preselectedType = 'photo') => {
    addMemorySelectedUsers = [];
    let connections = [];
    try {
      const res = await API.connections.getAll();
      connections = res.accepted || [];
    } catch (e) {}

    const today = new Date().toISOString().split('T')[0];

    const modalHtml = `
      <div id="add-memory-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('add-memory-modal')">
        <div class="modal-dialog modal-lg">
          <div class="modal-header">
            <h3 class="modal-title font-serif">Add to Memory Vault ❤️</h3>
            <button class="modal-close" onclick="Views.closeModal('add-memory-modal')">✕</button>
          </div>
          <div class="modal-body">
            <form id="add-memory-form" onsubmit="Views.handleAddMemorySubmit(event)">
              <!-- Step 1: Media Type -->
              <div style="margin-bottom: 1.5rem;">
                <label class="form-label" style="margin-bottom: 0.5rem; display: block;">Step 1: Choose Media Type</label>
                <div class="flex gap-4">
                  <label class="privacy-radio-card flex-1 ${preselectedType==='photo'?'selected':''}" id="type-opt-photo" onclick="Views.selectMediaType('photo')">
                    <input type="radio" name="media_type" value="photo" ${preselectedType==='photo'?'checked':''} style="display:none;">
                    <div style="font-size: 1.5rem;">📷</div>
                    <div>
                      <h4 style="font-size: 1rem;">Photo</h4>
                      <p class="text-xs text-muted">Cherished snapshots & portraits</p>
                    </div>
                  </label>
                  <label class="privacy-radio-card flex-1 ${preselectedType==='video'?'selected':''}" id="type-opt-video" onclick="Views.selectMediaType('video')">
                    <input type="radio" name="media_type" value="video" ${preselectedType==='video'?'checked':''} style="display:none;">
                    <div style="font-size: 1.5rem;">🎥</div>
                    <div>
                      <h4 style="font-size: 1rem;">Video</h4>
                      <p class="text-xs text-muted">Voices, laughter & moving clips</p>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Step 2: Upload File -->
              <div style="margin-bottom: 1.5rem;">
                <label class="form-label" style="margin-bottom: 0.5rem; display: block;">Step 2: Upload File</label>
                <div id="upload-dropzone" class="dropzone" onclick="document.getElementById('memory-file-input').click()">
                  <div class="dropzone-icon">☁️</div>
                  <h4 id="dropzone-text" style="margin-bottom: 0.25rem;">Click or drag file here</h4>
                  <p class="text-xs text-muted">Supports JPG, PNG, WebP, GIF, MP4, WebM (up to 100MB)</p>
                </div>
                <input type="file" id="memory-file-input" style="display: none;" onchange="Views.handleFilePreview(this)">
                <div id="file-preview-container" class="upload-preview-box" style="display: none; margin-top: 1rem;"></div>
              </div>

              <!-- Step 3: Enter Details -->
              <div style="margin-bottom: 1.5rem;">
                <label class="form-label" style="margin-bottom: 0.5rem; display: block;">Step 3: Enter Details</label>
                <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                  <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">Date of Memory *</label>
                    <input type="date" id="memory-date" class="form-input" value="${today}" required>
                    <small class="text-xs text-soft">When this moment actually took place</small>
                  </div>
                  <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">Location</label>
                    <input type="text" id="memory-location" class="form-input" placeholder="e.g. Bangalore, India">
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Title (Optional)</label>
                  <input type="text" id="memory-title" class="form-input" placeholder="e.g. First trip together ❤️">
                </div>

                <div class="form-group">
                  <label class="form-label">About this Memory / Story</label>
                  <textarea id="memory-description" class="form-textarea" placeholder="Write down what made this moment unforgettable..."></textarea>
                </div>
              </div>

              <!-- Step 4: Privacy Settings -->
              <div style="margin-bottom: 1.5rem;">
                <label class="form-label" style="margin-bottom: 0.5rem; display: block;">Step 4: Choose Privacy</label>
                <div class="privacy-options-grid">
                  <label class="privacy-radio-card selected" id="priv-opt-private" onclick="Views.selectPrivacy('private')">
                    <input type="radio" name="privacy" value="private" checked>
                    <div class="privacy-info">
                      <h4>🔒 Private</h4>
                      <p class="text-muted">Only you can see this memory. Completely hidden from everyone else.</p>
                    </div>
                  </label>

                  <label class="privacy-radio-card" id="priv-opt-connections" onclick="Views.selectPrivacy('connections')">
                    <input type="radio" name="privacy" value="connections">
                    <div class="privacy-info">
                      <h4>👥 Visible to Accepted Connections</h4>
                      <p class="text-muted">Can be viewed by people you have mutually accepted as connections.</p>
                    </div>
                  </label>

                  <label class="privacy-radio-card" id="priv-opt-selected" onclick="Views.selectPrivacy('selected')">
                    <input type="radio" name="privacy" value="selected">
                    <div class="privacy-info">
                      <h4>👤 Selected People Only</h4>
                      <p class="text-muted">Choose specifically which accepted connections can view this memory.</p>
                    </div>
                  </label>
                </div>

                <!-- Selective Users Box -->
                <div id="selected-users-wrapper" style="display: none; margin-top: 1rem;">
                  <label class="form-label" style="margin-bottom: 0.5rem; display: block;">Select Connected People:</label>
                  ${connections.length === 0 ? `
                    <p class="text-sm text-muted" style="padding: 0.75rem; background: var(--bg-surface-soft); border-radius: var(--radius-md);">
                      You don't have any accepted connections yet. Connect with someone first to share memories selectively.
                    </p>
                  ` : `
                    <div class="selected-users-box">
                      ${connections.map(c => `
                        <label class="selected-user-row">
                          <input type="checkbox" value="${c.user.id}" onchange="Views.toggleSelectedUser(${c.user.id})">
                          <div class="user-avatar" style="width: 26px; height: 26px; font-size: 0.7rem;">
                            ${escapeHtml(c.user.name[0])}
                          </div>
                          <span style="font-weight: 500; font-size: 0.9rem;">${escapeHtml(c.user.name)}</span>
                          <span class="text-xs text-soft">(@${escapeHtml(c.user.username)})</span>
                        </label>
                      `).join('')}
                    </div>
                  `}
                </div>
              </div>

              <!-- Step 5: Save -->
              <div class="modal-footer" style="padding: 1rem 0 0; background: transparent;">
                <button type="button" class="btn btn-secondary" onclick="Views.closeModal('add-memory-modal')">Cancel</button>
                <button type="submit" id="save-memory-btn" class="btn btn-primary">
                  <span>Save Memory ❤️</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  };

  const selectMediaType = (type) => {
    document.querySelectorAll('[name="media_type"]').forEach(r => r.checked = (r.value === type));
    document.getElementById('type-opt-photo').classList.toggle('selected', type === 'photo');
    document.getElementById('type-opt-video').classList.toggle('selected', type === 'video');
  };

  const selectPrivacy = (privacy) => {
    document.querySelectorAll('[name="privacy"]').forEach(r => r.checked = (r.value === privacy));
    document.getElementById('priv-opt-private').classList.toggle('selected', privacy === 'private');
    document.getElementById('priv-opt-connections').classList.toggle('selected', privacy === 'connections');
    document.getElementById('priv-opt-selected').classList.toggle('selected', privacy === 'selected');
    document.getElementById('selected-users-wrapper').style.display = (privacy === 'selected') ? 'block' : 'none';
  };

  const toggleSelectedUser = (userId) => {
    const idx = addMemorySelectedUsers.indexOf(userId);
    if (idx > -1) {
      addMemorySelectedUsers.splice(idx, 1);
    } else {
      addMemorySelectedUsers.push(userId);
    }
  };

  const handleFilePreview = (input) => {
    const file = input.files[0];
    if (!file) return;

    const previewBox = document.getElementById('file-preview-container');
    const dropzoneText = document.getElementById('dropzone-text');
    dropzoneText.innerText = `Selected: ${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)`;

    const isVideo = file.type.startsWith('video');
    const url = URL.createObjectURL(file);
    previewBox.style.display = 'flex';
    previewBox.innerHTML = isVideo 
      ? `<video src="${url}" controls style="max-height: 280px; width: 100%;"></video>`
      : `<img src="${url}" style="max-height: 280px; object-fit: contain;">`;
  };

  const handleAddMemorySubmit = async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('memory-file-input');
    if (!fileInput.files[0]) {
      showToast('Please select a photo or video to upload.', 'error');
      return;
    }

    const saveBtn = document.getElementById('save-memory-btn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span>Saving Memory... ❤️</span>';

    const mediaType = document.querySelector('[name="media_type"]:checked').value;
    const privacy = document.querySelector('[name="privacy"]:checked').value;
    const memoryDate = document.getElementById('memory-date').value;
    const location = document.getElementById('memory-location').value.trim();
    const title = document.getElementById('memory-title').value.trim();
    const description = document.getElementById('memory-description').value.trim();

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('media_type', mediaType);
    formData.append('privacy', privacy);
    formData.append('memory_date', memoryDate);
    formData.append('location', location);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('selected_users', JSON.stringify(addMemorySelectedUsers));

    try {
      const res = await API.memories.create(formData);
      showToast(res.message);
      closeModal('add-memory-modal');
      Router.refresh();
    } catch (err) {
      showToast(err.message, 'error');
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<span>Save Memory ❤️</span>';
    }
  };

  // 11. Memory Detail Modal (Full view with authorized media player)
  const openMemoryDetailModal = async (memoryId) => {
    try {
      const res = await API.memories.getById(memoryId);
      const memory = res.memory;
      const isOwner = memory.is_owner;
      const isVideo = memory.media_type === 'video';
      const mediaUrl = API.media.getMediaUrl(memory.storage_key);

      const modalHtml = `
        <div id="memory-detail-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('memory-detail-modal')">
          <div class="modal-dialog modal-lg">
            <div class="modal-header">
              <div class="flex items-center gap-2">
                <span class="media-type-tag">${isVideo ? '🎥 Video' : '📷 Photo'}</span>
                <span style="font-size: 0.85rem; color: var(--text-soft);">Memory of ${formatDate(memory.memory_date)}</span>
              </div>
              <button class="modal-close" onclick="Views.closeModal('memory-detail-modal')">✕</button>
            </div>

            <div class="modal-body" style="padding: 1.5rem;">
              <div class="media-detail-view">
                <!-- Media Player -->
                <div class="detail-media-container">
                  ${isVideo ? `
                    <video src="${mediaUrl}" controls autoplay style="max-height: 520px; width: 100%;"></video>
                  ` : `
                    <img src="${mediaUrl}" alt="${escapeHtml(memory.title)}" style="max-height: 520px; object-fit: contain;">
                  `}
                </div>

                <!-- Metadata -->
                <div>
                  <div class="detail-meta-header">
                    <div>
                      <h2 class="detail-title">${escapeHtml(memory.title || 'Untitled Memory')}</h2>
                      <div class="flex items-center gap-4 text-sm text-muted" style="flex-wrap: wrap;">
                        <span>📅 ${formatDate(memory.memory_date)}</span>
                        ${memory.location ? `<span>📍 ${escapeHtml(memory.location)}</span>` : ''}
                        <span>⏳ Uploaded ${formatDate(memory.uploaded_at ? memory.uploaded_at.split(' ')[0] : '')}</span>
                      </div>
                    </div>

                    ${isOwner ? `
                      <div class="flex gap-2">
                        <button class="btn btn-secondary text-sm" onclick="Views.openEditMemoryModal(${JSON.stringify(memory).replace(/"/g, '&quot;')})">
                          ✏️ Edit
                        </button>
                        <button class="btn btn-danger text-sm" onclick="Views.deleteMemory(${memory.id})">
                          🗑️ Delete
                        </button>
                      </div>
                    ` : `
                      <div class="shared-owner-badge" style="background: var(--bg-surface-soft); padding: 0.5rem 0.85rem; border-radius: var(--radius-full);">
                        <span>Shared by <strong>@${escapeHtml(memory.owner.username)}</strong></span>
                      </div>
                    `}
                  </div>

                  <!-- Story -->
                  ${memory.description ? `
                    <div style="margin-top: 1.25rem;">
                      <div class="detail-story-box">
                        ${escapeHtml(memory.description)}
                      </div>
                    </div>
                  ` : ''}

                  <!-- Privacy details for owner -->
                  ${isOwner ? `
                    <div style="margin-top: 1.25rem; padding: 0.85rem 1rem; background: var(--bg-surface-soft); border-radius: var(--radius-md); font-size: 0.85rem; display: flex; align-items: center; justify-content: space-between;">
                      <div>
                        <strong>Visibility:</strong>
                        <span style="text-transform: capitalize; margin-left: 0.25rem;">${memory.privacy}</span>
                        ${memory.privacy === 'selected' ? ` (${memory.permitted_users.length} connected people)` : ''}
                      </div>
                      ${memory.privacy === 'selected' ? `
                        <div class="flex gap-1">
                          ${memory.permitted_users.map(u => `<span class="privacy-badge selected">@${escapeHtml(u.username)}</span>`).join('')}
                        </div>
                      ` : ''}
                    </div>
                  ` : ''}
                </div>
              </div>
            </div>
          </div>
        </div>
      `;

      document.body.insertAdjacentHTML('beforeend', modalHtml);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 12. Edit Memory Modal
  const openEditMemoryModal = async (memory) => {
    closeModal('memory-detail-modal');

    let connections = [];
    try {
      const res = await API.connections.getAll();
      connections = res.accepted || [];
    } catch (e) {}

    const selectedIds = (memory.permitted_users || []).map(u => u.id);

    const modalHtml = `
      <div id="edit-memory-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('edit-memory-modal')">
        <div class="modal-dialog">
          <div class="modal-header">
            <h3 class="modal-title font-serif">Edit Memory Details</h3>
            <button class="modal-close" onclick="Views.closeModal('edit-memory-modal')">✕</button>
          </div>
          <div class="modal-body">
            <form onsubmit="Views.handleEditMemorySubmit(event, ${memory.id})">
              <div class="form-group">
                <label class="form-label">Title</label>
                <input type="text" id="edit-memory-title" class="form-input" value="${escapeHtml(memory.title || '')}">
              </div>

              <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="form-group">
                  <label class="form-label">Date of Memory</label>
                  <input type="date" id="edit-memory-date" class="form-input" value="${memory.memory_date}" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Location</label>
                  <input type="text" id="edit-memory-location" class="form-input" value="${escapeHtml(memory.location || '')}">
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Story / About</label>
                <textarea id="edit-memory-desc" class="form-textarea">${escapeHtml(memory.description || '')}</textarea>
              </div>

              <div class="form-group">
                <label class="form-label">Privacy Visibility</label>
                <select id="edit-memory-privacy" class="form-select" onchange="document.getElementById('edit-selected-users-wrap').style.display=(this.value==='selected'?'block':'none')">
                  <option value="private" ${memory.privacy==='private'?'selected':''}>🔒 Private (Only Me)</option>
                  <option value="connections" ${memory.privacy==='connections'?'selected':''}>👥 Accepted Connections</option>
                  <option value="selected" ${memory.privacy==='selected'?'selected':''}>👤 Selected People</option>
                </select>
              </div>

              <div id="edit-selected-users-wrap" style="display: ${memory.privacy==='selected'?'block':'none'}; margin-bottom: 1.5rem;">
                <label class="form-label">Choose People:</label>
                <div class="selected-users-box">
                  ${connections.map(c => `
                    <label class="selected-user-row">
                      <input type="checkbox" name="edit_selected_user" value="${c.user.id}" ${selectedIds.includes(c.user.id)?'checked':''}>
                      <span>${escapeHtml(c.user.name)} (@${escapeHtml(c.user.username)})</span>
                    </label>
                  `).join('')}
                </div>
              </div>

              <div class="modal-footer" style="padding: 1rem 0 0; background: transparent;">
                <button type="button" class="btn btn-secondary" onclick="Views.closeModal('edit-memory-modal')">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Changes ❤️</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  };

  const handleEditMemorySubmit = async (e, memoryId) => {
    e.preventDefault();
    const title = document.getElementById('edit-memory-title').value.trim();
    const memory_date = document.getElementById('edit-memory-date').value;
    const location = document.getElementById('edit-memory-location').value.trim();
    const description = document.getElementById('edit-memory-desc').value.trim();
    const privacy = document.getElementById('edit-memory-privacy').value;

    const selected_users = [];
    document.querySelectorAll('[name="edit_selected_user"]:checked').forEach(cb => {
      selected_users.push(parseInt(cb.value));
    });

    try {
      const res = await API.memories.update(memoryId, {
        title, memory_date, location, description, privacy, selected_users
      });
      showToast(res.message);
      closeModal('edit-memory-modal');
      Router.refresh();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const deleteMemory = async (memoryId) => {
    if (!confirm('Are you sure you want to permanently delete this memory from your vault?')) {
      return;
    }
    try {
      const res = await API.memories.delete(memoryId);
      showToast(res.message);
      closeModal('memory-detail-modal');
      Router.refresh();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 13. Search People Modal
  const openSearchModal = () => {
    const modalHtml = `
      <div id="search-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('search-modal')">
        <div class="modal-dialog">
          <div class="modal-header">
            <h3 class="modal-title font-serif">Search People 🔍</h3>
            <button class="modal-close" onclick="Views.closeModal('search-modal')">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <input type="text" id="user-search-input" class="form-input" placeholder="Search by name, @username, or registered email..." 
                     autofocus oninput="Views.handleUserSearch(this.value)">
              <small class="text-xs text-soft">Search by full name, @username, or registered email. Private details are never exposed.</small>
            </div>
            <div id="search-results-list" style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem;">
              <p class="text-center text-muted text-sm" style="padding: 1.5rem 0;">Type at least 2 characters to search for loved ones.</p>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  };

  let searchTimeout = null;
  const handleUserSearch = (query) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      const resultsEl = document.getElementById('search-results-list');
      const clean = (query || '').replace(/^@+/, '').trim();
      if (!clean || clean.length < 2) {
        resultsEl.innerHTML = '<p class="text-center text-muted text-sm" style="padding: 1.5rem 0;">Type at least 2 characters to search for loved ones.</p>';
        return;
      }

      resultsEl.innerHTML = '<p class="text-center text-muted text-sm">Searching...</p>';
      try {
        const res = await API.users.search(query.trim());
        const users = res.users || [];
        if (users.length === 0) {
          resultsEl.innerHTML = '<p class="text-center text-muted text-sm" style="padding: 1.5rem 0;">No people found. Make sure you entered the correct name, @username, or registered email.</p>';
          return;
        }

        resultsEl.innerHTML = users.map(u => `
          <div class="connection-card" style="padding: 0.85rem 1rem;">
            <div class="connection-info">
              <div class="user-avatar" style="width: 38px; height: 38px;">
                ${u.profile_picture ? `<img src="${API.media.getAvatarUrl(u.profile_picture)}" class="user-avatar" style="width:38px;height:38px;">` : escapeHtml(u.name[0])}
              </div>
              <div class="connection-meta">
                <h4 style="font-size: 0.95rem;">${escapeHtml(u.name)} ${u.connection_status === 'self' ? '<span class="text-xs text-muted" style="font-weight: normal;">(You)</span>' : ''}</h4>
                <p class="text-muted text-xs">@${escapeHtml(u.username)}</p>
              </div>
            </div>

            <div>
              ${u.connection_status === 'self' ? `
                <span class="privacy-badge" style="background: rgba(255,255,255,0.08); color: var(--text-color); border: 1px solid var(--border-color);">You</span>
              ` : u.connection_status === 'connected' ? `
                <span class="privacy-badge connections">Connected</span>
              ` : u.connection_status === 'pending_outgoing' ? `
                <span class="privacy-badge private">Pending</span>
              ` : u.connection_status === 'pending_incoming' ? `
                <button class="btn btn-primary text-xs" onclick="Views.acceptConnection(${u.connection_id}); Views.closeModal('search-modal');">Accept Request</button>
              ` : `
                <button class="btn btn-outline text-xs" onclick="Views.sendConnectionRequest(${u.id})">Send Request</button>
              `}
            </div>
          </div>
        `).join('');
      } catch (err) {
        resultsEl.innerHTML = `<p class="text-center text-danger text-sm">${escapeHtml(err.message)}</p>`;
      }
    }, 250);
  };

  const sendConnectionRequest = async (targetUserId) => {
    try {
      const res = await API.connections.sendRequest(targetUserId);
      showToast(res.message);
      closeModal('search-modal');
      Router.refresh();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 14. Notifications Dropdown / Modal
  const openNotificationsDropdown = async () => {
    try {
      const res = await API.notifications.getAll();
      const list = res.notifications || [];

      const modalHtml = `
        <div id="notifications-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('notifications-modal')">
          <div class="modal-dialog">
            <div class="modal-header">
              <h3 class="modal-title font-serif">Notifications 🔔</h3>
              <div class="flex items-center gap-2">
                ${list.some(n => !n.is_read) ? `<button class="btn btn-secondary text-xs" onclick="Views.markAllNotificationsRead()">Mark all as read</button>` : ''}
                <button class="modal-close" onclick="Views.closeModal('notifications-modal')">✕</button>
              </div>
            </div>
            <div class="modal-body" style="max-height: 400px;">
              ${list.length === 0 ? `
                <p class="text-center text-muted" style="padding: 2rem 0;">No notifications yet.</p>
              ` : `
                <div class="flex flex-col gap-2">
                  ${list.map(n => `
                    <div style="padding: 0.85rem 1rem; border-radius: var(--radius-md); background: ${n.is_read ? 'var(--bg-surface)' : 'var(--primary-soft)'}; border: 1px solid var(--border-subtle); display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem;">
                      <div>
                        <p style="font-size: 0.9rem; color: var(--text-main); font-weight: ${n.is_read ? 'normal' : '600'}; margin-bottom: 0.2rem;">
                          ${escapeHtml(n.message)}
                        </p>
                        <span class="text-xs text-soft">${formatDate(n.created_at.split(' ')[0])}</span>
                      </div>
                      ${!n.is_read ? `
                        <button class="btn btn-secondary text-xs" style="padding: 0.2rem 0.5rem;" onclick="Views.markNotificationRead(${n.id})">✓</button>
                      ` : ''}
                    </div>
                  `).join('')}
                </div>
              `}
            </div>
          </div>
        </div>
      `;

      document.body.insertAdjacentHTML('beforeend', modalHtml);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const markNotificationRead = async (id) => {
    await API.notifications.markRead(id);
    closeModal('notifications-modal');
    updateNotificationBadge();
  };

  const markAllNotificationsRead = async () => {
    await API.notifications.markAllRead();
    closeModal('notifications-modal');
    updateNotificationBadge();
  };

  const updateNotificationBadge = async () => {
    if (!Auth.isAuthenticated()) return;
    try {
      const res = await API.notifications.getAll();
      const badge = document.getElementById('notif-badge');
      if (badge) {
        badge.innerText = res.unread_count;
        badge.style.display = res.unread_count > 0 ? 'inline-block' : 'none';
      }
    } catch (e) {}
  };

  // 15. Authentication Modal (Login / Register / Forgot Password)
  const openAuthModal = (defaultTab = 'login') => {
    closeModal('auth-modal');

    const modalHtml = `
      <div id="auth-modal" class="modal-backdrop show" onclick="if(event.target===this)Views.closeModal('auth-modal')">
        <div class="modal-dialog" style="max-width: 480px;">
          <div class="modal-header">
            <h3 class="modal-title font-serif">Save Our Memory ❤️</h3>
            <button class="modal-close" onclick="Views.closeModal('auth-modal')">✕</button>
          </div>
          <div class="modal-body">
            <div class="tabs-container" style="margin-bottom: 1.5rem;">
              <button class="tab-btn ${defaultTab==='login'?'active':''}" id="auth-tab-login" onclick="Views.switchAuthTab('login')">Sign In</button>
              <button class="tab-btn ${defaultTab==='register'?'active':''}" id="auth-tab-register" onclick="Views.switchAuthTab('register')">Register</button>
              <button class="tab-btn ${defaultTab==='forgot'?'active':''}" id="auth-tab-forgot" onclick="Views.switchAuthTab('forgot')">Forgot Password</button>
            </div>

            <!-- Login Form -->
            <form id="form-login" style="display: ${defaultTab==='login'?'block':'none'};" onsubmit="Views.handleLoginSubmit(event)">
              <div class="form-group">
                <label class="form-label">Username or Email</label>
                <input type="text" id="login-id" class="form-input" placeholder="e.g. narayanan" required>
              </div>
              <div class="form-group">
                <div class="flex justify-between items-center">
                  <label class="form-label">Password</label>
                  <a href="javascript:void(0)" onclick="Views.switchAuthTab('forgot')" class="text-xs">Forgot password?</a>
                </div>
                <input type="password" id="login-password" class="form-input" placeholder="••••••••" required>
              </div>
              <button type="submit" class="btn btn-primary w-full" style="margin-top: 1rem;">
                <span>Sign In ❤️</span>
              </button>
            </form>

            <!-- Register Form -->
            <form id="form-register" style="display: ${defaultTab==='register'?'block':'none'};" onsubmit="Views.handleRegisterSubmit(event)">
              <div class="form-group">
                <label class="form-label">Full Name *</label>
                <input type="text" id="reg-name" class="form-input" placeholder="e.g. Narayanan Ram" required>
              </div>
              <div class="form-group">
                <label class="form-label">Unique Username *</label>
                <input type="text" id="reg-username" class="form-input" placeholder="e.g. narayanan" required>
                <small class="text-xs text-soft">Letters, numbers, and underscores only</small>
              </div>
              <div class="form-group">
                <label class="form-label">Email Address *</label>
                <input type="email" id="reg-email" class="form-input" placeholder="e.g. narayanan@example.com" required>
                <small class="text-xs text-soft">Kept strictly private</small>
              </div>
              <div class="form-group">
                <label class="form-label">Strong Password *</label>
                <input type="password" id="reg-password" class="form-input" placeholder="Min. 8 chars, uppercase, lowercase, number/symbol" required>
              </div>
              <div class="form-group">
                <label class="form-label">Confirm Password *</label>
                <input type="password" id="reg-confirm" class="form-input" placeholder="Repeat your password" required>
              </div>
              <button type="submit" class="btn btn-primary w-full" style="margin-top: 1rem;">
                <span>Create Memory Vault ❤️</span>
              </button>
            </form>

            <!-- Forgot Password Flow (3-Step: Email -> OTP Code -> New Password) -->
            <div id="form-forgot" style="display: ${defaultTab==='forgot'?'block':'none'};">
              <!-- Step 1: Enter Registered Email -->
              <div id="forgot-step-1">
                <p class="text-sm text-muted" style="margin-bottom: 1.25rem;">
                  Enter your registered email address. We will send a secure 6-digit one-time code to that email to verify your identity.
                </p>
                <form onsubmit="Views.handleForgotRequest(event)">
                  <div class="form-group">
                    <label class="form-label">Registered Email</label>
                    <input type="email" id="forgot-email" class="form-input" placeholder="e.g. narayanan@example.com" required>
                  </div>
                  <button type="submit" id="btn-request-code" class="btn btn-primary w-full">
                    <span>Send One-Time Code ✉️</span>
                  </button>
                  <div style="text-align: center; margin-top: 1rem;">
                    <a href="javascript:void(0)" onclick="Views.switchAuthTab('login')" class="text-xs text-muted">← Back to Sign In</a>
                  </div>
                </form>
              </div>

              <!-- Step 2: Enter One-Time Code -->
              <div id="forgot-step-2" style="display: none;">
                <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-bottom: 1.25rem;">
                  <p class="text-sm" style="margin: 0; color: var(--text-main);">
                    ✉️ We sent a 6-digit one-time code to: <br><strong id="forgot-sent-email" style="color: var(--primary);"></strong>
                  </p>
                  <p class="text-xs text-muted" style="margin: 0.35rem 0 0;">Check your inbox & spam folder. Code expires in 15 minutes.</p>
                </div>

                <div id="dev-code-banner" style="display: none; background: var(--accent-gold-soft); border: 1px dashed var(--accent-gold); padding: 0.85rem 1rem; border-radius: var(--radius-md); margin-bottom: 1.25rem;">
                  <div style="font-size: 0.8rem; font-weight: 600; color: var(--accent-gold); margin-bottom: 0.35rem;">
                    🔑 Verification Code:
                  </div>
                  <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">
                    <strong id="dev-code-text" style="font-size: 1.4rem; letter-spacing: 5px; color: var(--primary); font-family: monospace;"></strong>
                    <button type="button" class="btn btn-secondary text-xs" onclick="document.getElementById('reset-code').value=document.getElementById('dev-code-text').innerText">Click to Fill</button>
                  </div>
                  <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem;">
                    (SMTP email is not set up in .env yet. Use this code to proceed).
                  </div>
                </div>

                <form onsubmit="Views.handleVerifyCodeSubmit(event)">
                  <div class="form-group">
                    <label class="form-label">6-Digit One-Time Code</label>
                    <input type="text" id="reset-code" class="form-input" placeholder="• • • • • •" maxlength="6" inputmode="numeric" required style="letter-spacing: 6px; font-size: 1.25rem; font-weight: bold; text-align: center;">
                  </div>
                  <button type="submit" id="btn-verify-code" class="btn btn-primary w-full">
                    <span>Verify Code 🔒</span>
                  </button>
                  <div class="flex items-center justify-between" style="margin-top: 1rem;">
                    <a href="javascript:void(0)" onclick="Views.goToForgotStep(1)" class="text-xs text-muted">← Change Email</a>
                    <a href="javascript:void(0)" onclick="Views.handleResendCode()" class="text-xs" style="color: var(--primary); font-weight: 600;">Resend Code</a>
                  </div>
                </form>
              </div>

              <!-- Step 3: Create New Password -->
              <div id="forgot-step-3" style="display: none;">
                <div style="background: rgba(46, 125, 50, 0.1); border: 1px solid rgba(46, 125, 50, 0.3); border-radius: var(--radius-md); padding: 0.75rem 1rem; margin-bottom: 1.25rem;">
                  <p class="text-sm" style="margin: 0; color: #2e7d32; font-weight: 600;">
                    ✅ Code verified! Create your new password below.
                  </p>
                </div>

                <form onsubmit="Views.handleResetSubmit(event)">
                  <div class="form-group">
                    <label class="form-label">New Password</label>
                    <input type="password" id="reset-new-password" class="form-input" placeholder="Min 8 chars, 1 uppercase, 1 lowercase, 1 number" required>
                  </div>
                  <div class="form-group">
                    <label class="form-label">Confirm New Password</label>
                    <input type="password" id="reset-confirm-password" class="form-input" placeholder="Repeat new password" required>
                  </div>
                  <button type="submit" id="btn-save-new-password" class="btn btn-primary w-full" style="margin-top: 0.5rem;">
                    <span>Set New Password & Sign In ❤️</span>
                  </button>
                </form>
              </div>
            </div>

            <!-- Demo Quick Logins for Evaluator -->
            <div class="demo-accounts-bar">
              <p style="font-size: 0.8rem; font-weight: 600; color: var(--accent-gold);">
                ⚡ Quick 1-Click Demo Accounts
              </p>
              <div class="demo-accounts-buttons">
                <button class="demo-btn" onclick="Views.quickLogin('narayanan', 'LoveStory2026!')">Narayanan</button>
                <button class="demo-btn" onclick="Views.quickLogin('anumaria', 'LoveStory2026!')">Anu Maria</button>
                <button class="demo-btn" onclick="Views.quickLogin('sid', 'LoveStory2026!')">Siddharth</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  };

  const switchAuthTab = (tab) => {
    document.getElementById('auth-tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('auth-tab-register').classList.toggle('active', tab === 'register');
    document.getElementById('auth-tab-forgot').classList.toggle('active', tab === 'forgot');

    document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
    document.getElementById('form-forgot').style.display = tab === 'forgot' ? 'block' : 'none';

    if (tab === 'forgot') {
      goToForgotStep(1);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    const login = document.getElementById('login-id').value.trim();
    const password = document.getElementById('login-password').value;

    try {
      const res = await API.auth.login({ login, password });
      Auth.setSession(res.token, res.user);
      showToast(res.message);
      closeModal('auth-modal');
      Router.navigate('home');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm_password = document.getElementById('reg-confirm').value;

    try {
      const res = await API.auth.register({ name, username, email, password, confirm_password });
      Auth.setSession(res.token, res.user);
      showToast(res.message);
      closeModal('auth-modal');
      Router.navigate('home');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  let pendingForgotEmail = '';
  let verifiedResetCode = '';

  const goToForgotStep = (step) => {
    const s1 = document.getElementById('forgot-step-1');
    const s2 = document.getElementById('forgot-step-2');
    const s3 = document.getElementById('forgot-step-3');
    if (s1) s1.style.display = step === 1 ? 'block' : 'none';
    if (s2) s2.style.display = step === 2 ? 'block' : 'none';
    if (s3) s3.style.display = step === 3 ? 'block' : 'none';
  };

  const handleForgotRequest = async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value.trim();
    pendingForgotEmail = email;

    const btn = document.getElementById('btn-request-code');
    btn.disabled = true;
    btn.innerText = 'Sending One-Time Code...';

    try {
      const res = await API.auth.forgotPassword(email);
      showToast(res.message);

      const sentEmailEl = document.getElementById('forgot-sent-email');
      if (sentEmailEl) sentEmailEl.innerText = email;

      goToForgotStep(2);

      const devBanner = document.getElementById('dev-code-banner');
      const codeToShow = res.verification_code || res.dev_verification_code;
      if (codeToShow && devBanner) {
        devBanner.style.display = 'block';
        document.getElementById('dev-code-text').innerText = codeToShow;
      } else if (devBanner) {
        devBanner.style.display = 'none';
      }

      const codeInput = document.getElementById('reset-code');
      if (codeInput) {
        codeInput.value = '';
        setTimeout(() => codeInput.focus(), 150);
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerText = 'Send One-Time Code ✉️';
    }
  };

  const handleResendCode = async () => {
    if (!pendingForgotEmail) return;
    try {
      const res = await API.auth.forgotPassword(pendingForgotEmail);
      showToast('A new one-time code has been sent!');
      const devBanner = document.getElementById('dev-code-banner');
      const codeToShow = res.verification_code || res.dev_verification_code;
      if (codeToShow && devBanner) {
        devBanner.style.display = 'block';
        document.getElementById('dev-code-text').innerText = codeToShow;
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleVerifyCodeSubmit = async (e) => {
    e.preventDefault();
    const code = document.getElementById('reset-code').value.trim();
    if (code.length !== 6) {
      showToast('Please enter the full 6-digit code.', 'error');
      return;
    }

    const btn = document.getElementById('btn-verify-code');
    btn.disabled = true;
    btn.innerText = 'Verifying Code...';

    try {
      const res = await API.auth.verifyResetCode({
        email: pendingForgotEmail,
        code
      });
      verifiedResetCode = code;
      showToast(res.message || 'Code verified successfully!');
      goToForgotStep(3);
      setTimeout(() => {
        const pwdInput = document.getElementById('reset-new-password');
        if (pwdInput) pwdInput.focus();
      }, 150);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerText = 'Verify Code 🔒';
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    const password = document.getElementById('reset-new-password').value;
    const confirm_password = document.getElementById('reset-confirm-password').value;

    if (!verifiedResetCode) {
      showToast('Please enter and verify your one-time code first.', 'error');
      goToForgotStep(2);
      return;
    }

    const btn = document.getElementById('btn-save-new-password');
    btn.disabled = true;
    btn.innerText = 'Saving New Password...';

    try {
      const res = await API.auth.resetPassword({
        email: pendingForgotEmail,
        code: verifiedResetCode,
        password,
        confirm_password
      });
      showToast(res.message);
      goToForgotStep(1);
      verifiedResetCode = '';
      switchAuthTab('login');
      document.getElementById('login-id').value = pendingForgotEmail;
      document.getElementById('login-password').focus();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerText = 'Set New Password & Sign In ❤️';
    }
  };

  const quickLogin = async (login, password) => {
    try {
      const res = await API.auth.login({ login, password });
      Auth.setSession(res.token, res.user);
      showToast(res.message);
      closeModal('auth-modal');
      Router.navigate('home');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const closeModal = (modalId) => {
    const el = document.getElementById(modalId);
    if (el) el.remove();
  };

  const updateHeaderUser = () => {
    const user = Auth.getUser();
    const avatarEl = document.getElementById('header-user-avatar');
    const nameEl = document.getElementById('header-user-name');
    if (!avatarEl || !nameEl) return;

    if (user) {
      nameEl.innerText = user.name.split(' ')[0];
      if (user.profile_picture) {
        avatarEl.innerHTML = `<img src="${API.media.getAvatarUrl(user.profile_picture)}" class="user-avatar">`;
      } else {
        avatarEl.innerText = user.name[0];
      }
    }
  };

  return {
    showToast,
    renderUnauthenticatedState,
    renderDashboard,
    renderTimeline,
    renderGallery,
    renderShared,
    renderConnections,
    renderProfile,
    loadConnectionsData,
    switchConnTab,
    acceptConnection,
    rejectConnection,
    cancelRequest,
    removeConnection,
    openAddMemoryModal,
    selectMediaType,
    selectPrivacy,
    toggleSelectedUser,
    handleFilePreview,
    handleAddMemorySubmit,
    openMemoryDetailModal,
    openEditMemoryModal,
    handleEditMemorySubmit,
    deleteMemory,
    openSearchModal,
    handleUserSearch,
    sendConnectionRequest,
    openNotificationsDropdown,
    markNotificationRead,
    markAllNotificationsRead,
    updateNotificationBadge,
    openAuthModal,
    switchAuthTab,
    handleLoginSubmit,
    handleRegisterSubmit,
    handleForgotRequest,
    handleVerifyCodeSubmit,
    handleResendCode,
    goToForgotStep,
    handleResetSubmit,
    quickLogin,
    closeModal,
    handleProfileUpdate,
    updateHeaderUser,
    resetFilters
  };
})();
