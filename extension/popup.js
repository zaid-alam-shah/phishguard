const API_BASE = 'http://127.0.0.1:8080';

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
    const resp = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.trim() })
    });
    if (!resp.ok) {
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
    const resp = await fetch(`${API_BASE}/history?limit=10`);
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

loadHistory();
