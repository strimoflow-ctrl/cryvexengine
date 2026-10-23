// Bideo Creator Studio & YouTube Automation Client Logic

document.addEventListener('DOMContentLoaded', () => {
  // -----------------------------------------------------------
  // DOM Elements
  // -----------------------------------------------------------
  const authScreen = document.getElementById('authScreen');
  const appScreen = document.getElementById('appScreen');
  const loginForm = document.getElementById('loginForm');
  const loginBtn = document.getElementById('loginBtn');
  const cancelLoginBtn = document.getElementById('cancelLoginBtn');
  const authError = document.getElementById('authError');
  const logoutBtn = document.getElementById('logoutBtn');

  // Tabs
  const tabAutomationBtn = document.getElementById('tabAutomationBtn');
  const tabSingleLinkBtn = document.getElementById('tabSingleLinkBtn');
  const tabUploadBtn = document.getElementById('tabUploadBtn');
  const automationSection = document.getElementById('automationSection');
  const singleLinkSection = document.getElementById('singleLinkSection');
  const uploadSection = document.getElementById('uploadSection');

  // Single Link Form Elements
  const singleLinkForm = document.getElementById('singleLinkForm');
  const singleVideoUrl = document.getElementById('singleVideoUrl');
  const singleBideoSelect = document.getElementById('singleBideoSelect');
  const singleCategorySelect = document.getElementById('singleCategorySelect');
  const singleCustomTitle = document.getElementById('singleCustomTitle');
  const singleCustomDesc = document.getElementById('singleCustomDesc');
  const singleLinkSubmitBtn = document.getElementById('singleLinkSubmitBtn');
  const singleLinkAlert = document.getElementById('singleLinkAlert');
  const singleUploadStatusBox = document.getElementById('singleUploadStatusBox');

  // Nav Profile & Account Dropdown
  const accountMenuBtn = document.getElementById('accountMenuBtn');
  const accountDropdownMenu = document.getElementById('accountDropdownMenu');
  const accountsListDropdown = document.getElementById('accountsListDropdown');
  const addAccountBtn = document.getElementById('addAccountBtn');
  const navAvatar = document.getElementById('navAvatar');
  const navName = document.getElementById('navName');
  const navHandle = document.getElementById('navHandle');

  // Sidebar Profile Elements
  const sideAvatar = document.getElementById('sideAvatar');
  const sideChannelName = document.getElementById('sideChannelName');
  const sideHandle = document.getElementById('sideHandle');
  const sideFollowers = document.getElementById('sideFollowers');

  // Automation Hub Elements
  const statActivePairings = document.getElementById('statActivePairings');
  const statTotalPosted = document.getElementById('statTotalPosted');
  const syncAllBtn = document.getElementById('syncAllBtn');
  const pairingForm = document.getElementById('pairingForm');
  const ytChannelInput = document.getElementById('ytChannelInput');
  const pairingBideoSelect = document.getElementById('pairingBideoSelect');
  const pairingCategorySelect = document.getElementById('pairingCategorySelect');
  const savePairingBtn = document.getElementById('savePairingBtn');
  const pairingAlert = document.getElementById('pairingAlert');
  const pairingsContainer = document.getElementById('pairingsContainer');
  const refreshPairingsBtn = document.getElementById('refreshPairingsBtn');
  const logsList = document.getElementById('logsList');
  const refreshLogsBtn = document.getElementById('refreshLogsBtn');

  // Upload Form Elements
  const uploadForm = document.getElementById('uploadForm');
  const videoDropzone = document.getElementById('videoDropzone');
  const videoFileInput = document.getElementById('videoFileInput');
  const dropzoneText = document.getElementById('dropzoneText');
  const dropzoneSubtext = document.getElementById('dropzoneSubtext');
  const videoTitle = document.getElementById('videoTitle');
  const videoDescription = document.getElementById('videoDescription');
  const categorySelect = document.getElementById('categorySelect');
  const uploadTypeSelect = document.getElementById('uploadTypeSelect');
  const thumbFileInput = document.getElementById('thumbFileInput');
  const submitUploadBtn = document.getElementById('submitUploadBtn');
  const uploadAlert = document.getElementById('uploadAlert');

  // Video Preview Elements
  const videoPreviewContainer = document.getElementById('videoPreviewContainer');
  const videoPreview = document.getElementById('videoPreview');
  const metaDuration = document.getElementById('metaDuration');
  const metaDimensions = document.getElementById('metaDimensions');
  const metaTypeBadge = document.getElementById('metaTypeBadge');

  // Progress Elements
  const uploadProgressBox = document.getElementById('uploadProgressBox');
  const progressStatusText = document.getElementById('progressStatusText');
  const progressPercent = document.getElementById('progressPercent');
  const progressBarFill = document.getElementById('progressBarFill');

  // Recent Uploads Container
  const recentUploadsList = document.getElementById('recentUploadsList');

  // State
  let savedAccounts = [];
  let currentActiveAccount = null;
  let allCategories = [];
  let selectedVideoFile = null;

  // -----------------------------------------------------------
  // Tab Switching
  // -----------------------------------------------------------
  function switchTab(tab) {
    tabAutomationBtn.classList.toggle('active', tab === 'automation');
    if (tabSingleLinkBtn) tabSingleLinkBtn.classList.toggle('active', tab === 'single');
    tabUploadBtn.classList.toggle('active', tab === 'upload');

    automationSection.classList.toggle('hidden', tab !== 'automation');
    if (singleLinkSection) singleLinkSection.classList.toggle('hidden', tab !== 'single');
    uploadSection.classList.toggle('hidden', tab !== 'upload');
  }

  tabAutomationBtn.addEventListener('click', () => switchTab('automation'));
  if (tabSingleLinkBtn) tabSingleLinkBtn.addEventListener('click', () => switchTab('single'));
  tabUploadBtn.addEventListener('click', () => switchTab('upload'));

  // -----------------------------------------------------------
  // Multi-Account Switcher Dropdown
  // -----------------------------------------------------------
  accountMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    accountDropdownMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', () => {
    accountDropdownMenu.classList.add('hidden');
  });

  accountDropdownMenu.addEventListener('click', (e) => {
    e.stopPropagation();
  });

  addAccountBtn.addEventListener('click', () => {
    accountDropdownMenu.classList.add('hidden');
    cancelLoginBtn.classList.remove('hidden');
    authScreen.classList.remove('hidden');
    appScreen.classList.add('hidden');
  });

  cancelLoginBtn.addEventListener('click', () => {
    if (currentActiveAccount) {
      authScreen.classList.add('hidden');
      appScreen.classList.remove('hidden');
    }
  });

  // -----------------------------------------------------------
  // YouTube Cloud Cookies Modal Logic
  // -----------------------------------------------------------
  const openCookiesModalBtn = document.getElementById('openCookiesModalBtn');
  const closeCookiesModalBtn = document.getElementById('closeCookiesModalBtn');
  const cookiesModal = document.getElementById('cookiesModal');
  const cookiesForm = document.getElementById('cookiesForm');
  const cookiesTextInput = document.getElementById('cookiesTextInput');
  const cookiesAlert = document.getElementById('cookiesAlert');
  const cookiesStatusText = document.getElementById('cookiesStatusText');
  const saveCookiesBtn = document.getElementById('saveCookiesBtn');

  // In-page cookies elements
  const cardCookiesStatusText = document.getElementById('cardCookiesStatusText');
  const cardCookiesAlert = document.getElementById('cardCookiesAlert');
  const cardCookiesInput = document.getElementById('cardCookiesInput');
  const cardSaveCookiesBtn = document.getElementById('cardSaveCookiesBtn');

  async function checkCookiesStatus() {
    try {
      const res = await fetch('/api/cookies_status');
      const data = await res.json();
      const statusHtml = data.has_cookies
        ? `<span style="color:#34D399;">🟢 Active (${data.size_bytes}B)</span>`
        : `<span style="color:#EF4444;">🔴 Missing</span>`;

      if (cookiesStatusText) cookiesStatusText.innerHTML = statusHtml;
      if (cardCookiesStatusText) cardCookiesStatusText.innerHTML = statusHtml;
    } catch (e) {
      if (cookiesStatusText) cookiesStatusText.textContent = 'Unknown';
      if (cardCookiesStatusText) cardCookiesStatusText.textContent = 'Unknown';
    }
  }

  // Check immediately on load
  checkCookiesStatus();

  if (openCookiesModalBtn) {
    openCookiesModalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (cookiesModal) {
        cookiesModal.classList.remove('hidden');
        checkCookiesStatus();
      }
    });
  }

  if (closeCookiesModalBtn) {
    closeCookiesModalBtn.addEventListener('click', () => {
      if (cookiesModal) cookiesModal.classList.add('hidden');
    });
  }

  async function handleSaveCookies(text, alertEl, btnEl) {
    if (!text) {
      alertEl.textContent = 'Kripya cookies.txt ka text yahan paste karein.';
      alertEl.className = 'alert-box alert-error';
      alertEl.classList.remove('hidden');
      return;
    }

    const btnText = btnEl.querySelector('.btn-text');
    const spinner = btnEl.querySelector('.spinner');
    btnText.textContent = 'Saving...';
    if (spinner) spinner.classList.remove('hidden');
    btnEl.disabled = true;

    try {
      const res = await fetch('/api/save_cookies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cookies_text: text })
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || 'Failed to save');

      alertEl.textContent = data.message;
      alertEl.className = 'alert-box alert-success';
      alertEl.classList.remove('hidden');
      checkCookiesStatus();

      if (cookiesModal && !cookiesModal.classList.contains('hidden')) {
        setTimeout(() => { cookiesModal.classList.add('hidden'); }, 1800);
      }
    } catch (err) {
      alertEl.textContent = err.message;
      alertEl.className = 'alert-box alert-error';
      alertEl.classList.remove('hidden');
    } finally {
      btnText.textContent = '💾 Save Cookies to Botkeep';
      if (spinner) spinner.classList.add('hidden');
      btnEl.disabled = false;
    }
  }

  if (cookiesForm) {
    cookiesForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSaveCookies(cookiesTextInput.value.trim(), cookiesAlert, saveCookiesBtn);
    });
  }

  if (cardSaveCookiesBtn) {
    cardSaveCookiesBtn.addEventListener('click', (e) => {
      e.preventDefault();
      handleSaveCookies(cardCookiesInput.value.trim(), cardCookiesAlert, cardSaveCookiesBtn);
    });
  }

  logoutBtn.addEventListener('click', async () => {
    accountDropdownMenu.classList.add('hidden');
    if (!currentActiveAccount) return;

    const confirmLogout = confirm(`Kya aap '${currentActiveAccount.name || 'channel'}' ko disconnect karna chahte hain?`);
    if (confirmLogout) {
      await fetch(`/api/accounts/${currentActiveAccount._id}`, { method: 'DELETE' });
      localStorage.removeItem('bideo_token');
      localStorage.removeItem('bideo_user');
      initApp();
    }
  });

  // -----------------------------------------------------------
  // Initial Auth & Account Loading
  // -----------------------------------------------------------
  async function initApp() {
    await loadAccounts();

    if (savedAccounts.length > 0) {
      // Pick active account from localStorage or first in list
      const activeId = localStorage.getItem('bideo_active_user_id');
      const found = savedAccounts.find(a => a._id === activeId);
      setActiveAccount(found || savedAccounts[0]);

      authScreen.classList.add('hidden');
      appScreen.classList.remove('hidden');

      loadCategories();
      loadPairings();
      loadLogs();

      // Start periodic background log polling (every 15s)
      setInterval(() => {
        loadLogs(true);
        loadPairings(true);
      }, 15000);

    } else {
      cancelLoginBtn.classList.add('hidden');
      authScreen.classList.remove('hidden');
      appScreen.classList.add('hidden');
    }
  }

  async function loadAccounts() {
    try {
      const res = await fetch('/api/accounts');
      const data = await res.json();
      if (data.success && data.accounts) {
        savedAccounts = data.accounts;
        renderAccountDropdown();
        populatePairingAccountSelect();
      }
    } catch (e) {
      console.warn('Could not load accounts from Firebase:', e);
    }
  }

  function setActiveAccount(account) {
    currentActiveAccount = account;
    localStorage.setItem('bideo_active_user_id', account._id);
    localStorage.setItem('bideo_token', account.token);
    localStorage.setItem('bideo_user', JSON.stringify(account));

    renderUser(account);
    renderAccountDropdown();
  }

  function renderUser(user) {
    const avatarUrl = user.avatar || 'https://via.placeholder.com/80.png?text=User';
    const name = user.name || 'My Channel';
    const handle = user.channelName ? `@${user.channelName}` : `@user_${user._id ? user._id.slice(-4) : 'bideo'}`;
    const followers = user.followersCount !== undefined ? user.followersCount : 0;

    navAvatar.src = avatarUrl;
    navName.textContent = name;
    navHandle.textContent = handle;

    sideAvatar.src = avatarUrl;
    sideChannelName.textContent = name;
    sideHandle.textContent = handle;
    sideFollowers.textContent = followers;
  }

  function renderAccountDropdown() {
    accountsListDropdown.innerHTML = '';
    savedAccounts.forEach(acc => {
      const btn = document.createElement('button');
      btn.className = `account-item-btn ${currentActiveAccount && currentActiveAccount._id === acc._id ? 'active-acc' : ''}`;

      const avatar = acc.avatar || 'https://via.placeholder.com/30.png?text=B';
      const name = acc.name || 'Channel';
      const handle = acc.channelName ? `@${acc.channelName}` : (acc.phone || '');

      btn.innerHTML = `
        <img src="${avatar}" class="channel-avatar" style="width:28px;height:28px;">
        <div class="channel-info">
          <span class="channel-name" style="font-size:0.8rem;">${name}</span>
          <span class="channel-handle" style="font-size:0.68rem;">${handle}</span>
        </div>
      `;

      btn.addEventListener('click', () => {
        setActiveAccount(acc);
        accountDropdownMenu.classList.add('hidden');
      });

      accountsListDropdown.appendChild(btn);
    });
  }

  function populatePairingAccountSelect() {
    if (pairingBideoSelect) pairingBideoSelect.innerHTML = '<option value="">-- Target Bideo Account Chunein --</option>';
    if (singleBideoSelect) singleBideoSelect.innerHTML = '<option value="">-- Target Bideo Account Chunein --</option>';
    const batchSelect = document.getElementById('batchBideoAccountSelect');
    if (batchSelect) batchSelect.innerHTML = '<option value="">Select Bideo Account...</option>';

    savedAccounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc._id || acc.id;
      opt.textContent = `${acc.name || 'Channel'} (${acc.channelName ? '@' + acc.channelName : acc.phone})`;
      if (currentActiveAccount && (acc._id === currentActiveAccount._id || acc.id === currentActiveAccount.id)) {
        opt.selected = true;
      }
      if (pairingBideoSelect) pairingBideoSelect.appendChild(opt);
      if (singleBideoSelect) singleBideoSelect.appendChild(opt.cloneNode(true));
      if (batchSelect) batchSelect.appendChild(opt.cloneNode(true));
    });
  }

  // -----------------------------------------------------------
  // Login Handler (Saves to Firebase & Supports Multi-Account)
  // -----------------------------------------------------------
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authError.classList.add('hidden');

    const loginVal = document.getElementById('loginInput').value.trim();
    const password = document.getElementById('passwordInput').value;

    const btnText = loginBtn.querySelector('.btn-text');
    const spinner = loginBtn.querySelector('.spinner');

    btnText.textContent = 'Connecting...';
    spinner.classList.remove('hidden');
    loginBtn.disabled = true;

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: loginVal, password })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Login failed. Please check credentials.');
      }

      // Add to saved accounts
      const user = data.user;
      user.token = data.token;
      user.phone = loginVal;

      const existingIdx = savedAccounts.findIndex(a => a._id === user._id);
      if (existingIdx >= 0) {
        savedAccounts[existingIdx] = user;
      } else {
        savedAccounts.push(user);
      }

      setActiveAccount(user);
      populatePairingAccountSelect();

      authScreen.classList.add('hidden');
      appScreen.classList.remove('hidden');

      loadCategories();
      loadPairings();
      loadLogs();

    } catch (err) {
      authError.textContent = err.message;
      authError.classList.remove('hidden');
    } finally {
      btnText.textContent = 'Connect to My Channel';
      spinner.classList.add('hidden');
      loginBtn.disabled = false;
    }
  });

  // -----------------------------------------------------------
  // Categories Loader
  // -----------------------------------------------------------
  async function loadCategories() {
    try {
      const res = await fetch('/api/categories');
      const data = await res.json();

      if (data.success && data.categories) {
        allCategories = data.categories;

        // Populate manual upload select
        if (categorySelect) categorySelect.innerHTML = '<option value="">-- Choose Category --</option>';
        if (pairingCategorySelect) pairingCategorySelect.innerHTML = '<option value="">-- Default Category Chunein (Optional) --</option>';
        if (singleCategorySelect) singleCategorySelect.innerHTML = '<option value="">-- Category Chunein (Optional) --</option>';
        const batchCatSelect = document.getElementById('batchCategorySelect');
        if (batchCatSelect) batchCatSelect.innerHTML = '<option value="">Select Category...</option>';

        data.categories.forEach(cat => {
          if (categorySelect) {
            const opt1 = document.createElement('option');
            opt1.value = cat._id || cat.id;
            opt1.textContent = `${cat.name} (${cat.videosCount || 0} videos)`;
            categorySelect.appendChild(opt1);
          }

          if (pairingCategorySelect) {
            const opt2 = document.createElement('option');
            opt2.value = cat._id || cat.id;
            opt2.textContent = cat.name;
            pairingCategorySelect.appendChild(opt2);
          }

          if (singleCategorySelect) {
            const opt3 = document.createElement('option');
            opt3.value = cat._id || cat.id;
            opt3.textContent = cat.name;
            singleCategorySelect.appendChild(opt3);
          }

          if (batchCatSelect) {
            const opt4 = document.createElement('option');
            opt4.value = cat._id || cat.id;
            opt4.textContent = cat.name;
            batchCatSelect.appendChild(opt4);
          }
        });
      }
    } catch (e) {
      console.warn('Could not load categories:', e);
    }
  }

  // -----------------------------------------------------------
  // YouTube Automation Pairings Management
  // -----------------------------------------------------------
  async function loadPairings(isSilent = false) {
    try {
      const res = await fetch('/api/pairings');
      const data = await res.json();
      if (data.success && data.pairings) {
        renderPairings(data.pairings);

        // Update stats
        const activeCount = data.pairings.filter(p => p.is_active).length;
        const totalPostedCount = data.pairings.reduce((sum, p) => sum + (p.total_posted || 0), 0);

        if (statActivePairings) statActivePairings.textContent = activeCount;
        if (statTotalPosted) statTotalPosted.textContent = totalPostedCount;
      }
    } catch (e) {
      if (!isSilent) console.warn('Could not load pairings:', e);
    }
  }

  function renderPairings(pairings) {
    if (!pairingsContainer) return;
    if (!pairings || pairings.length === 0) {
      pairingsContainer.innerHTML = '<div class="empty-state">No YouTube channels linked yet. Add your first channel on the left!</div>';
      return;
    }

    pairingsContainer.innerHTML = '';
    pairings.forEach(p => {
      const card = document.createElement('div');
      card.className = 'pairing-item-card';

      const ytName = p.yt_channel_name || p.yt_channel_url;
      const bideoName = p.bideo_channel_name || 'Bideo Channel';
      const isActive = p.is_active !== false;
      const totalPosted = p.total_posted || 0;
      const lastPosted = p.last_posted_at ? new Date(p.last_posted_at).toLocaleTimeString() : 'Never';

      card.innerHTML = `
        <div class="pairing-top-row">
          <div class="pairing-title-group">
            <span class="yt-icon-chip">▶</span>
            <div>
              <div class="yt-name-text">${ytName}</div>
              <span class="pairing-target-pill">Target: ${bideoName}</span>
            </div>
          </div>
          <div class="pairing-actions">
            <button class="btn btn-secondary btn-sm explore-vids-btn" data-id="${p.id}" data-url="${p.yt_channel_url || ytName}" title="Browse all channel videos & upload status">
              📂 View Videos
            </button>
            <button class="btn btn-primary btn-sm sync-single-btn" data-id="${p.id}" title="Run download and upload now">
              ⚡ Sync Now
            </button>
            <button class="btn btn-secondary btn-sm toggle-btn" data-id="${p.id}" title="${isActive ? 'Pause' : 'Resume'}">
              ${isActive ? '🟢 Active' : '⏸️ Paused'}
            </button>
            <button class="btn btn-secondary btn-sm delete-btn" data-id="${p.id}" style="color:#EF4444;" title="Delete Channel">
              🗑️
            </button>
          </div>
        </div>
        <div class="pairing-meta-row">
          <span>📤 Published to Bideo: <b>${totalPosted} videos</b></span>
          <span>Last Post: <b>${lastPosted}</b></span>
          <span>Category: <b>${p.category_name || 'Default'}</b></span>
        </div>
      `;

      // Event Listeners
      const exploreBtn = card.querySelector('.explore-vids-btn');
      exploreBtn.addEventListener('click', () => {
        openChannelCatalog(p.yt_channel_url || p.yt_channel_name || ytName, p.id, p.bideo_user_id, p.category_id);
      });

      const syncBtn = card.querySelector('.sync-single-btn');
      syncBtn.addEventListener('click', async () => {
        syncBtn.textContent = '⏳ Starting...';
        syncBtn.disabled = true;
        try {
          const r = await fetch(`/api/pairings/${p.id}/sync`, { method: 'POST' });
          const d = await r.json();
          alert(d.message || 'Sync initiated!');
          setTimeout(loadLogs, 1500);
        } catch (err) {
          alert('Sync trigger failed: ' + err.message);
        } finally {
          syncBtn.textContent = '⚡ Sync Now';
          syncBtn.disabled = false;
        }
      });

      const toggleBtn = card.querySelector('.toggle-btn');
      toggleBtn.addEventListener('click', async () => {
        await fetch(`/api/pairings/${p.id}/toggle`, { method: 'PATCH' });
        loadPairings();
      });

      const deleteBtn = card.querySelector('.delete-btn');
      deleteBtn.addEventListener('click', async () => {
        if (confirm(`Kya aap YouTube channel '${ytName}' ki automation hatana chahte hain? Delete karne par ye channel aage se sync nahi hoga.`)) {
          await fetch(`/api/pairings/${p.id}`, { method: 'DELETE' });
          loadPairings();
        }
      });

      pairingsContainer.appendChild(card);
    });
  }

  // Create Pairing Form Submit
  if (pairingForm && savePairingBtn) {
    pairingForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (pairingAlert) pairingAlert.classList.add('hidden');

      const ytInput = ytChannelInput ? ytChannelInput.value.trim() : '';
      const bideoUserId = pairingBideoSelect ? pairingBideoSelect.value : '';
      const catId = pairingCategorySelect ? pairingCategorySelect.value : '';
      const catName = (pairingCategorySelect && pairingCategorySelect.options[pairingCategorySelect.selectedIndex]?.text) || '';

      if (!ytInput || !bideoUserId) {
        showPairingAlert('YouTube URL aur Target Bideo Account dono chunein!', 'error');
        return;
      }

      const btnText = savePairingBtn.querySelector('.btn-text');
      const spinner = savePairingBtn.querySelector('.spinner');

      if (btnText) btnText.textContent = 'Connecting Channel...';
      if (spinner) spinner.classList.remove('hidden');
      savePairingBtn.disabled = true;

      try {
        const res = await fetch('/api/pairings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            yt_channel: ytInput,
            bideo_user_id: bideoUserId,
            category_id: catId,
            category_name: catName
          })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.message || 'Channel link nahi ho saka.');
        }

        showPairingAlert(`🎉 YouTube Channel '${data.pairing.yt_channel_name}' Bideo ke sath connect ho gaya! Pehla video download aur upload shuru ho chuka hai.`, 'success');
        if (ytChannelInput) ytChannelInput.value = '';
        loadPairings();
        loadLogs();

        // Trigger immediate first video download & upload!
        if (data.pairing && data.pairing.id) {
          fetch(`/api/pairings/${data.pairing.id}/sync`, { method: 'POST' }).then(() => {
            setTimeout(loadLogs, 3000);
            setTimeout(loadPairings, 6000);
          }).catch(() => {});

          setTimeout(() => {
            openChannelCatalog(data.pairing.yt_channel_url || data.pairing.yt_channel_name, data.pairing.id, data.pairing.bideo_user_id, data.pairing.category_id);
          }, 500);
        }

      } catch (err) {
        showPairingAlert(err.message, 'error');
      } finally {
        if (btnText) btnText.textContent = '➕ Connect & Activate Automation';
        if (spinner) spinner.classList.add('hidden');
        savePairingBtn.disabled = false;
      }
    });
  }

  function showPairingAlert(msg, type) {
    if (pairingAlert) {
      pairingAlert.textContent = msg;
      pairingAlert.className = `alert-box ${type}`;
      pairingAlert.classList.remove('hidden');
    }
  }

  if (refreshPairingsBtn) {
    refreshPairingsBtn.addEventListener('click', () => loadPairings());
  }

  // Master Sync All Trigger
  if (syncAllBtn) {
    syncAllBtn.addEventListener('click', async () => {
      const btnText = syncAllBtn.querySelector('.btn-text');
      const spinner = syncAllBtn.querySelector('.spinner');

      if (btnText) btnText.textContent = 'Running All...';
      if (spinner) spinner.classList.remove('hidden');
    syncAllBtn.disabled = true;

    try {
      const res = await fetch('/api/sync_all', { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'All pairings sync cycle started!');
      setTimeout(() => {
        loadLogs();
        loadPairings();
      }, 3000);
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      btnText.textContent = '⚡ Run Master Sync Now';
      spinner.classList.add('hidden');
      syncAllBtn.disabled = false;
    }
    });
  }

  // -----------------------------------------------------------
  // Instant Single YouTube Video / Shorts Link Uploader
  // -----------------------------------------------------------
  if (singleLinkForm) {
    singleLinkForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      singleLinkAlert.classList.add('hidden');

      const videoUrl = singleVideoUrl.value.trim();
      const bideoUserId = singleBideoSelect.value;
      const categoryId = singleCategorySelect.value;
      const customTitle = singleCustomTitle.value.trim();
      const customDesc = singleCustomDesc.value.trim();

      if (!videoUrl) {
        showSingleAlert('YouTube Video URL daalna zaroori hai!', 'error');
        return;
      }
      if (!bideoUserId) {
        showSingleAlert('Kripya target Bideo account chunein!', 'error');
        return;
      }

      const btnText = singleLinkSubmitBtn.querySelector('.btn-text');
      const spinner = singleLinkSubmitBtn.querySelector('.spinner');

      btnText.textContent = 'Processing & Uploading...';
      spinner.classList.remove('hidden');
      singleLinkSubmitBtn.disabled = true;

      // Show live step-by-step progress box
      singleUploadStatusBox.innerHTML = `
        <div class="live-progress-steps">
          <div class="progress-step-item active">
            <span class="spinner" style="display:inline-block; width:16px; height:16px; border:2px solid var(--brand-orange); border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></span>
            <span>1. YouTube stream download ho rahi hai...</span>
          </div>
          <div class="progress-step-item">
            <span>🛡️</span>
            <span>2. Storage limit (&lt; 500MB) verify &amp; auto-compression check...</span>
          </div>
          <div class="progress-step-item">
            <span>📤</span>
            <span>3. Bideo channel me publish ho raha hai...</span>
          </div>
        </div>
      `;

      try {
        const res = await fetch('/api/upload_single_url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_url: videoUrl,
            bideo_user_id: bideoUserId,
            category_id: categoryId,
            title: customTitle,
            description: customDesc
          })
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          throw new Error(data.message || 'Upload fail ho gaya');
        }

        showSingleAlert(data.message, 'success');

        // Render success card with video details
        singleUploadStatusBox.innerHTML = `
          <div class="single-result-card">
            <h4>✅ Video Successfully Published!</h4>
            <div class="result-meta-item">
              <span class="lbl">Title:</span>
              <span class="val">${data.title || 'Published Video'}</span>
            </div>
            <div class="result-meta-item">
              <span class="lbl">Bideo Channel:</span>
              <span class="val">${data.channel_name || 'Your Channel'}</span>
            </div>
            <div class="result-meta-item">
              <span class="lbl">Downloaded Size:</span>
              <span class="val" style="color:#34D399;">${data.file_size_mb} MB (&lt; 500MB Safe)</span>
            </div>
            <div class="result-meta-item">
              <span class="lbl">Video ID:</span>
              <span class="val" style="font-family:monospace;">${data.video ? (data.video._id || data.video.id) : 'Success'}</span>
            </div>
          </div>
        `;

        singleVideoUrl.value = '';
        singleCustomTitle.value = '';
        singleCustomDesc.value = '';

        loadLogs();

      } catch (err) {
        showSingleAlert(err.message, 'error');
        singleUploadStatusBox.innerHTML = `
          <div class="status-placeholder" style="color:#EF4444;">
            <div class="status-icon">❌</div>
            <h4 style="color:#EF4444;">Upload Failed</h4>
            <p>${err.message}</p>
          </div>
        `;
      } finally {
        btnText.textContent = '🚀 Download & Upload to Bideo Now';
        spinner.classList.add('hidden');
        singleLinkSubmitBtn.disabled = false;
      }
    });
  }

  function showSingleAlert(msg, type) {
    if (!singleLinkAlert) return;
    singleLinkAlert.textContent = msg;
    singleLinkAlert.className = `alert-box ${type}`;
    singleLinkAlert.classList.remove('hidden');
  }

  // -----------------------------------------------------------
  // Live Activity Logs (Fetched from Firebase Realtime DB)
  // -----------------------------------------------------------
  async function loadLogs(isSilent = false) {
    try {
      const res = await fetch('/api/logs?limit=25');
      const data = await res.json();

      if (data.success && data.logs) {
        renderLogs(data.logs);
      }
    } catch (e) {
      if (!isSilent) console.warn('Could not fetch logs:', e);
    }
  }

  function renderLogs(logs) {
    if (!logs || logs.length === 0) {
      logsList.innerHTML = '<div class="empty-state">No activity logs recorded yet.</div>';
      return;
    }

    logsList.innerHTML = '';
    logs.forEach(log => {
      const row = document.createElement('div');
      row.className = `log-row ${log.status === 'error' ? 'error' : 'success'}`;

      const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '';

      row.innerHTML = `
        <div class="log-msg-col">
          <div class="log-title">${log.title}</div>
          <div class="log-desc">${log.message}</div>
        </div>
        <div class="log-time">${timeStr}</div>
      `;

      logsList.appendChild(row);
    });
  }

  refreshLogsBtn.addEventListener('click', () => loadLogs());

  // -----------------------------------------------------------
  // Direct PC Video Selection & Dropzone
  // -----------------------------------------------------------
  videoDropzone.addEventListener('click', () => {
    videoFileInput.click();
  });

  videoFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    videoDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      videoDropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    videoDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      videoDropzone.classList.remove('dragover');
    }, false);
  });

  videoDropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedVideoFile = file;

    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    dropzoneText.innerHTML = `Selected: <b>${file.name}</b>`;
    dropzoneSubtext.textContent = `Size: ${sizeMB} MB`;

    if (!videoTitle.value.trim()) {
      const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]+/g, ' ');
      videoTitle.value = cleanName;
    }

    const videoUrl = URL.createObjectURL(file);
    videoPreview.src = videoUrl;
    videoPreviewContainer.classList.remove('hidden');

    videoPreview.onloadedmetadata = () => {
      const durationSec = Math.round(videoPreview.duration);
      const minutes = Math.floor(durationSec / 60);
      const seconds = durationSec % 60;
      const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

      const w = videoPreview.videoWidth;
      const h = videoPreview.videoHeight;

      metaDuration.textContent = `⏳ ${formattedTime}`;
      metaDimensions.textContent = `📐 ${w}x${h}`;

      const isShort = (h >= w);
      metaTypeBadge.textContent = isShort ? '📱 Short / Reel' : '📺 Long Video';
      metaTypeBadge.style.color = isShort ? '#FF7A00' : '#6366F1';
    };
  }

  // -----------------------------------------------------------
  // Direct PC Upload Submission
  // -----------------------------------------------------------
  uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();
    uploadAlert.classList.add('hidden');

    if (!selectedVideoFile) {
      showAlert('Kripya pehle koi video file select karein!', 'error');
      return;
    }

    const token = currentActiveAccount?.token || localStorage.getItem('bideo_token');
    if (!token) {
      showAlert('Aapka session expire ho gaya hai. Dobara login karein.', 'error');
      initApp();
      return;
    }

    const formData = new FormData();
    formData.append('video', selectedVideoFile);
    formData.append('title', videoTitle.value.trim());
    formData.append('description', videoDescription.value.trim());

    if (categorySelect.value) {
      formData.append('category', categorySelect.value);
    }

    if (uploadTypeSelect.value !== 'auto') {
      formData.append('isShort', uploadTypeSelect.value === 'short' ? 'true' : 'false');
    }

    if (thumbFileInput.files && thumbFileInput.files[0]) {
      formData.append('thumbnail', thumbFileInput.files[0]);
    }

    uploadProgressBox.classList.remove('hidden');
    progressBarFill.style.width = '0%';
    progressPercent.textContent = '0%';
    progressStatusText.textContent = '🚀 Sending video to Bideo server...';

    const btnText = submitUploadBtn.querySelector('.btn-text');
    const spinner = submitUploadBtn.querySelector('.spinner');
    btnText.textContent = 'Publishing...';
    spinner.classList.remove('hidden');
    submitUploadBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) {
        const percentComplete = Math.round((evt.loaded / evt.total) * 95);
        progressBarFill.style.width = `${percentComplete}%`;
        progressPercent.textContent = `${percentComplete}%`;
        if (percentComplete >= 95) {
          progressStatusText.textContent = '⚡ Cloudflare R2 & Database Syncing...';
        }
      }
    };

    xhr.onload = () => {
      btnText.textContent = '🚀 Publish Video Directly to Channel';
      spinner.classList.add('hidden');
      submitUploadBtn.disabled = false;

      let resp;
      try {
        resp = JSON.parse(xhr.responseText);
      } catch (err) {
        showAlert('Invalid response from backend server.', 'error');
        return;
      }

      if (xhr.status >= 200 && xhr.status < 300 && resp.success) {
        progressBarFill.style.width = '100%';
        progressPercent.textContent = '100%';
        progressStatusText.textContent = '✅ Published successfully!';

        showAlert(`🎉 Video '${currentActiveAccount?.name || 'aapke channel'}' me live upload ho gayi!`, 'success');

        addToRecentList(resp.video || { title: videoTitle.value });

        setTimeout(() => {
          uploadProgressBox.classList.add('hidden');
          selectedVideoFile = null;
          videoFileInput.value = '';
          thumbFileInput.value = '';
          videoTitle.value = '';
          videoDescription.value = '';
          videoPreviewContainer.classList.add('hidden');
          dropzoneText.innerHTML = 'Drag & Drop video file here, or <span>Browse PC</span>';
          dropzoneSubtext.textContent = 'Supports 1080p, 4K, Shorts & Long videos';
        }, 3000);

      } else {
        showAlert(resp.message || 'Upload fail ho gaya. Kripya dobara try karein.', 'error');
      }
    };

    xhr.onerror = () => {
      btnText.textContent = '🚀 Publish Video Directly to Channel';
      spinner.classList.add('hidden');
      submitUploadBtn.disabled = false;
      showAlert('Network error connecting to backend.', 'error');
    };

    xhr.send(formData);
  });

  function showAlert(msg, type) {
    uploadAlert.textContent = msg;
    uploadAlert.className = `alert-box ${type}`;
    uploadAlert.classList.remove('hidden');
  }

  function addToRecentList(video) {
    const emptyState = recentUploadsList.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const item = document.createElement('div');
    item.className = 'recent-item';

    const thumb = video.thumbnail || 'https://via.placeholder.com/50x50.png?text=Video';
    const title = video.title || 'Untitled Video';

    item.innerHTML = `
      <img src="${thumb}" alt="thumb" class="recent-thumb">
      <div class="recent-meta">
        <div class="recent-title">${title}</div>
        <div class="recent-status">● Live in your channel</div>
      </div>
    `;

    recentUploadsList.prepend(item);
  }

  // -----------------------------------------------------------
  // Kaggle 24/7 Cloud Super-Engine Integration
  // -----------------------------------------------------------
  const kaggleStatusBadge = document.getElementById('kaggleStatusBadge');
  const kaggleStatusSubtext = document.getElementById('kaggleStatusSubtext');
  const kaggleActiveStrip = document.getElementById('kaggleActiveStrip');
  const kaggleUptimeText = document.getElementById('kaggleUptimeText');
  const kaggleRenewInText = document.getElementById('kaggleRenewInText');
  const kaggleLiveTaskText = document.getElementById('kaggleLiveTaskText');
  const kaggleUploadCountText = document.getElementById('kaggleUploadCountText');

  const openKaggleModalBtn = document.getElementById('openKaggleModalBtn');
  const closeKaggleModalBtn = document.getElementById('closeKaggleModalBtn');
  const cancelKaggleModalBtn = document.getElementById('cancelKaggleModalBtn');
  const kaggleConfigModal = document.getElementById('kaggleConfigModal');
  const kaggleConfigForm = document.getElementById('kaggleConfigForm');
  const kaggleAlert = document.getElementById('kaggleAlert');
  const kaggleUserInput = document.getElementById('kaggleUserInput');
  const kaggleKeyInput = document.getElementById('kaggleKeyInput');
  const kaggleSlugInput = document.getElementById('kaggleSlugInput');
  const kaggleAutoRenewCheck = document.getElementById('kaggleAutoRenewCheck');
  const saveKaggleConfigBtn = document.getElementById('saveKaggleConfigBtn');

  const startKaggleBtn = document.getElementById('startKaggleBtn');
  const stopKaggleBtn = document.getElementById('stopKaggleBtn');
  const kaggleNotebookLink = document.getElementById('kaggleNotebookLink');

  let kaggleConfigCache = {};

  async function loadKaggleStatus() {
    if (!kaggleStatusBadge) return;
    try {
      const res = await fetch('/api/kaggle/status');
      const data = await res.json();
      if (!data.success) return;

      const status = data.status || {};
      kaggleConfigCache = data.config || {};

      const user = kaggleConfigCache.kaggle_user || 'professorcryvex';
      const slug = kaggleConfigCache.kaggle_slug || 'bideo-automation-engine';

      if (kaggleNotebookLink) {
        kaggleNotebookLink.href = status.kaggle_url || `https://www.kaggle.com/code/${user}/${slug}`;
      }

      // ONLY active if Kaggle Python engine actually sent a heartbeat within the last 60 seconds!
      const isRunning = status.is_running === true && (Date.now() / 1000 - (status.last_heartbeat || 0) < 60);
      const isWaiting = status.state === 'waiting_heartbeat' || status.state === 'launching';

      if (isRunning) {
        kaggleStatusBadge.textContent = '🟢 Active (Google Cloud)';
        kaggleStatusBadge.style.background = 'rgba(34, 197, 94, 0.2)';
        kaggleStatusBadge.style.color = '#4ade80';
        kaggleStatusBadge.style.borderColor = '#22c55e';

        kaggleStatusSubtext.textContent = 'Multi-gigabit Google Cloud network active. Zero bot block video sync in progress.';
        if (kaggleActiveStrip) kaggleActiveStrip.classList.remove('hidden');

        if (kaggleUptimeText) kaggleUptimeText.textContent = status.uptime_str || '0h 0m';
        if (kaggleRenewInText) kaggleRenewInText.textContent = status.renew_in_str || '11h 30m';
        if (kaggleLiveTaskText) kaggleLiveTaskText.textContent = status.current_task || 'Idle - Monitoring Channels';
        if (kaggleUploadCountText) kaggleUploadCountText.textContent = status.total_uploaded_count || '0';

        if (startKaggleBtn) {
          startKaggleBtn.textContent = '🔄 Restart Engine';
          startKaggleBtn.style.background = 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)';
          startKaggleBtn.style.color = '#fff';
        }
        if (stopKaggleBtn) stopKaggleBtn.classList.remove('hidden');
      } else if (isWaiting) {
        kaggleStatusBadge.textContent = '🟡 Waiting for Kaggle Boot...';
        kaggleStatusBadge.style.background = 'rgba(234, 179, 8, 0.2)';
        kaggleStatusBadge.style.color = '#facc15';
        kaggleStatusBadge.style.borderColor = '#eab308';
        kaggleStatusSubtext.textContent = 'Kaggle par deploy ho gaya! Cloud boot aur first heartbeat ka wait ho raha hai (~30s)...';
        if (kaggleActiveStrip) kaggleActiveStrip.classList.add('hidden');
        if (stopKaggleBtn) stopKaggleBtn.classList.remove('hidden');
      } else {
        kaggleStatusBadge.textContent = '⚪ Offline';
        kaggleStatusBadge.style.background = 'rgba(100, 116, 139, 0.25)';
        kaggleStatusBadge.style.color = '#94a3b8';
        kaggleStatusBadge.style.borderColor = '#475569';
        kaggleStatusSubtext.textContent = 'Google Cloud multi-gigabit network se zero-bot block video download & upload. 11h 30m auto-renew loop ready.';
        if (kaggleActiveStrip) kaggleActiveStrip.classList.add('hidden');

        if (startKaggleBtn) {
          startKaggleBtn.textContent = '🚀 Start 24/7 Engine';
          startKaggleBtn.style.background = 'linear-gradient(135deg, #00C853 0%, #64DD17 100%)';
          startKaggleBtn.style.color = '#000';
        }
        if (stopKaggleBtn) stopKaggleBtn.classList.add('hidden');
      }
    } catch (err) {
      console.warn('Could not load Kaggle status:', err);
    }
  }

  function setupKaggleListeners() {
    if (openKaggleModalBtn) {
      openKaggleModalBtn.addEventListener('click', () => {
        if (kaggleConfigCache.kaggle_user) {
          kaggleUserInput.value = kaggleConfigCache.kaggle_user;
        }
        if (kaggleSlugInput && kaggleConfigCache.kaggle_slug) {
          kaggleSlugInput.value = kaggleConfigCache.kaggle_slug;
        }
        if (kaggleConfigCache.auto_renew !== undefined) {
          kaggleAutoRenewCheck.checked = kaggleConfigCache.auto_renew;
        }
        kaggleConfigModal.classList.remove('hidden');
      });
    }

    if (closeKaggleModalBtn) closeKaggleModalBtn.addEventListener('click', () => kaggleConfigModal.classList.add('hidden'));
    if (cancelKaggleModalBtn) cancelKaggleModalBtn.addEventListener('click', () => kaggleConfigModal.classList.add('hidden'));

    if (kaggleConfigForm) {
      kaggleConfigForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const user = kaggleUserInput.value.trim();
        const key = kaggleKeyInput.value.trim();
        const slug = (kaggleSlugInput ? kaggleSlugInput.value.trim() : '') || 'bideo-automation-engine';
        const autoRenew = kaggleAutoRenewCheck.checked;

        if (!user || !key) {
          showKaggleAlert('Kaggle Username aur API Key dono required hain!', 'error');
          return;
        }

        const btnText = saveKaggleConfigBtn.querySelector('.btn-text');
        const spinner = saveKaggleConfigBtn.querySelector('.spinner');
        btnText.textContent = 'Launching Engine...';
        spinner.classList.remove('hidden');
        saveKaggleConfigBtn.disabled = true;

        try {
          const res = await fetch('/api/kaggle/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              kaggle_user: user,
              kaggle_key: key,
              kaggle_slug: slug,
              auto_renew: autoRenew
            })
          });
          const data = await res.json();
          if (data.success) {
            kaggleConfigModal.classList.add('hidden');
            loadKaggleStatus();
          } else {
            showKaggleAlert(data.message || 'Kaggle launch failed', 'error');
          }
        } catch (err) {
          showKaggleAlert(err.message, 'error');
        } finally {
          btnText.textContent = '💾 Save & Launch Engine';
          spinner.classList.add('hidden');
          saveKaggleConfigBtn.disabled = false;
        }
      });
    }

    if (startKaggleBtn) {
      startKaggleBtn.addEventListener('click', async () => {
        if (!kaggleConfigCache.kaggle_user || !kaggleConfigCache.kaggle_key) {
          if (openKaggleModalBtn) openKaggleModalBtn.click();
          return;
        }

        startKaggleBtn.disabled = true;
        startKaggleBtn.textContent = 'Starting...';
        try {
          const res = await fetch('/api/kaggle/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(kaggleConfigCache)
          });
          const data = await res.json();
          if (data.success) {
            loadKaggleStatus();
          } else {
            alert('Kaggle start error: ' + data.message);
          }
        } catch (err) {
          alert('Network error starting Kaggle: ' + err.message);
        } finally {
          startKaggleBtn.disabled = false;
        }
      });
    }

    if (stopKaggleBtn) {
      stopKaggleBtn.addEventListener('click', async () => {
        if (!confirm('Kaggle 24/7 Engine stop karna chahte hain?')) return;
        try {
          await fetch('/api/kaggle/stop', { method: 'POST' });
          loadKaggleStatus();
        } catch (e) {
          console.warn('Error stopping Kaggle:', e);
        }
      });
    }

    function showKaggleAlert(msg, type) {
      kaggleAlert.textContent = msg;
      kaggleAlert.className = `alert-box ${type}`;
      kaggleAlert.classList.remove('hidden');
    }

    // Auto-refresh Kaggle status every 10 seconds
    setInterval(loadKaggleStatus, 10000);
    loadKaggleStatus();
  }

  // -----------------------------------------------------------
  // YOUTUBE CHANNEL VIDEO CATALOG EXPLORER
  // -----------------------------------------------------------
  const channelVideosModal = document.getElementById('channelVideosModal');
  const closeCatalogModalBtn = document.getElementById('closeCatalogModalBtn');
  const catalogModalTitle = document.getElementById('catalogModalTitle');
  const catalogModalYtLink = document.getElementById('catalogModalYtLink');
  const catalogModalSub = document.getElementById('catalogModalSub');
  const badgeTotalVids = document.getElementById('badgeTotalVids');
  const badgeUploadedVids = document.getElementById('badgeUploadedVids');
  const badgePendingVids = document.getElementById('badgePendingVids');
  const catalogVideosGrid = document.getElementById('catalogVideosGrid');
  const catalogSearchInput = document.getElementById('catalogSearchInput');
  const previewChannelBtn = document.getElementById('previewChannelBtn');

  let currentCatalogVideos = [];
  let currentActiveFilter = 'all';
  let currentSearchQuery = '';
  let currentTargetBideoUserId = null;
  let currentTargetCategoryId = null;

  async function openChannelCatalog(channelUrl, pairingId = null, bideoUserId = null, categoryId = null) {
    if (!channelUrl) return;

    currentTargetBideoUserId = bideoUserId || (currentActiveAccount ? (currentActiveAccount._id || currentActiveAccount.id) : null);
    currentTargetCategoryId = categoryId || (pairingCategorySelect ? pairingCategorySelect.value : '');

    if (channelVideosModal) channelVideosModal.classList.remove('hidden');
    catalogModalTitle.textContent = 'Loading Channel Videos...';
    catalogModalSub.textContent = `Fetching videos from YouTube: ${channelUrl}...`;
    catalogVideosGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 40px;">
        <div class="spinner" style="margin: 0 auto 16px auto; width: 32px; height: 32px;"></div>
        <p style="color: #94A3B8;">YouTube channel scan ho raha hai... Kripya thoda wait karein.</p>
      </div>
    `;

    try {
      const endpoint = pairingId
        ? `/api/pairings/${pairingId}/videos`
        : `/api/channel/videos?channel_url=${encodeURIComponent(channelUrl)}`;

      const res = await fetch(endpoint);
      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Videos fetch karne me dikkat aayi.');
      }

      catalogModalTitle.textContent = data.channel_name || 'Channel Videos';
      catalogModalYtLink.href = data.channel_url || `https://www.youtube.com/${channelUrl}`;
      catalogModalSub.textContent = `Target Bideo Account: ${data.bideo_channel_name || (currentActiveAccount ? currentActiveAccount.name : 'Active Account')}`;

      badgeTotalVids.textContent = `Total: ${data.total_videos}`;
      badgeUploadedVids.textContent = `🟢 Uploaded: ${data.uploaded_count}`;
      badgePendingVids.textContent = `⏳ Pending: ${data.pending_count}`;

      currentCatalogVideos = data.videos || [];
      renderCatalogVideos();

    } catch (err) {
      catalogVideosGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1; color: #EF4444;">
          ❌ Channel load error: ${err.message}
        </div>
      `;
    }
  }

  function renderCatalogVideos() {
    let list = [...currentCatalogVideos];

    if (currentActiveFilter === 'uploaded') {
      list = list.filter(v => v.is_uploaded);
    } else if (currentActiveFilter === 'pending') {
      list = list.filter(v => !v.is_uploaded);
    }

    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      list = list.filter(v => (v.title || '').toLowerCase().includes(q));
    }

    if (list.length === 0) {
      catalogVideosGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          Koi video nahi mili is filter ke mutabiq.
        </div>
      `;
      return;
    }

    catalogVideosGrid.innerHTML = '';
    list.forEach(v => {
      const card = document.createElement('div');
      card.className = 'channel-video-card';

      const thumbUrl = v.thumbnail || `https://i.ytimg.com/vi/${v.id}/hqdefault.jpg`;
      const durSec = Math.round(v.duration || 0);
      const durStr = durSec > 0 ? `${Math.floor(durSec / 60)}:${String(durSec % 60).padStart(2, '0')}` : (v.is_short ? 'Shorts' : 'HD');
      const isUp = !!v.is_uploaded;

      card.innerHTML = `
        <div class="channel-video-thumb-wrap">
          <img src="${thumbUrl}" alt="${v.title}" loading="lazy" onerror="this.src='https://placehold.co/640x360/1a1a24/ffffff?text=Video';">
          <span class="video-duration-pill">${durStr}</span>
        </div>
        <div class="channel-video-body">
          <div class="channel-video-title" title="${v.title}">${v.title}</div>
          <div class="channel-video-footer">
            ${isUp 
              ? `<span class="video-status-tag uploaded">🟢 Uploaded</span>`
              : `<span class="video-status-tag pending">⏳ Pending</span>`
            }
            ${isUp
              ? `<span style="color: #10B981; font-weight: 700; font-size: 0.8rem;">✅ Published</span>`
              : `<button class="btn btn-primary btn-sm upload-now-single-btn" data-url="${v.url}" data-id="${v.id}">⚡ Upload Now</button>`
            }
          </div>
        </div>
      `;

      if (!isUp) {
        const upBtn = card.querySelector('.upload-now-single-btn');
        upBtn.addEventListener('click', async () => {
          upBtn.textContent = '⏳ Uploading...';
          upBtn.disabled = true;

          try {
            const targetAccId = currentTargetBideoUserId || (currentActiveAccount ? (currentActiveAccount._id || currentActiveAccount.id) : null);
            if (!targetAccId) {
              alert('Kripya pehle ek Bideo channel select ya login karein!');
              upBtn.textContent = '⚡ Upload Now';
              upBtn.disabled = false;
              return;
            }

            const res = await fetch('/api/upload_single_url', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                video_url: v.url,
                bideo_user_id: targetAccId,
                category_id: currentTargetCategoryId || '',
                title: v.title
              })
            });

            const d = await res.json();
            if (res.ok && d.success) {
              v.is_uploaded = true;
              alert(`🎉 '${v.title}' successfully Bideo par upload ho gaya!`);
              // Update badges count
              const upCount = currentCatalogVideos.filter(x => x.is_uploaded).length;
              badgeUploadedVids.textContent = `🟢 Uploaded: ${upCount}`;
              badgePendingVids.textContent = `⏳ Pending: ${currentCatalogVideos.length - upCount}`;
              renderCatalogVideos();
              loadPairings();
              loadLogs();
            } else {
              alert(`Upload fail: ${d.message || 'Error uploading video'}`);
              upBtn.textContent = '⚡ Upload Now';
              upBtn.disabled = false;
            }
          } catch (err) {
            alert(`Network error: ${err.message}`);
            upBtn.textContent = '⚡ Upload Now';
            upBtn.disabled = false;
          }
        });
      }

      catalogVideosGrid.appendChild(card);
    });
  }

  // -----------------------------------------------------------
  // YOUTUBE CHANNEL STUDIO & ON-DEMAND BATCH ENGINE
  // -----------------------------------------------------------
  let studioCurrentChannel = null;
  let studioCurrentVideos = [];
  let studioActiveFilter = 'available'; // 'available', 'uploaded', 'all'
  let studioSelectedIds = new Set();
  let batchPollInterval = null;

  function setupChannelBatchStudio() {
    const channelFetchInput = document.getElementById('channelFetchInput');
    const fetchChannelBtn = document.getElementById('fetchChannelBtn');
    const savedChannelsSelect = document.getElementById('savedChannelsSelect');
    const channelFetchAlert = document.getElementById('channelFetchAlert');

    const currentChannelTitle = document.getElementById('currentChannelTitle');
    const currentChannelLink = document.getElementById('currentChannelLink');
    const statTotalVids = document.getElementById('statTotalVids');
    const statUploadedVids = document.getElementById('statUploadedVids');
    const statAvailableVids = document.getElementById('statAvailableVids');

    const filterAvailableBtn = document.getElementById('filterAvailableBtn');
    const filterUploadedBtn = document.getElementById('filterUploadedBtn');
    const filterAllBtn = document.getElementById('filterAllBtn');

    const selectNext4Btn = document.getElementById('selectNext4Btn');
    const selectNext6Btn = document.getElementById('selectNext6Btn');
    const selectNext10Btn = document.getElementById('selectNext10Btn');
    const selectAllAvailableBtn = document.getElementById('selectAllAvailableBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    const selectedCountBadge = document.getElementById('selectedCountBadge');

    const channelVideosGrid = document.getElementById('channelVideosGrid');

    const batchBideoAccountSelect = document.getElementById('batchBideoAccountSelect');
    const batchCategorySelect = document.getElementById('batchCategorySelect');
    const batchPacingSelect = document.getElementById('batchPacingSelect');
    const startBatchUploadBtn = document.getElementById('startBatchUploadBtn');
    const cancelActiveBatchBtn = document.getElementById('cancelActiveBatchBtn');

    // Populate Bideo accounts in Batch Select
    function populateBatchDropdowns() {
      if (batchBideoAccountSelect) {
        batchBideoAccountSelect.innerHTML = '<option value="">Select Bideo Account...</option>';
        savedAccounts.forEach(acc => {
          const opt = document.createElement('option');
          opt.value = acc._id || acc.id;
          opt.textContent = `${acc.name || acc.channelName} (${acc.phone || 'Connected'})`;
          batchBideoAccountSelect.appendChild(opt);
        });
        if (currentActiveAccount && savedAccounts.length > 0) {
          batchBideoAccountSelect.value = currentActiveAccount._id || currentActiveAccount.id;
        }
      }

      if (batchCategorySelect) {
        batchCategorySelect.innerHTML = '<option value="">Select Category...</option>';
        allCategories.forEach(cat => {
          const opt = document.createElement('option');
          opt.value = cat._id || cat.id;
          opt.textContent = cat.name || cat.title;
          batchCategorySelect.appendChild(opt);
        });
      }
    }

    // Load saved channels list from Firebase
    async function loadSavedChannelsList() {
      if (!savedChannelsSelect) return;
      try {
        const res = await fetch('/api/channels');
        const d = await res.json();
        if (d.success && Array.isArray(d.channels)) {
          savedChannelsSelect.innerHTML = '<option value="">Select a previously saved channel...</option>';
          d.channels.forEach(ch => {
            const opt = document.createElement('option');
            opt.value = ch.id;
            opt.textContent = `${ch.channel_name} (Total: ${ch.total_videos} | Uploaded: ${ch.uploaded_count})`;
            savedChannelsSelect.appendChild(opt);
          });
        }
      } catch (err) {
        console.warn('Failed to load saved channels:', err);
      }
    }

    // Fetch videos from YouTube channel
    async function handleFetchChannel() {
      const input = channelFetchInput ? channelFetchInput.value.trim() : '';
      if (!input) {
        if (channelFetchAlert) {
          channelFetchAlert.textContent = 'Kripya YouTube channel URL ya @handle enter karein!';
          channelFetchAlert.className = 'alert-box error';
          channelFetchAlert.classList.remove('hidden');
        }
        return;
      }

      if (channelFetchAlert) channelFetchAlert.classList.add('hidden');
      const btnText = fetchChannelBtn.querySelector('.btn-text');
      const spinner = fetchChannelBtn.querySelector('.spinner');
      if (btnText) btnText.textContent = 'Fetching...';
      if (spinner) spinner.classList.remove('hidden');
      fetchChannelBtn.disabled = true;

      try {
        const res = await fetch('/api/channels/fetch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel_input: input, max_results: 60 })
        });
        const data = await res.json();

        if (data.success && data.channel) {
          studioCurrentChannel = data.channel;
          studioCurrentVideos = data.videos || [];
          studioSelectedIds.clear();
          renderVideoGallery();
          loadSavedChannelsList();
          if (channelFetchAlert) {
            channelFetchAlert.textContent = `✅ '${data.channel.channel_name}' se ${studioCurrentVideos.length} videos load ho gaye!`;
            channelFetchAlert.className = 'alert-box success';
            channelFetchAlert.classList.remove('hidden');
          }
        } else {
          if (channelFetchAlert) {
            channelFetchAlert.textContent = data.message || 'Channel fetch failed';
            channelFetchAlert.className = 'alert-box error';
            channelFetchAlert.classList.remove('hidden');
          }
        }
      } catch (err) {
        if (channelFetchAlert) {
          channelFetchAlert.textContent = `Network error: ${err.message}`;
          channelFetchAlert.className = 'alert-box error';
          channelFetchAlert.classList.remove('hidden');
        }
      } finally {
        if (btnText) btnText.textContent = '🔍 Fetch Videos';
        if (spinner) spinner.classList.add('hidden');
        fetchChannelBtn.disabled = false;
      }
    }

    // Load existing channel from dropdown
    if (savedChannelsSelect) {
      savedChannelsSelect.addEventListener('change', async (e) => {
        const chId = e.target.value;
        if (!chId) return;
        channelVideosGrid.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1; padding: 40px; text-align: center;">Loading channel library...</div>';
        try {
          const res = await fetch(`/api/channels/${chId}/videos`);
          const data = await res.json();
          if (data.success) {
            studioCurrentVideos = data.videos || [];
            const selOpt = savedChannelsSelect.options[savedChannelsSelect.selectedIndex];
            studioCurrentChannel = {
              id: chId,
              channel_name: selOpt ? selOpt.textContent.split('(')[0].trim() : 'YouTube Channel'
            };
            studioSelectedIds.clear();
            renderVideoGallery();
          }
        } catch (err) {
          alert(`Error loading channel videos: ${err.message}`);
        }
      });
    }

    // Render Video Cards in Gallery
    function renderVideoGallery() {
      if (!channelVideosGrid) return;

      const total = studioCurrentVideos.length;
      const uploaded = studioCurrentVideos.filter(v => v.uploaded).length;
      const available = total - uploaded;

      if (statTotalVids) statTotalVids.textContent = total;
      if (statUploadedVids) statUploadedVids.textContent = uploaded;
      if (statAvailableVids) statAvailableVids.textContent = available;

      if (studioCurrentChannel && currentChannelTitle) {
        currentChannelTitle.textContent = studioCurrentChannel.channel_name || 'YouTube Channel';
        if (studioCurrentChannel.channel_url && currentChannelLink) {
          currentChannelLink.href = studioCurrentChannel.channel_url;
          currentChannelLink.classList.remove('hidden');
        }
      }

      let filtered = studioCurrentVideos;
      if (studioActiveFilter === 'available') {
        filtered = studioCurrentVideos.filter(v => !v.uploaded);
      } else if (studioActiveFilter === 'uploaded') {
        filtered = studioCurrentVideos.filter(v => v.uploaded);
      }

      channelVideosGrid.innerHTML = '';
      if (filtered.length === 0) {
        channelVideosGrid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1; padding: 40px; text-align: center; color: #94a3b8;">
          No videos found for filter '<strong>${studioActiveFilter}</strong>'.
        </div>`;
        updateSelectionCounter();
        return;
      }

      filtered.forEach(v => {
        const card = document.createElement('div');
        const isSelected = studioSelectedIds.has(v.id);
        const isUploaded = Boolean(v.uploaded);

        card.className = `gallery-video-card ${isSelected ? 'selected' : ''} ${isUploaded ? 'uploaded' : ''}`;

        const durMin = Math.floor((v.duration || 0) / 60);
        const durSec = (v.duration || 0) % 60;
        const durStr = `${durMin}:${durSec < 10 ? '0' : ''}${durSec}`;

        card.innerHTML = `
          <div class="gallery-card-thumb-wrap">
            <img src="${v.thumbnail || `https://i.ytimg.com/vi/${v.id}/hqdefault.jpg`}" alt="${v.title}" class="gallery-card-thumb" loading="lazy">
            <span class="video-duration-pill">${durStr}</span>
            <span class="video-type-badge ${v.is_short ? 'shorts' : 'long'}">${v.is_short ? '⚡ SHORT' : '▶ VIDEO'}</span>
            ${!isUploaded ? `
              <div class="video-check-overlay">
                <input type="checkbox" class="video-select-checkbox" data-id="${v.id}" ${isSelected ? 'checked' : ''}>
              </div>
            ` : ''}
          </div>
          <div class="channel-video-body">
            <div class="channel-video-title" title="${v.title}">${v.title}</div>
            <div class="channel-video-footer">
              ${isUploaded ? `
                <span class="video-status-tag uploaded">🟢 Uploaded to Bideo</span>
              ` : `
                <span class="video-status-tag pending">⚪ Available</span>
              `}
              <a href="${v.url || `https://www.youtube.com/watch?v=${v.id}`}" target="_blank" style="font-size: 0.75rem; color: #38bdf8;" onclick="event.stopPropagation();">
                Watch ↗
              </a>
            </div>
          </div>
        `;

        if (!isUploaded) {
          card.addEventListener('click', (e) => {
            if (e.target.tagName === 'A') return;
            if (studioSelectedIds.has(v.id)) {
              studioSelectedIds.delete(v.id);
            } else {
              studioSelectedIds.add(v.id);
            }
            renderVideoGallery();
          });
        }

        channelVideosGrid.appendChild(card);
      });

      updateSelectionCounter();
    }

    function updateSelectionCounter() {
      if (selectedCountBadge) {
        selectedCountBadge.textContent = `🎯 ${studioSelectedIds.size} Videos Selected`;
      }
    }

    // Quick selection logic
    function selectNextN(n) {
      const unuploaded = studioCurrentVideos.filter(v => !v.uploaded);
      let count = 0;
      for (const v of unuploaded) {
        if (!studioSelectedIds.has(v.id)) {
          studioSelectedIds.add(v.id);
          count++;
          if (count >= n) break;
        }
      }
      renderVideoGallery();
    }

    if (selectNext4Btn) selectNext4Btn.addEventListener('click', () => selectNextN(4));
    if (selectNext6Btn) selectNext6Btn.addEventListener('click', () => selectNextN(6));
    if (selectNext10Btn) selectNext10Btn.addEventListener('click', () => selectNextN(10));
    if (selectAllAvailableBtn) {
      selectAllAvailableBtn.addEventListener('click', () => {
        studioCurrentVideos.filter(v => !v.uploaded).forEach(v => studioSelectedIds.add(v.id));
        renderVideoGallery();
      });
    }
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', () => {
        studioSelectedIds.clear();
        renderVideoGallery();
      });
    }

    // Filter Buttons
    if (filterAvailableBtn) {
      filterAvailableBtn.addEventListener('click', () => {
        studioActiveFilter = 'available';
        filterAvailableBtn.classList.add('active');
        if (filterUploadedBtn) filterUploadedBtn.classList.remove('active');
        if (filterAllBtn) filterAllBtn.classList.remove('active');
        renderVideoGallery();
      });
    }
    if (filterUploadedBtn) {
      filterUploadedBtn.addEventListener('click', () => {
        studioActiveFilter = 'uploaded';
        filterUploadedBtn.classList.add('active');
        if (filterAvailableBtn) filterAvailableBtn.classList.remove('active');
        if (filterAllBtn) filterAllBtn.classList.remove('active');
        renderVideoGallery();
      });
    }
    if (filterAllBtn) {
      filterAllBtn.addEventListener('click', () => {
        studioActiveFilter = 'all';
        filterAllBtn.classList.add('active');
        if (filterAvailableBtn) filterAvailableBtn.classList.remove('active');
        if (filterUploadedBtn) filterUploadedBtn.classList.remove('active');
        renderVideoGallery();
      });
    }

    if (fetchChannelBtn) fetchChannelBtn.addEventListener('click', handleFetchChannel);
    if (channelFetchInput) {
      channelFetchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleFetchChannel();
      });
    }

    // START BATCH UPLOAD TO KAGGLE
    if (startBatchUploadBtn) {
      startBatchUploadBtn.addEventListener('click', async () => {
        if (studioSelectedIds.size === 0) {
          alert('Kripya pehle kam se kam 1 video select karein!');
          return;
        }

        const bideoUserId = batchBideoAccountSelect ? batchBideoAccountSelect.value : '';
        if (!bideoUserId) {
          alert('Kripya Target Bideo Channel select karein!');
          return;
        }

        const categoryId = batchCategorySelect ? batchCategorySelect.value : '';
        const pacingHours = batchPacingSelect ? parseFloat(batchPacingSelect.value || '9') : 9.0;

        const selectedList = studioCurrentVideos.filter(v => studioSelectedIds.has(v.id));

        const confirmMsg = `${selectedList.length} videos ko Kaggle pe push karna chahte hain?\nKaggle in sabko download karke ~${pacingHours} ghante me spaced-out post karega.`;
        if (!confirm(confirmMsg)) return;

        const btnText = startBatchUploadBtn.querySelector('.btn-text');
        const spinner = startBatchUploadBtn.querySelector('.spinner');
        if (btnText) btnText.textContent = 'Launching Kaggle Bot...';
        if (spinner) spinner.classList.remove('hidden');
        startBatchUploadBtn.disabled = true;

        try {
          const res = await fetch('/api/batch/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              selected_videos: selectedList,
              bideo_user_id: bideoUserId,
              category_id: categoryId,
              pacing_hours: pacingHours
            })
          });
          const d = await res.json();

          if (d.success) {
            alert(`🎉 ${d.message}`);
            studioSelectedIds.clear();
            renderVideoGallery();
            pollBatchAndKaggleStatus();
          } else {
            alert(`❌ Error: ${d.message}`);
          }
        } catch (err) {
          alert(`Network error: ${err.message}`);
        } finally {
          if (btnText) btnText.textContent = '🚀 Push Selected Videos to Kaggle';
          if (spinner) spinner.classList.add('hidden');
          startBatchUploadBtn.disabled = false;
        }
      });
    }

    // CANCEL ACTIVE BATCH
    if (cancelActiveBatchBtn) {
      cancelActiveBatchBtn.addEventListener('click', async () => {
        if (!confirm('Kya aap running batch aur Kaggle engine ko stop karna chahte hain?')) return;
        try {
          const res = await fetch('/api/batch/cancel', { method: 'POST' });
          const d = await res.json();
          alert(d.message || 'Batch cancelled');
          pollBatchAndKaggleStatus();
        } catch (err) {
          alert(`Error cancelling: ${err.message}`);
        }
      });
    }

    // Initial setup
    populateBatchDropdowns();
    loadSavedChannelsList();
    pollBatchAndKaggleStatus();
    if (!batchPollInterval) {
      batchPollInterval = setInterval(pollBatchAndKaggleStatus, 12000);
    }
  }

  // -----------------------------------------------------------
  // KAGGLE BATCH STATUS & TELEMETRY POLLING
  // -----------------------------------------------------------
  async function pollBatchAndKaggleStatus() {
    const kaggleStatusBadge = document.getElementById('kaggleStatusBadge');
    const kaggleActiveStrip = document.getElementById('kaggleActiveStrip');
    const batchProgressFraction = document.getElementById('batchProgressFraction');
    const batchProgressBarFill = document.getElementById('batchProgressBarFill');
    const batchPacingTimerText = document.getElementById('batchPacingTimerText');
    const kaggleLiveTaskText = document.getElementById('kaggleLiveTaskText');
    const kaggleUptimeText = document.getElementById('kaggleUptimeText');
    const kaggleUploadCountText = document.getElementById('kaggleUploadCountText');
    const cancelActiveBatchBtn = document.getElementById('cancelActiveBatchBtn');

    try {
      const res = await fetch('/api/batch/status');
      const data = await res.json();
      if (!data.success) return;

      const batch = data.batch || {};
      const status = data.kaggle_status || {};

      const isRunning = Boolean(status.is_running);
      const isBatchRunning = batch && batch.status === 'running';

      if (isRunning || isBatchRunning) {
        if (kaggleStatusBadge) {
          kaggleStatusBadge.textContent = '⚡ Running Batch';
          kaggleStatusBadge.style.background = 'rgba(74, 222, 128, 0.2)';
          kaggleStatusBadge.style.color = '#4ade80';
          kaggleStatusBadge.style.borderColor = '#4ade80';
        }
        if (kaggleActiveStrip) kaggleActiveStrip.classList.remove('hidden');
        if (cancelActiveBatchBtn) cancelActiveBatchBtn.classList.remove('hidden');

        const total = batch.total_count || 0;
        const done = batch.completed_count || 0;
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;

        if (batchProgressFraction) batchProgressFraction.textContent = `${done} / ${total} Videos`;
        if (batchProgressBarFill) batchProgressBarFill.style.width = `${pct}%`;

        if (kaggleLiveTaskText) kaggleLiveTaskText.textContent = status.current_task || 'Processing batch...';
        if (kaggleUptimeText) kaggleUptimeText.textContent = status.uptime_str || '0h 0m';
        if (kaggleUploadCountText) kaggleUploadCountText.textContent = status.total_uploaded_count || done;

        if (status.current_task && status.current_task.includes('Next video in')) {
          if (batchPacingTimerText) batchPacingTimerText.textContent = status.current_task;
        } else {
          if (batchPacingTimerText) batchPacingTimerText.textContent = `⚡ Uploading Video ${done + 1} of ${total}...`;
        }
      } else {
        if (kaggleStatusBadge) {
          if (status.state === 'completed' || batch.status === 'completed') {
            kaggleStatusBadge.textContent = '🟢 Batch Completed';
            kaggleStatusBadge.style.background = 'rgba(56, 189, 248, 0.2)';
            kaggleStatusBadge.style.color = '#38bdf8';
            kaggleStatusBadge.style.borderColor = '#38bdf8';
          } else {
            kaggleStatusBadge.textContent = '⚪ Ready';
            kaggleStatusBadge.style.background = 'rgba(100, 116, 139, 0.25)';
            kaggleStatusBadge.style.color = '#94a3b8';
            kaggleStatusBadge.style.borderColor = '#475569';
          }
        }
        if (cancelActiveBatchBtn) cancelActiveBatchBtn.classList.add('hidden');
      }
    } catch (err) {
      console.warn('Batch status poll error:', err);
    }
  }

  // -----------------------------------------------------------
  // KAGGLE MODAL & CONFIG LISTENERS
  // -----------------------------------------------------------
  function setupKaggleListeners() {
    const openBtn = document.getElementById('openKaggleModalBtn');
    const modal = document.getElementById('kaggleConfigModal');
    const closeBtn = document.getElementById('closeKaggleModalBtn');
    const cancelBtn = document.getElementById('cancelKaggleBtn');
    const saveBtn = document.getElementById('saveKaggleBtn');

    const userInput = document.getElementById('kaggleUserInput');
    const keyInput = document.getElementById('kaggleKeyInput');
    const slugInput = document.getElementById('kaggleSlugInput');
    const alertBox = document.getElementById('kaggleAlert');

    if (openBtn && modal) {
      openBtn.addEventListener('click', async () => {
        modal.classList.remove('hidden');
        if (alertBox) alertBox.classList.add('hidden');
        try {
          const res = await fetch('/api/kaggle/config');
          const d = await res.json();
          if (d.success && d.config) {
            if (userInput) userInput.value = d.config.kaggle_user || '';
            if (keyInput) keyInput.value = d.config.kaggle_key || '';
            if (slugInput) slugInput.value = d.config.kaggle_slug || 'bideo-automation-engine';
          }
        } catch (e) {
          console.warn('Could not load Kaggle config:', e);
        }
      });
    }

    function closeModal() {
      if (modal) modal.classList.add('hidden');
    }
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        const user = userInput ? userInput.value.trim() : '';
        const key = keyInput ? keyInput.value.trim() : '';
        const slug = slugInput ? slugInput.value.trim() : 'bideo-automation-engine';

        if (!user || !key) {
          if (alertBox) {
            alertBox.textContent = 'Kaggle Username aur API Key dono zaroori hain!';
            alertBox.className = 'alert-box error';
            alertBox.classList.remove('hidden');
          }
          return;
        }

        saveBtn.disabled = true;
        try {
          const res = await fetch('/api/kaggle/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kaggle_user: user, kaggle_key: key, kaggle_slug: slug })
          });
          const d = await res.json();
          if (d.success) {
            alert('Kaggle Configuration Saved!');
            closeModal();
          } else {
            if (alertBox) {
              alertBox.textContent = d.message || 'Failed to save';
              alertBox.className = 'alert-box error';
              alertBox.classList.remove('hidden');
            }
          }
        } catch (err) {
          if (alertBox) {
            alertBox.textContent = `Network error: ${err.message}`;
            alertBox.className = 'alert-box error';
            alertBox.classList.remove('hidden');
          }
        } finally {
          saveBtn.disabled = false;
        }
      });
    }
  }

  // -----------------------------------------------------------
  // Kickstart Application
  // -----------------------------------------------------------
  initApp();
  setupKaggleListeners();
  setupChannelBatchStudio();
});

