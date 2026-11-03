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

        const milestone = 5000;
        const pct = Math.min(100, Math.round((coins / milestone) * 100));
        if (coinProgressFill) coinProgressFill.style.width = `${pct}%`;
        if (coinProgressText) coinProgressText.textContent = `${coins.toFixed(1)} / ${milestone.toLocaleString()} Coins Milestone (${pct}%)`;

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

  // -------------------------------------------------------------
  // 6. Bootstrap Initial State & 24/7 Background Polling
  // -------------------------------------------------------------
  loadPodiumStatus();
  loadCryvexCoins();

  // Poll live rankings & logs every 3 seconds
  setInterval(loadPodiumStatus, 3000);

  // Poll Cryvex coin balance & cooldown every 10 seconds
  setInterval(loadCryvexCoins, 10000);
});
