from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from datetime import date

router = APIRouter()

@router.post("/")
async def create_goal(body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("goals").insert({
        "user_id":         user["user_id"],
        "name":            body["name"],
        "target_amount":   body["target_amount"],
        "current_savings": body.get("current_savings", 0),
        "target_date":     body["target_date"]
    }).execute().data[0]

@router.get("/{goal_id}/analysis")
async def analyze_goal(goal_id: str, user = Depends(get_current_user)):
    sb = get_supabase()
    goal = sb.table("goals").select("*").eq("id", goal_id).eq(
        "user_id", user["user_id"]
    ).single().execute().data

    remaining    = goal["target_amount"] - goal["current_savings"]
    today        = date.today()
    target       = date.fromisoformat(goal["target_date"])
    months_left  = max(1, (target.year - today.year) * 12 + (target.month - today.month))
    req_monthly  = round(remaining / months_left, 2)
    req_weekly   = round(req_monthly / 4.33, 2)

    month_key = f"{today.year}-{today.month:02d}"
    txs = sb.table("transactions").select("amount,direction").eq(
        "user_id", user["user_id"]
    ).like("date", f"{month_key}%").execute()
    income  = sum(t["amount"] for t in txs.data if t["direction"] == "income")
    expense = sum(t["amount"] for t in txs.data if t["direction"] == "expense")
    surplus = round(income - expense, 2)

    return {
        "goal":             goal,
        "remaining_amount": round(remaining, 2),
        "months_left":      months_left,
        "required_monthly": req_monthly,
        "required_weekly":  req_weekly,
        "current_surplus":  surplus,
        "achievable":       surplus >= req_monthly,
        "shortfall_monthly": round(max(0, req_monthly - surplus), 2)
    }
