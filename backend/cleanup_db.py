"""
Eski failed statement'leri temizler ve veritabanini duzeltir.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== Eski failed statement'leri temizleme ===")

# 1. Tum failed statement'lerin id'lerini al
failed = db.table("statements").select("id, file_name, status, error_message").eq("status", "failed").execute()
print(f"  {len(failed.data)} failed statement bulundu")

for stmt in failed.data:
    stmt_id = stmt["id"]
    print(f"  Siliniyor: {stmt['file_name']} - hata: {str(stmt.get('error_message', ''))[:80]}")
    
    # Once draft'lari sil
    try:
        db.table("transaction_drafts").delete().eq("statement_id", stmt_id).execute()
    except:
        pass
    
    # Sonra extraction log'larini sil
    try:
        db.table("statement_extractions").delete().eq("statement_id", stmt_id).execute()
    except:
        pass
    
    # En son statement'i sil
    try:
        db.table("statements").delete().eq("id", stmt_id).execute()
        print(f"    Silindi!")
    except Exception as e:
        print(f"    Silinemedi: {e}")

# 2. Test pipeline'dan kalan statement varsa onu da sil
test_stmts = db.table("statements").select("id").eq("file_name", "test_pipeline.pdf").execute()
for s in test_stmts.data:
    try:
        db.table("transaction_drafts").delete().eq("statement_id", s["id"]).execute()
        db.table("statement_extractions").delete().eq("statement_id", s["id"]).execute()
        db.table("statements").delete().eq("id", s["id"]).execute()
        print(f"  Test statement silindi: {s['id']}")
    except:
        pass

# 3. Monthly profile kontrol
print("\n=== Monthly profile kontrol ===")
user_res = db.table("statements").select("user_id").limit(1).execute()
if user_res.data:
    uid = user_res.data[0]["user_id"]
    profile = db.table("monthly_profiles").select("*").eq("user_id", uid).eq("month", "2026-05").execute()
    if profile.data:
        print(f"  2026-05 profili var: declared_income={profile.data[0].get('declared_income')}")
    else:
        print("  2026-05 profili YOK - olusturuluyor...")
        db.table("monthly_profiles").insert({
            "user_id": uid,
            "month": "2026-05",
            "declared_income": 0,
            "income_source": "none",
        }).execute()
        print("  Olusturuldu!")

print("\nTemizlik tamamlandi!")
