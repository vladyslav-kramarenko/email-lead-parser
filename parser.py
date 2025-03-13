import imaplib
import email
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Email credentials
IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')

# Proxy Server URL
PROXY_SERVER_URL = os.getenv('PROXY_SERVER_URL')

# Connect to email inbox
def connect_to_inbox():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select('inbox')
    return mail

# Extract lead data from email content
def parse_email_body(body):
    fields = {
        'name': '',
        'email': '',
        'phone': '',
        'note': '',
        'building_id': '25787',
        'adv_id': '10100002'
    }
    url = ''
    lines = body.splitlines()
    for line in lines:
        if line.startswith('Name:'):
            fields['name'] = line.replace('Name:', '').strip()
        elif line.startswith('Email:'):
            fields['email'] = line.replace('Email:', '').strip()
        elif line.startswith('Phone:'):
            fields['phone'] = line.replace('Phone:', '').strip()
        elif line.startswith('url:'):
            url = line.replace('url:', '').strip()
        elif line.startswith('Additional:'):
            fields['note'] = line.replace('Additional:', '').strip()

    # Combine URL with notes for CRM compatibility
    if fields['note']:
        fields['note'] += f" | unit: {url}"
    else:
        fields['note'] = f"unit: {url}"

    # Set email default if not provided
    if not fields.get('email'):
        fields['email'] = 'no-email@example.com'

    return fields

# Send lead to proxy server
def send_to_proxy(data):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://mail-parser.teus-group.com',
        'User-Agent': 'MailParserBot/1.0'
    }
    PROXY_SERVER_URL = os.getenv('PROXY_SERVER_URL')

    response = requests.post(PROXY_SERVER_URL, json=data, headers=headers)

    if response.status_code == 200:
        print(f"✅ Successfully sent lead: {data['name']}")
    else:
        print(f"❌ Failed to send lead: {response.status_code}, {response.text}")

# Fetch, parse, and forward new leads
def process_emails():
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASS = os.getenv('EMAIL_PASS')
    IMAP_SERVER = os.getenv('IMAP_SERVER')

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select('inbox')

    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages = messages[0].split()

    if not email_ids:
        print('📭 No new emails found.')
        return

    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # Extract email body
        email_body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    email_body = part.get_payload(decode=True).decode()
                    break
        else:
            email_body = msg.get_payload(decode=True).decode()

        print(f"Processing email:\n{email_body}")

        lead_data = parse_email_body(email_body)
        print("Parsed lead data:", lead_data)

        send_to_proxy(lead_data)

    mail.logout()

if __name__ == "__main__":
    process_emails()
