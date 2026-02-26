import os
import json
import csv
import io
import secrets
from functools import wraps
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

from services.category_service import categorize_transactions, categorize_with_rules
from services.insight_service import generate_insights, build_summary, calculate_health_score, calculate_runway, detect_anomalies
from services.ai_service import call_ai_streaming, is_ai_available
from services.openai_service import analyze_transactions, is_openai_available

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ---- Google OAuth Setup ----
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# In-memory store for demo
transactions_store: list[dict] = []


def login_required(f):
    """Decorator to protect routes — redirects to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---- Auth Routes ----

@app.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/login")
def auth_login():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    if user_info:
        session["user"] = {
            "name": user_info.get("name", "User"),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }
    return redirect(url_for("index"))


@app.route("/auth/logout")
def auth_logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---- Page Routes ----

@app.route("/")
@login_required
def index():
    return render_template("index.html", user=session.get("user"))


@app.route("/api/user")
@login_required
def get_user():
    """Return current user info."""
    return jsonify(session.get("user", {}))


# ---- API Routes ----

@app.route("/api/demo-data")
@login_required
def demo_data():
    """Load and return demo transactions (pre-categorized)."""
    global transactions_store
    data_path = os.path.join(os.path.dirname(__file__), "data", "demo_transactions.json")
    with open(data_path, "r") as f:
        raw = json.load(f)
    transactions_store = categorize_transactions(raw)
    return jsonify({"transactions": transactions_store, "ai_available": is_ai_available()})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_csv():
    """Parse uploaded CSV and categorize transactions."""
    global transactions_store
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        # Validate headers
        required = {"date", "description", "amount"}
        if not required.issubset({h.lower().strip() for h in (reader.fieldnames or [])}):
            return jsonify({"error": "CSV must have columns: date, description, amount"}), 400

        raw = []
        for i, row in enumerate(reader):
            # Normalize keys to lowercase
            row_lower = {k.lower().strip(): v.strip() for k, v in row.items()}
            try:
                amount = float(row_lower["amount"].replace(",", "").replace("$", ""))
            except ValueError:
                return jsonify({"error": f"Invalid amount on row {i + 2}: '{row_lower['amount']}'"}), 400

            # Respect 'type' column if present; negate positive expenses
            txn_type = row_lower.get("type", "").lower().strip()
            if txn_type == "expense" and amount > 0:
                amount = -amount
            elif txn_type == "income" and amount < 0:
                amount = abs(amount)

            raw.append({
                "id": i + 1,
                "date": row_lower["date"],
                "description": row_lower["description"],
                "amount": amount,
            })

        if not raw:
            return jsonify({"error": "CSV file is empty"}), 400

        transactions_store = categorize_transactions(raw)
        return jsonify({"transactions": transactions_store, "count": len(transactions_store), "ai_available": is_ai_available()})

    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400


@app.route("/api/insights", methods=["POST"])
@login_required
def get_insights():
    """Generate AI financial insights for current transactions."""
    data = request.get_json() or {}
    txns = data.get("transactions", transactions_store)
    if not txns:
        return jsonify({"error": "No transactions loaded"}), 400

    insights = generate_insights(txns)
    summary = build_summary(txns)
    health = calculate_health_score(txns)
    runway = calculate_runway(txns)
    anomalies = detect_anomalies(txns)
    return jsonify({
        "insights": insights,
        "summary": summary,
        "health_score": health,
        "runway": runway,
        "anomalies": anomalies,
    })


@app.route("/api/analyze", methods=["POST"])
@login_required
def analyze():
    """Analyze transactions using OpenAI gpt-4.1-mini."""
    data = request.get_json() or {}
    txns = data.get("transactions", transactions_store)
    if not txns:
        return jsonify({"error": "No transactions loaded"}), 400

    result = analyze_transactions(txns)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    """Chat with AI about finances — streaming response."""
    data = request.get_json() or {}
    message = data.get("message", "")
    txns = data.get("transactions", transactions_store)

    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not is_ai_available():
        return jsonify({"error": "Chat requires an OpenAI API key. Add OPENAI_API_KEY to your .env file."}), 400

    # Build context
    summary = build_summary(txns)
    cat_lines = "\n".join([f"  - {c}: ${a:,.2f}" for c, a in summary["top_categories"]])
    income_lines = "\n".join([f"  - {s}: ${a:,.2f}" for s, a in summary["top_income_sources"]])

    prompt = f"""You are CashPilot AI, a friendly financial advisor for a small business owner. Answer their question based on this financial data. Be specific, concise, and use plain language. Use bullet points for lists. Do not use markdown headers.

Financial Summary:
- Total Income: ${summary['total_income']:,.2f}
- Total Expenses: ${summary['total_expenses']:,.2f}
- Net Cashflow: ${summary['net_cashflow']:,.2f}
- Total Transactions: {summary['transaction_count']}

Top Expense Categories:
{cat_lines}

Top Income Sources:
{income_lines}

The user's question: {message}"""

    def generate():
        for chunk in call_ai_streaming(prompt):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
