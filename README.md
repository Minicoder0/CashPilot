# ✈️ CashPilot — AI Financial Co-Pilot

> AI-powered financial intelligence for micro-businesses. Upload your bank statement, get instant insights.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4.1--mini-412991?logo=openai&logoColor=white)
![Railway](https://img.shields.io/badge/Deployed-Railway-0B0D0E?logo=railway)

---

## 🚀 What It Does

CashPilot turns raw CSV bank statements into **actionable financial insights** in seconds — no accounting knowledge needed.

- **📊 Smart Dashboard** — Summary cards, monthly cashflow chart, expense breakdown pie chart
- **🧠 Creative AI Insights** — Includes a Financial Health Score (0-100), Cash Runway predictor, and Anomaly Detection (flagging unusual spending spikes)
- **🤖 Actionable Advice** — GPT-4.1-mini analyzes your spending and generates personalized tips
- **💬 AI Chat** — Ask CashPilot anything about your finances in plain English
- **🏷️ Auto-Categorization** — Transactions are categorized using AI (with rule-based fallback)
- **🔐 Google Auth** — Secure sign-in with your Google account
- **📱 Responsive UI** — Professional Light Theme, works on desktop, tablet, and phone

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, Flask, Gunicorn |
| **AI** | OpenAI GPT-4.1-mini |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Charts** | Chart.js |
| **Auth** | Google OAuth 2.0 (Authlib) |
| **Deployment** | Railway |

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Minicoder0/CashPilot.git
cd CashPilot
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FLASK_SECRET_KEY=any-random-secret-string
```

### 3. Run

```bash
python app.py
```

Visit **http://127.0.0.1:5000** → Sign in with Google → Upload a CSV or load demo data.

---

## 📄 CSV Format

Your CSV needs these columns:

```csv
date,description,amount,type
2025-01-05,OFFICE RENT,2000.00,expense
2025-01-06,CLIENT PAYMENT,5000.00,income
```

| Column | Required | Notes |
|--------|----------|-------|
| `date` | ✅ | YYYY-MM-DD format |
| `description` | ✅ | Transaction description |
| `amount` | ✅ | Numeric value |
| `type` | Optional | `income` or `expense` — auto-detected if missing |

---

## 📁 Project Structure

```
CashPilot/
├── app.py                    # Flask app + routes + Google OAuth
├── Procfile                  # Railway/Gunicorn config
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not in repo)
├── services/
│   ├── ai_service.py         # OpenAI API wrapper (chat + completions)
│   ├── openai_service.py     # Transaction analysis with caching
│   ├── category_service.py   # AI + rule-based categorization
│   └── insight_service.py    # Financial insight generation
├── templates/
│   ├── index.html            # Main dashboard
│   └── login.html            # Google sign-in page
├── static/
│   ├── css/style.css         # Clean B2B Light theme
│   └── js/
│       ├── app.js            # Dashboard logic
│       ├── charts.js         # Chart.js visualizations
│       └── chat.js           # AI chat interface
└── data/
    ├── demo_transactions.json
    └── demo-transactions.csv
```

---

## 🌐 Deployment

Deployed on **Railway** with auto-deploy from GitHub.

To deploy your own:
1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Add environment variables
4. Add `https://YOUR-URL/auth/callback` to Google OAuth redirect URIs

---

## 👤 Author

**Muhammad Minhal** — [GitHub](https://github.com/Minicoder0)

---

## 📜 License

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
