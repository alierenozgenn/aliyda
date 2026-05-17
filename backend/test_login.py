import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Hata: .env dosyasında SUPABASE_URL ve SUPABASE_ANON_KEY bulunamadı.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

email = input("Supabase Email: ")
password = input("Supabase Password: ")

try:
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print("\n✅ Giriş Başarılı!")
    print(f"User ID: {response.user.id}")
    print("\n--- Swagger'da Authorize kısmına kopyalamanız gereken JWT Token ---")
    print(response.session.access_token)
    print("-------------------------------------------------------------------")
except Exception as e:
    print(f"\n❌ Giriş Başarısız: {str(e)}")
