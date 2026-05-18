import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== Son Yüklenen Statement Durumları ===")
try:
    res = db.table("statements").select("id, file_name, status, error_message, created_at").order("created_at", desc=True).limit(5).execute()
    for s in res.data:
        print(f"ID: {s['id']}")
        print(f"Dosya: {s['file_name']}")
        print(f"Durum: {s['status']}")
        print(f"Hata: {s.get('error_message')}")
        print(f"Zaman: {s['created_at']}")
        print("-" * 50)
except Exception as e:
    print(f"Hata: {e}")
