import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
USER_ID = os.getenv("DEBUG_USER_ID")
STATEMENT_ID = os.getenv("DEBUG_STATEMENT_ID")
MONTH = os.getenv("DEBUG_MONTH")

db = create_client(SUPABASE_URL, SUPABASE_KEY)


def count(table, **filters):
    query = db.table(table).select("id")
    for key, value in filters.items():
        if value is not None:
            query = query.eq(key, value)
    return len(query.execute().data or [])


print("=== Aliyda pipeline durum kontrolü ===")
try:
    query = (
        db.table("statements")
        .select("id,user_id,month,file_name,status,error_message,created_at")
        .order("created_at", desc=True)
        .limit(5)
    )
    if USER_ID:
        query = query.eq("user_id", USER_ID)
    if STATEMENT_ID:
        query = query.eq("id", STATEMENT_ID)
    if MONTH:
        query = query.eq("month", MONTH)

    statements = query.execute().data or []
    if not statements:
        print("Statement bulunamadı. DEBUG_USER_ID, DEBUG_STATEMENT_ID veya DEBUG_MONTH filtrelerini kontrol edin.")

    for s in statements:
        statement_id = s["id"]
        user_id = s["user_id"]
        month = s["month"]

        print(f"ID: {statement_id}")
        print(f"Dosya: {s.get('file_name')}")
        print(f"Kullanıcı: {user_id}")
        print(f"Ay: {month}")
        print(f"Durum: {s.get('status')}")
        print(f"Hata: {s.get('error_message')}")
        print(f"Extraction kayıtları: {count('statement_extractions', user_id=user_id, statement_id=statement_id)}")
        print(f"Draft toplam: {count('transaction_drafts', user_id=user_id, statement_id=statement_id)}")
        print(f"Draft pending: {count('transaction_drafts', user_id=user_id, statement_id=statement_id, review_status='pending')}")
        print(f"Transactions: {count('transactions', user_id=user_id, statement_id=statement_id, is_deleted=False)}")
        print(f"Monthly summaries: {count('monthly_summaries', user_id=user_id, month=month)}")
        print(f"Chat sessions: {count('chat_sessions', user_id=user_id, month=month)}")
        print(f"Chat messages: {count('chat_messages', user_id=user_id)}")
        print("-" * 50)
except Exception as e:
    print(f"Hata: {e}")
