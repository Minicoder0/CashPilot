# AI Financial Co-Pilot — Hackathon Backlog (2 Days)

> **Problem:** AI Financial Co-Pilot for Micro Businesses
> **Timeline:** 2 Days
> **Goal:** Working demo that shows AI-powered financial intelligence

---

## Judging Criteria Alignment

From the problem statement, judges want to see:
- ✅ Lightweight, not enterprise-heavy
- ✅ AI classifies transactions automatically
- ✅ Generates insights like "Fuel up 22%", "Top 3 customers = 64% revenue"
- ✅ Clean, minimal interface
- ✅ Business owner says: "I finally understand my money"

---

## Out of Scope (Don't Build)

| Feature | Reason |
|---------|--------|
| User authentication | Demo mode only |
| Multi-currency | Time constraint |
| PDF export | Nice-to-have, not core |
| Email notifications | Not demo-critical |
| Password recovery | No auth needed |
| Accessibility compliance | Post-hackathon |
| Mobile responsiveness | Desktop demo is fine |
| Data encryption | Demo data only |

---

## Day 1 — Core Functionality (10 hours)

### Sprint Goal: Working data pipeline + basic dashboard

---

### Story 1.1 — Load Demo Transaction Dataset
**Priority:** P0 (Must Have)
**Time:** 1 hour

Allow users to instantly load sample data to demo the system.

**Acceptance Criteria:**
- "Load Demo Data" button on empty state
- Loads 50-100 pre-categorized transactions
- Data spans 6 months (for trend analysis)
- Mix of income and expenses

**Technical Notes:**
- Hardcode JSON file in `/data/demo-transactions.json`
- No API call needed

---

### Story 1.2 — Upload Transaction CSV
**Priority:** P0 (Must Have)
**Time:** 2 hours

Allow users to upload their own CSV file.

**Acceptance Criteria:**
- Accepts CSV with columns: date, description, amount
- Shows basic validation errors
- Parses and stores in state/memory
- Provide sample CSV template

**Technical Notes:**
- Client-side parsing (Papa Parse or similar)
- No backend storage needed for demo

---

### Story 1.3 — AI Auto-Categorize Transactions
**Priority:** P0 (Must Have)
**Time:** 3 hours

Use AI to assign categories to each transaction.

**Acceptance Criteria:**
- Categories: Rent, Utilities, Payroll, Marketing, Software, Travel, Supplies, Revenue, Other
- AI assigns category based on description
- Works on upload or demo load
- Shows category in transaction list

**Technical Notes:**
- Use OpenAI/Claude API with simple prompt
- Batch transactions to reduce API calls
- Fallback: rule-based matching if API fails

**Sample Prompt:**
```
Categorize these transactions into: Rent, Utilities, Payroll, Marketing, Software, Travel, Supplies, Revenue, Other

Transactions:
1. "SHELL PETROL STATION" - $85.00
2. "TRANSFER FROM JOHN SMITH" - $1200.00
3. "ADOBE CREATIVE CLOUD" - $54.99

Return JSON: [{"index": 1, "category": "Travel"}, ...]
```

---

### Story 1.4 — Display Financial Summary Cards
**Priority:** P0 (Must Have)
**Time:** 2 hours

Show key metrics at a glance.

**Acceptance Criteria:**
- Card 1: Total Income (this month)
- Card 2: Total Expenses (this month)
- Card 3: Net Cashflow (income - expenses)
- Card 4: Transaction Count
- Green/red color coding

**Technical Notes:**
- Calculate from loaded transactions
- Simple card components

---

### Story 1.5 — Monthly Cashflow Bar Chart
**Priority:** P0 (Must Have)
**Time:** 2 hours

Visualize income vs expenses over time.

**Acceptance Criteria:**
- Bar chart showing last 6 months
- Income bars (green) vs Expense bars (red)
- Net line overlay (optional)
- Hover shows values

**Technical Notes:**
- Use Chart.js, Recharts, or similar
- Group transactions by month

---

## Day 2 — AI Intelligence Layer (10 hours)

### Sprint Goal: AI insights + polish for demo

---

### Story 2.1 — Generate AI Financial Insights
**Priority:** P0 (Must Have)
**Time:** 3 hours

Produce 3-5 natural language insights about the business.

**Acceptance Criteria:**
- Insights like:
  - "Fuel expenses increased 22% compared to last month"
  - "Your top 3 customers account for 64% of revenue"
  - "Software subscriptions total $XXX/month"
  - "Cashflow may tighten in 2 weeks based on current burn rate"
- Display in dedicated "AI Insights" panel
- Each insight is specific to the data (not generic)

**Technical Notes:**
- Send transaction summary to LLM
- Prompt for business-owner-friendly language
- Cache results to avoid repeated API calls

**Sample Prompt:**
```
You are a financial advisor for a small business owner. Based on this transaction summary, generate 3-5 specific, actionable insights. Be concise and use plain language.

Summary:
- Total Income: $12,500
- Total Expenses: $9,800
- Top expense category: Travel ($2,100, up 35% from last month)
- Top income source: Customer "ABC Corp" ($5,000, 40% of revenue)
- Recurring expenses detected: Adobe ($55/mo), AWS ($120/mo)

Format as bullet points.
```

---

### Story 2.2 — Top Expense Categories Breakdown
**Priority:** P1 (Should Have)
**Time:** 1.5 hours

Show where money is going.

**Acceptance Criteria:**
- Pie or donut chart of expense categories
- Top 5 categories with percentages
- "Other" bucket for remaining
- Click to see transactions in category (optional)

**Technical Notes:**
- Aggregate by AI-assigned categories
- Simple chart component

---

### Story 2.3 — Transaction List with Categories
**Priority:** P1 (Should Have)
**Time:** 1.5 hours

Display all transactions with their AI-assigned categories.

**Acceptance Criteria:**
- Table: Date | Description | Category | Amount
- Sortable by date or amount
- Color-coded (income green, expense red)
- Shows category badge

**Technical Notes:**
- Basic table component
- No pagination needed for demo (show all)

---

### Story 2.4 — Conversational Chat Interface (Differentiator)
**Priority:** P2 (Nice to Have)
**Time:** 3 hours

Let users ask questions about their finances.

**Acceptance Criteria:**
- Chat input at bottom of dashboard
- User can ask: "What did I spend on travel?" or "Who are my top customers?"
- AI responds with specific answers from their data
- Shows conversation history

**Technical Notes:**
- Send transaction data as context with each question
- Use streaming for better UX
- This is a **differentiator** — judges will love it

**Sample Interaction:**
```
User: "What are my biggest expenses this month?"
AI: "Your top 3 expenses this month are:
1. Payroll - $4,200 (43%)
2. Rent - $2,000 (20%)  
3. Travel - $1,500 (15%)
Travel is up 22% from last month."
```

---

### Story 2.5 — Demo Polish & Flow
**Priority:** P0 (Must Have)
**Time:** 1 hour

Ensure smooth demo experience.

**Acceptance Criteria:**
- Clean landing state with clear CTA
- Loading states during AI processing
- Error handling (graceful fallbacks)
- Demo script tested end-to-end

---

## Project Folder Structure

```
cashpilot/
│
├── 📁 frontend/                    # React/Next.js application
│   ├── 📁 components/              # Reusable UI components
│   │   ├── 📁 cards/               # Summary cards
│   │   │   └── SummaryCard.jsx
│   │   ├── 📁 charts/              # Chart components
│   │   │   ├── CashflowBarChart.jsx
│   │   │   └── ExpensePieChart.jsx
│   │   ├── 📁 layout/              # Layout components
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── 📁 transactions/        # Transaction components
│   │   │   ├── TransactionList.jsx
│   │   │   └── TransactionRow.jsx
│   │   ├── 📁 insights/            # AI insights components
│   │   │   ├── InsightsPanel.jsx
│   │   │   └── InsightCard.jsx
│   │   ├── 📁 chat/                # Chat interface
│   │   │   ├── ChatBox.jsx
│   │   │   └── ChatMessage.jsx
│   │   └── 📁 upload/              # File upload components
│   │       ├── FileUploader.jsx
│   │       └── DemoDataButton.jsx
│   │
│   ├── 📁 pages/                   # Next.js pages (or routes/)
│   │   ├── index.jsx               # Landing/Dashboard page
│   │   └── _app.jsx                # App wrapper
│   │
│   ├── 📁 hooks/                   # Custom React hooks
│   │   ├── useTransactions.js      # Transaction state management
│   │   ├── useInsights.js          # AI insights fetching
│   │   └── useChat.js              # Chat functionality
│   │
│   ├── 📁 utils/                   # Utility functions
│   │   ├── csvParser.js            # CSV parsing logic
│   │   ├── calculations.js         # Sum, averages, trends
│   │   ├── formatters.js           # Currency, date formatting
│   │   └── constants.js            # Category list, colors
│   │
│   ├── 📁 styles/                  # CSS/Tailwind styles
│   │   ├── globals.css
│   │   └── components.css
│   │
│   └── 📁 assets/                  # Static assets
│       └── 📁 icons/
│
├── 📁 backend/                     # API routes (if needed)
│   ├── 📁 api/                     # API endpoints
│   │   ├── categorize.js           # POST /api/categorize
│   │   ├── insights.js             # POST /api/insights
│   │   └── chat.js                 # POST /api/chat
│   │
│   ├── 📁 services/                # Business logic
│   │   ├── aiService.js            # OpenAI/Claude API calls
│   │   ├── categoryService.js      # Categorization logic
│   │   └── insightService.js       # Insight generation
│   │
│   └── 📁 prompts/                 # AI prompt templates
│       ├── categorize.txt          # Categorization prompt
│       ├── insights.txt            # Insights generation prompt
│       └── chat.txt                # Chat system prompt
│
├── 📁 data/                        # Static data files
│   ├── demo-transactions.json      # Demo dataset
│   ├── sample-template.csv         # CSV template for users
│   └── categories.json             # Category definitions
│
├── 📁 docs/                        # Documentation
│   ├── CashPilot-Hackathon.md      # This backlog
│   └── demo-script.md              # Demo talking points
│
├── .env.local                      # Environment variables (API keys)
├── .gitignore
├── package.json
└── README.md
```

---

## Naming Conventions

### Files & Folders

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `SummaryCard.jsx`, `ChatBox.jsx` |
| Hooks | camelCase with `use` prefix | `useTransactions.js` |
| Utils/Services | camelCase | `csvParser.js`, `aiService.js` |
| API routes | lowercase | `categorize.js`, `insights.js` |
| Data files | kebab-case | `demo-transactions.json` |
| CSS | kebab-case or module | `globals.css`, `Card.module.css` |

### Variables & Functions

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `totalIncome`, `transactionList` |
| Constants | UPPER_SNAKE_CASE | `API_URL`, `CATEGORIES` |
| Functions | camelCase, verb prefix | `calculateTotal()`, `fetchInsights()` |
| Components | PascalCase | `<InsightCard />` |
| Event handlers | camelCase with `handle` | `handleUpload()`, `handleSend()` |

### Categories (Predefined)

```javascript
// data/categories.json
{
  "expense": [
    "rent",
    "utilities",
    "payroll",
    "marketing",
    "software",
    "travel",
    "supplies",
    "other"
  ],
  "income": [
    "revenue",
    "refund",
    "investment",
    "other"
  ]
}
```

### Color Coding

| Category Type | Color | Hex |
|---------------|-------|-----|
| Income | Green | `#22C55E` |
| Expense | Red | `#EF4444` |
| Net Positive | Green | `#22C55E` |
| Net Negative | Red | `#EF4444` |
| Neutral | Gray | `#6B7280` |

---

## Environment Variables

```env
# .env.local (DO NOT COMMIT)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
# OR
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

---

## Quick Start Commands

```bash
# 1. Create project
npx create-next-app@latest cashpilot --typescript --tailwind --app

# 2. Install dependencies
cd cashpilot
npm install recharts papaparse openai

# 3. Create folder structure
mkdir -p frontend/{components/{cards,charts,layout,transactions,insights,chat,upload},hooks,utils,styles,assets}
mkdir -p backend/{api,services,prompts}
mkdir -p data docs

# 4. Start development
npm run dev
```

---

## Tech Stack Recommendation

| Layer | Recommended | Alternative |
|-------|-------------|-------------|
| Frontend | Next.js + Tailwind | React + CSS |
| Charts | Recharts | Chart.js |
| AI | OpenAI GPT-4 | Claude API |
| CSV Parsing | Papa Parse | Native JS |
| State | React useState/Context | Zustand |
| Backend | None (client-side) | Vercel Edge Functions |

---

## Demo Script (3-5 minutes)

1. **Open app** — Show clean empty state
2. **Click "Load Demo Data"** — Transactions appear instantly
3. **Point to dashboard** — "Here's my income, expenses, net cashflow"
4. **Show bar chart** — "I can see my trend over 6 months"
5. **Show AI insights** — "The AI tells me fuel is up 22%, and my top customer is 40% of revenue"
6. **Show expense breakdown** — "I can see where my money goes"
7. **Open chat** — Ask "What should I be worried about?"
8. **AI responds** — Live insight generation
9. **Close** — "I finally understand my money"

---

## Time Budget Summary

| Day | Stories | Hours |
|-----|---------|-------|
| Day 1 | 1.1, 1.2, 1.3, 1.4, 1.5 | 10 |
| Day 2 | 2.1, 2.2, 2.3, 2.4, 2.5 | 10 |
| **Total** | **10 stories** | **20 hours** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI API rate limits | Cache responses, use demo mode fallback |
| CSV parsing edge cases | Stick to simple format, provide template |
| AI categorization errors | Show confidence, allow manual override (if time) |
| Time overrun | Cut Story 2.4 (chat) first — it's P2 |

---

## Success Metrics

After demo, judges should say:
- ✅ "This is simple and clean"
- ✅ "The AI insights are actually useful"
- ✅ "I could see a business owner using this"
- ✅ "It's not trying to be QuickBooks"

---

**Good luck! Ship fast, demo clean.**
