// BIDEO CYBER CORE v3.6 - 24/7 PODIUM COIN MINER HUD
// Dedicated 100% Autonomous Coin Domination Engine

document.addEventListener('DOMContentLoaded', () => {

  // -------------------------------------------------------------
  // DOM Elements
  // -------------------------------------------------------------
  const podiumRank1Coins = document.getElementById('podiumRank1Coins');
  const podiumRank1Ads = document.getElementById('podiumRank1Ads');
  const podiumRank2Coins = document.getElementById('podiumRank2Coins');
  const podiumRank2Ads = document.getElementById('podiumRank2Ads');
  const podiumRank3Coins = document.getElementById('podiumRank3Coins');
  const podiumRank3Ads = document.getElementById('podiumRank3Ads');
  const refreshPodiumBtn = document.getElementById('refreshPodiumBtn');

  const cryvexCoinsVal = document.getElementById('cryvexCoinsVal');
  const autoMinerBadge = document.getElementById('autoMinerBadge');
  const autoMinerStatusText = document.getElementById('autoMinerStatusText');
  const coinProgressFill = document.getElementById('coinProgressFill');
  const coinProgressText = document.getElementById('coinProgressText');
  const coinCooldownStatus = document.getElementById('coinCooldownStatus');
  const dailyAdsRemaining = document.getElementById('dailyAdsRemaining');
  const claimCoinsBtn = document.getElementById('claimCoinsBtn');
  const farmCoinsNavBtn = document.getElementById('farmCoinsNavBtn');

  const farmTerminalLogs = document.getElementById('farmTerminalLogs');
  const clearTermBtn = document.getElementById('clearTermBtn');

  let currentLogFilter = 'all';
  let cachedLogs = [];

  // -------------------------------------------------------------
  // 1. Live Podium Status & Terminal Stream Sync
  // -------------------------------------------------------------
  async function loadPodiumStatus() {
    try {
      const res = await fetch('/api/podium/status');
      const data = await res.json();
      if (!data.success || !data.podium) return;

      const pod = data.podium;
      const accounts = pod.accounts || [];

      // Update Top 3 Cards
      accounts.forEach(acc => {
        const coinsStr = Number(acc.coins || 0).toLocaleString('en-US', {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1
        });
        const adsWatched = acc.ads_watched || (16 - (acc.ads_remaining ?? 4));
        const adsStr = `${adsWatched}/16`;

        if (acc.rank === 1) {
          if (podiumRank1Coins) podiumRank1Coins.textContent = coinsStr;
          if (podiumRank1Ads) podiumRank1Ads.textContent = adsStr;
          if (cryvexCoinsVal) cryvexCoinsVal.textContent = coinsStr;
        } else if (acc.rank === 2) {
          if (podiumRank2Coins) podiumRank2Coins.textContent = coinsStr;
          if (podiumRank2Ads) podiumRank2Ads.textContent = adsStr;
        } else if (acc.rank === 3) {
          if (podiumRank3Coins) podiumRank3Coins.textContent = coinsStr;
          if (podiumRank3Ads) podiumRank3Ads.textContent = adsStr;
        }

        // Update 24H Limit & Toggle UI for this account
        const user = acc.username;
        const toggleEl = document.getElementById(`toggleMiner_${user}`);
        const limitInput = document.getElementById(`limitInput_${user}`);
        const barEl = document.getElementById(`barMined_${user}`);
        const txtEl = document.getElementById(`txtMined_${user}`);
        const badgeEl = document.getElementById(`statusBadge_${user}`);

        if (toggleEl && document.activeElement !== toggleEl) {
          toggleEl.checked = acc.enabled !== false;
        }

        if (limitInput && document.activeElement !== limitInput) {
          if (acc.daily_limit !== undefined) {
            limitInput.value = acc.daily_limit;
          }
        }

        const mined = Number(acc.mined_24h || 0);
        const limit = Number(acc.daily_limit || 0);

        if (barEl) {
          const pct = limit > 0 ? Math.min(100, Math.round((mined / limit) * 100)) : 100;
          barEl.style.width = `${pct}%`;
        }

        if (txtEl) {
          txtEl.textContent = limit > 0
            ? `${mined.toFixed(1)} / ${limit} Coins (24h)`
            : `${mined.toFixed(1)} Coins (Unlimited)`;
        }

        if (badgeEl) {
          if (acc.enabled === false) {
            badgeEl.className = 'ctrl-status-badge paused';
            badgeEl.textContent = '⏸️ MINING PAUSED (OFF)';
          } else if (limit > 0 && mined >= limit) {
            badgeEl.className = 'ctrl-status-badge limit';
            badgeEl.textContent = '⚠️ 24H LIMIT REACHED';
          } else {
            badgeEl.className = 'ctrl-status-badge active';
            badgeEl.textContent = '🟢 MINING ACTIVE';
          }
        }
      });

      // Render Extra Miners (> Rank 3)
      const extraGrid = document.getElementById('extraMinersGrid');
      if (extraGrid) {
        const extraAccounts = accounts.filter(a => a.rank > 3);
        if (extraAccounts.length === 0) {
          extraGrid.innerHTML = '';
        } else {
          extraGrid.innerHTML = extraAccounts.map(acc => {
            const mined = Number(acc.mined_24h || 0);
            const limit = Number(acc.daily_limit || 50);
            const pct = limit > 0 ? Math.min(100, Math.round((mined / limit) * 100)) : 100;
            const coinsStr = Number(acc.coins || 0).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
            const isPaused = acc.enabled === false;
            const isLimit = limit > 0 && mined >= limit;
            const badgeClass = isPaused ? 'ctrl-status-badge paused' : (isLimit ? 'ctrl-status-badge limit' : 'ctrl-status-badge active');
            const badgeText = isPaused ? '⏸️ PAUSED' : (isLimit ? '⚠️ LIMIT REACHED' : '🟢 MINING ACTIVE');
            return `
              <div class="podium-card extra-miner-card" style="border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 14px; background: rgba(15, 23, 42, 0.85);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span class="meta-pill" style="color: #fbbf24; font-weight: bold;">${acc.label || ('Miner #' + acc.rank)}</span>
                  <button class="btn-remove-miner" data-user="${acc.username}" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem; font-weight: bold;" title="Remove Miner">🗑️ Remove</button>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                  <div>
                    <h4 style="margin: 0; color: #fff; font-size: 1rem;">${acc.username}</h4>
                    <span style="font-size: 0.75rem; color: #94a3b8;">${acc.phone}</span>
                  </div>
                  <div style="text-align: right;">
                    <span style="font-size: 1.15rem; font-weight: bold; color: #fbbf24;">${coinsStr}</span>
                    <span style="font-size: 0.75rem; color: #94a3b8; display: block;">COINS</span>
                  </div>
                </div>
                <div class="podium-controls-box" style="margin-top: 8px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                  <div class="ctrl-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="ctrl-label" style="font-size: 0.75rem;">⚡ 24H BUDGET:</span>
                    <label class="cyber-switch">
                      <input type="checkbox" class="toggle-extra-miner" data-user="${acc.username}" ${!isPaused ? 'checked' : ''}>
                      <span class="cyber-slider"></span>
                    </label>
                  </div>
                  <div class="ctrl-limit-row" style="display: flex; gap: 8px; margin: 8px 0;">
                    <input type="number" class="limit-input-extra cyber-input-limit" data-user="${acc.username}" value="${limit}" min="0" step="5" style="width: 80px;">
                    <button class="btn-save-extra-limit" data-user="${acc.username}" style="padding: 4px 10px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; font-size: 0.75rem; cursor: pointer;">SAVE</button>
                  </div>
                  <div class="ctrl-progress-row">
                    <div class="ctrl-bar-track" style="height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden;">
                      <div class="ctrl-bar-fill gold-fill" style="width: ${pct}%; height: 100%; background: #f59e0b;"></div>
                    </div>
                    <span class="ctrl-mined-txt" style="font-size: 0.75rem; color: #94a3b8; display: block; margin-top: 4px;">${mined.toFixed(1)} / ${limit} Coins</span>
                  </div>
                  <div class="${badgeClass}" style="margin-top: 6px; font-size: 0.75rem;">${badgeText}</div>
                </div>
              </div>
            `;
          }).join('');
        }
      }

      // Update Live Terminal Logs
      if (Array.isArray(pod.recent_logs) && pod.recent_logs.length > 0) {
        cachedLogs = pod.recent_logs;
        renderTerminalLogs();
      }

    } catch (e) {
      // Quiet fail on network hiccup
    }
  }

  // -------------------------------------------------------------
  // 2. Render Cyberpunk Terminal Logs
  // -------------------------------------------------------------
  function renderTerminalLogs() {
    if (!farmTerminalLogs) return;

    let filtered = cachedLogs;
    if (currentLogFilter === 'coin') {
      filtered = cachedLogs.filter(l => {
        const text = `${l.title} ${l.message}`.toLowerCase();
        return text.includes('coin') || text.includes('reward') || text.includes('ad');
      });
    } else if (currentLogFilter === 'stream') {
      filtered = cachedLogs.filter(l => {
        const text = `${l.title} ${l.message}`.toLowerCase();
        return text.includes('stream') || text.includes('watch');
      });
    } else if (currentLogFilter === 'podium') {
      filtered = cachedLogs.filter(l => {
        const text = `${l.title} ${l.message}`.toLowerCase();
        return text.includes('podium') || text.includes('rank') || text.includes('pacing');
      });
    }

    if (filtered.length > 0) {
      farmTerminalLogs.innerHTML = filtered.map(log => {
        const raw = `${log.title} ${log.message}`.toLowerCase();
        let catClass = log.category || 'info';
        if (raw.includes('coin') || raw.includes('reward') || raw.includes('+1.0') || raw.includes('+2.0')) {
          catClass = 'coin-reward';
        } else if (raw.includes('stream') || raw.includes('watched')) {
          catClass = 'info';
        } else if (raw.includes('podium') || raw.includes('rank')) {
          catClass = 'stealth';
        }
        return `<div class="term-line">
          <span class="term-time">[${log.time || 'NOW'}]</span>
          <span class="term-msg ${catClass}"><b>${log.title}:</b> ${log.message}</span>
        </div>`;
      }).join('');
    } else if (cachedLogs.length > 0) {
      farmTerminalLogs.innerHTML = `<div class="term-line"><span class="term-time">[FILTER]</span> <span class="term-msg text-dim">No log entries matching '[${currentLogFilter.toUpperCase()}]' yet.</span></div>`;
    }
  }

  // -------------------------------------------------------------
  // 3. Terminal Tabs Filter
  // -------------------------------------------------------------
  document.querySelectorAll('.term-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.term-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentLogFilter = btn.getAttribute('data-filter') || 'all';
      renderTerminalLogs();
    });
  });

  if (clearTermBtn) {
    clearTermBtn.addEventListener('click', () => {
      if (farmTerminalLogs) {
        farmTerminalLogs.innerHTML = `<div class="term-line"><span class="term-time">[SYSTEM]</span> <span class="term-msg info">Terminal buffer cleared. Listening to live coin streams...</span></div>`;
      }
    });
  }

  // -------------------------------------------------------------
  // 4. Cryvex Vault Details & Auto-Miner Status
  // -------------------------------------------------------------
  async function loadCryvexCoins() {
    try {
      const [resCoins, resMiner] = await Promise.all([
        fetch('/api/cryvex/coins'),
        fetch('/api/cryvex/auto-miner-status').catch(() => null)
      ]);

      const data = await resCoins.json();
      if (data.success) {
        const coins = data.coins || 0;
        if (cryvexCoinsVal) {
          cryvexCoinsVal.textContent = Number(coins).toLocaleString('en-US', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
          });
        }

        if (coinProgressFill) coinProgressFill.style.width = `100%`;
        if (coinProgressText) coinProgressText.textContent = `⚡ 24/7 Turbo Multi-Stream Mining Active (No Limits)`;

        const daily = data.dailyAds || {};
        const dailyRemaining = daily.remaining !== undefined ? daily.remaining : Math.max(0, (daily.total || 16) - (daily.watched || 0));
        if (dailyAdsRemaining) dailyAdsRemaining.textContent = `${dailyRemaining} Daily Claims Left`;

        // Cooldown evaluation
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
      // Quiet fail
    }
  }

  // -------------------------------------------------------------
  // 5. 1-Click Instant Ad Claim
  // -------------------------------------------------------------
  async function claimCryvexCoins() {
    if (!claimCoinsBtn) return;
    claimCoinsBtn.disabled = true;
    claimCoinsBtn.innerHTML = '<span>⏳ Claiming Reward...</span>';

    try {
      const res = await fetch('/api/cryvex/claim-coins', { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        const earned = data.coinsEarned || data.reward || 2;
        claimCoinsBtn.innerHTML = `<span style="color: #00FF66;">✅ +${earned} Coins Claimed!</span>`;
        if (autoMinerStatusText) {
          autoMinerStatusText.innerHTML = `🎉 <b>Claim Success!</b> +${earned} Coins added to Cryvex Vault!`;
        }
        await loadCryvexCoins();
        await loadPodiumStatus();
      } else {
        claimCoinsBtn.innerHTML = `<span>⚠️ ${data.message || 'Cooldown Active'}</span>`;
        await loadCryvexCoins();
      }
    } catch (e) {
      claimCoinsBtn.innerHTML = `<span>⚠️ Failed</span>`;
    } finally {
      setTimeout(() => {
        if (claimCoinsBtn && !claimCoinsBtn.disabled) {
          claimCoinsBtn.innerHTML = '<span>🪙 Instant Claim (+2 to +5)</span>';
        }
      }, 3000);
    }
  }

  if (claimCoinsBtn) {
    claimCoinsBtn.addEventListener('click', claimCryvexCoins);
  }

  if (farmCoinsNavBtn) {
    farmCoinsNavBtn.addEventListener('click', () => {
      if (claimCoinsBtn) {
        claimCoinsBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
        claimCryvexCoins();
      }
    });
  }

  if (refreshPodiumBtn) {
    refreshPodiumBtn.addEventListener('click', () => {
      loadPodiumStatus();
      loadCryvexCoins();
    });
  }

  // -------------------------------------------------------------
  // 5b. 24H Coin Mining Limit & Toggle Controls
  // -------------------------------------------------------------
  document.querySelectorAll('.cyber-switch input').forEach(input => {
    input.addEventListener('change', async (e) => {
      const user = e.target.dataset.user;
      const enabled = e.target.checked;
      const limitInput = document.getElementById(`limitInput_${user}`);
      const limit = limitInput ? Number(limitInput.value) : 100;

      try {
        await fetch('/api/miner/limits', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: user, enabled, daily_limit: limit })
        });
        loadPodiumStatus();
      } catch (err) {
        console.error('Limit toggle error:', err);
      }
    });
  });

  document.querySelectorAll('.btn-save-limit').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const user = e.target.dataset.user;
      const limitInput = document.getElementById(`limitInput_${user}`);
      const toggleEl = document.getElementById(`toggleMiner_${user}`);
      const limit = limitInput ? Number(limitInput.value) : 100;
      const enabled = toggleEl ? toggleEl.checked : true;

      const originalText = e.target.textContent;
      e.target.textContent = 'SAVED!';
      e.target.style.background = '#10B981';
      e.target.style.color = '#fff';

      try {
        await fetch('/api/miner/limits', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: user, enabled, daily_limit: limit })
        });
        loadPodiumStatus();
      } catch (err) {
        console.error('Save limit error:', err);
      } finally {
        setTimeout(() => {
          e.target.textContent = originalText;
          e.target.style.background = '';
          e.target.style.color = '';
        }, 1200);
      }
    });
  });

  // Handle Add Miner Account
  const addMinerBtn = document.getElementById('addMinerBtn');
  const newMinerPhone = document.getElementById('newMinerPhone');
  const newMinerPassword = document.getElementById('newMinerPassword');
  const newMinerLimit = document.getElementById('newMinerLimit');

  if (addMinerBtn) {
    addMinerBtn.addEventListener('click', async () => {
      const phone = newMinerPhone ? newMinerPhone.value.trim() : '';
      const password = newMinerPassword ? newMinerPassword.value.trim() : '';
      const daily_limit = newMinerLimit ? Number(newMinerLimit.value) : 50;

      if (!phone || !password) {
        alert('Kripya Phone Number aur Password dono enter karein!');
        return;
      }

      const origText = addMinerBtn.innerHTML;
      addMinerBtn.innerHTML = '<span>ADDING...</span>';
      addMinerBtn.disabled = true;

      try {
        const res = await fetch('/api/podium/accounts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, password, daily_limit })
        });
        const data = await res.json();
        if (data.success) {
          alert('✅ ' + (data.message || 'Miner added successfully!'));
          if (newMinerPhone) newMinerPhone.value = '';
          if (newMinerPassword) newMinerPassword.value = '';
          loadPodiumStatus();
        } else {
          alert('⚠️ ' + (data.message || 'Failed to add miner'));
        }
      } catch (err) {
        console.error('Add miner error:', err);
        alert('⚠️ Network error while adding miner');
      } finally {
        addMinerBtn.innerHTML = origText;
        addMinerBtn.disabled = false;
      }
    });
  }

  // Handle Extra Miners Delegation (Remove, Toggle, Limit Save)
  const extraMinersGrid = document.getElementById('extraMinersGrid');
  if (extraMinersGrid) {
    extraMinersGrid.addEventListener('click', async (e) => {
      if (e.target.classList.contains('btn-remove-miner')) {
        const user = e.target.dataset.user;
        if (!confirm(`Are you sure you want to remove miner '${user}'?`)) return;
        try {
          const res = await fetch(`/api/podium/accounts/${encodeURIComponent(user)}`, { method: 'DELETE' });
          const data = await res.json();
          if (data.success) {
            loadPodiumStatus();
          } else {
            alert('⚠️ ' + (data.message || 'Failed to remove miner'));
          }
        } catch (err) {
          console.error('Remove miner error:', err);
        }
      }

      if (e.target.classList.contains('btn-save-extra-limit')) {
        const user = e.target.dataset.user;
        const card = e.target.closest('.extra-miner-card');
        const input = card ? card.querySelector('.limit-input-extra') : null;
        const toggle = card ? card.querySelector('.toggle-extra-miner') : null;
        const limit = input ? Number(input.value) : 50;
        const enabled = toggle ? toggle.checked : true;

        const origText = e.target.textContent;
        e.target.textContent = 'SAVED!';
        e.target.style.background = '#10B981';

        try {
          await fetch('/api/miner/limits', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, enabled, daily_limit: limit })
          });
          loadPodiumStatus();
        } catch (err) {
          console.error('Save extra limit error:', err);
        } finally {
          setTimeout(() => {
            e.target.textContent = origText;
            e.target.style.background = '';
          }, 1200);
        }
      }
    });

    extraMinersGrid.addEventListener('change', async (e) => {
      if (e.target.classList.contains('toggle-extra-miner')) {
        const user = e.target.dataset.user;
        const enabled = e.target.checked;
        const card = e.target.closest('.extra-miner-card');
        const input = card ? card.querySelector('.limit-input-extra') : null;
        const limit = input ? Number(input.value) : 50;

        try {
          await fetch('/api/miner/limits', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, enabled, daily_limit: limit })
          });
          loadPodiumStatus();
        } catch (err) {
          console.error('Toggle extra miner error:', err);
        }
      }
    });
  }

  // -------------------------------------------------------------
  // 5c. 24H View Limits & Multi-Channel Automation Controls
  // -------------------------------------------------------------
  const totalViews24hBadge = document.getElementById('totalViews24hBadge');
  const activeChannelsCountBadge = document.getElementById('activeChannelsCountBadge');
  const farmingModeBadge = document.getElementById('farmingModeBadge');
  const refreshViewsBtn = document.getElementById('refreshViewsBtn');
  const addChannelForm = document.getElementById('addChannelForm');
  const newChannelInput = document.getElementById('newChannelInput');
  const newChannelLimit = document.getElementById('newChannelLimit');
  const addChannelSubmitBtn = document.getElementById('addChannelSubmitBtn');
  const addChannelFeedback = document.getElementById('addChannelFeedback');
  const channelsViewsGrid = document.getElementById('channelsViewsGrid');

  // Master Global View Controller Elements
  const globalViewToggle = document.getElementById('globalViewToggle');
  const globalSwitchLabel = document.getElementById('globalSwitchLabel');
  const globalLimitInput = document.getElementById('globalLimitInput');
  const saveGlobalLimitBtn = document.getElementById('saveGlobalLimitBtn');
  const resetGlobalViewsBtn = document.getElementById('resetGlobalViewsBtn');
  const globalViewsProgressTxt = document.getElementById('globalViewsProgressTxt');
  const globalBreakdownTxt = document.getElementById('globalBreakdownTxt');
  const globalBarFill = document.getElementById('globalBarFill');
  const globalStatusBadge = document.getElementById('globalStatusBadge');

  let cachedChannels = [];

  async function loadViewChannels() {
    try {
      const [resViews, resFarm] = await Promise.all([
        fetch('/api/views/channels'),
        fetch('/api/farm/status').catch(() => null)
      ]);

      const data = await resViews.json();
      if (!data.success) return;

      cachedChannels = data.channels || [];

      // Update Header Stats
      if (totalViews24hBadge) {
        totalViews24hBadge.textContent = `${data.total_views_24h || 0} Views`;
      }
      if (activeChannelsCountBadge) {
        const count = data.active_channels || 0;
        activeChannelsCountBadge.textContent = `${count} Channel${count === 1 ? '' : 's'}`;
      }

      // Update Master Global View Controller UI
      if (globalViewToggle && document.activeElement !== globalViewToggle) {
        globalViewToggle.checked = data.global_enabled !== false;
      }
      if (globalSwitchLabel) {
        const isGlobalOn = data.global_enabled !== false;
        globalSwitchLabel.textContent = isGlobalOn ? 'VIEW BOT: ON' : 'VIEW BOT: OFF';
        globalSwitchLabel.className = isGlobalOn ? 'switch-helper-text' : 'switch-helper-text off';
      }
      if (globalLimitInput && document.activeElement !== globalLimitInput) {
        if (data.global_daily_limit !== undefined) {
          globalLimitInput.value = data.global_daily_limit;
        }
      }
      if (globalViewsProgressTxt) {
        const gLimit = data.global_daily_limit || 100;
        const gTotal = data.total_views_24h || 0;
        const gPct = data.global_progress_pct || 0;
        globalViewsProgressTxt.textContent = gLimit > 0
          ? `${gTotal} / ${gLimit} Global Views (${gPct}%)`
          : `${gTotal} Global Views (Unlimited)`;
      }
      if (globalBreakdownTxt) {
        globalBreakdownTxt.textContent = `Channels: ${data.channel_views_24h || 0} | Explore: ${data.stealth_views_24h || 0}`;
      }
      if (globalBarFill) {
        globalBarFill.style.width = `${data.global_progress_pct || 0}%`;
      }
      if (globalStatusBadge) {
        if (data.global_enabled === false) {
          globalStatusBadge.className = 'ctrl-status-badge paused global-badge';
          globalStatusBadge.textContent = '⏸️ MASTER VIEW ENGINE OFF (STANDBY)';
        } else if (data.global_daily_limit > 0 && (data.total_views_24h || 0) >= data.global_daily_limit) {
          globalStatusBadge.className = 'ctrl-status-badge standby global-badge';
          globalStatusBadge.textContent = '💤 24H GLOBAL LIMIT COMPLETED (STANDBY)';
        } else {
          globalStatusBadge.className = 'ctrl-status-badge active global-badge';
          globalStatusBadge.textContent = '🟢 GLOBAL ENGINE ACTIVE';
        }
      }

      // Check farming engine mode
      if (resFarm && resFarm.ok) {
        const farmData = await resFarm.json();
        if (farmData.success && farmData.status && farmingModeBadge) {
          const mode = farmData.status.current_mode || 'Target Channel Views';
          if (mode.toLowerCase().includes('standby')) {
            farmingModeBadge.className = 'mode-badge-stealth';
            farmingModeBadge.textContent = '💤 ENGINE STANDBY (TARGET MET / OFF)';
          } else if (mode.toLowerCase().includes('stealth')) {
            farmingModeBadge.className = 'mode-badge-stealth';
            farmingModeBadge.textContent = '🛡️ STEALTH BROWSING (EXPLORE FEED)';
          } else {
            farmingModeBadge.className = 'mode-badge-green';
            farmingModeBadge.textContent = '🟢 TARGET BOOSTING';
          }
        }
      }

      renderViewChannels(cachedChannels);
    } catch (e) {
      console.error('loadViewChannels error:', e);
    }
  }

  function renderViewChannels(channels) {
    if (!channelsViewsGrid) return;

    // Check if user is currently typing in an input inside channelsViewsGrid
    const activeEl = document.activeElement;
    const isUserEditing = activeEl && channelsViewsGrid.contains(activeEl);

    // If user is actively typing, only update values of non-focused elements
    if (isUserEditing) {
      channels.forEach(ch => {
        const barEl = document.getElementById(`barView_${ch.channel_id}`);
        const txtEl = document.getElementById(`txtView_${ch.channel_id}`);
        const badgeEl = document.getElementById(`statusBadgeView_${ch.channel_id}`);

        if (barEl) {
          barEl.style.width = `${ch.progress_pct || 0}%`;
        }
        if (txtEl) {
          txtEl.textContent = ch.daily_limit > 0
            ? `${ch.views_24h} / ${ch.daily_limit} Views (24h)`
            : `${ch.views_24h} Views (Unlimited)`;
        }
        if (badgeEl) {
          if (!ch.enabled) {
            badgeEl.className = 'ctrl-status-badge paused';
            badgeEl.textContent = '⏸️ PAUSED (OFF)';
          } else if (ch.daily_limit > 0 && ch.views_24h >= ch.daily_limit) {
            badgeEl.className = 'ctrl-status-badge limit';
            badgeEl.textContent = '⚠️ 24H TARGET COMPLETED';
          } else {
            badgeEl.className = 'ctrl-status-badge active';
            badgeEl.textContent = '🟢 BOOSTING ACTIVE';
          }
        }
      });
      return;
    }

    // Full render
    channelsViewsGrid.innerHTML = channels.map(ch => {
      const isCryvex = ch.channel_id === '6ada0b9dfb39968c7c48dd7b' || ch.username === 'cryvex';
      const initials = (ch.name || ch.username || 'CH').slice(0, 2).toUpperCase();
      const pct = ch.progress_pct || 0;

      let badgeClass = 'active';
      let badgeText = '🟢 BOOSTING ACTIVE';
      if (!ch.enabled) {
        badgeClass = 'paused';
        badgeText = '⏸️ PAUSED (OFF)';
      } else if (ch.daily_limit > 0 && ch.views_24h >= ch.daily_limit) {
        badgeClass = 'limit';
        badgeText = '⚠️ 24H TARGET COMPLETED (BROWSING STEALTH)';
      }

      const avatarHtml = ch.avatar
        ? `<img src="${ch.avatar}" class="ch-avatar-img" onerror="this.onerror=null; this.outerHTML='<div class=\\'ch-avatar-fallback\\'>${initials}</div>'">`
        : `<div class="ch-avatar-fallback">${initials}</div>`;

      return `
        <div class="channel-view-card ${isCryvex ? 'is-cryvex' : ''}" data-id="${ch.channel_id}">
          <div class="ch-card-header">
            <div class="ch-avatar-info">
              ${avatarHtml}
              <div class="ch-meta-col">
                <div class="ch-name-row">
                  <span class="ch-title-text">${ch.name || ch.username}</span>
                  ${isCryvex ? '<span class="ch-master-badge">👑 MASTER</span>' : ''}
                </div>
                <span class="ch-id-text" title="${ch.channel_id}">ID: ${ch.channel_id.slice(0, 10)}...</span>
              </div>
            </div>
            <label class="cyber-switch" title="Toggle 24H Views ON/OFF">
              <input type="checkbox" class="ch-toggle-input" data-id="${ch.channel_id}" ${ch.enabled ? 'checked' : ''}>
              <span class="cyber-slider"></span>
            </label>
          </div>

          <div class="ch-controls-box">
            <div class="ctrl-header">
              <span class="ctrl-label">⚡ 24H VIEW TARGET:</span>
              <span class="ctrl-mined-txt" id="txtView_${ch.channel_id}">
                ${ch.daily_limit > 0 ? `${ch.views_24h} / ${ch.daily_limit} Views (24h)` : `${ch.views_24h} Views`}
              </span>
            </div>

            <div class="ctrl-limit-row">
              <div class="input-with-label">
                <span class="input-prefix">LIMIT:</span>
                <input type="number" id="limitInputView_${ch.channel_id}" class="cyber-input-limit" value="${ch.daily_limit}" min="10" step="10">
                <span class="input-suffix">VIEWS</span>
              </div>
              <button class="btn-save-limit btn-save-view-limit" data-id="${ch.channel_id}">SAVE</button>
            </div>

            <div class="ctrl-progress-row">
              <div class="ctrl-bar-track">
                <div id="barView_${ch.channel_id}" class="ctrl-bar-fill ${isCryvex ? 'gold-fill' : 'cyan-fill'}" style="width: ${pct}%"></div>
              </div>
            </div>

            <div id="statusBadgeView_${ch.channel_id}" class="ctrl-status-badge ${badgeClass}">${badgeText}</div>
          </div>

          ${!isCryvex ? `
            <button class="btn-remove-channel" data-id="${ch.channel_id}" data-name="${ch.name || ch.username}">
              🗑️ Remove Channel
            </button>
          ` : ''}
        </div>
      `;
    }).join('');

    // Attach Event Listeners to Cards
    channelsViewsGrid.querySelectorAll('.ch-toggle-input').forEach(input => {
      input.addEventListener('change', async (e) => {
        const chId = e.target.dataset.id;
        const enabled = e.target.checked;
        try {
          await fetch(`/api/views/channels/${chId}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
          });
          loadViewChannels();
        } catch (err) {
          console.error('Toggle error:', err);
        }
      });
    });

    channelsViewsGrid.querySelectorAll('.btn-save-view-limit').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const chId = e.target.dataset.id;
        const limitInput = document.getElementById(`limitInputView_${chId}`);
        const limitVal = limitInput ? Number(limitInput.value) : 200;

        const origText = e.target.textContent;
        e.target.textContent = 'SAVED!';
        e.target.style.background = '#10B981';
        e.target.style.color = '#fff';

        try {
          await fetch(`/api/views/channels/${chId}/limit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ daily_limit: limitVal })
          });
          loadViewChannels();
        } catch (err) {
          console.error('Save view limit error:', err);
        } finally {
          setTimeout(() => {
            e.target.textContent = origText;
            e.target.style.background = '';
            e.target.style.color = '';
          }, 1200);
        }
      });
    });

    channelsViewsGrid.querySelectorAll('.btn-remove-channel').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const chId = e.target.dataset.id;
        const chName = e.target.dataset.name;
        if (!confirm(`Kya aap sach me '${chName}' ko 24h view automation se remove karna chahte hain?`)) {
          return;
        }

        try {
          const res = await fetch(`/api/views/channels/${chId}`, { method: 'DELETE' });
          const d = await res.json();
          if (d.success) {
            loadViewChannels();
          } else {
            alert(d.message || 'Failed to remove channel');
          }
        } catch (err) {
          console.error('Remove channel error:', err);
        }
      });
    });
  }

  // Handle Add Channel Form
  if (addChannelForm) {
    addChannelForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const identifier = newChannelInput ? newChannelInput.value.trim() : '';
      const dailyLimit = newChannelLimit ? Number(newChannelLimit.value) : 200;

      if (!identifier) return;

      if (addChannelSubmitBtn) {
        addChannelSubmitBtn.disabled = true;
      }
      if (addChannelFeedback) {
        addChannelFeedback.className = 'add-channel-feedback';
        addChannelFeedback.textContent = '⏳ Resolving channel and adding to 24H automation...';
      }

      try {
        const res = await fetch('/api/views/channels', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ identifier, daily_limit: dailyLimit })
        });
        const data = await res.json();

        if (data.success) {
          if (addChannelFeedback) {
            addChannelFeedback.className = 'add-channel-feedback success';
            addChannelFeedback.textContent = `✅ ${data.message || 'Channel added successfully!'}`;
          }
          if (newChannelInput) newChannelInput.value = '';
          await loadViewChannels();
        } else {
          if (addChannelFeedback) {
            addChannelFeedback.className = 'add-channel-feedback error';
            addChannelFeedback.textContent = `⚠️ ${data.message || 'Failed to add channel'}`;
          }
        }
      } catch (err) {
        if (addChannelFeedback) {
          addChannelFeedback.className = 'add-channel-feedback error';
          addChannelFeedback.textContent = '⚠️ Network error while adding channel';
        }
      } finally {
        if (addChannelSubmitBtn) {
          addChannelSubmitBtn.disabled = false;
        }
        setTimeout(() => {
          if (addChannelFeedback) addChannelFeedback.textContent = '';
        }, 5000);
      }
    });
  }

  // Handle Master Global View Controller Toggle & Limit Save
  if (globalViewToggle) {
    globalViewToggle.addEventListener('change', async (e) => {
      const enabled = e.target.checked;
      try {
        await fetch('/api/views/global/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled })
        });
        loadViewChannels();
      } catch (err) {
        console.error('Global toggle error:', err);
      }
    });
  }

  if (saveGlobalLimitBtn) {
    saveGlobalLimitBtn.addEventListener('click', async (e) => {
      const limitVal = globalLimitInput ? Number(globalLimitInput.value) : 100;
      const toggleChecked = globalViewToggle ? globalViewToggle.checked : true;

      const origText = saveGlobalLimitBtn.textContent;
      saveGlobalLimitBtn.textContent = 'SAVED!';
      saveGlobalLimitBtn.style.background = '#10B981';
      saveGlobalLimitBtn.style.color = '#fff';

      try {
        await fetch('/api/views/global', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ daily_limit: limitVal, enabled: toggleChecked })
        });
        loadViewChannels();
      } catch (err) {
        console.error('Save global limit error:', err);
      } finally {
        setTimeout(() => {
          saveGlobalLimitBtn.textContent = origText;
          saveGlobalLimitBtn.style.background = '';
          saveGlobalLimitBtn.style.color = '';
        }, 1200);
      }
    });
  }

  if (resetGlobalViewsBtn) {
    resetGlobalViewsBtn.addEventListener('click', async () => {
      const origText = resetGlobalViewsBtn.innerHTML;
      resetGlobalViewsBtn.innerHTML = '<span>RESETTING...</span>';
      try {
        const res = await fetch('/api/views/global/reset', { method: 'POST' });
        const data = await res.json();
        if (data && data.success) {
          resetGlobalViewsBtn.innerHTML = '<span>CLEARED!</span>';
          resetGlobalViewsBtn.style.borderColor = '#10B981';
          resetGlobalViewsBtn.style.color = '#10B981';
          loadViewChannels();
        }
      } catch (err) {
        console.error('Reset global views error:', err);
      } finally {
        setTimeout(() => {
          resetGlobalViewsBtn.innerHTML = origText;
          resetGlobalViewsBtn.style.borderColor = '';
          resetGlobalViewsBtn.style.color = '';
        }, 1500);
      }
    });
  }

  if (refreshViewsBtn) {
    refreshViewsBtn.addEventListener('click', loadViewChannels);
  }

  // -------------------------------------------------------------
  // 6. Bootstrap Initial State & 24/7 Background Polling
  // -------------------------------------------------------------
  loadPodiumStatus();
  loadCryvexCoins();
  loadViewChannels();

  // Poll live rankings, logs & views every 3 seconds
  setInterval(() => {
    loadPodiumStatus();
    loadViewChannels();
  }, 3000);

  // Poll Cryvex coin balance & cooldown every 10 seconds
  setInterval(loadCryvexCoins, 10000);
});
