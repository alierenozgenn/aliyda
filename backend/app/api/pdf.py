from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from app.dependencies.auth import get_current_user
from app.services.supabase_client import get_supabase
from app.agents.graph import finance_graph

router = APIRouter()
MAX_SIZE_MB = 10

@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Yalnizca PDF dosyasi kabul edilir.")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"Dosya boyutu {MAX_SIZE_MB}MB'i gecemez.")

    sb = get_supabase()
    upload = sb.table("pdf_uploads").insert({
        "user_id": user["user_id"],
        "file_name": file.filename,
        "status": "uploaded"
    }).execute()
    upload_id = upload.data[0]["id"]

    background_tasks.add_task(run_finance_pipeline, contents, user["user_id"], upload_id)
    return {"upload_id": upload_id, "status": "processing"}

async def run_finance_pipeline(pdf_bytes: bytes, user_id: str, upload_id: str):
    sb = get_supabase()
    sb.table("pdf_uploads").update({"status": "processing"}).eq("id", upload_id).execute()
    try:
        result = await finance_graph.ainvoke({
            "pdf_bytes": pdf_bytes, "user_id": user_id, "upload_id": upload_id,
            "retry_count": 0, "status": "processing"
        })
        sb.table("pdf_uploads").update({"status": result.get("status", "completed")}).eq("id", upload_id).execute()
    except Exception as e:
        sb.table("pdf_uploads").update({"status": "failed", "error_message": str(e)}).eq("id", upload_id).execute()

@router.get("/uploads")
async def list_uploads(user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("pdf_uploads").select("*").eq("user_id", user["user_id"]).order("created_at", desc=True).execute().data

@router.get("/uploads/{upload_id}")
async def get_upload(upload_id: str, user = Depends(get_current_user)):
    sb = get_supabase()
    return sb.table("pdf_uploads").select("*").eq("id", upload_id).eq("user_id", user["user_id"]).single().execute().data
