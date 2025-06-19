import os
from datetime import datetime
from pathlib import Path
from io import BytesIO
import requests
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
VERSION = 'v18.0'


def send_text_message(recipient, text):
    """Send a plain text message via WhatsApp API."""
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print(f"✅ Message sent to {recipient}")
    except requests.RequestException as e:
        print(f"❌ Message error: {e}")


def generate_fee_statement_pdf_in_memory(student, balance):
    """Generate fee statement PDF in memory and return BytesIO buffer."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, "Fee Statement")

    # Generated timestamp
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 80, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Student details
    y = height - 120
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Student Details:")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Name: {student.col_firstname} {student.col_lastname}")
    y -= 20
    c.drawString(50, y, f"Reg No: {student.col_cust_no}")

    # Fee balance
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Fee Balance:")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Amount: ${balance:.2f}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2.0, 50, "Thank you for your support.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


def upload_pdf_to_whatsapp(pdf_buffer, filename="fee_statement.pdf"):
    """Upload PDF bytes to WhatsApp Cloud and return media_id."""
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    params = {
        "messaging_product": "whatsapp"
    }

    files = {
        "file": (filename, pdf_buffer, "application/pdf")
    }

    response = requests.post(url, headers=headers, params=params, files=files)

    if response.ok:
        media_id = response.json().get("id")
        print(f"✅ Uploaded PDF, media_id: {media_id}")
        return media_id
    else:
        print(f"❌ Failed to upload PDF: {response.text}")
        return None


def send_document_message(phone, media_id, caption=""):
    """Send a document message by media_id via WhatsApp API."""
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption,
            "filename": "FeeStatement.pdf"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        print(f"📄 PDF sent to {phone}")
    else:
        print(f"❌ Failed to send PDF: {response.text}")
