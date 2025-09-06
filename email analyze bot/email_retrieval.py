#!/usr/bin/env python3
"""
Email Retrieval and Filtering Module
Fetches emails from Gmail and filters support-related emails.
"""

import os.path
import base64
from datetime import datetime, timedelta
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Support-related keywords for filtering
SUPPORT_KEYWORDS = [
    'support', 'query', 'request', 'help', 'issue', 'problem',
    'assistance', 'trouble', 'error', 'bug', 'complaint',
    'question', 'inquiry', 'concern', 'urgent', 'critical'
]

class EmailRetriever:
    def __init__(self, credentials_file="client_secret.json", token_file="token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Check for existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no valid credentials, get them
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        # Build the Gmail service
        self.service = build("gmail", "v1", credentials=creds)
        print("✅ Gmail API authenticated successfully!")
    
    def get_todays_emails(self):
        """Fetch all emails received today."""
        try:
            # Calculate today's date range
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            tomorrow_start = today_start + timedelta(days=1)
            
            # Convert to Gmail query format (epoch timestamp)
            after_timestamp = int(today_start.timestamp())
            before_timestamp = int(tomorrow_start.timestamp())
            
            # Gmail search query for today's emails
            query = f"after:{after_timestamp} before:{before_timestamp}"
            
            print(f"📅 Fetching emails from {today_start.strftime('%Y-%m-%d')}...")
            
            # Get all message IDs for today
            results = self.service.users().messages().list(
                userId="me", 
                q=query,
                maxResults=500  # Adjust as needed
            ).execute()
            
            messages = results.get("messages", [])
            
            if not messages:
                print("📭 No emails found for today.")
                return []
            
            print(f"📊 Found {len(messages)} emails for today.")
            
            # Fetch full email data
            emails = []
            for i, message in enumerate(messages, 1):
                print(f"📧 Processing email {i}/{len(messages)}...", end="\r")
                email_data = self._get_email_details(message["id"])
                if email_data:
                    emails.append(email_data)
            
            print(f"\n✅ Successfully retrieved {len(emails)} emails.")
            return emails
            
        except HttpError as error:
            print(f"❌ Error fetching emails: {error}")
            return []
    
    def _get_email_details(self, message_id):
        """Get detailed information for a specific email."""
        try:
            message = self.service.users().messages().get(
                userId="me", 
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message["payload"].get("headers", [])
            email_data = {
                "message_id": message_id,
                "gmail_id": message.get("id"),
                "thread_id": message.get("threadId"),
                "label_ids": message.get("labelIds", []),
                "snippet": message.get("snippet", ""),
                "internal_date": message.get("internalDate")
            }
            
            # Parse headers
            for header in headers:
                name = header["name"].lower()
                value = header["value"]
                
                if name == "subject":
                    email_data["subject"] = value
                elif name == "from":
                    email_data["sender"] = value
                    email_data["sender_email"] = self._extract_email_from_sender(value)
                    email_data["sender_name"] = self._extract_name_from_sender(value)
                elif name == "date":
                    email_data["date"] = value
                    email_data["received_date"] = self._parse_email_date(value)
                elif name == "to":
                    email_data["to"] = value
                elif name == "cc":
                    email_data["cc"] = value
                elif name == "message-id":
                    email_data["original_message_id"] = value
            
            # Extract email body
            email_data["body"] = self._extract_email_body(message["payload"])
            
            # Filter for support-related emails
            email_data["is_support_related"] = self._is_support_related(
                email_data.get("subject", ""),
                email_data.get("body", "")
            )
            
            return email_data
            
        except HttpError as error:
            print(f"❌ Error getting email details for {message_id}: {error}")
            return None
    
    def _extract_email_body(self, payload):
        """Extract email body from payload."""
        body = ""
        
        def decode_body(data):
            """Decode base64 email body."""
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            except:
                return ""
        
        # Handle multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                
                if mime_type == "text/plain":
                    if "data" in part.get("body", {}):
                        body = decode_body(part["body"]["data"])
                        break
                elif mime_type == "text/html" and not body:
                    if "data" in part.get("body", {}):
                        body = decode_body(part["body"]["data"])
                elif "parts" in part:  # Nested parts
                    nested_body = self._extract_email_body(part)
                    if nested_body:
                        body = nested_body
                        break
        
        # Handle single part messages
        elif payload.get("mimeType") == "text/plain":
            if "data" in payload.get("body", {}):
                body = decode_body(payload["body"]["data"])
        
        return body.strip()
    
    def _extract_email_from_sender(self, sender_string):
        """Extract email address from sender string."""
        email_pattern = r'<([^>]+)>|([^\s<>]+@[^\s<>]+)'
        match = re.search(email_pattern, sender_string)
        if match:
            return match.group(1) or match.group(2)
        return sender_string.strip()
    
    def _extract_name_from_sender(self, sender_string):
        """Extract name from sender string."""
        if '<' in sender_string:
            name = sender_string.split('<')[0].strip().strip('"')
            return name if name else None
        return None
    
    def _parse_email_date(self, date_string):
        """Parse email date string to datetime object."""
        try:
            # Remove timezone name if present and parse
            date_string = re.sub(r'\s+\([^)]+\)$', '', date_string)
            
            # Common email date formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If all else fails, return current time
            return datetime.now()
            
        except Exception as e:
            print(f"⚠️ Error parsing date '{date_string}': {e}")
            return datetime.now()
    
    def _is_support_related(self, subject, body):
        """Check if email is support-related based on keywords."""
        text_to_check = f"{subject} {body}".lower()
        
        for keyword in SUPPORT_KEYWORDS:
            if keyword in text_to_check:
                return True
        
        return False
    
    def filter_support_emails(self, emails):
        """Filter emails for support-related content."""
        support_emails = [email for email in emails if email.get("is_support_related", False)]
        
        print(f"🔍 Filtered {len(support_emails)} support-related emails from {len(emails)} total emails.")
        
        return support_emails
    
    def display_email_summary(self, emails):
        """Display a summary of retrieved emails."""
        if not emails:
            print("📭 No emails to display.")
            return
        
        print(f"\n📊 EMAIL SUMMARY")
        print("=" * 80)
        print(f"Total emails: {len(emails)}")
        
        support_count = sum(1 for email in emails if email.get("is_support_related", False))
        print(f"Support-related emails: {support_count}")
        
        print("\n📧 RECENT EMAILS:")
        print("-" * 80)
        
        for i, email in enumerate(emails[:10], 1):  # Show first 10
            status = "🎫" if email.get("is_support_related") else "📨"
            sender = email.get("sender_name") or email.get("sender_email", "Unknown")
            subject = email.get("subject", "No Subject")[:50]
            
            print(f"{status} {i:2d}. From: {sender[:30]:<30} | Subject: {subject}")
        
        if len(emails) > 10:
            print(f"... and {len(emails) - 10} more emails")
        
        print("-" * 80)

def main():
    """Main function for testing email retrieval."""
    print("📧 Email Retrieval and Filtering Test")
    print("=" * 50)
    
    # Initialize email retriever
    retriever = EmailRetriever()
    
    # Get today's emails
    emails = retriever.get_todays_emails()
    
    # Display summary
    retriever.display_email_summary(emails)
    
    # Filter support emails
    support_emails = retriever.filter_support_emails(emails)
    
    if support_emails:
        print(f"\n🎫 SUPPORT EMAILS DETAILS:")
        print("=" * 80)
        
        for i, email in enumerate(support_emails, 1):
            print(f"\n{i}. SUPPORT EMAIL")
            print("-" * 40)
            print(f"From: {email.get('sender', 'Unknown')}")
            print(f"Subject: {email.get('subject', 'No Subject')}")
            print(f"Date: {email.get('date', 'Unknown')}")
            print(f"Body Preview: {email.get('body', '')[:200]}...")
            print("-" * 40)

if __name__ == "__main__":
    main()
