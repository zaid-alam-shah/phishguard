// ── API Key & Settings Management ──
let API_BASE = 'http://127.0.0.1:8080';

// Load saved API_BASE and API key
async function loadSettings() {
    const data = await chrome.storage.local.get(['apiBase', 'apiKey']);
    if (data.apiBase) API_BASE = data.apiBase;
    return data;
}

async function getApiKey() {
    const data = await chrome.storage.local.get('apiKey');
    if (data.apiKey) return data.apiKey;
    // Fetch a new one
    try {
        const resp = await fetch(API_BASE + '/api/client-key');
        if (resp.ok) {
            const result = await resp.json();
            const key = result.api_key;
            await chrome.storage.local.set({ apiKey: key });
            return key;
        }
    } catch (e) {
        console.warn('PhishGuard: Could not fetch API key', e);
    }
    return null;
}

async function refreshApiKey() {
    await chrome.storage.local.remove('apiKey');
    return await getApiKey();
}

async function apiFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (!options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    const key = await getApiKey();
    if (key) {
        options.headers['Authorization'] = 'Bearer ' + key;
    }
    return fetch(url, options);
}


const urlInput = document.getElementById('urlInput');
const scanBtn = document.getElementById('scanBtn');
const status = document.getElementById('status');
const statusContent = document.getElementById('statusContent');
const details = document.getElementById('details');
const detailUrl = document.getElementById('detailUrl');
const detailMl = document.getElementById('detailMl');
const detailAge = document.getElementById('detailAge');
const detailSsl = document.getElementById('detailSsl');
const shortenerInfo = document.getElementById('shortenerInfo');
const historyList = document.getElementById('historyList');
const historyCount = document.getElementById('historyCount');
const tabUrlBtn = document.getElementById('tabUrlBtn');
const clipboardBtn = document.getElementById('clipboardBtn');
const clearBtn = document.getElementById('clearBtn');
const apiBaseInput = document.getElementById('apiBaseInput');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel = document.getElementById('settingsPanel');
const settingsArrow = document.getElementById('settingsArrow');
const connStatus = document.getElementById('connStatus');
const refreshKeyBtn = document.getElementById('refreshKeyBtn');
const footerStatus = document.getElementById('footerStatus');

// ── Real-Time Protection Toggle ──
const realtimeToggle = document.getElementById('realtimeToggle');
const protectionStatus = document.getElementById('protectionStatus');

function updateProtectionUI(enabled) {
  realtimeToggle.checked = enabled;
  protectionStatus.textContent = enabled ? 'ON' : 'OFF';
  protectionStatus.className = `protection-status ${enabled ? 'active' : 'inactive'}`;
}

// Load saved state
chrome.storage.local.get('realtimeProtection', (data) => {
  updateProtectionUI(data.realtimeProtection === true);
});

// Save on toggle
realtimeToggle.addEventListener('change', () => {
  const enabled = realtimeToggle.checked;
  chrome.storage.local.set({ realtimeProtection: enabled });
  updateProtectionUI(enabled);
});

// ── Scan Logic ──

function setLoading() {
  status.className = 'status loading';
  statusContent.innerHTML = '<div class="verdict">Scanning...</div>';
  details.classList.remove('show');
  scanBtn.disabled = true;
}

function setResult(data) {
  scanBtn.disabled = false;
  const verdict = data.final_verdict || 'safe';
  const isPhishing = verdict === 'phishing';
  const isRisky = verdict === 'risky';
  const statusClass = isPhishing ? 'phishing' : (isRisky ? 'risky' : 'safe');
  status.className = `status ${statusClass}`;
  const issues = data.rule_based?.issues || [];
  const verdictLabel = isPhishing ? '🔴 PHISHING DETECTED' : (isRisky ? '⚠️ RISKY' : '✓ SAFE');
  statusContent.innerHTML = `
    <div class="verdict">${verdictLabel}</div>
    <div class="issues">${issues.slice(0, 3).map(i => '• ' + i.text).join('<br>')}</div>
  `;

  details.classList.add('show');
  detailUrl.textContent = data.url || '';
  detailMl.textContent = data.ml_result?.phishing_probability
    ? `${data.ml_result.phishing_probability}% phishing`
    : 'N/A';
  detailAge.textContent = data.domain_age_days != null
    ? `${data.domain_age_days} days`
    : 'Unknown';
  detailSsl.textContent = data.domain_age_days != null ? 'Checked' : 'N/A';

  if (data.was_shortened && data.original_url) {
    shortenerInfo.style.display = 'block';
    shortenerInfo.innerHTML = `<strong>🔗 Shortened URL</strong> → ${escapeHtml(data.original_url)}`;
  } else {
    shortenerInfo.style.display = 'none';
  }
}

function setError(msg) {
  scanBtn.disabled = false;
  status.className = 'status error';
  statusContent.innerHTML = `<div class="verdict">Error</div><div class="issues">${escapeHtml(msg)}</div>`;
  details.classList.remove('show');
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

async function scanUrl(url) {
  if (!url || !url.trim()) { setError('Please enter a URL'); return; }
  setLoading();
  try {
    const resp = await apiFetch(`${API_BASE}/predict`, {
      method: 'POST',
      body: JSON.stringify({ url: url.trim() })
    });
    if (!resp.ok) {
      // If auth error, try refreshing the key and retry once
      if (resp.status === 401) {
        await refreshApiKey();
        const retryResp = await apiFetch(`${API_BASE}/predict`, {
          method: 'POST',
          body: JSON.stringify({ url: url.trim() })
        });
        if (!retryResp.ok) {
          const err = await retryResp.json();
          setError(err.error || `HTTP ${retryResp.status}`);
          return;
        }
        const data = await retryResp.json();
        setResult(data);
        loadHistory();
        return;
      }
      const err = await resp.json();
      setError(err.error || `HTTP ${resp.status}`);
      return;
    }
    const data = await resp.json();
    setResult(data);
    loadHistory();
  } catch (e) {
    setError('Cannot connect to PhishGuard API. Is the server running on port 8080?');
  }
}

async function loadHistory() {
  try {
    const resp = await apiFetch(`${API_BASE}/history?limit=10`);
    if (!resp.ok) return;
    const data = await resp.json();
    const scans = data.history || [];
    historyCount.textContent = `${data.count || 0}`;
    historyList.innerHTML = scans.map(s => {
      const score = s.risk_score || 0;
      const isPhish = score >= 60;
      const isRisky = score >= 40 && score < 60;
      const badgeClass = isPhish ? 'phishing' : (isRisky ? 'risky' : 'safe');
      const badgeLabel = isPhish ? 'Phish' : (isRisky ? 'Risky' : 'Safe');
      const displayUrl = s.url ? s.url.substring(0, 40) + (s.url.length > 40 ? '...' : '') : 'unknown';
      return `<div class="history-item">
        <span class="hurl" title="${escapeHtml(s.url || '')}">${escapeHtml(displayUrl)}</span>
        <span class="badge ${badgeClass}">${badgeLabel} ${score || ''}</span>
      </div>`;
    }).join('');
  } catch (e) {}
}

scanBtn.addEventListener('click', () => scanUrl(urlInput.value));
urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') scanUrl(urlInput.value); });

tabUrlBtn.addEventListener('click', async () => {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]?.url) scanUrl(tabs[0].url);
  } catch (e) { setError('Cannot access current tab URL'); }
});

clipboardBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    urlInput.value = text;
    scanUrl(text);
  } catch (e) { setError('Cannot read clipboard. Paste manually.'); }
});

clearBtn.addEventListener('click', () => {
  urlInput.value = '';
  status.className = 'status';
  details.classList.remove('show');
});

// ── Settings UI ──

settingsToggle.addEventListener('click', () => {
  const isOpen = settingsPanel.style.display !== 'none';
  settingsPanel.style.display = isOpen ? 'none' : 'block';
  settingsArrow.textContent = isOpen ? '▸' : '▾';
  if (!isOpen) updateConnectionStatus();
});

saveSettingsBtn.addEventListener('click', async () => {
  const newBase = apiBaseInput.value.trim();
  if (newBase) {
    await chrome.storage.local.set({ apiBase: newBase });
    API_BASE = newBase;
    await chrome.storage.local.remove('apiKey');
    updateConnectionStatus();
  }
});

refreshKeyBtn.addEventListener('click', async () => {
  refreshKeyBtn.disabled = true;
  refreshKeyBtn.textContent = '🔄 Refreshing...';
  await refreshApiKey();
  refreshKeyBtn.textContent = '✅ Key Refreshed';
  setTimeout(() => {
    refreshKeyBtn.disabled = false;
    refreshKeyBtn.textContent = '🔄 Refresh API Key';
  }, 2000);
  updateConnectionStatus();
});

async function updateConnectionStatus() {
  connStatus.textContent = 'Checking...';
  connStatus.style.color = '#94a3b8';
  try {
    const resp = await apiFetch(`${API_BASE}/api/health`);
    if (resp.ok) {
      connStatus.textContent = '✅ Connected';
      connStatus.style.color = '#34d399';
      footerStatus.textContent = `PhishGuard v1.0 — API: ${API_BASE}`;
    } else {
      connStatus.textContent = '❌ API Error';
      connStatus.style.color = '#fca5a5';
    }
  } catch (e) {
    connStatus.textContent = '❌ Cannot Connect';
    connStatus.style.color = '#fca5a5';
  }
}

loadSettings().then(data => {
  if (data.apiBase) {
    apiBaseInput.value = data.apiBase;
    footerStatus.textContent = `PhishGuard v1.0 — API: ${data.apiBase}`;
  }
});

loadHistory();
