#!/usr/bin/env python3
"""
Set Gmail signature for ferretti.argosautomotive@gmail.com
Uses OAuth2 Desktop flow with credentials from Downloads.
"""
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.settings.basic']
CREDS_FILE = os.path.expanduser('~/Downloads/argos-gmail-credentials.json')
TOKEN_FILE = os.path.expanduser('~/.argos-gmail-token.json')
SIGNATURE_FILE = os.path.join(os.path.dirname(__file__), '..', 'copy', 'email_signature.html')

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds

def main():
    print("[ARGOS] Setting Gmail signature...")

    # Read signature HTML
    with open(SIGNATURE_FILE, 'r') as f:
        raw = f.read()

    # Extract only the <table> part (skip HTML comments)
    import re
    tables = re.findall(r'(<table[\s\S]*?</table>)\s*$', raw)
    if tables:
        signature_html = tables[-1]
    else:
        signature_html = raw

    # Get credentials and build service
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    # Get current send-as aliases
    result = service.users().settings().sendAs().list(userId='me').execute()
    aliases = result.get('sendAs', [])

    primary = None
    for alias in aliases:
        if alias.get('isPrimary'):
            primary = alias
            break

    if not primary:
        print("[ERROR] No primary send-as alias found")
        return

    print(f"[ARGOS] Primary email: {primary['sendAsEmail']}")

    # Update signature
    primary['signature'] = signature_html
    service.users().settings().sendAs().update(
        userId='me',
        sendAsEmail=primary['sendAsEmail'],
        body={'signature': signature_html}
    ).execute()

    print(f"[ARGOS] Signature set successfully for {primary['sendAsEmail']}")
    print(f"[ARGOS] Signature length: {len(signature_html)} chars")

if __name__ == '__main__':
    main()
