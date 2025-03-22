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
        'building_id': '',
        'adv_id': '10000101',  # Default adv_id
        'lang': 'en'
    }

    # Replace <br> with new lines for easier parsing
    body = body.replace('<br>', '\n')

    url = ''
    agency_name = ''
    form_type = None
    lines = [line.strip() for line in body.splitlines() if line.strip()]

    # Assign default adv_id mapping for general and real estate forms
    real_estate_adv_ids = {
        'en': '10000102',
        'ru': '20000102',
        'ua': '30000102',
        'tr': '40000102'
    }
    general_adv_ids = {
        'en': '10000101',
        'ru': '20000101',
        'ua': '30000101',
        'tr': '40000101'
    }

    # Debug log
    # print("Lines after cleanup:")
    # for line in lines:
    #     print(f"  {line}")

     # Improved form detection: match form label and value
    for i in range(len(lines) - 1):
        label = re.sub(r'<.*?>', '', lines[i].lower())
        value = re.sub(r'<.*?>', '', lines[i + 1].lower())
        if label == 'form' and 'real estate agencies form' in value:
            form_type = 'real_estate_agency'
            break

    # Determine email type and extract fields
    if 'Teus Group' in body:
        for line in lines:
            if line.startswith('Name:'):
                fields['name'] = line.replace('Name:', '').strip()
            elif line.startswith('Name 2:'):
                fields['name'] = line.replace('Name 2:', '').strip()
            elif line.startswith('Agency name:'):
                agency_name = line.replace('Agency name:', '').strip()
            elif line.startswith('Email:') or line.startswith('Email 2:'):
                fields['email'] = line.replace('Email:', '').replace('Email 2:', '').strip()
            elif line.startswith('Phone:') or line.startswith('Phone 2:'):
                fields['phone'] = line.replace('Phone:', '').replace('Phone 2:', '').strip()
            elif line.startswith('Версия страницы:'):
                lang_version = line.replace('Версия страницы:', '').strip().lower()
                fields['lang'] = lang_version
            elif line.startswith('Comment/Question:'):
                fields['note'] = line.replace('Comment/Question:', '').strip()

        # Debug log for form type and lang
        # print(f"Detected form_type: {form_type}, lang: {fields['lang']}")

        # Assign adv_id after lang is defined
        lang_version = fields['lang']
        if form_type == 'real_estate_agency':
            fields['adv_id'] = real_estate_adv_ids.get(lang_version, '10000102')
        else:
            fields['adv_id'] = general_adv_ids.get(lang_version, '10000101')

        # Add agency name to notes
        if agency_name:
            if fields['note']:
                fields['note'] = f"Agency Name: {agency_name} | {fields['note']}"
            else:
                fields['note'] = f"Agency Name: {agency_name}"
    else:
        for line in lines:
            if line.startswith('Name:') or (fields['name'] == '' and not line.startswith(('Email:', 'Phone:', 'url:', 'Additional:'))):
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
        if url:
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
