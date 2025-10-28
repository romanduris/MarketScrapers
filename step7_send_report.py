"""
STEP 7 – Odoslanie HTML reportu emailom cez Mailjet API
Bez potreby osobného emailu / hesla.
"""

import os
from mailjet_rest import Client
from pathlib import Path

# =============== KONFIGURÁCIA =================
MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_SECRET_KEY = os.getenv("MAILJET_SECRET_KEY")

SENDER_EMAIL = "your_verified_email@example.com"   # Mail, ktorý si overil v Mailjet
SENDER_NAME = "MarketScraper AI"
RECIPIENT_EMAIL = "your_email@example.com"         # Kam chceš poslať report

REPORT_FILE = Path("data/ai_report.html")

# ===============================================

def send_ai_report():
    print("📡 Odosielam AI report cez Mailjet...")

    # kontrola API kľúčov
    if not MAILJET_API_KEY or not MAILJET_SECRET_KEY:
        print("⚠️ Chýbajú Mailjet API kľúče! Nastav ich ako environment variables:")
        print("   export MAILJET_API_KEY='your_key_here'")
        print("   export MAILJET_SECRET_KEY='your_secret_here'")
        return

    # kontrola reportu
    if not REPORT_FILE.exists():
        print(f"⚠️ Súbor {REPORT_FILE} neexistuje, najprv spusti step6_report_html.py")
        return

    html_content = REPORT_FILE.read_text(encoding="utf-8")

    # Inicializácia Mailjet klienta
    mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": SENDER_EMAIL,
                    "Name": SENDER_NAME
                },
                "To": [
                    {
                        "Email": RECIPIENT_EMAIL,
                        "Name": "Investor"
                    }
                ],
                "Subject": "📊 MarketScraper AI – Denný report Top 10 akcií",
                "HTMLPart": html_content,
                "Attachments": [
                    {
                        "ContentType": "text/html",
                        "Filename": "AI_Report.html",
                        "Base64Content": REPORT_FILE.read_bytes().decode("latin1", errors="ignore")
                    }
                ]
            }
        ]
    }

    try:
        result = mailjet.send.create(data=data)
        if result.status_code == 200:
            print("✅ Email bol úspešne odoslaný!")
        else:
            print(f"⚠️ Chyba pri odosielaní: {result.status_code} -> {result.json()}")
    except Exception as e:
        print(f"❌ Výnimka pri odosielaní emailu: {e}")


if __name__ == "__main__":
    send_ai_report()
