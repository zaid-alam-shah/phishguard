// ── PhishGuard Warning Page Script ──
// Extracted to external file to comply with MV3 CSP (inline scripts not allowed)

(function () {
  'use strict';

  // ── Load data: try session storage first, then fall back to URL params ──
  const params = new URLSearchParams(window.location.search);
  const storageKey = params.get('tk');  // e.g., 'warn_123' — identifies storage entry

  let score = params.get('score') || '--';
  let blockedUrl = params.get('url') || '';
  let issues = params.get('issues') || '';

  // ── Render function ──
  function renderWarning(score, blockedUrl, issues) {
    // Set verdict bar based on score
    const bar = document.getElementById('verdictBar');
    const numericScore = parseInt(score, 10);
    if (!isNaN(numericScore) && numericScore >= 60) {
      bar.className = 'verdict-bar phishing';
      bar.textContent = '\uD83D\uDD34 PHISHING DETECTED';
    } else if (!isNaN(numericScore) && numericScore >= 40) {
      bar.className = 'verdict-bar risky';
      bar.textContent = '\u26A0\uFE0F RISKY';
    }
    document.getElementById('blockedUrl').textContent = blockedUrl;
    if (issues) {
      document.getElementById('issuesList').textContent = '\uD83D\uDEA9 ' + issues;
    }

    // Block button: go to safe blank page
    document.getElementById('btnBlock').addEventListener('click', () => {
      window.location.replace('about:blank');
    });

    // Continue Anyway: ask background to add URL to bypass list
    document.getElementById('btnContinue').addEventListener('click', () => {
      if (blockedUrl) {
        chrome.runtime.sendMessage({
          type: 'continue_to_url',
          url: blockedUrl
        });
        document.getElementById('btnContinue').disabled = true;
        document.getElementById('btnContinue').textContent = 'Loading...';
      }
    });
  }

  // ── Load data strategy ──
  if (storageKey) {
    chrome.storage.session.get(storageKey, (data) => {
      const stored = data[storageKey];
      if (stored) {
        score = String(stored.score ?? score);
        blockedUrl = stored.url || blockedUrl;
        issues = stored.issues || issues;
        chrome.storage.session.remove(storageKey);
      }
      renderWarning(score, blockedUrl, issues);
    });
  } else {
    renderWarning(score, blockedUrl, issues);
  }

})();
