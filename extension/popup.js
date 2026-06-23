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

function setLoading() {
  status.className = 'status loading';
  statusContent.innerHTML = '<div class="risk-score">...</div><div class="verdict">Scanning...</div>';
  details.classList.remove('show');
  scanBtn.disabled = true;
}

function setResult(data) {
  scanBtn.disabled = false;
  const isPhishing = data.final_verdict === 'phishing';
  status.className = `status ${isPhishing ? 'phishing' : 'safe'}`;
  const issues = data.rule_based?.issues || [];
  statusContent.innerHTML = `
    <div class="risk-score">${data.combined_risk_score || 0}</div>
    <div class="verdict">${isPhishing ? '⚠ PHISHING DETECTED' : '✓ SAFE'}</div>
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
      const isPhish = s.ml_result === 'phishing' || (s.risk_score || 0) > 50;
      const displayUrl = s.url ? s.url.substring(0, 40) + (s.url.length > 40 ? '...' : '') : 'unknown';
      return `<div class="history-item">
        <span class="hurl" title="${escapeHtml(s.url || '')}">${escapeHtml(displayUrl)}</span>
        <span class="badge ${isPhish ? 'phishing' : 'safe'}">${isPhish ? 'Phish' : 'Safe'} ${s.risk_score || ''}</span>
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
