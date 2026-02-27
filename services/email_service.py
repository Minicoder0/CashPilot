"""
CashPilot Email Service
-----------------------
Sends plain-English financial summaries to users via Resend.
No jargon. Like a friend explaining your finances over coffee.
"""

import os
import threading
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "CashPilot <onboarding@resend.dev>")
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")


def is_email_available() -> bool:
    """Check if Resend API key is configured."""
    return bool(RESEND_API_KEY)


# ---------------------------------------------------------------------------
# Plain-English Formatter — converts accounting jargon to human language
# ---------------------------------------------------------------------------

def _fmt(amount: float) -> str:
    """Format a number as $X,XXX.XX"""
    return f"${abs(amount):,.2f}"


def _health_plain(score: int, tier: str) -> str:
    """Convert health score to conversational text."""
    if score >= 80:
        return f"Your financial health is {score} out of 100 — you're doing great! Keep it up."
    elif score >= 60:
        return f"Your financial health is {score} out of 100 — you're doing pretty good."
    elif score >= 40:
        return f"Your financial health is {score} out of 100 — not bad, but there's room to improve."
    else:
        return f"Your financial health is {score} out of 100 — things are a bit tight. Let's look at what's going on."


def _net_plain(income: float, expenses: float, net: float) -> str:
    """Convert net cashflow into friendly language."""
    if net > 0:
        return (
            f"You made {_fmt(income)} and spent {_fmt(expenses)}.\n"
            f"That means you kept {_fmt(net)} — nice!"
        )
    elif net == 0:
        return (
            f"You made {_fmt(income)} and spent {_fmt(expenses)}.\n"
            f"You're breaking even — staying afloat, but not building any cushion yet."
        )
    else:
        return (
            f"You made {_fmt(income)} but spent {_fmt(expenses)}.\n"
            f"You're {_fmt(abs(net))} in the red — might want to check where that's going."
        )


def _categories_plain(categories: list) -> str:
    """Convert top expense categories to friendly bullet points."""
    if not categories:
        return "We couldn't find enough expense data to break down."

    labels = {
        "payroll": "Paying your team",
        "rent": "Rent",
        "utilities": "Utilities (power, water, internet)",
        "travel": "Travel & Gas",
        "marketing": "Marketing & Ads",
        "software": "Software subscriptions",
        "supplies": "Supplies & Equipment",
        "other": "Other expenses",
        "refund": "Refunds",
    }

    total = sum(amt for _, amt in categories)
    lines = []
    for i, (cat, amt) in enumerate(categories[:5]):
        pct = round((amt / total) * 100) if total > 0 else 0
        friendly_name = labels.get(cat.lower(), cat.title())
        suffix = " — this is your biggest expense" if i == 0 else ""
        lines.append(f"  • {friendly_name}: {_fmt(amt)} ({pct}%){suffix}")

    return "\n".join(lines)


def _insights_plain(summary: dict) -> list[str]:
    """Generate plain-English insights from summary data (no API cost)."""
    insights = []
    income = summary["total_income"]
    expenses = summary["total_expenses"]
    categories = summary.get("top_categories", [])
    income_sources = summary.get("top_income_sources", [])
    monthly = summary.get("monthly", {})

    # Top income source concentration
    if income_sources and income > 0:
        top_src, top_amt = income_sources[0]
        pct = round((top_amt / income) * 100)
        if pct >= 35:
            insights.append(
                f"Most of your money is coming from \"{top_src}\" — "
                f"they make up {pct}% of your income. "
                f"Maybe try to get a couple more clients like them so you're not too dependent on one source?"
            )
        else:
            insights.append(
                f"Your biggest income source is \"{top_src}\" at {pct}% of total income. "
                f"Good news — your income isn't too concentrated in one place."
            )

    # Monthly expense trend
    months_sorted = sorted(monthly.keys())
    if len(months_sorted) >= 2:
        recent_exp = monthly[months_sorted[-1]]["expenses"]
        prev_exp = monthly[months_sorted[-2]]["expenses"]
        if prev_exp > 0:
            change = ((recent_exp - prev_exp) / prev_exp) * 100
            if change > 15:
                insights.append(
                    f"Your spending went up {round(change)}% compared to last month. "
                    f"Keep an eye on this — make sure it's for a good reason!"
                )
            elif change < -10:
                insights.append(
                    f"Nice! Your spending dropped {round(abs(change))}% compared to last month. "
                    f"Whatever you did, keep doing it."
                )

    # Software subscription awareness
    if categories:
        for cat, amt in categories:
            if cat.lower() == "software":
                monthly_est = round(amt / max(len(months_sorted), 1), 2)
                insights.append(
                    f"Your software subscriptions add up to about {_fmt(monthly_est)} per month. "
                    f"Check if you're actually using all of them."
                )
                break

    # Savings ratio
    if income > 0:
        savings_pct = round(((income - expenses) / income) * 100)
        if savings_pct >= 20:
            insights.append(
                f"You're saving about {savings_pct}% of what you earn. That's solid!"
            )
        elif savings_pct >= 0:
            insights.append(
                f"You're saving around {savings_pct}% of your income. "
                f"Try to get that above 20% for a healthier cushion."
            )

    return insights if insights else ["Your finances look steady. Keep tracking to spot trends over time!"]


def _anomalies_plain(anomalies: list[dict]) -> str:
    """Convert anomalies to friendly 'heads up' warnings."""
    if not anomalies:
        return ""

    lines = ["⚠️ Heads Up — We Noticed Something Unusual:\n"]
    for a in anomalies[:3]:
        lines.append(
            f"  • {a['category'].title()} — You spent {_fmt(a['amount'])} on \"{a['description']}\", "
            f"but you normally spend around {_fmt(a['average'])}.\n"
            f"    That's {a['multiplier']}x more than usual. Everything okay?"
        )
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# HTML Email Builder
# ---------------------------------------------------------------------------

def build_email_html(user_name: str, summary: dict, health: dict, anomalies: list[dict], is_demo: bool = False) -> str:
    """Build a beautiful HTML email with plain-English financial summary."""

    income = summary["total_income"]
    expenses = summary["total_expenses"]
    net = summary["net_cashflow"]
    categories = summary.get("top_categories", [])

    net_color = "#22C55E" if net >= 0 else "#EF4444"
    health_colors = {"green": "#22C55E", "blue": "#3B82F6", "amber": "#F59E0B", "red": "#EF4444"}
    h_color = health_colors.get(health.get("color", "blue"), "#3B82F6")

    # Generate plain-English content
    money_summary = _net_plain(income, expenses, net)
    health_text = _health_plain(health["score"], health["tier"])
    cat_text = _categories_plain(categories)
    insights = _insights_plain(summary)
    anomaly_text = _anomalies_plain(anomalies)

    demo_banner = ""
    if is_demo:
        demo_banner = """
        <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; font-size: 14px; color: #92400E;">
            📋 This is a <strong>demo analysis</strong> using sample data. Upload your own CSV for real insights!
        </div>"""

    insights_html = "\n".join([
        f'<div style="background: #F0FDF4; border-left: 3px solid #22C55E; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 10px; font-size: 14px; color: #15803D;">💡 {ins}</div>'
        for ins in insights
    ])

    anomaly_html = ""
    if anomalies:
        anomaly_items = "\n".join([
            f'''<div style="background: #FEF2F2; border-left: 3px solid #EF4444; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 10px; font-size: 14px; color: #991B1B;">
                ⚠️ <strong>{a["category"].title()}</strong> — You spent {_fmt(a["amount"])} on "{a["description"]}", but you normally spend around {_fmt(a["average"])}. That's {a["multiplier"]}x more than usual.
            </div>'''
            for a in anomalies[:3]
        ])
        anomaly_html = f"""
        <div style="margin-top: 28px;">
            <h2 style="font-size: 18px; font-weight: 700; color: #991B1B; margin-bottom: 12px;">⚠️ Heads Up — Unusual Spending</h2>
            {anomaly_items}
        </div>"""

    # Category rows for table
    total_exp = sum(amt for _, amt in categories) if categories else 1
    cat_rows = "\n".join([
        f'''<tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 14px;">{cat.title()}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 14px; text-align: right; font-weight: 600;">{_fmt(amt)}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 14px; text-align: right; color: #6B7280;">{round((amt / total_exp) * 100)}%</td>
        </tr>'''
        for cat, amt in categories[:5]
    ])

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #F9FAFB; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
<div style="max-width: 600px; margin: 0 auto; padding: 32px 16px;">

    <!-- Header -->
    <div style="text-align: center; margin-bottom: 32px;">
        <div style="font-size: 32px; margin-bottom: 8px;">✈️</div>
        <h1 style="font-size: 24px; font-weight: 800; color: #111827; margin: 0;">
            Cash<span style="color: #3B82F6;">Pilot</span>
        </h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 4px;">Your AI Financial Co-Pilot</p>
    </div>

    <!-- Main Card -->
    <div style="background: #FFFFFF; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

        {demo_banner}

        <!-- Greeting -->
        <p style="font-size: 16px; color: #374151; margin-bottom: 24px;">
            Hi {user_name},<br><br>
            {"Here's your sample financial analysis:" if is_demo else "Your financial analysis is ready! Here's what's happening with your money:"}
        </p>

        <!-- Money Summary -->
        <div style="background: #F9FAFB; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <h2 style="font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px 0;">💵 Your Money at a Glance</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-size: 14px; color: #6B7280;">You made</td>
                    <td style="padding: 8px 0; font-size: 16px; font-weight: 700; color: #22C55E; text-align: right;">{_fmt(income)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-size: 14px; color: #6B7280;">You spent</td>
                    <td style="padding: 8px 0; font-size: 16px; font-weight: 700; color: #EF4444; text-align: right;">{_fmt(expenses)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-size: 14px; color: #6B7280; border-top: 2px solid #E5E7EB;">{"You kept" if net >= 0 else "You're short"}</td>
                    <td style="padding: 8px 0; font-size: 18px; font-weight: 800; color: {net_color}; text-align: right; border-top: 2px solid #E5E7EB;">{"+" if net >= 0 else "-"}{_fmt(net)}</td>
                </tr>
            </table>
        </div>

        <!-- Health Score -->
        <div style="background: linear-gradient(135deg, {h_color}11, {h_color}22); border: 1px solid {h_color}44; border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
            <div style="font-size: 42px; font-weight: 800; color: {h_color}; margin-bottom: 4px;">{health["score"]}</div>
            <div style="font-size: 14px; color: {h_color}; font-weight: 600; margin-bottom: 8px;">out of 100 — {health["tier"]}</div>
            <p style="font-size: 14px; color: #374151; margin: 0;">{health_text}</p>
        </div>

        <!-- Where Your Money Goes -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 12px;">💸 Where Your Money Goes</h2>
            <table style="width: 100%; border-collapse: collapse; background: #F9FAFB; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: #F3F4F6;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase;">Category</th>
                        <th style="padding: 10px 12px; text-align: right; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase;">Amount</th>
                        <th style="padding: 10px 12px; text-align: right; font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase;">Share</th>
                    </tr>
                </thead>
                <tbody>
                    {cat_rows}
                </tbody>
            </table>
        </div>

        <!-- Insights -->
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 12px;">💡 Things You Should Know</h2>
            {insights_html}
        </div>

        <!-- Anomalies -->
        {anomaly_html}

        <!-- CTA -->
        <div style="text-align: center; margin-top: 32px;">
            <a href="{APP_URL}" style="display: inline-block; background: #3B82F6; color: #FFFFFF; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 15px;">
                View Full Dashboard →
            </a>
            <p style="font-size: 13px; color: #9CA3AF; margin-top: 12px;">
                You can also ask CashPilot AI any question about your finances using the chat on your dashboard.
            </p>
        </div>

    </div>

    <!-- Footer -->
    <div style="text-align: center; margin-top: 24px; padding: 16px;">
        <p style="font-size: 12px; color: #9CA3AF; margin: 0;">
            ✈️ CashPilot — AI Financial Co-Pilot<br>
            This email was sent because you {"loaded demo data" if is_demo else "uploaded transactions"} on CashPilot.
        </p>
    </div>

</div>
</body>
</html>"""

    return html


def build_email_plain(user_name: str, summary: dict, health: dict, anomalies: list[dict], is_demo: bool = False) -> str:
    """Build plain-text fallback version of the email."""

    income = summary["total_income"]
    expenses = summary["total_expenses"]
    net = summary["net_cashflow"]
    categories = summary.get("top_categories", [])

    money = _net_plain(income, expenses, net)
    health_text = _health_plain(health["score"], health["tier"])
    cat_text = _categories_plain(categories)
    insights = _insights_plain(summary)
    anomaly_text = _anomalies_plain(anomalies)

    demo_note = "\n📋 Note: This is a demo analysis using sample data.\n" if is_demo else ""

    insights_text = "\n".join([f"  💡 {ins}" for ins in insights])

    return f"""Hi {user_name},

{"Here's your sample financial analysis:" if is_demo else "Your financial analysis is ready! Here's what's happening with your money:"}
{demo_note}
💵 YOUR MONEY AT A GLANCE
{money}

🏆 FINANCIAL HEALTH: {health["score"]}/100 ({health["tier"]})
{health_text}

💸 WHERE YOUR MONEY GOES
{cat_text}

💡 THINGS YOU SHOULD KNOW
{insights_text}

{anomaly_text}

View your full dashboard: {APP_URL}

---
✈️ CashPilot — AI Financial Co-Pilot
"""


# ---------------------------------------------------------------------------
# Email Sender (via Resend)
# ---------------------------------------------------------------------------

def send_analysis_email(
    user_email: str,
    user_name: str,
    summary: dict,
    health: dict,
    anomalies: list[dict],
    is_demo: bool = False,
) -> bool:
    """Send the financial summary email. Returns True on success."""
    if not is_email_available():
        print("[Email Service] No RESEND_API_KEY configured — skipping email")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        # Pick subject based on scenario
        net = summary.get("net_cashflow", 0)
        if is_demo:
            subject = "Your Demo Financial Analysis is Ready 📊"
        elif net >= 0:
            subject = "Here's What's Up With Your Money 💰"
        else:
            subject = "Your Financial Summary (+ A Few Concerns) ⚠️"

        html = build_email_html(user_name, summary, health, anomalies, is_demo)
        text = build_email_plain(user_name, summary, health, anomalies, is_demo)

        params = {
            "from": FROM_EMAIL,
            "to": [user_email],
            "subject": subject,
            "html": html,
            "text": text,
        }

        result = resend.Emails.send(params)
        print(f"[Email Service] ✅ Email sent to {user_email} (id: {result.get('id', 'unknown')})")
        return True

    except Exception as e:
        print(f"[Email Service] ❌ Failed to send email to {user_email}: {e}")
        return False


def send_email_background(
    user_email: str,
    user_name: str,
    summary: dict,
    health: dict,
    anomalies: list[dict],
    is_demo: bool = False,
):
    """Fire-and-forget: send email in a background thread so the API response isn't delayed."""
    if not is_email_available():
        return

    thread = threading.Thread(
        target=send_analysis_email,
        args=(user_email, user_name, summary, health, anomalies, is_demo),
        daemon=True,
    )
    thread.start()
    print(f"[Email Service] 📩 Background email queued for {user_email}")
