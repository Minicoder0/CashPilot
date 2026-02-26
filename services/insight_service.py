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
