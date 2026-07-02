const API_BASE = '';

// ── API Key Management ──
// Fetches a client API key from the backend on first use and caches it.
let _cachedApiKey = null;

async function getApiKey() {
    if (_cachedApiKey) return _cachedApiKey;
    let key = sessionStorage.getItem('pg_api_key');
    if (key) {
        _cachedApiKey = key;
        return key;
    }
    try {
        const resp = await fetch('/api/client-key');
        if (resp.ok) {
            const data = await resp.json();
            key = data.api_key;
            _cachedApiKey = key;
            sessionStorage.setItem('pg_api_key', key);
        }
    } catch (e) {
        console.warn('Could not fetch API key, requests may fail:', e);
    }
    return key;
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


document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initAnalyze();
    initHistory();
    initDashboard();
    initChatbot();
    loadStats();
    loadHistory();
});


function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(s => {
                s.classList.remove('active');
                s.classList.add('hidden');
            });
            btn.classList.add('active');
            const section = document.getElementById(tabId);
            if (section) {
                section.classList.add('active');
                section.classList.remove('hidden');
            }
            if (tabId === 'tabDashboard') loadStats();
            if (tabId === 'tabHistory') loadHistory();
        });
    });
}

function initAnalyze() {
    const btn = document.getElementById('analyzeBtn');
    const input = document.getElementById('urlInput');
    const bulkBtn = document.getElementById('bulkAnalyzeBtn');
    const bulkInput = document.getElementById('bulkInput');

    btn.addEventListener('click', () => analyzeUrl(input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') analyzeUrl(input.value);
    });

    document.querySelectorAll('.example-btn').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelector('.mode-option[data-mode="single"]').click();
            input.value = el.textContent;
            analyzeUrl(input.value);
        });
    });

    bulkBtn.addEventListener('click', () => analyzeBulkUrls());

    bulkInput.addEventListener('input', updateBulkCount);

    document.querySelectorAll('.mode-option').forEach(opt => {
        opt.addEventListener('click', () => {
            document.querySelectorAll('.mode-option').forEach(o => o.classList.remove('active'));
            document.querySelectorAll('.mode-panel').forEach(p => p.classList.remove('active'));
            opt.classList.add('active');
            const mode = opt.getAttribute('data-mode');
            document.getElementById(mode + 'Mode').classList.add('active');
            if (mode === 'bulk') updateBulkCount();
        });
    });
}

function updateBulkCount() {
    const input = document.getElementById('bulkInput');
    const count = document.getElementById('bulkCount');
    const urls = input.value.split('\n').filter(u => u.trim()).length;
    if (urls > 0) {
        count.textContent = urls + ' URL' + (urls > 1 ? 's' : '') + ' detected';
    } else {
        count.textContent = '';
    }
}

function showLoading(title, sub, showProgress) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('hidden');
    overlay.style.display = 'flex';
    document.getElementById('loadingTitle').textContent = title;
    document.getElementById('loadingSub').textContent = sub;
    const progress = document.getElementById('loadingProgress');
    if (showProgress) {
        progress.style.display = 'block';
        document.getElementById('progressText').textContent = '0 / 0 URLs';
        document.getElementById('progressPct').textContent = '0%';
        document.getElementById('progressBar').style.width = '0%';
    } else {
        progress.style.display = 'none';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('hidden');
    overlay.style.display = 'none';
}

function updateProgress(current, total) {
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    document.getElementById('progressText').textContent = current + ' / ' + total + ' URLs';
    document.getElementById('progressPct').textContent = pct + '%';
    document.getElementById('progressBar').style.width = pct + '%';
}

async function analyzeUrl(url) {
    const btn = document.getElementById('analyzeBtn');
    const input = document.getElementById('urlInput');

    if (!url || !url.trim()) {
        input.focus();
        input.style.borderColor = '#ef4444';
        setTimeout(() => input.style.borderColor = '', 2000);
        return;
    }

    showLoading('ANALYZING URL', 'Running ML model and rule-based checks', false);
    btn.disabled = true;

    try {
        const response = await apiFetch(API_BASE + '/predict', {
            method: 'POST',
            body: JSON.stringify({ url: url.trim() })
        });

        const data = await response.json();

        if (!response.ok) {
            alert('Error: ' + (data.error || 'Unknown error'));
            return;
        }

        displayResults(data);
        const prevS = parseInt(sessionStorage.getItem('pg_session_scans') || '0');
        sessionStorage.setItem('pg_session_scans', prevS + 1);
        loadStats();
        loadHistory();
    } catch (err) {
            alert('Could not connect to server. Make sure the backend is running on port 8080');
    } finally {
        hideLoading();
        btn.disabled = false;
    }
}

async function analyzeBulkUrls() {
    const input = document.getElementById('bulkInput');
    const btn = document.getElementById('bulkAnalyzeBtn');

    const urls = input.value.split('\n').map(u => u.trim()).filter(u => u);
    if (urls.length === 0) {
        input.focus();
        input.style.borderColor = '#ef4444';
        setTimeout(() => input.style.borderColor = '', 2000);
        return;
    }

    if (urls.length > 20) {
        alert('Maximum 20 URLs per bulk scan.');
        return;
    }

    btn.disabled = true;
    showLoading('BULK SCANNING', 'Scanning ' + urls.length + ' URLs...', true);

    try {
        const response = await apiFetch(API_BASE + '/bulk-predict', {
            method: 'POST',
            body: JSON.stringify({ urls: urls })
        });

        if (!response.ok) {
            const data = await response.json();
            alert('Error: ' + (data.error || 'Bulk scan failed'));
            return;
        }

        const data = await response.json();

        const prev = parseInt(sessionStorage.getItem('pg_session_scans') || '0');
        sessionStorage.setItem('pg_session_scans', prev + 1);

        displayBulkResults(data.results);
        loadStats();
        loadHistory();
    } catch (err) {
        alert('Could not connect to server. Make sure the backend is running on port 8080');
    } finally {
        hideLoading();
        btn.disabled = false;
    }
}

function displayResults(data) {
    const container = document.getElementById('resultContainer');
    container.classList.remove('hidden');

    const verdict = data.final_verdict;
    const badge = document.getElementById('verdictBadge');
    const badgeClass = verdict === 'phishing' ? 'bg-red-500/20 text-red-400' : (verdict === 'risky' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400');
    badge.className = `px-4 py-1.5 rounded-full text-sm font-medium ${badgeClass}`;
    badge.textContent = verdict === 'phishing' ? 'Phishing' : (verdict === 'risky' ? 'Risky' : 'Safe');

    const urlInfo = document.getElementById('urlShortenerInfo');
    if (data.was_shortened && data.original_url) {
        urlInfo.classList.remove('hidden');
        document.getElementById('originalUrl').textContent = data.original_url;
        document.getElementById('resolvedUrl').textContent = data.url;
    } else {
        urlInfo.classList.add('hidden');
    }

    const mlResult = data.ml_result;
    document.getElementById('mlPrediction').textContent = mlResult.prediction === 'phishing' ? 'Phishing' : 'Safe';
    document.getElementById('mlPrediction').className = `text-lg font-semibold ${mlResult.prediction === 'phishing' ? 'text-red-400' : 'text-green-400'}`;

    const mlPct = mlResult.phishing_probability;
    const mlBar = document.getElementById('mlBar');
    mlBar.style.width = mlPct + '%';
    mlBar.className = `h-2 rounded-full transition-all duration-500 ${mlPct > 50 ? 'bg-red-500' : 'bg-green-500'}`;
    document.getElementById('mlPercent').textContent = mlPct + '% phishing probability';

    const ruleData = data.rule_based;
    document.getElementById('ruleRisk').textContent = ruleData.risk_level.toUpperCase();
    document.getElementById('ruleRisk').className = `text-lg font-semibold ${
        ruleData.risk_level === 'critical' || ruleData.risk_level === 'high' ? 'text-red-400' :
        ruleData.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
    }`;

    const ruleBar = document.getElementById('ruleBar');
    ruleBar.style.width = ruleData.risk_score + '%';
    ruleBar.className = `h-2 rounded-full transition-all duration-500 ${
        ruleData.risk_score > 50 ? 'bg-red-500' : ruleData.risk_score > 25 ? 'bg-yellow-500' : 'bg-green-500'
    }`;
    document.getElementById('rulePercent').textContent = ruleData.risk_score + '% risk score';

    const combined = data.combined_risk_score;
    const combinedLabel = combined >= 60 ? 'Phishing' : (combined >= 40 ? 'Risky' : 'Safe');
    const combinedColor = combined >= 60 ? 'text-red-400' : (combined >= 40 ? 'text-yellow-400' : 'text-green-400');
    document.getElementById('combinedScore').textContent = combinedLabel;
    document.getElementById('combinedScore').className = `text-lg font-semibold ${combinedColor}`;

    const combinedBar = document.getElementById('combinedBar');
    combinedBar.style.width = combined + '%';
    const barColor = combined >= 60 ? 'bg-red-500' : (combined >= 40 ? 'bg-yellow-500' : 'bg-green-500');
    combinedBar.className = `h-2 rounded-full transition-all duration-500 ${barColor}`;
    document.getElementById('combinedPercent').textContent = combined + '% combined risk';

    // Risk Assessment Bar
    const riskFill = document.getElementById('riskAssessFill');
    const riskText = document.getElementById('riskAssessText');
    if (riskFill && riskText) {
        riskFill.style.width = combined + '%';
        if (combined < 33) {
            riskFill.style.background = 'linear-gradient(90deg, #34e89e, #0fce86)';
            riskText.textContent = 'Low Risk (' + combined + '%)';
            riskText.style.color = '#34e89e';
        } else if (combined < 66) {
            riskFill.style.background = 'linear-gradient(90deg, #ffb648, #ff8c00)';
            riskText.textContent = 'Medium Risk (' + combined + '%)';
            riskText.style.color = '#ffb648';
        } else {
            riskFill.style.background = 'linear-gradient(90deg, #ff5470, #cc2244)';
            riskText.textContent = 'High Risk (' + combined + '%)';
            riskText.style.color = '#ff5470';
        }
    }

    const details = ruleData.details;
    if (details) {
        document.getElementById('urlDetails').classList.remove('hidden');
        const table = document.getElementById('detailTable');
        table.innerHTML = '';
        const allDetails = {...details};
        if (data.domain_age_days !== null && data.domain_age_days !== undefined) {
            allDetails['Domain Age'] = data.domain_age_days + ' days';
        }
        Object.entries(allDetails).forEach(([key, value]) => {
            table.innerHTML += `<div class="text-gray-400">${key}</div><div class="text-gray-200 truncate" title="${value}">${value}</div>`;
        });
    }

    const issues = ruleData.issues;
    if (issues && issues.length > 0) {
        document.getElementById('issuesContainer').classList.remove('hidden');
        const list = document.getElementById('issuesList');
        list.innerHTML = '';
        issues.forEach(issue => {
            const severityColors = {
                'high': 'bg-red-500/10 text-red-400 border-red-500/20',
                'medium': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
                'low': 'bg-blue-500/10 text-blue-400 border-blue-500/20'
            };
            list.innerHTML += `
                <div class="flex items-start gap-3 p-3 rounded-lg border ${severityColors[issue.severity] || severityColors.low}">
                    <span class="text-xs font-medium uppercase px-1.5 py-0.5 rounded ${issue.severity === 'high' ? 'bg-red-500/20' : issue.severity === 'medium' ? 'bg-yellow-500/20' : 'bg-blue-500/20'}">${issue.severity}</span>
                    <span class="text-sm">${issue.text}</span>
                </div>
            `;
        });
    } else {
        document.getElementById('issuesContainer').classList.add('hidden');
    }

    document.getElementById('resultContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function initHistory() {
    document.getElementById('clearHistory').addEventListener('click', async () => {
        if (!confirm('Clear all scan history?')) return;
        try {
            await apiFetch(API_BASE + '/history', { method: 'DELETE' });
            loadHistory();
            loadStats();
        } catch (err) {
            alert('Failed to clear history');
        }
    });
}

async function loadHistory() {
    const tbody = document.getElementById('historyBody');
    try {
        const response = await apiFetch(API_BASE + '/history?limit=50');
        const data = await response.json();
        const scans = data.history || [];

        if (scans.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-gray-500">No scan history yet</td></tr>';
            return;
        }

        tbody.innerHTML = scans.map(scan => {
            const resultClass = scan.ml_result === 'phishing' ? 'text-red-400' : 'text-green-400';
            const issues = scan.rule_flags ? JSON.parse(scan.rule_flags) : [];
            const issuesText = issues.length > 0
                ? `<span class="text-xs text-gray-400">${escapeHtml(issues.slice(0, 2).join('; '))}${issues.length > 2 ? '...' : ''}</span>`
                : '<span class="text-xs text-gray-500">None</span>';
            const timestamp = scan.timestamp ? new Date(scan.timestamp + 'Z').toLocaleString() : '-';
            const origDisplay = scan.original_url ? `<span class="text-xs text-yellow-400/60 truncate block max-w-[150px]" title="${escapeHtml(scan.original_url)}">${escapeHtml(scan.original_url)}</span>` : '<span class="text-xs text-gray-600">-</span>';
            return `
                <tr>
                    <td class="px-4 py-3 max-w-[180px] truncate" title="${escapeHtml(scan.url)}">${escapeHtml(scan.url)}</td>
                    <td class="px-4 py-3">${origDisplay}</td>
                    <td class="px-4 py-3 font-medium ${resultClass}">${escapeHtml(scan.ml_result)}</td>
                    <td class="px-4 py-3">${scan.ml_score || 0}%</td>
                    <td class="px-4 py-3">${scan.risk_score || 0}%</td>
                    <td class="px-4 py-3">${issuesText}</td>
                    <td class="px-4 py-3 text-xs text-gray-400">${timestamp}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center text-gray-500">Failed to load history</td></tr>';
    }
}

function initDashboard() {
}

async function loadStats() {
    try {
        const response = await apiFetch(API_BASE + '/stats');
        const stats = await response.json();

        const total = stats.total_scans || 0;
        document.getElementById('statTotal').textContent = total;
        document.getElementById('statPhishing').textContent = stats.phishing_count || 0;
        document.getElementById('statPhishingPct').textContent = (stats.phishing_percentage || 0);
        document.getElementById('statSafePct').textContent = (stats.safe_percentage || 0);

        document.getElementById('dashTotal').textContent = total;
        document.getElementById('dashPhishing').textContent = stats.phishing_count || 0;
        document.getElementById('dashSafe').textContent = stats.safe_count || 0;
        document.getElementById('dashAvgRisk').textContent = (stats.average_risk_score || 0) + '%';

        const sessionEl = document.getElementById('statSession');
        if (sessionEl) {
            sessionEl.textContent = sessionStorage.getItem('pg_session_scans') || '0';
        }

        drawPieChart(stats.safe_count || 0, stats.phishing_count || 0);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

function drawPieChart(safe, phishing) {
    const canvas = document.getElementById('pieChart');
    const ctx = canvas.getContext('2d');
    const total = safe + phishing;

    document.getElementById('chartCenterText').textContent = total;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const r = 80;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (total === 0) {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 20;
        ctx.stroke();
        return;
    }

    const safeAngle = (safe / total) * Math.PI * 2;
    const phishingAngle = (phishing / total) * Math.PI * 2;

    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + safeAngle);
    ctx.strokeStyle = '#22c55e';
    ctx.lineWidth = 20;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2 + safeAngle, -Math.PI / 2 + safeAngle + phishingAngle);
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 20;
    ctx.stroke();
}

function initChatbot() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');

    sendBtn.addEventListener('click', () => sendChatMessage(input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendChatMessage(input.value);
    });

    document.querySelectorAll('.chat-quick').forEach(el => {
        el.addEventListener('click', () => {
            input.value = el.textContent;
            sendChatMessage(input.value);
        });
    });
}

async function sendChatMessage(message) {
    const input = document.getElementById('chatInput');
    const messages = document.getElementById('chatMessages');
    const sendBtn = document.getElementById('chatSend');

    if (!message || !message.trim()) return;

    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg-user';
    userDiv.innerHTML = `<div class="chat-bubble-user">${escapeHtml(message)}</div>`;
    messages.appendChild(userDiv);

    input.value = '';
    sendBtn.disabled = true;
    messages.scrollTop = messages.scrollHeight;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg-bot';
    typingDiv.innerHTML = `<div class="chat-avatar-pg">PG</div><div class="chat-bubble-bot chat-typing"><span></span><span></span><span></span></div>`;
    messages.appendChild(typingDiv);
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await apiFetch(API_BASE + '/chatbot', {
            method: 'POST',
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        typingDiv.remove();
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-msg-bot';
        botDiv.innerHTML = `<div class="chat-avatar-pg">PG</div><div class="chat-bubble-bot">${renderMarkdown(data.reply)}</div>`;
        messages.appendChild(botDiv);
    } catch (err) {
        typingDiv.remove();
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-msg-bot';
        errDiv.innerHTML = `<div class="chat-avatar-pg">PG</div><div class="chat-bubble-bot chat-error">Could not connect. Make sure the backend is running.</div>`;
        messages.appendChild(errDiv);
    }

    sendBtn.disabled = false;
    messages.scrollTop = messages.scrollHeight;
}

function renderMarkdown(text) {
    if (!text) return '';
    const lines = text.split('\n');
    let html = '';
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        if (line.includes('|') && i + 1 < lines.length && /^\|[\s\-\|]+\|$/.test(lines[i+1].trim())) {
            const headers = line.split('|').map(h => h.trim()).filter(h => h);
            i += 2;
            let t = '<table class="chat-table"><thead><tr>';
            headers.forEach(h => { t += `<th>${inlineMarkdown(h)}</th>`; });
            t += '</tr></thead><tbody>';
            while (i < lines.length && lines[i].includes('|')) {
                const cells = lines[i].split('|').map(c => c.trim()).filter((c, idx, arr) => !(idx === 0 && c === '') && !(idx === arr.length-1 && c === ''));
                if (cells.length > 0) { t += '<tr>'; cells.forEach(c => { t += `<td>${inlineMarkdown(c)}</td>`; }); t += '</tr>'; }
                i++;
            }
            html += t + '</tbody></table>'; continue;
        }
        if (/^[\*\-] /.test(line)) {
            let l = '<ul class="chat-list">';
            while (i < lines.length && /^[\*\-] /.test(lines[i])) { l += `<li>${inlineMarkdown(lines[i].replace(/^[\*\-] /, ''))}</li>`; i++; }
            html += l + '</ul>'; continue;
        }
        if (/^\d+\. /.test(line)) {
            let l = '<ol class="chat-list">';
            while (i < lines.length && /^\d+\. /.test(lines[i])) { l += `<li>${inlineMarkdown(lines[i].replace(/^\d+\. /, ''))}</li>`; i++; }
            html += l + '</ol>'; continue;
        }
        if (line.trim() === '') { html += '<br>'; i++; continue; }
        html += `<p>${inlineMarkdown(line)}</p>`; i++;
    }
    return html;
}

function inlineMarkdown(text) {
    let t = escapeHtml(text);
    t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    t = t.replace(/\*(.+?)\*/g, '<em>$1</em>');
    t = t.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');
    return t;
}

function displayBulkResults(results) {
    const existing = document.getElementById('bulkResultsPanel');
    if (existing) existing.remove();

    const total = results.length;
    const phishing = results.filter(r => !r.error && r.final_verdict === 'phishing').length;
    const risky = results.filter(r => !r.error && r.final_verdict === 'risky').length;
    const safe = results.filter(r => !r.error && r.final_verdict === 'safe').length;
    const errors = results.filter(r => r.error).length;

    const panel = document.createElement('div');
    panel.id = 'bulkResultsPanel';
    panel.className = 'card mt-4';
    panel.innerHTML = `
        <div class="flex items-center gap-3 mb-5">
            <div class="section-label">Bulk Scan Results</div>
            <div class="section-line"></div>
            <button onclick="document.getElementById('bulkResultsPanel').remove()"
                style="background:transparent;border:1px solid var(--border);color:var(--text-muted);padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px;">
                Clear
            </button>
        </div>
        <div class="bulk-summary-row">
            <div class="bulk-sum-card">
                <div class="bulk-sum-num">${total}</div>
                <div class="bulk-sum-label">Total Scanned</div>
            </div>
            <div class="bulk-sum-card danger">
                <div class="bulk-sum-num" style="color:var(--accent)">${phishing}</div>
                <div class="bulk-sum-label">Phishing</div>
            </div>
            ${risky > 0 ? `<div class="bulk-sum-card">
                <div class="bulk-sum-num" style="color:var(--warning)">${risky}</div>
                <div class="bulk-sum-label">Risky</div>
            </div>` : ''}
            <div class="bulk-sum-card safe">
                <div class="bulk-sum-num" style="color:var(--primary)">${safe}</div>
                <div class="bulk-sum-label">Safe</div>
            </div>
            ${errors > 0 ? `<div class="bulk-sum-card"><div class="bulk-sum-num" style="color:var(--warning)">${errors}</div><div class="bulk-sum-label">Errors</div></div>` : ''}
        </div>
        <div class="table-wrap mt-4">
            <table>
                <thead><tr>
                    <th style="width:36px">#</th>
                    <th>URL</th>
                    <th style="width:110px;text-align:center">Verdict</th>
                    <th style="width:90px;text-align:center">ML Score</th>
                    <th style="width:90px;text-align:center">Risk</th>
                </tr></thead>
                <tbody>${results.map((r, i) => {
                    if (r.error) {
                        return `<tr>
                            <td style="color:var(--text-muted);text-align:center">${i+1}</td>
                            <td style="font-family:var(--font-mono);font-size:12px;color:var(--text-muted)">${escapeHtml(r.url)}</td>
                            <td colspan="3" style="text-align:center;color:var(--warning);font-size:12px">${escapeHtml(r.error)}</td>
                        </tr>`;
                    }
                    const v = r.final_verdict || 'safe';
                    const isP = v === 'phishing';
                    const isR = v === 'risky';
                    const mlPct = r.ml_result ? r.ml_result.phishing_probability : 0;
                    const risk = r.combined_risk_score || 0;
                    const vc = isP ? 'var(--accent)' : (isR ? 'var(--warning)' : 'var(--primary)');
                    const vBg = isP ? 'var(--accent-dim)' : (isR ? 'rgba(245,158,11,0.15)' : 'var(--primary-dim)');
                    const vLabel = isP ? 'PHISHING' : (isR ? 'RISKY' : 'SAFE');
                    const rc = risk > 66 ? 'var(--accent)' : risk > 33 ? 'var(--warning)' : 'var(--primary)';
                    return `<tr>
                        <td style="color:var(--text-muted);text-align:center">${i+1}</td>
                        <td><a href="${escapeHtml(r.url)}" target="_blank" rel="noopener"
                            style="font-family:var(--font-mono);font-size:12px;color:var(--text-dim);text-decoration:none;display:block;max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                            title="${escapeHtml(r.url)}">${escapeHtml(r.url)}</a></td>
                        <td style="text-align:center">
                            <span style="font-family:var(--font-heading);font-size:12px;font-weight:600;color:${vc};background:${vBg};padding:3px 10px;border-radius:5px">
                                ${vLabel}
                            </span>
                        </td>
                        <td style="text-align:center;font-family:var(--font-mono);font-size:13px;color:${mlPct > 50 ? 'var(--accent)' : 'var(--primary)'}">${mlPct}%</td>
                        <td style="text-align:center">
                            <div style="display:flex;align-items:center;gap:6px;justify-content:center">
                                <div style="flex:1;height:5px;background:var(--border);border-radius:3px;max-width:50px">
                                    <div style="height:100%;width:${risk}%;background:${rc};border-radius:3px"></div>
                                </div>
                                <span style="font-size:12px;color:${rc};font-family:var(--font-mono);min-width:28px">${risk}%</span>
                            </div>
                        </td>
                    </tr>`;
                }).join('')}</tbody>
            </table>
        </div>`;

    document.getElementById('tabAnalyze').appendChild(panel);
    setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}