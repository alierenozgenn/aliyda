"""
Standalone Google AI Studio connectivity test.

This script does not import FastAPI, Supabase, or the Aliyda app services.
It only checks:
1. google-genai package import
2. GOOGLE_API_KEY / GEMINI_API_KEY loading from .env
3. text generation with gemini-3.1-flash-lite
4. optional PDF upload + model call + file cleanup
"""

import argparse
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv


MODEL = "gemini-3.1-flash-lite"


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return value[:4] + "..."
    return value[:8] + "..." + value[-4:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", help="Optional PDF path to test Google Files upload")
    args = parser.parse_args()

    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

    print("=== Google AI standalone test ===")
    print(f"Working dir: {Path.cwd()}")
    print(f".env path: {env_path}")
    print(f".env exists: {env_path.exists()}")
    print(f"Model: {MODEL}")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    print(f"API key loaded: {'YES ' + mask_key(api_key) if api_key else 'NO'}")
    if not api_key:
        print("ERROR: Put GOOGLE_API_KEY=... into backend/.env")
        return 1

    try:
        import importlib.metadata
        from google import genai
        from google.genai import types

        print(f"google-genai version: {importlib.metadata.version('google-genai')}")
        client = genai.Client(api_key=api_key)
        print("Client created: OK")
    except Exception as exc:
        print("ERROR: google-genai import/client creation failed")
        print(exc)
        traceback.print_exc()
        return 1

    print("\n[1] Text generation test")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents="Sadece OK yaz.",
            config=types.GenerateContentConfig(temperature=0),
        )
        print("Raw response:", repr(response.text))
        if not response.text:
            print("ERROR: Empty model response")
            return 1
        print("Text generation: OK")
    except Exception as exc:
        print("ERROR: Text generation failed")
        print(exc)
        traceback.print_exc()
        return 1

    if not args.pdf:
        print("\n[2] PDF upload test skipped. Pass --pdf path\\to\\file.pdf to test it.")
        print("\nRESULT: Google AI model connection works.")
        return 0

    pdf_path = Path(args.pdf).resolve()
    print("\n[2] PDF upload + analyze test")
    print(f"PDF path: {pdf_path}")
    print(f"PDF exists: {pdf_path.exists()}")
    if not pdf_path.exists():
        print("ERROR: PDF file does not exist")
        return 1

    uploaded_file = None
    try:
        uploaded_file = client.files.upload(
            file=str(pdf_path),
            config=types.UploadFileConfig(
                mime_type="application/pdf",
                display_name=pdf_path.name,
            ),
        )
        print("Upload returned:")
        print(f"  name: {getattr(uploaded_file, 'name', None)}")
        print(f"  uri: {getattr(uploaded_file, 'uri', None)}")
        print(f"  mime_type: {getattr(uploaded_file, 'mime_type', None)}")
        print(f"  state: {getattr(uploaded_file, 'state', None)}")

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                uploaded_file,
                "Bu PDF okunabiliyorsa sadece OK yaz. Okunamıyorsa kısa hata yaz.",
            ],
            config=types.GenerateContentConfig(temperature=0),
        )
        print("PDF model response:", repr(response.text))
        if not response.text:
            print("ERROR: Empty PDF response")
            return 1
        print("PDF upload/analyze: OK")
    except Exception as exc:
        print("ERROR: PDF upload/analyze failed")
        print(exc)
        traceback.print_exc()
        return 1
    finally:
        if uploaded_file and getattr(uploaded_file, "name", None):
            try:
                client.files.delete(name=uploaded_file.name)
                print("Uploaded Google file deleted: OK")
            except Exception as exc:
                print("WARNING: Uploaded Google file could not be deleted")
                print(exc)

    print("\nRESULT: Google AI text + PDF path works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
