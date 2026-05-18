"""
Tam upload pipeline testi — Supabase RPC cagrilarini test eder.
Hangi adimda hata oldugunu bulur.
"""
import os
import sys
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Gerekli bilgiler ---
# user_id ve account_id'yi statements tablosundan cekelim
print("=== Mevcut statement ve account bilgileri ===")
try:
    stmts = db.table("statements").select("user_id, account_id, status, error_message").order("created_at", desc=True).limit(3).execute()
    for s in stmts.data:
        print(f"  user_id={s['user_id'][:12]}... account_id={s['account_id'][:12]}... status={s['status']} error={s.get('error_message', '-')[:100] if s.get('error_message') else '-'}")
    
    USER_ID = stmts.data[0]["user_id"] if stmts.data else None
    ACCOUNT_ID = stmts.data[0]["account_id"] if stmts.data else None
except Exception as e:
    print(f"HATA: {e}")
    USER_ID = None
    ACCOUNT_ID = None

if not USER_ID:
    print("Kullanici bulunamadi!")
    sys.exit(1)

print(f"\nUser: {USER_ID}")
print(f"Account: {ACCOUNT_ID}")

# --- Simdi Gemini extraction yapalim ---
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

PDF_PATH = "demo_ekstre.pdf"
if not os.path.exists(PDF_PATH):
    print("demo_ekstre.pdf bulunamadi!")
    sys.exit(1)

from app.services.gemini_service import GeminiService
gemini = GeminiService()

print("\n=== Adim 1: Gemini PDF extraction ===")
try:
    extracted = gemini.extract_transactions_from_pdf(PDF_PATH)
    txs = extracted.get("transactions", [])
    print(f"  BASARILI: {len(txs)} islem cikarildi")
except Exception as e:
    print(f"  HATA: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n=== Adim 2: Statement olustur ===")
try:
    stmt_res = db.table("statements").insert({
        "user_id": USER_ID,
        "account_id": ACCOUNT_ID,
        "month": "2026-05",
        "source": "pdf",
        "file_name": "test_pipeline.pdf",
        "file_mime_type": "application/pdf",
        "file_size_bytes": 1303,
        "status": "extracting",
    }).execute()
    STMT_ID = stmt_res.data[0]["id"]
    print(f"  BASARILI: statement_id={STMT_ID}")
except Exception as e:
    print(f"  HATA: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n=== Adim 3: Extraction log kaydet ===")
try:
    from app.core.config import settings
    db.rpc("save_statement_extraction", {
        "p_statement_id": STMT_ID,
        "p_provider": "gemini",
        "p_model": settings.GEMINI_MODEL_EXTRACTION,
        "p_prompt_version": "v2.0",
        "p_raw_output": str(extracted)[:4000],
        "p_parsed_output": extracted,
        "p_status": "success",
        "p_error_message": None,
    }).execute()
    print("  BASARILI")
except Exception as e:
    print(f"  HATA: {e}")
    traceback.print_exc()
    # devam et

print(f"\n=== Adim 4: Draft olustur ({len(txs)} islem) ===")
success_count = 0
fail_count = 0
for i, tx in enumerate(txs):
    try:
        db.rpc("create_transaction_draft", {
            "p_user_id": USER_ID,
            "p_account_id": ACCOUNT_ID,
            "p_statement_id": STMT_ID,
            "p_month": "2026-05",
            "p_transaction_date": tx.get("transaction_date"),
            "p_transaction_time": tx.get("transaction_time"),
            "p_description": tx.get("description", ""),
            "p_original_description": tx.get("original_description", ""),
            "p_amount": float(tx.get("amount", 0)),
            "p_currency": tx.get("currency", "TRY"),
            "p_direction": tx.get("direction", "expense"),
            "p_category": tx.get("category"),
            "p_subcategory": tx.get("subcategory"),
            "p_counterparty": tx.get("counterparty"),
            "p_confidence_score": float(tx.get("confidence", 0.8)),
            "p_needs_review": True,
        }).execute()
        success_count += 1
    except Exception as e:
        fail_count += 1
        print(f"  Draft #{i+1} HATA: {e}")

print(f"  Sonuc: {success_count} basarili, {fail_count} basarisiz")

print("\n=== Adim 5: Status guncelle -> pending_review ===")
try:
    db.table("statements").update({"status": "pending_review"}).eq("id", STMT_ID).execute()
    print("  BASARILI")
except Exception as e:
    print(f"  HATA: {e}")
    traceback.print_exc()

print(f"\nPipeline testi tamamlandi! statement_id={STMT_ID}")
print("Simdi frontend'den bu statement'in draftlarini gorebilirsiniz.")
