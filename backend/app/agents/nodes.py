from app.agents.state import FinanceAgentState
from app.services.gemini_service import extract_transactions_from_pdf
from app.services.supabase_client import get_supabase
from app.services.finance_summary_service import calculate_financial_summary
from datetime import datetime, date, timedelta
from collections import defaultdict
import json
import google.generativeai as genai
from app.core.config import settings

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
    sb = get_supabase()
    anomalies = []

    three_months_ago = (date.today() - timedelta(days=90)).isoformat()
    history = sb.table("transactions").select(
        "direction,category_id,amount,categories(name)"
    ).eq("user_id", state["user_id"]).eq("direction", "expense").gte("date", three_months_ago).execute()

    monthly_totals = defaultdict(lambda: {"total": 0, "count": 0})
    for t in history.data:
        cat_name = t.get("categories", {}).get("name", "Diger")
        monthly_totals[cat_name]["total"] += t["amount"]
        monthly_totals[cat_name]["count"] += 1

    current_by_cat = defaultdict(float)
    for item in state.get("categorized_transactions", []):
        if item["direction"] == "expense":
            current_by_cat[item.get("estimated_category", "Diger")] += item["amount"]

    for cat, current_total in current_by_cat.items():
        if cat in monthly_totals:
            hist = monthly_totals[cat]
            avg = hist["total"] / max(hist["count"] / 30, 1)
            if current_total > avg * 1.25 and current_total > 500:
                pct = round((current_total - avg) / avg * 100, 1)
                anomalies.append({
                    "category": cat,
                    "current": current_total,
                    "average": round(avg, 2),
                    "increase_pct": pct,
                    "message": f"{cat} harcamalariniz gecmis ortalamanin %{pct} uzerinde."
                })

    return {**state, "anomalies": anomalies}

async def analytics_node(state: FinanceAgentState) -> FinanceAgentState:
    summary = calculate_financial_summary(
        state.get("categorized_transactions", []),
        state.get("anomalies", [])
    )
    return {**state, "financial_summary": summary}

genai.configure(api_key=settings.GEMINI_API_KEY)
insight_model = genai.GenerativeModel("gemini-2.5-flash")

async def insight_node(state: FinanceAgentState) -> FinanceAgentState:
    summary = state.get("financial_summary", {})
    prompt = f"""
Sen bir kisisel finans asistanisin.
Kullanicinin bu ayki finansal ozeti:

{json.dumps(summary, ensure_ascii=False, indent=2)}

KURALLARI:
- Maksimum 4 cumle yaz
- Teknik terim kullanma
- Yatirim, hisse, kripto, doviz onerisi yapma kesinlikle
- Son cumlede mutlaka su notu ekle: "Bu yatirim tavsiyesi degildir."
- Turkce yaz
- Anomalileri varsa bir cumlede belirt

Sadece ozet metni yaz, baska hicbir sey ekleme.
"""
    response = insight_model.generate_content(prompt)
    return {**state, "insight_text": response.text.strip(), "status": "completed"}
