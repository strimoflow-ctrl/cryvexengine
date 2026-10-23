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
    pairingBideoSelect.innerHTML = '<option value="">-- Target Bideo Account Chunein --</option>';
    if (singleBideoSelect) singleBideoSelect.innerHTML = '<option value="">-- Target Bideo Account Chunein --</option>';

    savedAccounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc._id;
      opt.textContent = `${acc.name || 'Channel'} (${acc.channelName ? '@' + acc.channelName : acc.phone})`;
      if (currentActiveAccount && acc._id === currentActiveAccount._id) {
        opt.selected = true;
      }
      pairingBideoSelect.appendChild(opt);

      if (singleBideoSelect) {
        const optSingle = opt.cloneNode(true);
        singleBideoSelect.appendChild(optSingle);
      }
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
        categorySelect.innerHTML = '<option value="">-- Choose Category --</option>';
        pairingCategorySelect.innerHTML = '<option value="">-- Default Category Chunein (Optional) --</option>';
        if (singleCategorySelect) singleCategorySelect.innerHTML = '<option value="">-- Category Chunein (Optional) --</option>';

        data.categories.forEach(cat => {
          const opt1 = document.createElement('option');
          opt1.value = cat._id;
          opt1.textContent = `${cat.name} (${cat.videosCount || 0} videos)`;
          categorySelect.appendChild(opt1);

          const opt2 = document.createElement('option');
          opt2.value = cat._id;
          opt2.textContent = cat.name;
          pairingCategorySelect.appendChild(opt2);

          if (singleCategorySelect) {
            const opt3 = document.createElement('option');
            opt3.value = cat._id;
            opt3.textContent = cat.name;
            singleCategorySelect.appendChild(opt3);
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

        statActivePairings.textContent = activeCount;
        statTotalPosted.textContent = totalPostedCount;
      }
    } catch (e) {
      if (!isSilent) console.warn('Could not load pairings:', e);
    }
  }

  function renderPairings(pairings) {
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
            <button class="btn btn-primary btn-sm sync-single-btn" data-id="${p.id}" title="Run download and upload now">
              ⚡ Sync Now
            </button>
            <button class="btn btn-secondary btn-sm toggle-btn" data-id="${p.id}" title="${isActive ? 'Pause' : 'Resume'}">
              ${isActive ? '🟢 Active' : '⏸️ Paused'}
            </button>
            <button class="btn btn-secondary btn-sm delete-btn" data-id="${p.id}" style="color:#EF4444;" title="Delete">
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
        if (confirm(`Kya aap YouTube channel '${ytName}' ki automation hatana chahte hain?`)) {
          await fetch(`/api/pairings/${p.id}`, { method: 'DELETE' });
          loadPairings();
        }
      });

      pairingsContainer.appendChild(card);
    });
  }

  // Create Pairing Form Submit
  pairingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    pairingAlert.classList.add('hidden');

    const ytInput = ytChannelInput.value.trim();
    const bideoUserId = pairingBideoSelect.value;
    const catId = pairingCategorySelect.value;
    const catName = pairingCategorySelect.options[pairingCategorySelect.selectedIndex]?.text || '';

    if (!ytInput || !bideoUserId) {
      showPairingAlert('YouTube URL aur Target Bideo Account dono chunein!', 'error');
      return;
    }

    const btnText = savePairingBtn.querySelector('.btn-text');
    const spinner = savePairingBtn.querySelector('.spinner');

    btnText.textContent = 'Connecting Channel...';
    spinner.classList.remove('hidden');
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
      ytChannelInput.value = '';
      loadPairings();
      loadLogs();

      // Trigger immediate first video download & upload!
      if (data.pairing && data.pairing.id) {
        fetch(`/api/pairings/${data.pairing.id}/sync`, { method: 'POST' }).then(() => {
          setTimeout(loadLogs, 3000);
          setTimeout(loadPairings, 6000);
        }).catch(() => {});
      }

    } catch (err) {
      showPairingAlert(err.message, 'error');
    } finally {
      btnText.textContent = '➕ Connect & Activate Automation';
      spinner.classList.add('hidden');
      savePairingBtn.disabled = false;
    }
  });

  function showPairingAlert(msg, type) {
    pairingAlert.textContent = msg;
    pairingAlert.className = `alert-box ${type}`;
    pairingAlert.classList.remove('hidden');
  }

  refreshPairingsBtn.addEventListener('click', () => loadPairings());

  // Master Sync All Trigger
  syncAllBtn.addEventListener('click', async () => {
    const btnText = syncAllBtn.querySelector('.btn-text');
    const spinner = syncAllBtn.querySelector('.spinner');

    btnText.textContent = 'Running All...';
    spinner.classList.remove('hidden');
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
  // Kickstart Application
  // -----------------------------------------------------------
  initApp();
});
