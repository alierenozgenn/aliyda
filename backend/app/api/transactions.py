from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase

router = APIRouter()

@router.get("/")
async def list_transactions(
    date_from:   Optional[str]  = Query(None),
    date_to:     Optional[str]  = Query(None),
    category_id: Optional[str]  = Query(None),
    direction:   Optional[str]  = Query(None),
    is_verified: Optional[bool] = Query(None),
    page:        int = Query(1, ge=1),
    per_page:    int = Query(50, le=200),
    user = Depends(get_current_user)
):
    sb = get_supabase()
    q = sb.table("transactions").select("*, categories(name,color)").eq("user_id", user["user_id"])
    if date_from:   q = q.gte("date", date_from)
    if date_to:     q = q.lte("date", date_to)
    if category_id: q = q.eq("category_id", category_id)
    if direction:   q = q.eq("direction", direction)
    if is_verified is not None: q = q.eq("is_verified", is_verified)
    offset = (page - 1) * per_page
    return q.order("date", desc=True).range(offset, offset + per_page - 1).execute().data

@router.patch("/{transaction_id}/verify")
async def verify_transaction(transaction_id: str, body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    update_data = {k: v for k, v in body.items()
                   if k in ("category_id","description","amount","direction","date")}
    update_data["is_verified"] = True
    result = sb.table("transactions").update(update_data).eq(
        "id", transaction_id
    ).eq("user_id", user["user_id"]).execute()

    # Kategori degisikliginde ogrenilen kural kaydet
    if "category_id" in body and "description" in body:
        keyword = body["description"][:30].lower().strip()
        sb.table("category_rules").upsert({
            "user_id": user["user_id"],
            "keyword": keyword,
            "category_id": body["category_id"]
        }, on_conflict="user_id,keyword").execute()

    return result.data

@router.patch("/bulk-verify")
async def bulk_verify(body: dict, user = Depends(get_current_user)):
    sb = get_supabase()
    ids = body.get("transaction_ids", [])
    if not ids: return {"updated": 0}
    result = sb.table("transactions").update({"is_verified": True}).in_(
        "id", ids
    ).eq("user_id", user["user_id"]).execute()
    return {"updated": len(result.data)}
