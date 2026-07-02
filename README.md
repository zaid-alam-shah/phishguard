# PhishGuard 🔒

**Advanced Phishing URL Detection System** — A final-year cybersecurity project by students at **Hamdard University, Karachi**.

PhishGuard analyzes URLs using a **dual-detection approach**: rule-based heuristics (SSL, WHOIS, URL structure, brand keyword detection) combined with a **Random Forest ML model** (31 features) to classify URLs with a **3-tier verdict**: ✅ Safe, ⚡ Risky, 🛑 Phishing.

🌐 **Live Demo:** [https://phishguard.onrender.com](https://phishguard.onrender.com)

---

## ✨ Features

### 🔍 Core Detection Engine
- **ML-Powered Detection** — Random Forest trained on 500K+ URLs (92% accuracy)
- **Rule-Based Engine** — SSL checks, WHOIS domain age, URL shortener unrolling (with **SSRF protection** 🔒), brand impersonation detection, suspicious TLD detection
- **3-Tier Verdict System** — URLs classified as **Safe** (<40), **Risky** (40-59), or **Phishing** (60+)
- **Client-Side Pre-check** — Instant local URL analysis catches common phishing patterns BEFORE the API call (zero-delay warnings)
- **Bulk Scanning** — Scan up to 20 URLs at once with parallel processing

### 🛡️ Chrome Extension — Real-Time Protection
- **Auto-block phishing URLs** — Intercepts navigation before the page loads
- **Standalone Warning Page** — Full-page warning with color-coded verdict bar
- **Page Load Prevention** — The phishing URL **never loads** until the user explicitly clicks "Continue Anyway"
- **"Continue Anyway" Bypass** — User-approved URLs are temporarily whitelisted (10-second window)
- **Settings Panel** — Configurable API Server URL (switch between local & cloud)
- **Auto API Key Provisioning** — Extension automatically fetches a session API key from the server

### 🔐 Security Hardening
- **API Key Authentication** — All endpoints require a valid API key by default (`REQUIRE_API_KEY=true`)
- **Auto Key Provisioning** — Frontend & extension auto-fetch keys via `/api/client-key` (rate-limited)
- **Admin Key Management** — Create, list & revoke API keys via admin endpoints
- **SSRF Protection** — URL shortener resolver validates resolved IPs, blocks private/internal networks
- **Rate Limiting** — 30 requests per 60 seconds per IP
- **Security Headers** — CSP, X-Frame-Options, X-Content-Type-Options, etc.

### 🌐 Web Interface
- **Dashboard & History** — Visual scan statistics, pie charts, scan history
- **Security Chatbot** — Ask phishing/security questions via integrated AI chatbot (powered by OpenRouter)
- **Real-time URL Analysis** — Paste a URL and get instant results
- **Dark Theme** — Modern dark UI with gradient accents

### 🚀 Deployment Options
- **Local** — Run with Python directly (SQLite)
- **Docker** — One-command deployment with optional nginx reverse proxy
- **Render** — Free cloud hosting with one-click deploy via `render.yaml`
- **PostgreSQL** — Optional production database (set `DATABASE_URL`)

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required for local setup |
| pip | Latest | Comes with Python |
| Git | Latest | To clone the repo |
| Docker & Docker Compose | Latest | Optional (for Docker setup) |
| Chrome Browser | Latest | Required for the extension |

---

## 🚀 Quick Start (Local Setup)

### Step 1: Clone the Repository

```bash
git clone https://github.com/zaid-alam-shah/phishguard.git
cd phishguard
```

### Step 2: Create Virtual Environment

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
python -m venv venv
venv\Scripts\activate
```
</details>

<details>
<summary><b>Linux / macOS</b></summary>

```bash
python3 -m venv venv
source venv/bin/activate
```
</details>

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment (Optional)

```bash
cp .env.example .env
```

The server works **out of the box without a `.env` file**. If you do create one:

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUIRE_API_KEY` | `true` | Require API key for endpoints (frontend auto-fetches keys) |
| `SECRET_KEY` | *(auto)* | Flask session secret key |
| `ADMIN_API_KEY` | *(auto)* | Admin key (printed on first server start) |
| `OPENROUTER_API_KEY` | — | API key for chatbot (get from [openrouter.ai](https://openrouter.ai)) |
| `DATABASE_URL` | — | PostgreSQL connection string (omit for SQLite) |
| `SSL_CERT_PATH` | — | Path to SSL certificate (for HTTPS) |
| `SSL_KEY_PATH` | — | Path to SSL key (for HTTPS) |
| `AUTO_RETRAIN_ENABLED` | `false` | Enable 24-hour model auto-retraining |

> **Note:** When `REQUIRE_API_KEY=true` (default), the frontend and extension automatically fetch API keys via `/api/client-key`. No manual key setup needed for normal use.

### Step 5: Download Dataset

> The ML model requires a dataset of **500K+ URLs** for training. The dataset is **not included** in the repository.

```bash
# Download the dataset (~55MB)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/iamzaidmalik/phishguard-data/main/phishing_site_urls.csv" -OutFile "data/phishing_site_urls.csv"
```

**Alternative sources:**
- [Kaggle — Malicious & Benign URLs](https://www.kaggle.com/datasets/siddharthkumar25/malicious-and-benign-urls)
- [Google Drive Mirror](https://drive.google.com/drive/folders/1-KU8hhM4oUKcxYr57oNP6rxKdhdnefvO?usp=sharing)

Place the downloaded `phishing_site_urls.csv` in the `data/` folder.

### Step 6: Train the ML Model

```bash
python backend/train_model.py
```

This will:
- Load and deduplicate the dataset
- Extract 31 features from each URL
- Train a Random Forest classifier (150 trees)
- Save the model to `backend/phishing_model.pkl`
- Print accuracy metrics

### Step 7: Start the Server

```bash
python backend/app.py
```

The server starts at **http://127.0.0.1:8080**.

---

## 🐳 Quick Start (Docker)

### Step 1: Download Dataset

Same as Step 5 above — place `phishing_site_urls.csv` in the `data/` folder.

### Step 2: Build & Run

```bash
docker-compose up --build
```

Or run in background:

```bash
docker-compose up -d
```

The app will be available at **http://localhost:8080**.

### With nginx Reverse Proxy (HTTPS)

```bash
# Uncomment the nginx service in docker-compose.yml, then:
docker-compose up -d
# Access at https://localhost
```

### Stop Docker

```bash
docker-compose down
```

---

## ☁️ Deploy to Render (Free Hosting)

### Option A — One-Click Deploy (render.yaml)

1. Push your repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **Blueprints**
3. Connect your repo — Render auto-detects `render.yaml`
4. Click **Apply** — everything is pre-configured

### Option B — Manual Web Service

1. Create a **Web Service** on Render
2. Connect your GitHub repo
3. Settings:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan:** Free
4. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.0`
   - `FLASK_HOST`: `0.0.0.0`
   - `SECRET_KEY`: (auto-generate)
   - `ADMIN_API_KEY`: (auto-generate)
5. Deploy!

> **Note on Render Free Tier:** SQLite data is ephemeral (lost on restart). For persistent data, add a free PostgreSQL database from [Supabase](https://supabase.com) and set `DATABASE_URL`.

### After Deploying

1. Open your Render URL (e.g., `https://phishguard.onrender.com`)
2. The frontend auto-fetches an API key — scanning works immediately
3. For the Chrome extension, go to **Settings** → change **API Server URL** to your Render URL

---

## 🧩 Chrome Extension Setup

### Step 1: Ensure Backend is Running

The extension communicates with the backend. Make sure the server is running first (either locally or on Render).

### Step 2: Load the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `extension/` folder from this project

### Step 3: Configure for Cloud (if using Render)

1. Click the PhishGuard icon in the toolbar
2. Click **⚙️ Settings** at the bottom
3. Change **API Server URL** from `http://127.0.0.1:8080` to your Render URL (e.g., `https://phishguard.onrender.com`)
4. Click **Save**, then **🔄 Refresh API Key**
5. Connection status should show ✅ Connected

### Step 4: Enable Real-Time Protection

1. Click the PhishGuard icon in the toolbar
2. Toggle **Real-Time Protection** ON 🛡️
3. Now every URL you visit is automatically scanned

### How Real-Time Protection Works

```
User clicks/enters a URL
    ↓
┌─────────────────────────────────────┐
│ webNavigation.onBeforeNavigate fires │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Client-Side Pre-check (instant)     │
│ ✓ Suspicious TLD?                   │
│ ✓ Brand impersonation?              │
│ ✓ Phishing keywords?                │
│ ✓ HTTP (no SSL)?                    │
└─────────────────────────────────────┘
    ↓ Score ≥ 40?
    ↓
┌─────────────────────────────────────┐
│ 🚫 PAGE LOAD BLOCKED               │
│ Redirect to warning.html           │
│ (Phishing URL NEVER loads)          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ User sees:                          │
│ 🔴 PHISHING DETECTED  (red bar)    │
│   OR                                │
│ ⚠️ RISKY             (orange bar)  │
│                                     │
│ [🛑 Block — Go to Safety]          │
│ [⚠️ Continue Anyway]               │
└─────────────────────────────────────┘
```

### Extension Features

- **Right-click** any link → **Scan URL with PhishGuard**
- **Select text** containing a URL → **Scan URL with PhishGuard**
- Click the extension icon to open the popup scanner
- **Real-Time Protection** toggle in the popup
- **Settings panel** — API Server URL, connection status, key refresh

---

## 📖 How to Use

### Scan a Single URL

1. Open the app at **http://127.0.0.1:8080** (or your Render URL)
2. Paste a URL in the input field
3. Click **Scan URL** (or press Enter)
4. View the result showing:
   - **ML Prediction** — phishing probability score
   - **Rule Analysis** — risk level with flagged issues
   - **Combined Verdict** — final Safe / Risky / Phishing decision
   - **URL Details** — protocol, domain, path, query params
   - **Flagged Issues** — specific security concerns found

### Bulk Scan (Up to 20 URLs)

1. Click **Bulk Scan** tab
2. Paste URLs (one per line, max 20)
3. Click **Scan All URLs**
4. Results appear in a table with color-coded verdicts

### View Dashboard

- See scan distribution (safe, risky, phishing)
- View total scans, phishing count, average risk score
- Pie chart visualization

### Use the Security Chatbot

1. Go to the **AI Security Assistant** tab
2. Ask questions like:
   - "What is phishing?"
   - "How to detect phishing emails?"
   - "How does PhishGuard work?"
   - "What is 2FA?"

---

## 📊 Risk Thresholds

| Risk Score | Verdict | Color | Example |
|-----------|---------|-------|---------|
| **0-39%** | ✅ Safe | 🟢 Green | `google.com` → 19% |
| **40-59%** | ⚡ Risky | 🟡 Orange | `maryhoffmann.com/hsbc/...` → 50% |
| **60-100%** | 🛑 Phishing | 🔴 Red | `secure-paypal-login.xyz/webscr` → 100% |

The combined score formula:
```
combined_risk_score = max(rule_score, ml_score)
                   + boost (if 2+ high-severity flags)
```

---

## 📡 API Reference

### Base URL

```
Local:   http://127.0.0.1:8080
Render:  https://phishguard.onrender.com
```

### Authentication

When `REQUIRE_API_KEY=true` (default), all `/predict` and `/bulk-predict` endpoints require authentication.

**Method 1 — Auto Key (Frontend):** The frontend automatically fetches a session key via `/api/client-key`.

**Method 2 — Bearer Token:**
```bash
curl -X POST https://phishguard.onrender.com/predict \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Method 3 — Query Parameter:**
```bash
curl -X POST "https://phishguard.onrender.com/predict?api_key=<your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | — | Serves the frontend |
| `GET` | `/api/health` | — | Server health check |
| `GET` | `/api/client-key` | Rate-limited | Get a session API key (for frontend/extension) |
| `POST` | `/predict` | ✅ API Key | Analyze a single URL |
| `POST` | `/bulk-predict` | ✅ API Key | Analyze multiple URLs (max 20) |
| `GET` | `/stats` | — | Get scan statistics |
| `GET` | `/history` | — | Get scan history (`?limit=N`) |
| `DELETE` | `/history` | — | Clear scan history |
| `POST` | `/chatbot` | — | Ask the security chatbot |
| `GET` | `/api/admin/keys` | 🔑 Admin Key | List all API keys |
| `POST` | `/api/admin/keys` | 🔑 Admin Key | Create a new API key |
| `DELETE` | `/api/admin/keys/<hash>` | 🔑 Admin Key | Revoke an API key |

> **Admin endpoints** require `X-Admin-Key` header with the admin key (printed on first server start or set in `.env`).

### Predict a Single URL

```bash
curl -X POST http://127.0.0.1:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://suspicious-login-page.com/update"}'
```

**Response:**

```json
{
  "url": "http://suspicious-login-page.com/update",
  "combined_risk_score": 84,
  "final_verdict": "phishing",
  "ml_result": {
    "prediction": "phishing",
    "phishing_probability": 84.2
  },
  "rule_based": {
    "risk_score": 100,
    "risk_level": "high",
    "issues": [
      {"severity": "low", "text": "Uses insecure HTTP protocol instead of HTTPS"},
      {"severity": "low", "text": "Contains sensitive action keywords in path"}
    ]
  },
  "domain_age_days": null,
  "was_shortened": false
}
```

### Bulk Predict

```bash
curl -X POST http://127.0.0.1:8080/bulk-predict \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://google.com", "http://suspicious.tk/login"]}'
```

### Get a Client API Key

```bash
curl http://127.0.0.1:8080/api/client-key
```

```json
{
  "api_key": "phg_abc123...",
  "message": "Store this key for the session."
}
```

### Admin: Create API Key

```bash
curl -X POST http://127.0.0.1:8080/api/admin/keys \
  -H "X-Admin-Key: <your-admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app-key"}'
```

### Health Check

```bash
curl http://127.0.0.1:8080/api/health
```

```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "1.1.0"
}
```

---

## 🔧 Configuration Reference

All settings are managed through the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `127.0.0.1` | Server bind address |
| `FLASK_PORT` | `8080` | Server port |
| `FLASK_DEBUG` | `False` | Enable debug mode |
| `SECRET_KEY` | *(auto)* | Flask session secret key |
| `DATABASE_PATH` | `backend/phishguard.db` | SQLite database path |
| `DATABASE_URL` | — | PostgreSQL connection string (for Render/cloud) |
| `REQUIRE_API_KEY` | `true` | Require API key for endpoints ⚠️ |
| `ADMIN_API_KEY` | *(auto)* | Admin key for managing API keys |
| `OPENROUTER_API_KEY` | — | API key for chatbot (get from [openrouter.ai](https://openrouter.ai)) |
| `CORS_ALLOWED_ORIGINS` | `localhost` | Comma-separated allowed origins |
| `SSL_CERT_PATH` | — | Path to SSL cert (for HTTPS) |
| `SSL_KEY_PATH` | — | Path to SSL key (for HTTPS) |
| `AUTO_RETRAIN_ENABLED` | `false` | Enable 24-hour model retraining |

---

## 🧪 Model Training Details

### Training Command

```bash
python backend/train_model.py
```

### Feature Engineering (31 Features)

| Category | Features |
|----------|----------|
| **URL Structure** | Length, subdomain count, path length, dot count, slash count, hyphen count |
| **Security** | HTTPS usage, IP address, @ symbol, double slash redirect |
| **Domain** | TLD length, suspicious TLDs, digit ratio, entropy, hyphen presence |
| **Brand Detection** | PayPal, Apple, Amazon, Google, Microsoft, Facebook, etc. in domain/path |
| **Content** | Sensitive keywords, encoded characters, redirect arrows, special chars |

### Performance

| Metric | Value |
|--------|-------|
| Accuracy | **92.10%** |
| Phishing Precision | **92%** |
| Phishing Recall | **71%** |
| Training Data | ~509K URLs (395K safe, 114K phishing) |

---

## 🏗️ Project Structure

```
phishguard/
├── backend/                    # Flask API server
│   ├── app.py                  # Routes & server logic (HTTPS, auth, CORS)
│   ├── config.py               # Configuration loader (env vars)
│   ├── database.py             # SQLite & PostgreSQL support
│   ├── train_model.py          # ML training pipeline
│   ├── auto_retrain.py         # 24-hour retraining scheduler
│   ├── phishing_model.pkl      # Trained ML model (generated)
│   ├── phishguard.db           # SQLite database (generated)
│   ├── models/
│   │   └── detector.py         # ML model loader
│   └── utils/
│       ├── auth.py             # API key auth (generate, validate, manage)
│       ├── feature_extractor.py    # 31-feature extraction
│       ├── rule_analyzer.py        # Rule-based heuristics
│       ├── ssl_checker.py          # SSL certificate validation
│       ├── whois_checker.py        # WHOIS lookup
│       ├── unshortener.py          # URL shortener resolver (SSRF protected)
│       ├── validators.py           # URL validation
│       └── __init__.py
├── frontend/                   # Web UI (served by Flask)
│   ├── index.html              # Main scanner page
│   ├── about.html, contact.html, terms.html
│   ├── results.html            # Bulk scan results
│   ├── script.js               # Frontend logic (auto API key, auth headers)
│   └── style.css               # Dark theme styles
├── extension/                  # Chrome extension (MV3)
│   ├── manifest.json           # Extension config
│   ├── background.js           # Service worker (pre-check, API, blocking)
│   ├── popup.html              # Popup UI (settings panel)
│   ├── popup.js                # Popup logic (API key mgmt, settings)
│   ├── warning.html            # Standalone warning page
│   └── warning.js              # Warning page logic
├── scripts/
│   ├── init_model.py, add_safe_urls.py, retrain.py, retrain.bat
│   ├── generate_certs.bat      # Generate self-signed SSL certs (Windows)
│   └── generate_certs.sh       # Generate self-signed SSL certs (Linux/macOS)
├── nginx/
│   └── nginx.conf              # Production reverse proxy config
├── data/
│   └── phishing_site_urls.csv  # Dataset (not included)
├── docs/                       # Documentation & FYP presentation
├── Dockerfile
├── docker-compose.yml          # With optional nginx service
├── Procfile                    # Render web service start command
├── render.yaml                 # One-click Render deploy config
├── requirements.txt
├── .env.example                # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## ❓ Troubleshooting

### Server won't start — "Address already in use"

Port 8080 is occupied. Either:
- Kill the process using port 8080
- Change `FLASK_PORT` in `.env` to another value (e.g., `8081`)

### ML model not loaded

The model file `backend/phishing_model.pkl` doesn't exist. Run:
```bash
python backend/train_model.py
```

### Extension can't connect

- Make sure the backend is running on `http://127.0.0.1:8080`
- If using Render, update the **API Server URL** in extension Settings
- Click **Refresh API Key** after changing the URL

### Extension shows "Valid API key required"

The server has `REQUIRE_API_KEY=true` but the extension hasn't fetched a key yet. Either:
- Click **🔄 Refresh API Key** in extension Settings
- Or set `REQUIRE_API_KEY=false` in your `.env` file

### Extension shows "Cannot connect to PhishGuard API"

The API Server URL in extension Settings is wrong. Update it to point to your server.

### "No tab with id" error (harmless)

This happens when a tab is closed before the API responds. Already handled with proper error handling.

### Dataset download failed

Try alternative sources:
- [Kaggle Dataset](https://www.kaggle.com/datasets/siddharthkumar25/malicious-and-benign-urls)
- [Google Drive](https://drive.google.com/drive/folders/1Yl2Uq8Pf1e_TKjKRAhYoGcr5vQqKjI7p)

---

## 👥 Team

| Member | Role |
|--------|------|
| **Ibtehaj Mubarak** | Frontend & UI Design |
| **Zaid Alam Shah** | Backend & ML Model |
| **Azaan Rashid** | Testing & Documentation |

**Supervisor:** Hamdard University, Karachi — Department of Computer Science

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

> **Disclaimer:** PhishGuard is an academic project for educational purposes. It is not a substitute for professional cybersecurity solutions. No phishing detection system can guarantee 100% accuracy.
