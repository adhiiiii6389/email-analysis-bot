import os
import base64
import json
import email
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Email
from .services import EmailAnalysisService

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False


class GmailService:
    """Service for fetching emails from Gmail"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.service = None
        self.analysis_service = EmailAnalysisService()
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        if not GMAIL_AVAILABLE:
            raise ImportError("Gmail API libraries not installed")
        
        creds = None
        token_path = 'token.json'
        credentials_path = 'credentials.json'
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        "credentials.json not found. Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def fetch_support_emails(self, days_back=1):
        """Fetch support emails from Gmail"""
        if not self.service:
            self.authenticate()
        
        try:
            # Build query for support emails
            since_date = datetime.now() - timedelta(days=days_back)
            support_keywords = settings.EMAIL_SUPPORT_KEYWORDS
            
            # Create query string
            keyword_queries = [f'subject:"{keyword}"' for keyword in support_keywords]
            query = f'after:{since_date.strftime("%Y/%m/%d")} AND ({" OR ".join(keyword_queries)})'
            
            print(f"Searching Gmail with query: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            if not messages:
                print("No support emails found")
                return []
            
            print(f"Found {len(messages)} emails to process")
            
            # Process each message
            processed_emails = []
            for message in messages:
                try:
                    email_data = self._process_message(message['id'])
                    if email_data:
                        processed_emails.append(email_data)
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    continue
            
            return processed_emails
            
        except HttpError as error:
            print(f"Gmail API error: {error}")
            return []
    
    def _process_message(self, message_id):
        """Process a single Gmail message"""
        try:
            # Get full message
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            
            # Extract email data
            email_data = self._extract_email_data(message)
            if not email_data:
                return None
            
            # Check if email already exists
            existing_email = Email.objects.filter(
                sender_email=email_data['sender_email'],
                subject=email_data['subject'],
                received_at__date=email_data['received_at'].date()
            ).first()
            
            if existing_email:
                print(f"Email already exists: {email_data['sender_email']}")
                return existing_email
            
            # Create new email object
            email_obj = Email.objects.create(**email_data)
            
            # Analyze the email using AI
            analyzed_email = self.analysis_service.analyze_email(email_obj)
            
            print(f"✅ Processed: {analyzed_email.sender_email} - {analyzed_email.subject[:50]}")
            print(f"   Priority: {analyzed_email.priority}, Sentiment: {analyzed_email.sentiment}")
            
            return analyzed_email
            
        except Exception as e:
            print(f"Error processing message {message_id}: {str(e)}")
            return None
    
    def _extract_email_data(self, message):
        """Extract structured data from Gmail message"""
        try:
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extract headers
            sender_email = ''
            subject = ''
            date_received = None
            
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                
                if name == 'from':
                    # Extract email from "Name <email@domain.com>" format
                    if '<' in value and '>' in value:
                        sender_email = value.split('<')[1].split('>')[0].strip()
                    else:
                        sender_email = value.strip()
                elif name == 'subject':
                    subject = value
                elif name == 'date':
                    try:
                        # Parse email date
                        date_received = email.utils.parsedate_to_datetime(value)
                        if date_received.tzinfo is None:
                            date_received = timezone.make_aware(date_received)
                    except:
                        date_received = timezone.now()
            
            # Extract body
            body = self._extract_body(payload)
            
            if not sender_email or not subject:
                print(f"Missing required fields: sender={sender_email}, subject={subject}")
                return None
            
            return {
                'sender_email': sender_email,
                'subject': subject,
                'body': body,
                'received_at': date_received or timezone.now()
            }
            
        except Exception as e:
            print(f"Error extracting email data: {str(e)}")
            return None
    
    def _extract_body(self, payload):
        """Extract email body from payload"""
        try:
            body = ''
            
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                    elif part['mimeType'] == 'text/html' and 'data' in part['body'] and not body:
                        # Fallback to HTML
                        data = part['body']['data']
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Basic HTML to text conversion
                        import re
                        body = re.sub('<[^<]+?>', '', html_body)
            else:
                # Single part message
                if payload['mimeType'] == 'text/plain' and 'data' in payload['body']:
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                elif payload['mimeType'] == 'text/html' and 'data' in payload['body']:
                    data = payload['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    import re
                    body = re.sub('<[^<]+?>', '', html_body)
            
            return body.strip() if body else "No body content found"
            
        except Exception as e:
            print(f"Error extracting body: {str(e)}")
            return "Error extracting email body"


class EmailSenderService:
    """Service for sending email responses"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_address = os.getenv('SMTP_EMAIL')
        self.email_password = os.getenv('SMTP_PASSWORD')
    
    def send_response(self, email_obj, custom_response=None):
        """Send AI-generated response to an email"""
        if not SMTP_AVAILABLE:
            print("SMTP libraries not available")
            return False
        
        if not self.email_address or not self.email_password:
            print("SMTP credentials not configured in environment variables")
            return False
        
        try:
            # Use custom response or AI-generated response
            response_body = custom_response or email_obj.ai_response
            if not response_body:
                print("No response content available")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = email_obj.sender_email
            msg['Subject'] = f"Re: {email_obj.subject}"
            
            # Email body with professional signature
            full_response = f"""Dear {email_obj.sender_email.split('@')[0].title()},

{response_body}

Best regards,
Customer Support Team
Email Assistant System

---
This is an automated response generated by our AI-powered email assistant.
If you need further assistance, please don't hesitate to contact us.
"""
            
            msg.attach(MIMEText(full_response, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_address, email_obj.sender_email, text)
            server.quit()
            
            # Update email status
            email_obj.is_responded = True
            email_obj.save()
            
            print(f"✅ Response sent to: {email_obj.sender_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email to {email_obj.sender_email}: {str(e)}")
            return False
    
    def send_bulk_responses(self, email_queryset):
        """Send responses to multiple emails"""
        sent_count = 0
        failed_count = 0
        
        for email_obj in email_queryset:
            if email_obj.is_responded:
                print(f"⏭️  Skipping {email_obj.sender_email} - already responded")
                continue
            
            if self.send_response(email_obj):
                sent_count += 1
            else:
                failed_count += 1
        
        print(f"📊 Bulk send complete: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}


class EmailWorkflowService:
    """Complete email processing workflow"""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.sender_service = EmailSenderService()
    
    def process_new_emails(self, days_back=1, auto_respond=False):
        """Complete workflow: fetch -> analyze -> optionally respond"""
        print("🔄 Starting email processing workflow...")
        
        try:
            # Step 1: Fetch emails from Gmail
            print("📥 Fetching emails from Gmail...")
            emails = self.gmail_service.fetch_support_emails(days_back)
            
            if not emails:
                print("ℹ️  No new emails to process")
                return
            
            print(f"📧 Processed {len(emails)} emails")
            
            # Step 2: Prioritize urgent emails
            urgent_emails = [e for e in emails if e.is_urgent]
            normal_emails = [e for e in emails if not e.is_urgent]
            
            print(f"🚨 Urgent emails: {len(urgent_emails)}")
            print(f"📝 Normal emails: {len(normal_emails)}")
            
            # Step 3: Auto-respond if enabled
            if auto_respond:
                print("🤖 Sending automated responses...")
                
                # Respond to urgent emails first
                if urgent_emails:
                    print("🚨 Responding to urgent emails first...")
                    self.sender_service.send_bulk_responses(urgent_emails)
                
                # Then respond to normal emails
                if normal_emails:
                    print("📝 Responding to normal emails...")
                    self.sender_service.send_bulk_responses(normal_emails)
            else:
                print("ℹ️  Auto-respond disabled. Responses generated but not sent.")
            
            # Step 4: Print summary
            self._print_summary(emails)
            
        except Exception as e:
            print(f"❌ Error in email workflow: {str(e)}")
    
    def _print_summary(self, emails):
        """Print processing summary"""
        print("\n" + "="*60)
        print("📊 EMAIL PROCESSING SUMMARY")
        print("="*60)
        
        for email_obj in emails:
            status = "✅ Responded" if email_obj.is_responded else "⏳ Pending"
            priority = "🚨 URGENT" if email_obj.is_urgent else "📝 Normal"
            sentiment = {
                'positive': '😊 Positive',
                'negative': '😞 Negative',
                'neutral': '😐 Neutral'
            }.get(email_obj.sentiment, '❓ Unknown')
            
            print(f"""
From: {email_obj.sender_email}
Subject: {email_obj.subject[:60]}...
Priority: {priority}
Sentiment: {sentiment}
Category: {email_obj.get_category_display() or 'Uncategorized'}
Status: {status}
Response Preview: {(email_obj.ai_response or 'No response')[:100]}...
{'-'*60}""")
        
        print(f"\n📈 Total processed: {len(emails)}")
        print(f"🚨 Urgent: {len([e for e in emails if e.is_urgent])}")
        print(f"✅ Responded: {len([e for e in emails if e.is_responded])}")
        print("="*60)


# Demo function for testing without real Gmail
def create_demo_emails():
    """Create demo emails that simulate real Gmail fetching"""
    demo_emails = [
        {
            'sender_email': 'urgent.customer@company.com',
            'subject': 'URGENT: Cannot access my account - critical business issue',
            'body': '''Hello,
            
I am unable to access my account for the past 3 hours and this is causing major disruption to our business operations. We have an important client presentation in 2 hours and I need access immediately!

This is extremely urgent. Please help ASAP!

My phone: +1-555-0199
Alt email: backup@company.com

Best regards,
John Smith
CEO, TechCorp Inc.''',
            'received_at': timezone.now() - timedelta(minutes=30)
        },
        {
            'sender_email': 'support.query@business.org',
            'subject': 'Support Request: API integration help needed',
            'body': '''Hi Support Team,

I hope you're doing well. I'm working on integrating your API into our application and need some assistance with the authentication process.

Could you please provide:
1. Updated documentation for OAuth2 flow
2. Example code snippets
3. Rate limiting information

This is not urgent, but I would appreciate your help within the next few days.

Thank you for your excellent service!

Sarah Johnson
Developer, BusinessCorp
Phone: +1-555-0234''',
            'received_at': timezone.now() - timedelta(hours=2)
        },
        {
            'sender_email': 'frustrated.user@email.com',
            'subject': 'Help - Your service is down and causing problems!',
            'body': '''This is absolutely ridiculous!

Your service has been down for the entire morning and my team cannot work. We're losing money every minute this continues!

I'm extremely frustrated and disappointed. This is the third outage this month. What are you doing to fix this?

I need:
- Immediate resolution
- Explanation of what happened
- Compensation for downtime

Contact me immediately: +1-555-0987
Alt: emergency@email.com

Mark Wilson
Operations Manager''',
            'received_at': timezone.now() - timedelta(minutes=45)
        },
        {
            'sender_email': 'happy.customer@domain.com',
            'subject': 'Query about new features and pricing',
            'body': '''Hello!

I've been using your service for 6 months now and I absolutely love it! You've made our workflow so much more efficient.

I have a few questions about the new features I saw announced:
1. What's included in the premium plan?
2. When will the new dashboard be available?
3. Are there any discounts for annual subscriptions?

Keep up the great work!

Best,
Lisa Chen
Product Manager, StartupXYZ''',
            'received_at': timezone.now() - timedelta(hours=4)
        }
    ]
    
    analysis_service = EmailAnalysisService()
    created_emails = []
    
    print("🎭 Creating demo emails (simulating Gmail fetch)...")
    
    for email_data in demo_emails:
        # Check if email already exists
        existing = Email.objects.filter(
            sender_email=email_data['sender_email'],
            subject=email_data['subject']
        ).first()
        
        if not existing:
            # Create and analyze email
            email_obj = Email.objects.create(**email_data)
            analyzed_email = analysis_service.analyze_email(email_obj)
            created_emails.append(analyzed_email)
            print(f"✅ Created: {email_obj.sender_email}")
        else:
            created_emails.append(existing)
            print(f"⏭️  Exists: {email_data['sender_email']}")
    
    return created_emails
