# ✈️ CashPilot — AI Financial Co-Pilot

> AI-powered financial intelligence for micro-businesses. Upload your bank statement, get instant insights.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4.1--mini-412991?logo=openai&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-000000?logo=vercel)

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
| **Backend** | Python, Flask |
| **AI** | OpenAI GPT-4.1-mini |
| **Database** | PostgreSQL (Neon) + SQLAlchemy |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Charts** | Chart.js |
| **Auth** | Google OAuth 2.0 (Authlib) |
| **Deployment** | Vercel (Serverless) |

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
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
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
├── models.py                 # SQLAlchemy DB models (User + Transaction)
├── vercel.json               # Vercel serverless config
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not in repo)
├── services/
│   ├── ai_service.py         # OpenAI API wrapper (chat + completions)
│   ├── openai_service.py     # Transaction analysis with caching
│   ├── category_service.py   # AI + rule-based categorization
│   ├── email_service.py      # Email summary via Resend
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

## 🌐 Deployment (Vercel + Neon)

### Database Setup (Neon)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project → copy the PostgreSQL connection string
3. Tables are auto-created on first request

### Deploy to Vercel

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import your GitHub repo
3. Add environment variables in Vercel dashboard (Settings → Environment Variables):

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Neon connection string |
| `FLASK_SECRET_KEY` | A random secret string |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `APP_URL` | `https://your-app.vercel.app` |
| `RESEND_API_KEY` | (Optional) For email summaries |

4. Deploy! 🚀
5. Add `https://YOUR-VERCEL-URL/auth/callback` to Google OAuth redirect URIs in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

---

## 👤 Author

**Muhammad Minhal** — [GitHub](https://github.com/Minicoder0)

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

