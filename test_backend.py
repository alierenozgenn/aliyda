import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('backend/.env')
url = os.getenv('SUPABASE_URL')
svc = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
uid = '6b0f50c6-afb0-4d75-9ba6-79971f8e4491'
acc_id = '367161fc-9c3f-4758-aa19-df448affe7cb'

db = create_client(url, svc)

print("=== TRANSACTIONS ===")
txs = db.table('transactions').select('id, description, month').eq('user_id', uid).execute()
print(f"Count: {len(txs.data)}")
for t in txs.data:
    print(f"  - {t['description']} ({t['month']})")

print("\n=== RECALC SUMMARY ===")
try:
    db.rpc('recalculate_monthly_summary', {'p_user_id': uid, 'p_month': '2026-05'}).execute()
    summary = db.table('monthly_summaries').select('total_income,total_expense,net_balance,transaction_count').eq('user_id', uid).eq('month', '2026-05').execute()
    print("Summary:", summary.data)
except Exception as e:
    print("HATA:", e)

print("\n=== V_MONTHLY_DASHBOARD ===")
dash = db.table('v_monthly_dashboard').select('*').eq('user_id', uid).eq('month', '2026-05').execute()
print("Dashboard:", dash.data)

print("\n=== V_CONFIRMED_TRANSACTIONS ===")
v = db.table('v_confirmed_transactions').select('description, direction, amount').eq('user_id', uid).execute()
print(f"Count: {len(v.data)}")
for t in v.data:
    print(f"  - {t['description']} {t['direction']} {t['amount']}TL")
