import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from io import BytesIO

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


def upload_pdf_to_whatsapp(pdf_buffer: BytesIO, filename="fee_statement.pdf"):
    """Upload PDF file to WhatsApp servers and return media_id."""
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

    try:
        response = requests.post(url, headers=headers, params=params, files=files)
        response.raise_for_status()
        media_id = response.json().get("id")
        print(f"✅ Uploaded PDF, media_id: {media_id}")
        return media_id
    except requests.RequestException as e:
        print(f"❌ Failed to upload PDF: {e}")
        return None


def send_document_message(phone, media_id, caption=""):
    """Send a document via WhatsApp using media_id."""
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

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"📄 PDF sent to {phone}")
    except requests.RequestException as e:
        print(f"❌ Failed to send PDF: {e}")
