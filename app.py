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
from services.email_service import send_email_background, is_email_available
from models import db, User, Transaction

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ---- Persistence config ----
database_url = os.getenv("DATABASE_URL", "sqlite:///cashpilot.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

print(f"[DB] Using database: {database_url[:30]}...")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        # Migrate: add new columns to existing tables if missing
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            existing_cols = {c['name'] for c in inspector.get_columns('users')}
            with db.engine.connect() as conn:
                if 'password_hash' not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                    conn.commit()
                    print("[DB] Added password_hash column")
                if 'auth_provider' not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) DEFAULT 'google'"))
                    conn.commit()
                    print("[DB] Added auth_provider column")
        print("[DB] Tables ready")
    except Exception as e:
        print(f"[DB] Error during setup: {e}")

# ---- Session cookie config for HTTPS ----
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PREFERRED_URL_SCHEME"] = "https"

# ---- Google OAuth Setup ----
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ---- DB Access Helper ----

def get_db_user():
    user_info = session.get("user")
    if user_info and "email" in user_info:
        return User.query.filter_by(email=user_info["email"]).first()
    return None

def get_user_transactions():
    user = get_db_user()
    if user:
        txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
        return [t.to_dict() for t in txns]
    return []


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
    # Use APP_URL env var if available, otherwise fall back to url_for
    app_url = os.getenv("APP_URL")  # e.g. https://your-app.vercel.app
    if app_url:
        redirect_uri = app_url.rstrip("/") + "/auth/callback"
    else:
        redirect_uri = url_for("auth_callback", _external=True)
    print(f"[DEBUG] OAuth redirect_uri: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    if user_info:
        email = user_info.get("email", "")
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                google_id=user_info.get("sub"),
                email=email,
                name=user_info.get("name", "User"),
                picture=user_info.get("picture", ""),
                auth_provider="google"
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update info & link google if they registered with email first
            user.name = user_info.get("name", user.name)
            user.picture = user_info.get("picture", user.picture)
            if not user.google_id:
                user.google_id = user_info.get("sub")
            if user.auth_provider == "email":
                user.auth_provider = "both"
            db.session.commit()

        session["user"] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "picture": user.picture or "",
        }
    return redirect(url_for("index"))


# ---- Email/Password Auth Routes ----

@app.route("/auth/register", methods=["POST"])
def auth_register():
    """Register a new user with email and password."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.auth_provider in ("google", "both"):
            return jsonify({"error": "This email is linked to a Google account. Please sign in with Google."}), 400
        return jsonify({"error": "An account with this email already exists. Please sign in."}), 400

    user = User(
        email=email,
        name=name,
        auth_provider="email"
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user"] = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture or "",
    }
    return jsonify({"success": True, "redirect": url_for("index")})


@app.route("/auth/email-login", methods=["POST"])
def auth_email_login():
    """Sign in with email and password."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with this email."}), 400

    if not user.password_hash:
        return jsonify({"error": "This account uses Google sign-in. Please sign in with Google."}), 400

    if not user.check_password(password):
        return jsonify({"error": "Incorrect password."}), 400

    session["user"] = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture or "",
    }
    return jsonify({"success": True, "redirect": url_for("index")})


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
    """Load and return demo transactions (pre-categorized) to DB."""
    user = get_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_path = os.path.join(os.path.dirname(__file__), "data", "demo_transactions.json")
    with open(data_path, "r") as f:
        raw = json.load(f)

    # Categorize raw data
    categorized = categorize_transactions(raw)

    # Clear old data for this user
    Transaction.query.filter_by(user_id=user.id).delete()

    # Save to DB
    for txn_dict in categorized:
        new_txn = Transaction(
            user_id=user.id,
            date=txn_dict["date"],
            description=txn_dict["description"],
            amount=txn_dict["amount"],
            category=txn_dict["category"],
            type=txn_dict["type"]
        )
        db.session.add(new_txn)
    db.session.commit()

    txns = [t.to_dict() for t in Transaction.query.filter_by(user_id=user.id).all()]

    # Send email summary in background (zero delay)
    email_sent = False
    if is_email_available() and user.email:
        summary = build_summary(txns)
        health = calculate_health_score(txns)
        anomalies = detect_anomalies(txns)
        send_email_background(user.email, user.name or "there", summary, health, anomalies, is_demo=True)
        email_sent = True

    return jsonify({"transactions": txns, "ai_available": is_ai_available(), "email_sent": email_sent})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_csv():
    """Parse uploaded CSV, categorize, and save to DB."""
    user = get_db_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

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
                "date": row_lower["date"],
                "description": row_lower["description"],
                "amount": amount,
            })

        if not raw:
            return jsonify({"error": "CSV file is empty"}), 400

        # Categorize
        categorized = categorize_transactions(raw)

        # Append to user's transactions (don't clear by default for upload?)
        # For simplicity in this demo, it's safer to append, but user might want to clear.
        # Let's keep existing behavior if it replaced it before.
        # From original: it replaced 'transactions_store'. So we'll clear.
        Transaction.query.filter_by(user_id=user.id).delete()

        for t in categorized:
            new_txn = Transaction(
                user_id=user.id,
                date=t.get("date"),
                description=t.get("description"),
                amount=t.get("amount"),
                category=t.get("category"),
                type=t.get("type")
            )
            db.session.add(new_txn)
        db.session.commit()

        txns = [t.to_dict() for t in Transaction.query.filter_by(user_id=user.id).all()]

        # Send email summary in background (zero delay)
        email_sent = False
        if is_email_available() and user.email:
            summary = build_summary(txns)
            health = calculate_health_score(txns)
            anomalies = detect_anomalies(txns)
            send_email_background(user.email, user.name or "there", summary, health, anomalies, is_demo=False)
            email_sent = True

        return jsonify({"transactions": txns, "count": len(txns), "ai_available": is_ai_available(), "email_sent": email_sent})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400


@app.route("/api/insights", methods=["POST"])
@login_required
def get_insights():
    """Generate AI financial insights for current transactions."""
    data = request.get_json() or {}
    txns = data.get("transactions", get_user_transactions())
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
    """Analyze transactions using OpenAI."""
    data = request.get_json() or {}
    txns = data.get("transactions", get_user_transactions())
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
    txns = data.get("transactions", get_user_transactions())

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


@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
