import os
import base64
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.utils import timezone
from .models import Email

class GmailRetriever:
    """Gmail API service based on your working email_retrieval.py implementation"""
    
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        
        # Try to use credentials from your working folder
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.working_credentials = os.path.join(project_dir, 'email analyze bot', 'client_secret.json')
        self.working_token = os.path.join(project_dir, 'email analyze bot', 'token.json')
    
    def authenticate_gmail(self):
        """Authenticate with Gmail API using your working implementation"""
        creds = None
        
        # Try to load existing token
        token_file = self.working_token if os.path.exists(self.working_token) else self.token_path
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                # Use working credentials file if available
                creds_file = self.working_credentials if os.path.exists(self.working_credentials) else self.credentials_path
                
                if not os.path.exists(creds_file):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found. Please ensure {creds_file} exists.\n"
                        "You can download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail authentication successful!")
            return True
        except Exception as e:
            print(f"❌ Error building Gmail service: {e}")
            return False
    
    def get_email_list(self, query='', max_results=10):
        """Get list of emails based on your working implementation"""
        try:
            if not self.service:
                if not self.authenticate_gmail():
                    return []
            
            # Default query for unread emails
            if not query:
                query = 'is:unread'
            
            print(f"🔍 Searching emails with query: '{query}'")
            
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            print(f"📧 Found {len(messages)} emails")
            
            return messages
        
        except HttpError as error:
            print(f"❌ Error fetching email list: {error}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def get_email_details(self, message_id):
        """Get detailed email content based on your working implementation"""
        try:
            if not self.service:
                if not self.authenticate_gmail():
                    return None
            
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self.parse_email_message(message)
        
        except HttpError as error:
            print(f"❌ Error fetching email details for {message_id}: {error}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching email {message_id}: {e}")
            return None
    
    def parse_email_message(self, message):
        """Parse Gmail message into structured format based on your working implementation"""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            subject = ''
            sender_email = ''
            sender_name = ''
            date_received = ''
            
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                
                if name == 'subject':
                    subject = value
                elif name == 'from':
                    # Parse sender info
                    if '<' in value and '>' in value:
                        sender_name = value.split('<')[0].strip().strip('"')
                        sender_email = value.split('<')[1].split('>')[0].strip()
                    else:
                        sender_email = value.strip()
                        sender_name = sender_email
                elif name == 'date':
                    date_received = value
            
            # Extract body
            body = self.extract_email_body(message['payload'])
            
            # Convert date
            received_at = self.parse_email_date(date_received)
            
            email_data = {
                'message_id': message['id'],
                'subject': subject,
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body,
                'received_at': received_at,
                'thread_id': message.get('threadId', ''),
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
            print(f"📩 Parsed email: {subject[:50]}... from {sender_email}")
            return email_data
        
        except Exception as e:
            print(f"❌ Error parsing email message: {e}")
            return None
    
    def extract_email_body(self, payload):
        """Extract email body from payload based on your working implementation"""
        body = ""
        
        try:
            # Check if payload has parts (multipart)
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                    elif part['mimeType'] == 'text/html' and not body:
                        # Fallback to HTML if no plain text
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Basic HTML cleaning
                            import re
                            body = re.sub('<[^<]+?>', '', body)
            else:
                # Single part message
                if payload['mimeType'] in ['text/plain', 'text/html']:
                    data = payload['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        if payload['mimeType'] == 'text/html':
                            import re
                            body = re.sub('<[^<]+?>', '', body)
        
        except Exception as e:
            print(f"❌ Error extracting email body: {e}")
            body = "Error extracting email content"
        
        return body.strip()
    
    def parse_email_date(self, date_string):
        """Parse email date string to datetime based on your working implementation"""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_string)
        except Exception as e:
            print(f"❌ Error parsing date '{date_string}': {e}")
            return timezone.now()
    
    def fetch_and_store_emails(self, max_emails=10, query='is:unread', filter_support=True):
        """Fetch emails from Gmail and store in Django database with support filtering"""
        try:
            print(f"🚀 Starting email fetch process...")
            
            # Enhanced query for support emails if filtering is enabled
            if filter_support:
                support_terms = ['support', 'query', 'request', 'help', 'assistance', 'issue', 'problem']
                support_query = ' OR '.join([f'subject:"{term}"' for term in support_terms])
                if query == 'is:unread':
                    query = f'is:unread AND ({support_query})'
                else:
                    query = f'({query}) AND ({support_query})'
                print(f"🔍 Using support email filter")
            
            # Get email list
            messages = self.get_email_list(query=query, max_results=max_emails)
            
            if not messages:
                print("📭 No emails found")
                return []
            
            stored_emails = []
            
            for i, message in enumerate(messages, 1):
                print(f"📥 Processing email {i}/{len(messages)}")
                
                # Get email details
                email_data = self.get_email_details(message['id'])
                
                if not email_data:
                    print(f"❌ Failed to get details for email {message['id']}")
                    continue
                
                # Check if email already exists
                if Email.objects.filter(message_id=email_data['message_id']).exists():
                    print(f"⏭️ Email already exists, skipping...")
                    continue
                
                # Additional support filtering if not done by query
                if filter_support:
                    from .services import PerplexityService
                    perplexity = PerplexityService()
                    if not perplexity.is_support_email(email_data['subject'], email_data['body']):
                        print(f"⏭️ Not a support email, skipping...")
                        continue
                
                # Create Email object
                email_obj = Email.objects.create(
                    message_id=email_data['message_id'],
                    subject=email_data['subject'],
                    sender_email=email_data['sender_email'],
                    sender_name=email_data['sender_name'],
                    body=email_data['body'],
                    received_at=email_data['received_at'],
                    thread_id=email_data['thread_id'],
                    snippet=email_data['snippet']
                )
                
                stored_emails.append(email_obj)
                print(f"✅ Stored support email: {email_obj.subject[:50]}...")
            
            print(f"🎉 Successfully processed {len(stored_emails)} support emails")
            return stored_emails
        
        except Exception as e:
            print(f"❌ Error in fetch_and_store_emails: {e}")
            return []
    
    def mark_as_read(self, message_id):
        """Mark email as read in Gmail"""
        try:
            if not self.service:
                if not self.authenticate_gmail():
                    return False
            
            # Remove UNREAD label
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return True
        
        except Exception as e:
            print(f"❌ Error marking email as read: {e}")
            return False
    
    def get_user_profile(self):
        """Get Gmail user profile information"""
        try:
            if not self.service:
                if not self.authenticate_gmail():
                    return None
            
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        
        except Exception as e:
            print(f"❌ Error getting user profile: {e}")
            return None
