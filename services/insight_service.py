import json
from services.ai_service import call_ai, is_ai_available
from services.openai_service import analyze_transactions, is_openai_available


SAMPLE_INSIGHTS = [
    {"text": "Your top client ABC Corp accounts for 40% of total revenue. Consider diversifying your client base to reduce dependency.", "icon": "⚠️", "type": "warning"},
    {"text": "Payroll is your largest expense at 43% of total spending. This is typical for service-based businesses.", "icon": "💰", "type": "info"},
    {"text": "Marketing spend has increased 30% over the last 3 months. Track ROI to ensure this investment is paying off.", "icon": "📈", "type": "trend"},
    {"text": "Software subscriptions total ~$137/month. Review whether all subscriptions are actively being used.", "icon": "💡", "type": "tip"},
    {"text": "Your net cashflow is positive — you're spending less than you earn. Keep maintaining this healthy ratio.", "icon": "✅", "type": "positive"},
]


def build_summary(transactions: list[dict]) -> dict:
    """Build a financial summary from categorized transactions."""
    total_income = sum(t["amount"] for t in transactions if t.get("type") == "income")
    total_expenses = sum(abs(t["amount"]) for t in transactions if t.get("type") == "expense")
    net = total_income - total_expenses

    # Category breakdown
    category_totals = {}
    for t in transactions:
        cat = t.get("category", "other")
        if t.get("type") == "expense":
            category_totals[cat] = category_totals.get(cat, 0) + abs(t["amount"])

    # Sort categories by amount
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

    # Top income sources
    income_sources = {}
    for t in transactions:
        if t.get("type") == "income":
            desc = t.get("description", "Unknown")
            income_sources[desc] = income_sources.get(desc, 0) + t["amount"]
    sorted_income = sorted(income_sources.items(), key=lambda x: x[1], reverse=True)

    # Monthly breakdown
    monthly = {}
    for t in transactions:
        month = t["date"][:7]  # YYYY-MM
        if month not in monthly:
            monthly[month] = {"income": 0, "expenses": 0}
        if t.get("type") == "income":
            monthly[month]["income"] += t["amount"]
        else:
            monthly[month]["expenses"] += abs(t["amount"])

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_cashflow": round(net, 2),
        "transaction_count": len(transactions),
        "top_categories": sorted_categories[:5],
        "top_income_sources": sorted_income[:3],
        "monthly": monthly,
    }


def calculate_health_score(transactions: list[dict]) -> dict:
    """Calculate a 0-100 financial health score from transaction data."""
    summary = build_summary(transactions)
    income = summary["total_income"]
    expenses = summary["total_expenses"]
    monthly = summary["monthly"]

    score = 0

    # 1. Net cashflow ratio (30 pts) — income / expenses
    if expenses > 0:
        ratio = income / expenses
        score += min(ratio * 15, 30)  # 2.0 ratio = full 30
    elif income > 0:
        score += 30  # No expenses = perfect

    # 2. Expense trend (20 pts) — is spending growing?
    months_sorted = sorted(monthly.keys())
    if len(months_sorted) >= 2:
        recent = monthly[months_sorted[-1]]["expenses"]
        previous = monthly[months_sorted[-2]]["expenses"]
        if previous > 0:
            growth = (recent - previous) / previous
            if growth <= 0:
                score += 20  # Expenses decreased
            elif growth < 0.1:
                score += 15
            elif growth < 0.25:
                score += 10
            else:
                score += 5  # High growth
        else:
            score += 15
    else:
        score += 10  # Not enough data

    # 3. Income diversity (20 pts) — unique income sources
    income_sources = len(summary["top_income_sources"])
    if income_sources >= 5:
        score += 20
    elif income_sources >= 3:
        score += 15
    elif income_sources >= 2:
        score += 10
    else:
        score += 5

    # 4. Expense concentration (15 pts) — no single category > 50%
    if expenses > 0 and summary["top_categories"]:
        top_cat_pct = summary["top_categories"][0][1] / expenses
        if top_cat_pct < 0.3:
            score += 15
        elif top_cat_pct < 0.5:
            score += 10
        else:
            score += 5

    # 5. Consistency (15 pts) — variance in monthly income
    if len(months_sorted) >= 2:
        incomes = [monthly[m]["income"] for m in months_sorted]
        avg_income = sum(incomes) / len(incomes) if incomes else 0
        if avg_income > 0:
            variance = sum((i - avg_income) ** 2 for i in incomes) / len(incomes)
            cv = (variance ** 0.5) / avg_income  # coefficient of variation
            if cv < 0.15:
                score += 15
            elif cv < 0.3:
                score += 10
            else:
                score += 5
        else:
            score += 5
    else:
        score += 8

    score = min(round(score), 100)

    # Determine tier
    if score >= 80:
        tier = "Excellent"
        color = "green"
    elif score >= 60:
        tier = "Good"
        color = "blue"
    elif score >= 40:
        tier = "Fair"
        color = "amber"
    else:
        tier = "At Risk"
        color = "red"

    return {"score": score, "tier": tier, "color": color}


def calculate_runway(transactions: list[dict]) -> dict:
    """Calculate cash runway in months based on burn rate."""
    summary = build_summary(transactions)
    monthly = summary["monthly"]
    months_sorted = sorted(monthly.keys())

    if len(months_sorted) < 1:
        return {"months": 0, "status": "unknown", "color": "gray"}

    # Average monthly income and expenses
    avg_income = sum(monthly[m]["income"] for m in months_sorted) / len(months_sorted)
    avg_expenses = sum(monthly[m]["expenses"] for m in months_sorted) / len(months_sorted)
    monthly_burn = avg_expenses - avg_income

    if monthly_burn <= 0:
        # Profitable — sustainable
        return {"months": -1, "status": "sustainable", "color": "green", "label": "∞ Sustainable"}

    # Calculate runway
    # Use net cashflow as current "balance"
    balance = summary["net_cashflow"]
    if balance <= 0:
        return {"months": 0, "status": "critical", "color": "red", "label": "0 months"}

    runway = round(balance / monthly_burn, 1)

    if runway >= 6:
        status = "healthy"
        color = "green"
    elif runway >= 3:
        status = "caution"
        color = "amber"
    else:
        status = "critical"
        color = "red"

    return {"months": runway, "status": status, "color": color, "label": f"{runway} months"}


def detect_anomalies(transactions: list[dict]) -> list[dict]:
    """Detect spending anomalies — transactions 2x above category average."""
    # Group expenses by category
    cat_amounts = {}
    for t in transactions:
        if t.get("type") == "expense":
            cat = t.get("category", "other")
            if cat not in cat_amounts:
                cat_amounts[cat] = []
            cat_amounts[cat].append(abs(t["amount"]))

    # Calculate category averages
    cat_avg = {}
    for cat, amounts in cat_amounts.items():
        if len(amounts) >= 2:  # Need at least 2 to compare
            cat_avg[cat] = sum(amounts) / len(amounts)

    # Find anomalies
    anomalies = []
    for t in transactions:
        if t.get("type") == "expense":
            cat = t.get("category", "other")
            amt = abs(t["amount"])
            if cat in cat_avg and amt > cat_avg[cat] * 2:
                multiplier = round(amt / cat_avg[cat], 1)
                anomalies.append({
                    "description": t.get("description", "Unknown"),
                    "amount": amt,
                    "category": cat,
                    "average": round(cat_avg[cat], 2),
                    "multiplier": multiplier,
                    "reason": f"This ${amt:,.2f} {cat} expense is {multiplier}x your average (${cat_avg[cat]:,.2f})",
                    "date": t.get("date", ""),
                })

    # Sort by multiplier, return top 5
    anomalies.sort(key=lambda x: x["multiplier"], reverse=True)
    return anomalies[:5]


def generate_insights(transactions: list[dict]) -> list[dict]:
    """Generate financial insights using OpenAI, with static fallback."""
    if not is_ai_available():
        return SAMPLE_INSIGHTS

    summary = build_summary(transactions)

    # Format for the prompt
    cat_lines = "\n".join(
        [f"  - {cat}: ${amt:,.2f}" for cat, amt in summary["top_categories"]]
    )
    income_lines = "\n".join(
        [f"  - {src}: ${amt:,.2f}" for src, amt in summary["top_income_sources"]]
    )
    monthly_lines = "\n".join(
        [f"  - {m}: Income ${d['income']:,.2f}, Expenses ${d['expenses']:,.2f}" for m, d in sorted(summary["monthly"].items())]
    )

    prompt = f"""You are a financial advisor for a small business owner. Based on this transaction summary, generate 4-5 specific, actionable insights. Be concise and use plain language a non-financial person would understand.

Summary:
- Total Income: ${summary['total_income']:,.2f}
- Total Expenses: ${summary['total_expenses']:,.2f}
- Net Cashflow: ${summary['net_cashflow']:,.2f}
- Transaction Count: {summary['transaction_count']}

Top Expense Categories:
{cat_lines}

Top Income Sources:
{income_lines}

Monthly Breakdown:
{monthly_lines}

Return ONLY a valid JSON array. Each object must have:
- "text": The insight (1-2 sentences max)
- "icon": An emoji that fits the insight
- "type": One of "positive", "warning", "trend", "tip", "info"

Example: [{{"text": "Fuel expenses increased 22%", "icon": "⛽", "type": "warning"}}]

No markdown, no code fences, ONLY the JSON array."""

    result = call_ai(prompt)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            insights = json.loads(cleaned.strip())
            if isinstance(insights, list) and len(insights) > 0:
                return insights
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[Insight Service] Failed to parse AI insights: {e}")

    return SAMPLE_INSIGHTS
