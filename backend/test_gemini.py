import asyncio
from app.services.gemini_service import extract_transactions_from_pdf

async def test():
    with open("demo_ekstre.pdf", "rb") as f:
        pdf_bytes = f.read()
    result = await extract_transactions_from_pdf(pdf_bytes)
    for tx in result.get("transactions", []):
        label = "ONAYLANDI" if tx.get("confidence", 0) >= 0.80 else "ONAY GEREKIR"
        print(f"{label} | {tx.get('date', '')} | {tx.get('description', '')[:30]:30} | {tx.get('amount', 0):10.2f} TL | {tx.get('estimated_category', '')} ({tx.get('confidence', 0):.2f})")

asyncio.run(test())
