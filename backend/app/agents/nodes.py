from app.agents.state import FinanceAgentState
from app.services.gemini_service import extract_transactions_from_pdf
from app.services.supabase_client import get_supabase
from datetime import datetime

CONFIDENCE_THRESHOLD = 0.80
VALID_DIRECTIONS = {"income", "expense"}
VALID_CATEGORIES = {
    "Market","Kira","Ulasim","Yemek","Fatura","Egitim",
    "Saglik","Eglence","Abonelik","Giyim","Transfer",
    "Maas","Freelance","Diger"
}

async def pdf_reader_node(state: FinanceAgentState) -> FinanceAgentState:
    try:
        result = await extract_transactions_from_pdf(state["pdf_bytes"])
        return {
            **state,
            "raw_transactions": result.get("transactions", []),
            "extraction_error": None,
        }
    except Exception as e:
        return {
            **state,
            "raw_transactions": [],
            "extraction_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
        }

async def validation_node(state: FinanceAgentState) -> FinanceAgentState:
    valid, invalid = [], []

    for item in state.get("raw_transactions", []):
        errors = []

        try:
            datetime.strptime(item.get("date", ""), "%Y-%m-%d")
        except ValueError:
            errors.append("invalid_date")

        if not isinstance(item.get("amount"), (int, float)) or item.get("amount") <= 0:
            errors.append("invalid_amount")

        if item.get("direction") not in VALID_DIRECTIONS:
            errors.append("invalid_direction")

        if not item.get("description", "").strip():
            errors.append("empty_description")

        confidence = item.get("confidence", 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            confidence = 0.5
            item["confidence"] = confidence

        if item.get("estimated_category") not in VALID_CATEGORIES:
            item["estimated_category"] = "Diger"
            item["confidence"] = min(confidence, 0.5)

        if errors:
            item["validation_errors"] = errors
            invalid.append(item)
        else:
            item["is_verified"] = confidence >= CONFIDENCE_THRESHOLD
            valid.append(item)

    return {**state, "valid_transactions": valid, "invalid_transactions": invalid}

async def category_node(state: FinanceAgentState) -> FinanceAgentState:
    sb = get_supabase()
    user_id = state["user_id"]

    # Ogrenilen kurallari cek
    rules_res = sb.table("category_rules").select("*").eq("user_id", user_id).execute()
    rules = {r["keyword"].lower(): r["category_id"] for r in rules_res.data}

    # Kategori adi -> id
    cats_res = sb.table("categories").select("id,name").execute()
    cat_name_to_id = {c["name"]: c["id"] for c in cats_res.data}

    # Duplicate kontrolu
    existing = sb.table("transactions").select("date,amount,description").eq("user_id", user_id).execute()
    existing_keys = {
        (r["date"], str(r["amount"]), r["description"].lower())
        for r in existing.data
    }

    categorized, to_insert = [], []
    for item in state.get("valid_transactions", []):
        # Once ogrenilen kurallar
        matched_cat_id = None
        for keyword, cat_id in rules.items():
            if keyword in item["description"].lower():
                matched_cat_id = cat_id
                item["confidence"] = min(item["confidence"] + 0.15, 1.0)
                break

        if not matched_cat_id:
            gemini_cat = item.get("estimated_category", "Diger")
            matched_cat_id = cat_name_to_id.get(gemini_cat, cat_name_to_id.get("Diger"))

        item["category_id"] = matched_cat_id
        categorized.append(item)

        # Duplicate degilse ekle
        key = (item["date"], str(item["amount"]), item["description"].lower())
        if key not in existing_keys:
            to_insert.append({
                "user_id":     user_id,
                "upload_id":   state["upload_id"],
                "date":        item["date"],
                "description": item["description"],
                "amount":      item["amount"],
                "direction":   item["direction"],
                "category_id": matched_cat_id,
                "source":      "pdf",
                "confidence":  item.get("confidence", 0.5),
                "is_verified": item.get("is_verified", False),
                "raw_text":    item.get("raw_text"),
            })

    if to_insert:
        sb.table("transactions").insert(to_insert).execute()

    return {**state, "categorized_transactions": categorized}

async def anomaly_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Anormal harcamalari tespit et
    return {**state, "anomalies": []}

async def analytics_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Deterministik finansal hesaplama (LLM kullanma!)
    return {**state, "financial_summary": {}}

async def insight_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 4 - Gemini ile dogal dil ozeti uret
    return {**state, "insight_text": "", "status": "completed"}
