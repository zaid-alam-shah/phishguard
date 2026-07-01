const API_BASE = 'http://127.0.0.1:8080';

// ── User-approved URLs (bypass list) ──
// URLs that the user clicked "Continue Anyway" on — skip protection for these.
// Uses chrome.storage.session to persist across service worker restarts.
// Falls back to in-memory Set if session storage is unavailable.
let bypassUrls = new Set();

// Load any persisted bypasses when service worker starts
chrome.storage.session.get('phishguard_bypass', (data) => {
  if (data.phishguard_bypass) {
    bypassUrls = new Set(data.phishguard_bypass);
  }
});

function addBypass(url) {
  bypassUrls.add(url);
  // Persist to session storage (survives worker restart, cleared on browser close)
  chrome.storage.session.set({ phishguard_bypass: [...bypassUrls] });
  // Remove after 10 seconds
  setTimeout(() => {
    bypassUrls.delete(url);
    chrome.storage.session.set({ phishguard_bypass: [...bypassUrls] });
  }, 10000);
}

// ── Context Menu (existing) ──
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scanPhishGuard',
    title: 'Scan URL with PhishGuard',
    contexts: ['link', 'selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const url = info.linkUrl || info.selectionText || '';
  if (url) {
    chrome.storage.local.set({ pendingScan: url }, () => {
      chrome.action.openPopup();
    });
  }
});

// ── Message Handler: User clicked "Continue Anyway" on warning page ──
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'continue_to_url') {
    // Add to bypass list (persisted via chrome.storage.session)
    addBypass(message.url);
    // Navigate the tab to the original URL — this is the ONLY navigation
    if (sender.tab && sender.tab.id) {
      chrome.tabs.update(sender.tab.id, { url: message.url }).catch(() => {});
    } else {
      // Fallback if sender.tab is not available (shouldn't happen for extension pages)
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) chrome.tabs.update(tabs[0].id, { url: message.url }).catch(() => {});
      });
    }
    sendResponse({ ok: true });
    return; // No async needed
  }
});

// ── Real-Time Protection ──

// Cache to avoid re-checking the same URL within a short window
const urlCache = new Map();
const CACHE_TTL = 60_000; // 1 minute

// Periodically clear stale cache entries
setInterval(() => {
  const now = Date.now();
  for (const [url, entry] of urlCache) {
    if (now - entry.timestamp > CACHE_TTL) urlCache.delete(url);
  }
}, 120_000);

/**
 * Intercept main-frame navigations and check URLs against PhishGuard.
 */
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  // Only outermost (main) frame navigations
  if (details.frameType !== 'outermost_frame') return;

  const url = details.url;
  // Only check http(s) URLs
  if (!url.startsWith('http://') && !url.startsWith('https://')) return;

  // Skip bypassed URLs (user clicked "Continue Anyway")
  if (bypassUrls.has(url)) {
    bypassUrls.delete(url); // One-time use
    return;
  }

  // Check if the user has real-time protection enabled
  chrome.storage.local.get('realtimeProtection', (result) => {
    if (!result.realtimeProtection) return;
    checkUrl(details.tabId, url);
  });
});

// ── Instant Client-Side Pre-check ──
// Quickly checks URL for obvious phishing patterns BEFORE the API call.
// This makes the warning feel INSTANT for common phishing URLs.
const SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', '.click', '.link', '.info', '.online', '.site', '.website'];
const PHISHING_KEYWORDS = ['login', 'signin', 'verify', 'secure', 'update', 'confirm', 'webscr', 'cmd='];
const TARGETED_BRANDS = ['paypal', 'apple', 'amazon', 'microsoft', 'google', 'facebook', 'netflix', 'bank', 'chase', 'wellsfargo', 'citibank', 'dropbox', 'linkedin', 'instagram', 'outlook', 'icloud', 'hsbc'];

function quickPreCheck(url) {
  const urlLower = url.toLowerCase();
  let score = 0;
  const flags = [];

  // Check for suspicious TLD
  for (const tld of SUSPICIOUS_TLDS) {
    if (urlLower.includes(tld)) {
      score += 25;
      flags.push('Suspicious TLD: ' + tld);
      break;
    }
  }

  // Check for brand impersonation in domain
  let hostname = '';
  try { hostname = new URL(url).hostname.toLowerCase(); } catch(e) { hostname = urlLower.replace(/https?:\/\//, '').split('/')[0]; }
  for (const brand of TARGETED_BRANDS) {
    if (hostname.includes(brand) && !hostname.endsWith(brand + '.com') && !hostname.endsWith(brand + '.org')) {
      score += 25;
      flags.push('Possible ' + brand + ' impersonation');
      break;
    }
  }

  // Check for phishing keywords in path (beyond the domain)
  let path = '';
  try { path = new URL(url).pathname.toLowerCase(); } catch(e) {
    const idx = urlLower.indexOf('/', 8);
    path = idx >= 0 ? urlLower.substring(idx) : '';
  }
  if (path) {
    for (const kw of PHISHING_KEYWORDS) {
      if (path.includes(kw)) {
        score += 20;
        flags.push('Suspicious keyword: ' + kw);
        break;
      }
    }
  }

  // Check for HTTP (no HTTPS)
  if (urlLower.startsWith('http://')) {
    score += 10;
    flags.push('Uses HTTP (no SSL)');
  }

  return { score, flags };
}

/**
 * Fetch /predict for the given URL and inject a warning modal if phishing.
 * Runs an instant local pre-check first, then confirms with the API.
 */
async function checkUrl(tabId, url) {
  // Cache hit – avoid redundant API calls
  const cached = urlCache.get(url);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    if (cached.isPhishing) {
      injectWarningModal(tabId, url, cached.score, cached.issues);
    }
    return;
  }

  // Step 1: INSTANT local pre-check (no API call needed)
  const preCheck = quickPreCheck(url);
  if (preCheck.score >= 40) {
    // Show warning IMMEDIATELY from local check
    injectWarningModal(tabId, url, preCheck.score, preCheck.flags);
    // Still do the API call in background for a more accurate score
    // Still do the API call in background for a more accurate score
    fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    }).then(resp => resp.json()).then(data => {
      const apiScore = data.combined_risk_score || preCheck.score;
      urlCache.set(url, { 
        isPhishing: apiScore >= 40, 
        score: apiScore, 
        issues: data.issues || data.rule_based?.issues || preCheck.flags, 
        timestamp: Date.now() 
      });
    }).catch(() => {});
    return;
  }

  // Step 2: Full API check for borderline URLs
  try {
    const resp = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!resp.ok) return;

    const data = await resp.json();
    const score = data.combined_risk_score;
    const isPhishing = score >= 40;

    // Cache result
    urlCache.set(url, {
      isPhishing,
      score: score,
      issues: data.issues || data.rule_based?.issues || [],
      timestamp: Date.now()
    });

    if (isPhishing) {
      injectWarningModal(tabId, url, score, data.issues || data.rule_based?.issues || []);
    }
  } catch (err) {
    console.error('PhishGuard: API error for', url, err);
  }
}

/**
 * Store warning data in session storage so warning.html can retrieve it reliably.
 * URL params are used as fallback, but session storage avoids encoding/length issues.
 */
function storeWarningData(tabId, data) {
  return new Promise((resolve) => {
    const key = 'phishguard_warn_' + tabId;
    chrome.storage.session.set({ [key]: data }, () => {
      resolve();
    });
  });
}

/**
 * BLOCK navigation and show warning page.
 * Instead of injecting an overlay (which still lets the page load in background),
 * we redirect to the extension's warning.html which COMPLETELY replaces the 
 * navigation — the phishing page NEVER loads until user clicks "Continue Anyway".
 */
function injectWarningModal(tabId, url, score, issues = []) {
  const issuesList = issues.slice(0, 4).map(i => (typeof i === 'string' ? i : i.text)).join(', ');

  // Store data in session storage FIRST, then navigate
  storeWarningData(tabId, {
    score: score,
    url: url,
    issues: issuesList
  }).then(() => {
    // Use a short token in URL — just identifies which storage entry to read
    const params = new URLSearchParams({
      tk: 'phishguard_warn_' + tabId,  // must match storeWarningData key
      score: String(score), // fallback: direct URL param
      url: url,
      issues: issuesList
    });

    chrome.tabs.update(tabId, {
      url: chrome.runtime.getURL('warning.html?' + params.toString())
    }).catch(() => {});
  });
}
