import json
from services.ai_service import call_ai

# Rule-based fallback categories
CATEGORY_RULES = {
    "rent": ["rent", "lease", "landlord"],
    "utilities": ["electric", "water", "utility", "gas bill", "internet", "phone bill"],
    "payroll": ["payroll", "salary", "wages"],
    "marketing": ["ads", "campaign", "marketing", "advertising", "facebook ads", "google ads"],
    "software": ["adobe", "slack", "zoom", "aws", "cloud", "subscription", "software", "saas", "license"],
    "travel": ["petrol", "fuel", "uber", "lyft", "flight", "hotel", "taxi", "travel", "airline", "booking"],
    "supplies": ["staples", "office depot", "amazon", "supplies", "printer", "equipment"],
    "revenue": ["transfer from", "client payment", "freelance payment", "invoice", "payment received"],
    "refund": ["refund", "return", "credit"],
}


def categorize_with_rules(transactions: list[dict]) -> list[dict]:
    """Categorize transactions using keyword-based rules."""
    categorized = []
    for txn in transactions:
        desc = txn.get("description", "").lower()
        category = "other"
        for cat, keywords in CATEGORY_RULES.items():
            if any(kw in desc for kw in keywords):
                category = cat
                break

        txn_copy = dict(txn)
        txn_copy["category"] = category
        txn_copy["type"] = "income" if txn.get("amount", 0) >= 0 else "expense"
        categorized.append(txn_copy)
    return categorized


def categorize_with_ai(transactions: list[dict]) -> list[dict] | None:
    """Categorize transactions using Gemini AI."""
    # Build transaction list string
    txn_lines = []
    for i, txn in enumerate(transactions):
        txn_lines.append(f'{i + 1}. "{txn["description"]}" - ${abs(txn["amount"]):.2f}')

    prompt = f"""You are a financial transaction categorizer. Categorize each transaction into EXACTLY ONE of these categories:
rent, utilities, payroll, marketing, software, travel, supplies, revenue, refund, other

Transactions:
{chr(10).join(txn_lines)}

Return ONLY a valid JSON array with objects containing "index" (1-based) and "category" fields.
Example: [{{"index": 1, "category": "travel"}}]

Do NOT include any markdown formatting, code fences, or explanation. Return ONLY the JSON array."""

    result = call_ai(prompt)
    if not result:
        return None

    try:
        # Clean up potential markdown code fences
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        
        categories = json.loads(cleaned.strip())
        
        categorized = []
        for i, txn in enumerate(transactions):
            txn_copy = dict(txn)
            # Find the AI-assigned category
            cat_entry = next((c for c in categories if c["index"] == i + 1), None)
            txn_copy["category"] = cat_entry["category"].lower() if cat_entry else "other"
            txn_copy["type"] = "income" if txn.get("amount", 0) >= 0 else "expense"
            categorized.append(txn_copy)
        return categorized
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[Category Service] Failed to parse AI response: {e}")
        return None


def categorize_transactions(transactions: list[dict]) -> list[dict]:
    """Categorize transactions — try AI first, fall back to rules."""
    # Try AI categorization first
    result = categorize_with_ai(transactions)
    if result:
        return result
    # Fallback to rule-based
    print("[Category Service] Using rule-based fallback")
    return categorize_with_rules(transactions)
