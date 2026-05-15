from fpdf import FPDF
import os

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

content = """Islem Tarihi  Aciklama                Tutar
01.05.2026    MAAS YATISI             +18.500,00 TL
03.05.2026    A101 MARKET             -   430,50 TL
05.05.2026    IGDAS FATURA            -   620,00 TL
07.05.2026    NETFLIX TR              -   169,99 TL
09.05.2026    MIGROS MARKET           -   890,00 TL
11.05.2026    UBER                    -   145,00 TL
12.05.2026    AKBANKA KIRA ODEMESI   - 4.500,00 TL
13.05.2026    YEMEGE CIKMA ODEMESI   -   380,00 TL
15.05.2026    XYZ TRANSFER            - 1.200,00 TL
16.05.2026    TURK TELEKOM            -   249,00 TL
18.05.2026    CARREFOURSA             -   560,00 TL
22.05.2026    SPOTIFY                 -    49,99 TL
24.05.2026    PHARMACY ECZANE         -   230,00 TL
"""
for line in content.split("\n"):
    pdf.cell(200, 10, txt=line, ln=True, align="L")
pdf.output("demo_ekstre.pdf")
print("demo_ekstre.pdf created.")
