from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from app.services.finance_summary_service import calculate_financial_summary
from datetime import date
from collections import defaultdict

router = APIRouter()

@router.get("/summary")
async def get_summary(month: str = Query(None), user = Depends(get_current_user)):
    sb = get_supabase()
    if not month:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"
    txs = sb.table("transactions").select("*, categories(name)").eq(
        "user_id", user["user_id"]
    ).gte("date", f"{month}-01").lte("date", f"{month}-31").execute()
    transactions = [
        {**t, "estimated_category": t.get("categories", {}).get("name", "Diger") if t.get("categories") else "Diger"}
        for t in txs.data
    ]
    return calculate_financial_summary(transactions, [])

@router.get("/pending-review")
async def get_pending(user = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("transactions").select("*, categories(name)").eq(
        "user_id", user["user_id"]
    ).eq("is_verified", False).order("confidence").execute()
    return {"pending": result.data, "count": len(result.data)}

@router.get("/monthly-trend")
async def monthly_trend(user = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("transactions").select("date,amount,direction").eq(
        "user_id", user["user_id"]
    ).order("date").execute()
    monthly = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in result.data:
        monthly[t["date"][:7]][t["direction"]] += t["amount"]
    return [
        {"month": k, **v, "net": round(v["income"] - v["expense"], 2)}
        for k, v in sorted(monthly.items())
    ]
