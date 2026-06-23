# PhishGuard 🔒

**Advanced Phishing URL Detection System** — A final-year cybersecurity project by students at **Hamdard University, Karachi**.

PhishGuard analyzes URLs using a **dual-detection approach**: rule-based heuristics (SSL, WHOIS, URL structure, brand keyword detection) combined with a **Random Forest ML model** (31 features) to classify URLs as **safe** or **phishing**.

---

## ✨ Features

- **Real-time URL Analysis** — Paste a URL and get instant results
- **ML-Powered Detection** — Random Forest trained on 500K+ URLs
- **Rule-Based Engine** — SSL checks, WHOIS domain age, URL shortener unrolling, brand impersonation detection, suspicious TLD detection
- **Security Chatbot** — Ask phishing/security questions via integrated chatbot
- **Dashboard & History** — Visual scan statistics, pie charts, scan history
- **Bulk Scanning** — Scan up to 20 URLs at once
- **Chrome Extension** — Right-click any link or selected text to scan instantly
- **Docker Support** — One-command deployment

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
<summary><b>Windows</b></summary>

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

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Set a random string for Flask sessions |
| `OPENROUTER_API_KEY` | ❌ | Needed only for the chatbot feature |
| `ADMIN_API_KEY` | ❌ | Needed if `REQUIRE_API_KEY=true` |
| `REQUIRE_API_KEY` | ❌ | Set to `true` to enforce API authentication |

### Step 5: Download Dataset

> The ML model requires a dataset of **500K+ URLs** for training. The dataset is **not included** in the repository.

```bash
# Download the dataset (~55MB)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/iamzaidmalik/phishguard-data/main/phishing_site_urls.csv" -OutFile "data/phishing_site_urls.csv"
```

**Alternative sources:**
- [Kaggle — Malicious & Benign URLs](https://www.kaggle.com/datasets/siddharthkumar25/malicious-and-benign-urls)
- [Google Drive Mirror]([https://drive.google.com/drive/folders/1Yl2Uq8Pf1e_TKjKRAhYoGcr5vQqKjI7p](https://drive.google.com/drive/folders/1-KU8hhM4oUKcxYr57oNP6rxKdhdnefvO?usp=sharing))

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

> **Note:** Set `REQUIRE_API_KEY=true` and provide `ADMIN_API_KEY` in Docker environment for production use. The Dockerfile defaults to `REQUIRE_API_KEY=true` for security.

### Stop Docker

```bash
docker-compose down
```

---

## 🧩 Chrome Extension Setup

### Step 1: Ensure Backend is Running

The extension communicates with the backend at `http://127.0.0.1:8080`. Make sure the server is running first.

### Step 2: Load the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `extension/` folder from this project

### Step 3: Use the Extension

- **Right-click** any link → **Scan URL with PhishGuard**
- **Select text** containing a URL → **Scan URL with PhishGuard**
- Click the extension icon in the toolbar to open the popup scanner

---

## 📖 How to Use

### Scan a Single URL

1. Open the app at **http://127.0.0.1:8080**
2. Paste a URL in the input field
3. Click **Scan URL** (or press Enter)
4. View the result showing:
   - **ML Prediction** — phishing probability score
   - **Rule Analysis** — risk level with flagged issues
   - **Combined Verdict** — final Safe / Phishing decision
   - **URL Details** — protocol, domain, path, query params
   - **Flagged Issues** — specific security concerns found

### Bulk Scan (Up to 20 URLs)

1. Click **Bulk Scan** tab
2. Paste URLs (one per line, max 20)
3. Click **Scan All URLs**
4. Results appear in a table with color-coded verdicts

### View Dashboard

- See scan distribution (safe vs phishing)
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

## 📡 API Reference

### Base URL

```
http://127.0.0.1:8080
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend |
| `GET` | `/health` | Server health check |
| `POST` | `/predict` | Analyze a single URL |
| `POST` | `/bulk-predict` | Analyze multiple URLs (max 20) |
| `GET` | `/stats` | Get scan statistics |
| `GET` | `/history` | Get scan history (`?limit=N`) |
| `DELETE` | `/history` | Clear scan history |
| `POST` | `/chatbot` | Ask the security chatbot |

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

### Health Check

```bash
curl http://127.0.0.1:8080/health
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
| `REQUIRE_API_KEY` | `false` | Require API key for endpoints |
| `ADMIN_API_KEY` | *(auto)* | Admin key for managing API keys |
| `OPENROUTER_API_KEY` | — | API key for chatbot (get from [openrouter.ai](https://openrouter.ai)) |

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
│   ├── app.py                  # Routes & server logic
│   ├── config.py               # Configuration loader
│   ├── database.py             # SQLite operations
│   ├── train_model.py          # ML training pipeline
│   ├── auto_retrain.py         # 24-hour retraining scheduler
│   ├── phishing_model.pkl      # Trained ML model (generated)
│   ├── phishguard.db           # SQLite database (generated)
│   ├── models/
│   │   └── detector.py         # ML model loader
│   └── utils/
│       ├── feature_extractor.py    # 31-feature extraction
│       ├── rule_analyzer.py        # Rule-based heuristics
│       ├── ssl_checker.py          # SSL certificate validation
│       ├── whois_checker.py        # WHOIS lookup
│       ├── unshortener.py          # URL shortener resolver
│       ├── validators.py           # URL validation
│       └── auth.py                 # JWT authentication
├── frontend/                   # Web UI (served by Flask)
│   ├── index.html              # Main scanner page
│   ├── about.html              # About page
│   ├── contact.html            # Contact form
│   ├── terms.html              # Terms & conditions
│   ├── results.html            # Bulk scan results
│   ├── script.js               # Frontend logic
│   └── style.css               # Dark theme styles
├── extension/                  # Chrome extension
│   ├── manifest.json           # Extension config
│   ├── background.js           # Context menu handler
│   ├── popup.html              # Popup UI
│   ├── popup.js                # Popup logic
│   └── icons/                  # Extension icons
├── scripts/                    # Utility scripts
│   ├── init_model.py
│   ├── add_safe_urls.py
│   ├── retrain.py
│   └── retrain.bat
├── data/
│   └── phishing_site_urls.csv  # Dataset (not included)
├── docs/                       # Documentation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example                # Environment template
└── .gitignore
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
- The extension only works when the server is active

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
