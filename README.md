# Email Lead Parser and CRM Proxy Forwarder

A Python script to parse incoming emails for lead information and forward it securely to a proxy server.

## 📌 Features

- Fetch unread emails from a Gmail inbox.
- Extracts key lead details: name, phone, email, and notes.
- Combines URLs into notes for compatibility with CRM.
- Securely forwards leads to a proxyserver.

## 🛠️ Requirements

- Python 3.8 or later
- Gmail account with IMAP enabled and an App Password

## ⚙️ Installation

### 1. Clone the Repository

### 2. Install Python Dependencies
```
cp .env.example .env
```
### 3. Configure Environment Variables
create an .env file and fill it out:
```
IMAP_SERVER=imap.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
PROXY_SERVER_URL=https://your-url
```
## ✅ Example Email Format
Emails must follow this format:
```
Name: John Doe
Email: johndoe@example.com
Phone: +123456789
url: https://example.com/property/123
Additional: Interested in a 2-bedroom apartment


