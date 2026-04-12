import os
import json
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# In-memory cache: hash of transactions -> analysis result
_analysis_cache: dict[str, str] = {}


def _get_client() -> OpenAI | None:
    """Initialize and return an OpenAI client using env-only API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _hash_transactions(transactions: list[dict]) -> str:
    """Create a deterministic hash of the transaction list for caching."""
    serialized = json.dumps(transactions, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def analyze_transactions(transactions: list[dict]) -> dict:
    """
    Analyze transactions using OpenAI gpt-4.1-mini.
    - Limits input to 50 transactions max
    - Uses max_tokens=250
    - Caches results per unique transaction set
    Returns {"analysis": "..."} or {"error": "..."}.
    """
    if not transactions:
        return {"error": "No transactions provided"}

    # Limit to 50 transactions
    limited = transactions[:50]

    # Check cache
    cache_key = _hash_transactions(limited)
    if cache_key in _analysis_cache:
        return {"analysis": _analysis_cache[cache_key], "cached": True}

    client = _get_client()
    if not client:
        return {"error": "OpenAI API key not configured. Add OPENAI_API_KEY to your .env file."}

    # Build a concise summary for the prompt
    txn_lines = []
    for t in limited:
        txn_lines.append(
            f"  {t.get('date', 'N/A')} | {t.get('description', 'N/A')} | "
            f"${t.get('amount', 0):,.2f} | {t.get('category', 'other')} | {t.get('type', 'expense')}"
        )
    txn_text = "\n".join(txn_lines)

    prompt = (
        "You are CashPilot AI, a concise financial analyst for small businesses. "
        "Analyze these transactions and provide: 1) a brief spending summary, "
        "2) top concerns or risks, 3) one actionable tip. "
        "Be specific with numbers. Keep the entire response under 200 words.\n\n"
        f"Transactions ({len(limited)} of {len(transactions)} total):\n"
        f"  Date | Description | Amount | Category | Type\n{txn_text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.4,
        )
        result = response.choices[0].message.content.strip()
        # Cache the result
        _analysis_cache[cache_key] = result
        return {"analysis": result, "cached": False}
    except Exception as e:
        print(f"[OpenAI Service] API error: {e}")
        return {"error": f"OpenAI API error: {str(e)}"}


def is_openai_available() -> bool:
    """Check if the OpenAI API key is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))
