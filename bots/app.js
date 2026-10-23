// Bideo Growth Studio & Video Pipeline Client Logic (Cryvex Edition)

document.addEventListener('DOMContentLoaded', () => {
  // Constants
  const CRYVEX_CHANNEL_ID = '6ada0b9dfb39968c7c48dd7b';

  // Cryvex Stats Elements
  const cryvexAvatar = document.getElementById('cryvexAvatar');
  const cryvexChannelName = document.getElementById('cryvexChannelName');
  const cryvexFollowersCount = document.getElementById('cryvexFollowersCount');
  const cryvexVideosCount = document.getElementById('cryvexVideosCount');
  const cryvexAvailableBots = document.getElementById('cryvexAvailableBots');

  // Follower Controller Elements
  const followerCountInput = document.getElementById('followerCountInput');
  const sendFollowersBtn = document.getElementById('sendFollowersBtn');
  const followAlert = document.getElementById('followAlert');
  const trackerTotalBots = document.getElementById('trackerTotalBots');
  const trackerFollowed = document.getElementById('trackerFollowed');
  const trackerAvailable = document.getElementById('trackerAvailable');
  const presetChips = document.querySelectorAll('.preset-chips .chip');

  // Video Pipeline Elements
  const videosGrid = document.getElementById('videosGrid');
  const refreshVideosBtn = document.getElementById('refreshVideosBtn');
  const passAllReviewsBtn = document.getElementById('passAllReviewsBtn');
  const toggleBatchPanelBtn = document.getElementById('toggleBatchPanelBtn');
  const batchBoostPanel = document.getElementById('batchBoostPanel');
  const executeBatchBoostBtn = document.getElementById('executeBatchBoostBtn');
  const batchViewsInput = document.getElementById('batchViewsInput');
  const batchLikesInput = document.getElementById('batchLikesInput');
  const batchWatchTimeSelect = document.getElementById('batchWatchTimeSelect');
  const batchAlert = document.getElementById('batchAlert');
  const videoActionAlert = document.getElementById('videoActionAlert');
  const farmCoinsNavBtn = document.getElementById('farmCoinsNavBtn');

  // Bot Vault Elements
  const statTotalBots = document.getElementById('statTotalBots');
  const botsContainer = document.getElementById('botsContainer');
  const botFilterInput = document.getElementById('botFilterInput');
  const refreshBotsBtn = document.getElementById('refreshBotsBtn');
  const genSingleBtn = document.getElementById('genSingleBtn');
  const gen5Btn = document.getElementById('gen5Btn');
  const gen10Btn = document.getElementById('gen10Btn');
  const customPrefix = document.getElementById('customPrefix');
  const genAlert = document.getElementById('genAlert');

  // Video Boost Modal Elements
  const videoBoostModal = document.getElementById('videoBoostModal');
  const closeVideoModalBtn = document.getElementById('closeVideoModalBtn');
  const modalVideoTitle = document.getElementById('modalVideoTitle');
  const modalVideoId = document.getElementById('modalVideoId');
  const modalViewsCount = document.getElementById('modalViewsCount');
  const modalLikesCount = document.getElementById('modalLikesCount');
  const modalWatchTime = document.getElementById('modalWatchTime');
  const confirmVideoBoostBtn = document.getElementById('confirmVideoBoostBtn');
  const modalBoostAlert = document.getElementById('modalBoostAlert');

  // Account Modal Elements
  const accountModal = document.getElementById('accountModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const modalAvatar = document.getElementById('modalAvatar');
  const modalName = document.getElementById('modalName');
  const modalId = document.getElementById('modalId');
  const modalPhone = document.getElementById('modalPhone');
  const modalPassword = document.getElementById('modalPassword');
  const modalToken = document.getElementById('modalToken');

  // Coin Vault Elements
  const cryvexCoinsVal = document.getElementById('cryvexCoinsVal');
  const coinProgressFill = document.getElementById('coinProgressFill');
  const coinProgressText = document.getElementById('coinProgressText');
  const coinCooldownStatus = document.getElementById('coinCooldownStatus');
  const dailyAdsRemaining = document.getElementById('dailyAdsRemaining');
  const claimCoinsBtn = document.getElementById('claimCoinsBtn');
  const autoMinerStatusText = document.getElementById('autoMinerStatusText');

  // State
  let allBots = [];
  let cryvexVideos = [];
  let cryvexStats = {};
  let cryvexCoins = 25;
  let selectedVideoForModal = null;

  // -----------------------------------------------------------
  // 1. Initial Data Fetching
  // -----------------------------------------------------------
  async function init() {
    await Promise.all([
      loadBots(),
      loadCryvexStats(),
      loadCryvexVideos(),
      loadCryvexCoins()
    ]);
  }

  // -----------------------------------------------------------
  // 2. Load Cryvex Stats & Follower Tracking
  // -----------------------------------------------------------
  async function loadCryvexStats() {
    try {
      const res = await fetch(`/api/cryvex/stats?channel_id=${CRYVEX_CHANNEL_ID}`);
      const data = await res.json();
      if (data.success && data.stats) {
        cryvexStats = data.stats;
        trackerTotalBots.innerHTML = `Total Vault: <b>${cryvexStats.total_bots}</b>`;
        trackerFollowed.innerHTML = `Already Followed: <b>${cryvexStats.already_followed}</b>`;
        trackerAvailable.innerHTML = `Ready to Follow: <b class="text-cyan">${cryvexStats.available_to_follow}</b>`;
        cryvexAvailableBots.textContent = cryvexStats.available_to_follow;

        // Set max on follower input
        followerCountInput.max = cryvexStats.available_to_follow || 1;
        if (parseInt(followerCountInput.value) > cryvexStats.available_to_follow) {
          followerCountInput.value = Math.max(1, cryvexStats.available_to_follow);
        }
      }
    } catch (e) {
      console.warn('Failed to load Cryvex stats:', e);
    }
  }

  // -----------------------------------------------------------
  // 3. Load Cryvex Videos
  // -----------------------------------------------------------
  async function loadCryvexVideos() {
    videosGrid.innerHTML = `
      <div class="loading-state">
        <div class="spinner-large"></div>
        <p>Loading uploaded videos from Bideo live server...</p>
      </div>
    `;

    try {
      const res = await fetch(`/api/cryvex/videos?channel_id=${CRYVEX_CHANNEL_ID}`);
      const data = await res.json();
      if (data.success && Array.isArray(data.videos)) {
        cryvexVideos = data.videos;
        cryvexVideosCount.textContent = cryvexVideos.length;
        renderVideos(cryvexVideos);
      } else {
        videosGrid.innerHTML = '<div class="empty-state">Koi uploaded video nahi mila.</div>';
      }
    } catch (e) {
      videosGrid.innerHTML = `<div class="empty-state error">Video fetch failed: ${e.message}</div>`;
    }
  }

  function renderVideos(videos) {
    if (!videos || videos.length === 0) {
      videosGrid.innerHTML = '<div class="empty-state">No videos found for this channel.</div>';
      return;
    }

    videosGrid.innerHTML = '';
    videos.forEach(v => {
      const card = document.createElement('div');
      card.className = 'video-card glass-card';

      const thumb = v.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400';
      const durationSec = Math.round(v.duration || 0);
      const mins = Math.floor(durationSec / 60);
      const secs = durationSec % 60;
      const durationStr = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

      const title = v.title || 'Untitled Video';
      const views = v.viewsCount || v.views || 0;
      const likes = v.likesCount || (Array.isArray(v.likes) ? v.likes.length : 0);
      const date = v.createdAt ? new Date(v.createdAt).toLocaleDateString() : 'Recent';

      const isPassed = v.reviewStatus === 'passed';
      const reviewBadgeHtml = isPassed
        ? `<span class="video-monetization-badge passed" title="Monetization Approved">✅ Passed</span>`
        : `<span class="video-monetization-badge in-review" title="Creator Payout Review: ${v.adsWatched || 0}/4 Ads Watched">⚡ In Review (${v.adsWatched || 0}/4)</span>`;

      card.innerHTML = `
        <div class="video-thumb-wrap">
          <img src="${thumb}" alt="Thumbnail" class="video-thumb" loading="lazy">
          <span class="video-duration">${durationStr}</span>
          <span class="video-visibility-badge" title="Publicly accessible on Bideo">Public</span>
          ${reviewBadgeHtml}
        </div>
        <div class="video-content">
          <h4 class="video-title" title="${title}">${title}</h4>
          <div class="video-meta-row">
            <span class="meta-item">👁️ <b>${views}</b> views</span>
            <span class="meta-item">❤️ <b>${likes}</b> likes</span>
            <span class="meta-item date">${date}</span>
          </div>
          <div class="video-actions">
            ${!isPassed ? `
            <button class="btn btn-warning btn-xs pass-single-review-btn" data-review-id="${v.reviewId || ''}" data-video-id="${v._id}" title="Pass this video audit review instantly without watching ads!">
              <span>⚡ Pass (No Ads)</span>
            </button>` : ''}
            <button class="btn btn-secondary btn-xs quick-boost-btn" data-id="${v._id}" title="Send 10 Views + 5 Likes + 30s Retention (100% Free Organic Boost)">
              <span>⚡ Quick +10</span>
            </button>
            <button class="btn btn-primary btn-xs custom-boost-btn" data-id="${v._id}">
              <span>⚙️ Custom</span>
            </button>
            <button class="btn btn-outline btn-xs pin-highlight-btn" data-id="${v._id}" title="Pin this video to Home Feed top highlight slots (Costs 100 Coins)">
              <span>⭐ Pin Top</span>
            </button>
          </div>
        </div>
      `;

      // Pass Review (No Ads) Single Button
      const passBtn = card.querySelector('.pass-single-review-btn');
      if (passBtn) {
        passBtn.addEventListener('click', async () => {
          passBtn.disabled = true;
          passBtn.innerHTML = '<span>⏳ Passing...</span>';
          try {
            const res = await fetch('/api/cryvex/pass-review', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ review_id: v.reviewId, video_id: v._id })
            });
            const d = await res.json();
            if (d.success) {
              showAlert(videoActionAlert, `🎉 Zabardast! Video monetization audit bina ads dekhe successfully Pass ho gayi!`, 'success');
              await loadCryvexVideos();
            } else {
              showAlert(videoActionAlert, d.message || 'Pass failed', 'error');
            }
          } catch (e) {
            showAlert(videoActionAlert, `Error: ${e.message}`, 'error');
          } finally {
            passBtn.disabled = false;
            passBtn.innerHTML = '<span>⚡ Pass (No Ads)</span>';
          }
        });
      }

      // Quick Boost Button
      const quickBtn = card.querySelector('.quick-boost-btn');
      quickBtn.addEventListener('click', async () => {
        quickBtn.disabled = true;
        quickBtn.innerHTML = '<span>⏳ Boosting...</span>';
        try {
          const res = await fetch('/api/bots/boost-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              video_id: v._id,
              views_count: 10,
              likes_count: 5,
              watch_time: 30
            })
          });
          const d = await res.json();
          if (d.success) {
            showAlert(videoActionAlert, `🎉 Zabardast! Sent ${d.views_delivered} views and ${d.likes_delivered} likes to video!`, 'success');
            setTimeout(loadCryvexVideos, 1500);
          } else {
            showAlert(videoActionAlert, d.message || 'Boost failed', 'error');
          }
        } catch (e) {
          showAlert(videoActionAlert, `Error: ${e.message}`, 'error');
        } finally {
          quickBtn.disabled = false;
          quickBtn.innerHTML = '<span>⚡ Quick +10</span>';
        }
      });

      // Pin Highlight Button
      const pinBtn = card.querySelector('.pin-highlight-btn');
      pinBtn.addEventListener('click', async () => {
        if (cryvexCoins < 100) {
          showAlert(
            videoActionAlert,
            `⚠️ Pin Top ke liye 100 Coins chahiye (Aapke paas ${cryvexCoins} Coins hain). Upar diye gaye 'Claim Free Coins' button se free coins claim karein, ya '⚡ Quick +10' use karein jo Free (0 coins) me video ko rank karata hai!`,
            'error'
          );
          return;
        }

        if (!confirm(`Kya aap is video ko Bideo Home Feed ke Top Highlight slot par pin karna chahte hain? (Cost: 100 Coins)`)) return;
        pinBtn.disabled = true;
        pinBtn.innerHTML = '<span>⏳ Pinning...</span>';
        try {
          const res = await fetch('/api/bots/pin-highlight', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: v._id, duration: 1 })
          });
          const d = await res.json();
          if (d.success) {
            showAlert(videoActionAlert, `🎉 Video Home Feed Top Highlights me pin ho gayi!`, 'success');
            await loadCryvexCoins();
          } else {
            showAlert(videoActionAlert, d.message || 'Highlight pinning failed.', 'error');
          }
        } catch (e) {
          showAlert(videoActionAlert, `Error: ${e.message}`, 'error');
        } finally {
          pinBtn.disabled = false;
          pinBtn.innerHTML = '<span>⭐ Pin Top</span>';
        }
      });

      // Custom Boost Modal
      const customBtn = card.querySelector('.custom-boost-btn');
      customBtn.addEventListener('click', () => {
        openVideoModal(v);
      });

      videosGrid.appendChild(card);
    });
  }

  // -----------------------------------------------------------
  // 4. Controllable Follower Booster
  // -----------------------------------------------------------
  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      presetChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const countVal = chip.dataset.count;
      if (countVal === 'all') {
        followerCountInput.value = cryvexStats.available_to_follow || 1;
      } else {
        followerCountInput.value = Math.min(parseInt(countVal), cryvexStats.available_to_follow || 1);
      }
    });
  });

  sendFollowersBtn.addEventListener('click', async () => {
    const count = parseInt(followerCountInput.value) || 5;
    if (count <= 0) {
      showAlert(followAlert, 'Kripya kam se kam 1 bot select karein!', 'error');
      return;
    }

    setLoading(sendFollowersBtn, true);
    followAlert.classList.add('hidden');

    try {
      const res = await fetch('/api/bots/follow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_channel_id: CRYVEX_CHANNEL_ID,
          count: count
        })
      });
      const data = await res.json();

      if (data.success) {
        showAlert(
          followAlert,
          `🎉 Zabardast! Successfully sent ${data.followed_count} new followers to Cryvex! Sabhi bot accounts views ke liye active hain.`,
          'success'
        );
        // Refresh live follower count and stats
        await loadCryvexStats();
      } else {
        showAlert(followAlert, data.message || 'Follower boost failed', 'error');
      }
    } catch (e) {
      showAlert(followAlert, `Network Error: ${e.message}`, 'error');
    } finally {
      setLoading(sendFollowersBtn, false);
    }
  });

  // -----------------------------------------------------------
  // 5. Batch Boost All Videos
  // -----------------------------------------------------------
  toggleBatchPanelBtn.addEventListener('click', () => {
    batchBoostPanel.classList.toggle('hidden');
  });

  executeBatchBoostBtn.addEventListener('click', async () => {
    const views = parseInt(batchViewsInput.value) || 5;
    const likes = parseInt(batchLikesInput.value) || 3;
    const watchTime = parseInt(batchWatchTimeSelect.value) || 30;

    if (!confirm(`Sare ${cryvexVideos.length} videos par ${views} views aur ${likes} likes bhejein?`)) return;

    setLoading(executeBatchBoostBtn, true);
    batchAlert.classList.add('hidden');

    try {
      const res = await fetch('/api/bots/batch-boost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel_id: CRYVEX_CHANNEL_ID,
          views_per_video: views,
          likes_per_video: likes,
          watch_time: watchTime
        })
      });
      const data = await res.json();

      if (data.success) {
        showAlert(
          batchAlert,
          `🎉 Batch Complete! Boosted ${data.videos_boosted} videos. Delivered: ${data.total_views_delivered} views, ${data.total_likes_delivered} likes!`,
          'success'
        );
        setTimeout(loadCryvexVideos, 2000);
      } else {
        showAlert(batchAlert, data.message || 'Batch boost failed', 'error');
      }
    } catch (e) {
      showAlert(batchAlert, `Error: ${e.message}`, 'error');
    } finally {
      setLoading(executeBatchBoostBtn, false);
    }
  });

  if (refreshVideosBtn) {
    refreshVideosBtn.addEventListener('click', loadCryvexVideos);
  }

  if (passAllReviewsBtn) {
    passAllReviewsBtn.addEventListener('click', async () => {
      if (!confirm('Kya aap sabhi In-Review videos ko bina koi ad dekhe turant Pass karwana chahte hain?')) return;
      passAllReviewsBtn.disabled = true;
      passAllReviewsBtn.innerHTML = '<span>⏳ Passing All Videos...</span>';
      try {
        const res = await fetch('/api/cryvex/pass-all-reviews', { method: 'POST' });
        const d = await res.json();
        if (d.success) {
          showAlert(videoActionAlert, d.message || `🎉 Sabhi videos successfully pass ho gayi!`, 'success');
          await loadCryvexVideos();
        } else {
          showAlert(videoActionAlert, d.message || 'Pass all failed', 'error');
        }
      } catch (e) {
        showAlert(videoActionAlert, `Error: ${e.message}`, 'error');
      } finally {
        passAllReviewsBtn.disabled = false;
        passAllReviewsBtn.innerHTML = '⚡ 1-Click Pass All (No Ads)';
      }
    });
  }

  // -----------------------------------------------------------
  // 6. Farm Coins Button
  // -----------------------------------------------------------
  farmCoinsNavBtn.addEventListener('click', async () => {
    farmCoinsNavBtn.disabled = true;
    farmCoinsNavBtn.innerHTML = '<span>⏳ Farming Coins...</span>';
    try {
      const res = await fetch('/api/bots/farm-coins', { method: 'POST' });
      const d = await res.json();
      if (d.success) {
        alert(`🪙 Successfully claimed ${d.coins_farmed} free boost coins from ad rewards!`);
      }
    } catch (e) {
      alert(`Error farming coins: ${e.message}`);
    } finally {
      farmCoinsNavBtn.disabled = false;
      farmCoinsNavBtn.innerHTML = '<span>🪙 Farm Boost Coins</span>';
    }
  });

  // -----------------------------------------------------------
  // 7. Video Boost Modal
  // -----------------------------------------------------------
  function openVideoModal(video) {
    selectedVideoForModal = video;
    modalVideoTitle.textContent = video.title || 'Boost Video';
    modalVideoId.textContent = `ID: ${video._id}`;
    modalBoostAlert.classList.add('hidden');
    videoBoostModal.classList.remove('hidden');
  }

  closeVideoModalBtn.addEventListener('click', () => {
    videoBoostModal.classList.add('hidden');
    selectedVideoForModal = null;
  });

  confirmVideoBoostBtn.addEventListener('click', async () => {
    if (!selectedVideoForModal) return;

    const views = parseInt(modalViewsCount.value) || 10;
    const likes = parseInt(modalLikesCount.value) || 5;
    const watchTime = parseInt(modalWatchTime.value) || 30;

    setLoading(confirmVideoBoostBtn, true);
    modalBoostAlert.classList.add('hidden');

    try {
      const res = await fetch('/api/bots/boost-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: selectedVideoForModal._id,
          views_count: views,
          likes_count: likes,
          watch_time: watchTime
        })
      });
      const data = await res.json();

      if (data.success) {
        showAlert(
          modalBoostAlert,
          `Delivered ${data.views_delivered} views and ${data.likes_delivered} likes with ${data.watch_time_seconds}s retention!`,
          'success'
        );
        setTimeout(() => {
          videoBoostModal.classList.add('hidden');
          loadCryvexVideos();
        }, 1500);
      } else {
        showAlert(modalBoostAlert, data.message || 'Boost failed', 'error');
      }
    } catch (e) {
      showAlert(modalBoostAlert, `Error: ${e.message}`, 'error');
    } finally {
      setLoading(confirmVideoBoostBtn, false);
    }
  });

  // -----------------------------------------------------------
  // 8. Bot Accounts Management
  // -----------------------------------------------------------
  async function loadBots() {
    try {
      const res = await fetch('/api/bots');
      const data = await res.json();
      if (data.success && data.bots) {
        allBots = data.bots;
        statTotalBots.textContent = allBots.length;
        renderBots(allBots);
      }
    } catch (e) {
      console.warn('Failed to load bots:', e);
    }
  }

  function renderBots(botsToRender) {
    if (!botsToRender || botsToRender.length === 0) {
      botsContainer.innerHTML = '<div class="empty-state">No bot accounts found. Generate bots on the left!</div>';
      return;
    }

    botsContainer.innerHTML = '';
    botsToRender.forEach(bot => {
      const card = document.createElement('div');
      card.className = 'bot-card-item';

      const avatar = bot.avatar || `https://api.dicebear.com/9.x/initials/svg?seed=${bot.name}`;
      const name = bot.name || 'Bot Account';
      const phone = bot.phone || 'N/A';

      card.innerHTML = `
        <img src="${avatar}" alt="Avatar" class="bot-avatar">
        <div class="bot-info">
          <div class="bot-name">${name}</div>
          <div class="bot-phone">📱 ${phone}</div>
        </div>
        <div class="bot-actions-row">
          <span class="view-badge">Vault</span>
          <button class="delete-bot-btn" data-id="${bot._id}" title="Delete Bot">🗑️</button>
        </div>
      `;

      card.addEventListener('click', (e) => {
        if (e.target.closest('.delete-bot-btn')) return;
        openAccountModal(bot);
      });

      const deleteBtn = card.querySelector('.delete-bot-btn');
      deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm(`Account '${name}' (${phone}) ko delete karna chahte hain?`)) {
          await fetch(`/api/bots/${bot._id}`, { method: 'DELETE' });
          await loadBots();
          await loadCryvexStats();
        }
      });

      botsContainer.appendChild(card);
    });
  }

  botFilterInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderBots(allBots);
      return;
    }
    const filtered = allBots.filter(b =>
      (b.name && b.name.toLowerCase().includes(q)) ||
      (b.phone && b.phone.includes(q))
    );
    renderBots(filtered);
  });

  refreshBotsBtn.addEventListener('click', () => {
    loadBots();
    loadCryvexStats();
  });

  refreshVideosBtn.addEventListener('click', loadCryvexVideos);

  // -----------------------------------------------------------
  // 9. Bot Generator Actions
  // -----------------------------------------------------------
  async function handleGenerate(count, btn) {
    setLoading(btn, true);
    genAlert.classList.add('hidden');

    try {
      const res = await fetch('/api/bots/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          count: count,
          custom_name: customPrefix.value.trim() || null
        })
      });
      const data = await res.json();

      if (data.success) {
        showAlert(genAlert, data.message || `Successfully created ${count} accounts!`, 'success');
        customPrefix.value = '';
        await loadBots();
        await loadCryvexStats();
      } else {
        showAlert(genAlert, data.message || 'Generation failed', 'error');
      }
    } catch (e) {
      showAlert(genAlert, `Error: ${e.message}`, 'error');
    } finally {
      setLoading(btn, false);
    }
  }

  genSingleBtn.addEventListener('click', () => handleGenerate(1, genSingleBtn));
  gen5Btn.addEventListener('click', () => handleGenerate(5, gen5Btn));
  gen10Btn.addEventListener('click', () => handleGenerate(10, gen10Btn));

  // -----------------------------------------------------------
  // 10. Account Modal
  // -----------------------------------------------------------
  function openAccountModal(bot) {
    modalAvatar.src = bot.avatar || `https://api.dicebear.com/9.x/initials/svg?seed=${bot.name}`;
    modalName.textContent = bot.name || 'Account';
    modalId.textContent = `ID: ${bot._id}`;
    modalPhone.value = bot.phone || '';
    modalPassword.value = bot.password || '';
    modalToken.value = bot.token || '';
    accountModal.classList.remove('hidden');
  }

  closeModalBtn.addEventListener('click', () => {
    accountModal.classList.add('hidden');
  });

  // Copy Buttons
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetId = e.target.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input && input.value) {
        navigator.clipboard.writeText(input.value);
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => {
          btn.textContent = originalText;
        }, 1500);
      }
    });
  });

  // -----------------------------------------------------------
  // 11. Cryvex Coin Vault & Free Coin Farming
  // -----------------------------------------------------------
  async function loadCryvexCoins() {
    try {
      const [resCoins, resMiner] = await Promise.all([
        fetch('/api/cryvex/coins'),
        fetch('/api/cryvex/auto-miner-status').catch(() => null)
      ]);
      const data = await resCoins.json();
      if (data.success) {
        cryvexCoins = data.coins || 0;
        if (cryvexCoinsVal) cryvexCoinsVal.textContent = cryvexCoins;

        const pct = Math.min(100, Math.round((cryvexCoins / 100) * 100));
        if (coinProgressFill) coinProgressFill.style.width = `${pct}%`;
        if (coinProgressText) coinProgressText.textContent = `${cryvexCoins} / 100 Coins (${pct}%)`;

        const daily = data.dailyAds || {};
        const dailyRemaining = daily.remaining !== undefined ? daily.remaining : Math.max(0, (daily.total || 16) - (daily.watched || 0));
        if (dailyAdsRemaining) dailyAdsRemaining.textContent = `${dailyRemaining} Daily Claims Left`;

        // Check if cooldown is active
        const hasCooldown = (daily.canWatch === false) || (daily.cooldownSeconds && daily.cooldownSeconds > 0);
        if (hasCooldown) {
          const secs = daily.cooldownSeconds || 600;
          const diffMins = Math.ceil(secs / 60);
          if (coinCooldownStatus) {
            coinCooldownStatus.className = 'cooldown-tag cooldown';
            coinCooldownStatus.textContent = `⏳ Cooldown: ${diffMins}m remaining`;
          }
          if (claimCoinsBtn) {
            claimCoinsBtn.disabled = true;
            claimCoinsBtn.innerHTML = `<span>⏳ Cooldown (${diffMins}m)</span>`;
          }
        } else {
          if (coinCooldownStatus) {
            coinCooldownStatus.className = 'cooldown-tag ready';
            coinCooldownStatus.textContent = '🟢 Ready to Claim!';
          }
          if (claimCoinsBtn) {
            claimCoinsBtn.disabled = false;
            claimCoinsBtn.innerHTML = '<span>🪙 Instant Claim (+2 to +5)</span>';
          }
        }
      }

      // Update Auto-Miner Live Text
      if (resMiner && resMiner.ok) {
        const mData = await resMiner.json();
        if (mData.success && mData.status && autoMinerStatusText) {
          const st = mData.status;
          if (st.message) {
            autoMinerStatusText.innerHTML = `🤖 <b>Auto-Miner:</b> ${st.message}`;
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load Cryvex coins:', e);
    }
  }

  async function claimCryvexCoins() {
    if (!claimCoinsBtn) return;
    claimCoinsBtn.disabled = true;
    claimCoinsBtn.innerHTML = '<span>⏳ Claiming Coins...</span>';

    try {
      const res = await fetch('/api/cryvex/claim-coins', { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        const earned = data.coinsEarned || data.reward || 3;
        const total = data.totalCoins || data.coins || cryvexCoins;
        showAlert(
          videoActionAlert,
          `🎉 Coin Claim Success! +${earned} Free Coins add ho gaye! Cryvex New Balance: ${total} Coins.`,
          'success'
        );
        await loadCryvexCoins();
      } else {
        showAlert(
          videoActionAlert,
          `⚠️ ${data.message || 'Coin claim failed or cooldown active.'}`,
          'error'
        );
        await loadCryvexCoins();
      }
    } catch (e) {
      showAlert(videoActionAlert, `Error: ${e.message}`, 'error');
    } finally {
      if (claimCoinsBtn && !claimCoinsBtn.disabled) {
        claimCoinsBtn.innerHTML = '<span>🪙 Claim Free Coins (+2 to +5)</span>';
      }
    }
  }

  if (claimCoinsBtn) {
    claimCoinsBtn.addEventListener('click', claimCryvexCoins);
  }

  // -----------------------------------------------------------
  // Helper Functions
  // -----------------------------------------------------------
  function setLoading(btn, isLoading) {
    btn.disabled = isLoading;
    const spinner = btn.querySelector('.spinner');
    if (spinner) {
      if (isLoading) spinner.classList.remove('hidden');
      else spinner.classList.add('hidden');
    }
  }

  function showAlert(alertEl, message, type = 'success') {
    alertEl.textContent = message;
    alertEl.className = `alert-box ${type}`;
    alertEl.classList.remove('hidden');
  }

  // -----------------------------------------------------------
  // 24/7 AUTONOMOUS CLOUD FARMING CONTROLLER (CLIENT LOGIC)
  // -----------------------------------------------------------
  const farmToggleBtn = document.getElementById('farmToggleBtn');
  const farmToggleIcon = document.getElementById('farmToggleIcon');
  const farmToggleText = document.getElementById('farmToggleText');
  const farmStatusBadge = document.getElementById('farmStatusBadge');
  const farmBotsCount = document.getElementById('farmBotsCount');
  const farmBotsFill = document.getElementById('farmBotsFill');
  const farmNextSpawnTag = document.getElementById('farmNextSpawnTag');
  const farmNextViewCountdown = document.getElementById('farmNextViewCountdown');
  const farmCryvexViews = document.getElementById('farmCryvexViews');
  const farmCryvexInteractions = document.getElementById('farmCryvexInteractions');
  const farmStealthViews = document.getElementById('farmStealthViews');
  const farmReviewsPassedVal = document.getElementById('farmReviewsPassedVal');
  const farmTerminalLogs = document.getElementById('farmTerminalLogs');

  function formatSeconds(secs) {
    if (isNaN(secs) || secs <= 0) return '00:00';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  async function loadFarmStatus() {
    try {
      const res = await fetch('/api/farm/status');
      const data = await res.json();
      if (!data.success || !data.status) return;

      const st = data.status;

      // Status Badge & Toggle Button
      if (farmStatusBadge) {
        if (st.is_active) {
          farmStatusBadge.textContent = '🟢 24/7 Active';
          farmStatusBadge.className = 'status-live-badge';
          if (farmToggleIcon) farmToggleIcon.textContent = '⏸️';
          if (farmToggleText) farmToggleText.textContent = 'Pause Farm';
          if (farmToggleBtn) farmToggleBtn.className = 'btn btn-secondary btn-sm';
        } else {
          farmStatusBadge.textContent = '🔴 Paused';
          farmStatusBadge.className = 'status-live-badge text-dim';
          if (farmToggleIcon) farmToggleIcon.textContent = '▶️';
          if (farmToggleText) farmToggleText.textContent = 'Resume Farm';
          if (farmToggleBtn) farmToggleBtn.className = 'btn btn-primary btn-sm';
        }
      }

      // Bots Pool & Progress
      const totalBots = st.total_bots || 0;
      const maxBots = st.max_bots || 150;
      const pct = Math.min(100, Math.round((totalBots / maxBots) * 100));
      if (farmBotsCount) farmBotsCount.textContent = totalBots;
      if (farmBotsFill) farmBotsFill.style.width = `${pct}%`;

      // Next Bot Spawner Tag
      if (farmNextSpawnTag) {
        if (totalBots >= maxBots) {
          farmNextSpawnTag.textContent = 'Cap Reached (150/150)';
          farmNextSpawnTag.className = 'tile-tag green-tag';
        } else {
          const spawnMins = Math.ceil((st.next_spawn_seconds || 3600) / 60);
          farmNextSpawnTag.textContent = `Spawn in: ~${spawnMins}m`;
          farmNextSpawnTag.className = 'tile-tag cyan-tag';
        }
      }

      // Anti-Rush Next View Countdown
      if (farmNextViewCountdown) {
        const nextViewSec = st.next_cryvex_view_seconds || 0;
        if (nextViewSec > 0) {
          farmNextViewCountdown.textContent = formatSeconds(nextViewSec);
          farmNextViewCountdown.className = 'tile-main-val text-cyan';
        } else {
          farmNextViewCountdown.textContent = 'Active';
          farmNextViewCountdown.className = 'tile-main-val text-orange';
        }
      }

      // Cryvex Engagement metrics
      if (farmCryvexViews) farmCryvexViews.textContent = st.cryvex_views_today || 0;
      if (farmCryvexInteractions) {
        farmCryvexInteractions.innerHTML = `❤️ <b>${st.cryvex_likes_today || 0}</b> Likes (50%) • 💬 <b>${st.cryvex_comments_today || 0}</b> Comments (30%)`;
      }

      // Stealth Views & Reviews Passed
      if (farmStealthViews) farmStealthViews.textContent = st.stealth_views_today || 0;
      if (farmReviewsPassedVal) farmReviewsPassedVal.textContent = (st.reviews_passed_total || 0) + 13;

      // Terminal logs rendering
      if (farmTerminalLogs && Array.isArray(st.recent_logs)) {
        if (st.recent_logs.length > 0) {
          farmTerminalLogs.innerHTML = st.recent_logs.map(log => {
            const catClass = log.category || 'info';
            return `<div class="term-line">
              <span class="term-time">[${log.time || 'NOW'}]</span>
              <span class="term-msg ${catClass}"><b>${log.title}:</b> ${log.message}</span>
            </div>`;
          }).join('');
        }
      }

    } catch (e) {
      console.warn('Failed to load farm status:', e);
    }
  }

  if (farmToggleBtn) {
    farmToggleBtn.addEventListener('click', async () => {
      farmToggleBtn.disabled = true;
      try {
        const res = await fetch('/api/farm/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        await res.json();
        await loadFarmStatus();
      } catch (e) {
        console.error('Failed to toggle farm:', e);
      } finally {
        farmToggleBtn.disabled = false;
      }
    });
  }

  // Start
  init();
  loadFarmStatus();

  // 24/7 background live sync
  setInterval(loadCryvexCoins, 15000);
  setInterval(loadFarmStatus, 4000);
});

