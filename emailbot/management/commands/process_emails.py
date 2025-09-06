from django.core.management.base import BaseCommand
from django.utils import timezone
from emailbot.models import Email
from emailbot.gmail_service import GmailRetriever
from emailbot.services import EmailAnalysisService
import time

class Command(BaseCommand):
    help = 'Fetch emails from Gmail and analyze them using your working implementation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-emails',
            type=int,
            default=10,
            help='Maximum number of emails to process (default: 10)'
        )
        parser.add_argument(
            '--query',
            type=str,
            default='is:unread',
            help='Gmail search query (default: is:unread)'
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze emails with AI after fetching'
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Create demo data instead of fetching real emails'
        )
        parser.add_argument(
            '--auto-respond',
            action='store_true',
            help='Automatically send responses to processed emails'
        )
        parser.add_argument(
            '--priority-queue',
            action='store_true',
            help='Process existing emails in priority order (urgent first)'
        )
        parser.add_argument(
            '--enhanced',
            action='store_true',
            default=True,
            help='Use enhanced AI analysis (default: True)'
        )
        parser.add_argument(
            '--filter-support',
            action='store_true',
            default=True,
            help='Only process support-related emails (default: True)'
        )
        parser.add_argument(
            '--time-filter',
            type=str,
            choices=['today', 'yesterday', 'this-week', 'this-month', 'all'],
            default='today',
            help='Filter emails by time period (default: today)'
        )

    def handle(self, *args, **options):
        if options['demo']:
            self.create_demo_data()
            return
            
        if options.get('priority_queue'):
            self.process_priority_queue(options)
            return
            
        max_emails = options['max_emails']
        query = options['query']
        analyze = options['analyze']
        auto_respond = options.get('auto_respond', False)
        enhanced = options.get('enhanced', True)
        filter_support = options.get('filter_support', True)
        time_filter = options.get('time_filter', 'today')
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting enhanced email processing...')
        )
        self.stdout.write(f'📊 Max emails: {max_emails}')
        self.stdout.write(f'🔍 Query: "{query}"')
        self.stdout.write(f'🤖 AI Analysis: {"Enhanced" if enhanced else "Basic"} {"+ Auto-Respond" if auto_respond else ""}')
        self.stdout.write(f'🎯 Support Filter: {"Enabled" if filter_support else "Disabled"}')
        self.stdout.write(f'📅 Time Filter: {time_filter.upper()}')
        self.stdout.write('-' * 60)
        
        try:
            # Initialize Gmail service with your working implementation
            gmail_service = GmailRetriever()
            
            # Test authentication first
            if not gmail_service.authenticate_gmail():
                self.stdout.write(
                    self.style.ERROR('❌ Gmail authentication failed!')
                )
                self.stdout.write(
                    'Please ensure you have the correct credentials.json file from your working email analyze bot folder.'
                )
                return
            
            # Fetch and store emails
            self.stdout.write('📥 Fetching emails from Gmail...')
            
            # Build time-based query
            time_query = self.build_time_query(time_filter, query)
            self.stdout.write(f'🔍 Using time-filtered query: {time_query[:100]}...')
            
            stored_emails = gmail_service.fetch_and_store_emails(
                max_emails=max_emails,
                query=time_query,
                filter_support=filter_support
            )
            
            if not stored_emails:
                self.stdout.write(
                    self.style.WARNING('📭 No new emails to process')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully fetched {len(stored_emails)} emails')
            )
            
            # Analyze emails with AI if requested
            if analyze:
                self.stdout.write('🤖 Starting AI analysis...')
                analysis_service = EmailAnalysisService()
                
                analyzed_count = 0
                for i, email in enumerate(stored_emails, 1):
                    self.stdout.write(f'🔍 Analyzing email {i}/{len(stored_emails)}: {email.subject[:50]}...')
                    
                    try:
                        analysis_service.analyze_email(email)
                        analyzed_count += 1
                        
                        # Add small delay to avoid rate limiting
                        time.sleep(1)
                        
                        self.stdout.write(
                            f'   ✅ Priority: {email.priority}, Sentiment: {email.sentiment}, Category: {email.category}'
                        )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Analysis failed: {e}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'🎉 Successfully analyzed {analyzed_count}/{len(stored_emails)} emails')
                )
            
            # Summary
            self.stdout.write('-' * 50)
            self.stdout.write(self.style.SUCCESS('📊 PROCESSING SUMMARY'))
            self.stdout.write(f'📥 Emails fetched: {len(stored_emails)}')
            
            if analyze:
                urgent_count = sum(1 for email in stored_emails if email.priority == 'urgent')
                self.stdout.write(f'🚨 Urgent emails: {urgent_count}')
                
                sentiments = {}
                categories = {}
                
                for email in stored_emails:
                    sentiments[email.sentiment] = sentiments.get(email.sentiment, 0) + 1
                    categories[email.category] = categories.get(email.category, 0) + 1
                
                self.stdout.write(f'� Sentiment breakdown: {dict(sentiments)}')
                self.stdout.write(f'📂 Category breakdown: {dict(categories)}')
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Email processing completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during email processing: {e}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def create_demo_data(self):
        """Create demo emails for testing"""
        self.stdout.write(self.style.SUCCESS('🎭 Creating demo data...'))
        
        demo_emails = [
            {
                'subject': 'Urgent: System Down - Cannot Access Application',
                'sender_email': 'john.smith@company.com',
                'sender_name': 'John Smith',
                'body': 'Hi, our entire team cannot access the application. This is affecting our productivity. Please help ASAP!',
                'priority': 'urgent',
                'sentiment': 'negative',
                'category': 'technical_issue',
                'is_urgent': True,
            },
            {
                'subject': 'Thank you for the excellent service!',
                'sender_email': 'sarah.johnson@example.com',
                'sender_name': 'Sarah Johnson',
                'body': 'I wanted to thank your team for the outstanding support. The issue was resolved quickly and professionally.',
                'priority': 'normal',
                'sentiment': 'positive',
                'category': 'general',
                'is_urgent': False,
            },
            {
                'subject': 'Password Reset Request',
                'sender_email': 'mike.wilson@corp.com',
                'sender_name': 'Mike Wilson',
                'body': 'I forgot my password and need to reset it. Can you please help me with the process?',
                'priority': 'normal',
                'sentiment': 'neutral',
                'category': 'account_support',
                'is_urgent': False,
            },
            {
                'subject': 'Billing Question About Monthly Charges',
                'sender_email': 'finance@startup.io',
                'sender_name': 'Finance Team',
                'body': 'We noticed some unexpected charges on our monthly bill. Could you please explain what these are for?',
                'priority': 'normal',
                'sentiment': 'neutral',
                'category': 'billing',
                'is_urgent': False,
            },
            {
                'subject': 'Feature Request: Mobile App Support',
                'sender_email': 'product@techfirm.com',
                'sender_name': 'Product Manager',
                'body': 'Our team would love to see mobile app support. Is this something you have on your roadmap?',
                'priority': 'normal',
                'sentiment': 'positive',
                'category': 'product_inquiry',
                'is_urgent': False,
            },
        ]
        
        # Create demo emails
        for email_data in demo_emails:
            email = Email.objects.create(
                message_id=f"demo_{timezone.now().timestamp()}_{email_data['sender_email']}",
                subject=email_data['subject'],
                sender_email=email_data['sender_email'],
                sender_name=email_data['sender_name'],
                body=email_data['body'],
                received_at=timezone.now(),
                priority=email_data['priority'],
                sentiment=email_data['sentiment'],
                category=email_data['category'],
                is_urgent=email_data['is_urgent'],
                sentiment_confidence=0.85,
                ai_response=f"Thank you for contacting us regarding '{email_data['subject']}'. We have received your message and will respond promptly.",
                response_generated_at=timezone.now(),
                extracted_info={
                    "phone_numbers": [],
                    "alternate_emails": [],
                    "requirements": "Demo requirement",
                    "deadlines": "",
                    "technical_details": "",
                    "business_context": ""
                }
            )
            self.stdout.write(f'✅ Created: {email.subject}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Successfully created {len(demo_emails)} demo emails!')
        )
    
    def process_priority_queue(self, options):
        """Process existing emails in priority order"""
        max_emails = options.get('max_emails', 50)
        auto_respond = options.get('auto_respond', False)
        
        self.stdout.write(
            self.style.SUCCESS('🚨 Processing Priority Queue (Urgent First)...')
        )
        self.stdout.write(f'📊 Max emails to process: {max_emails}')
        self.stdout.write(f'📧 Auto-respond: {"Enabled" if auto_respond else "Disabled"}')
        self.stdout.write('-' * 60)
        
        try:
            analysis_service = EmailAnalysisService()
            processed_emails = analysis_service.process_priority_queue(
                max_emails=max_emails,
                auto_respond=auto_respond
            )
            
            if processed_emails:
                self.display_processing_summary(processed_emails, True, True)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error processing priority queue: {e}')
            )
    
    def display_processing_summary(self, emails, analyzed=False, enhanced=False):
        """Display comprehensive processing summary"""
        self.stdout.write('-' * 60)
        self.stdout.write(self.style.SUCCESS('📊 ENHANCED PROCESSING SUMMARY'))
        self.stdout.write(f'📥 Support emails processed: {len(emails)}')
        
        if analyzed:
            urgent_count = sum(1 for email in emails if email.is_urgent)
            responded_count = sum(1 for email in emails if email.is_responded)
            
            self.stdout.write(f'🚨 Urgent emails: {urgent_count}')
            self.stdout.write(f'📧 Auto-responded: {responded_count}')
            
            # Sentiment breakdown
            sentiments = {}
            categories = {}
            emotional_tones = {}
            
            for email in emails:
                sentiments[email.sentiment] = sentiments.get(email.sentiment, 0) + 1
                categories[email.category] = categories.get(email.category, 0) + 1
                
                if enhanced and email.extracted_info.get('sentiment_analysis'):
                    tone = email.extracted_info['sentiment_analysis'].get('emotional_tone', 'neutral')
                    emotional_tones[tone] = emotional_tones.get(tone, 0) + 1
            
            self.stdout.write(f'😊 Sentiment breakdown: {dict(sentiments)}')
            self.stdout.write(f'📂 Category breakdown: {dict(categories)}')
            
            if enhanced and emotional_tones:
                self.stdout.write(f'🎭 Emotional tones: {dict(emotional_tones)}')
            
            # Show empathy requirements
            if enhanced:
                empathy_required = sum(1 for email in emails 
                                     if email.extracted_info.get('sentiment_analysis', {}).get('empathy_required', False))
                if empathy_required > 0:
                    self.stdout.write(f'💝 Emails requiring empathy: {empathy_required}')
        
        # Get overall statistics
        try:
            analysis_service = EmailAnalysisService()
            stats = analysis_service.get_priority_statistics()
            
            self.stdout.write('\n📈 OVERALL STATISTICS:')
            self.stdout.write(f'📧 Total emails in system: {stats.get("total_emails", 0)}')
            self.stdout.write(f'🚨 Total urgent emails: {stats.get("urgent_emails", 0)}')
            self.stdout.write(f'⏰ Pending urgent emails: {stats.get("pending_urgent", 0)}')
            self.stdout.write(f'⚡ Average response time: {stats.get("avg_response_time", "N/A")}')
            
        except Exception as e:
            self.stdout.write(f'⚠️ Could not fetch statistics: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Enhanced email processing completed successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS(
                '💡 Next steps:\n'
                '  • Visit http://127.0.0.1:8000/ for the enhanced dashboard\n'
                '  • Use --priority-queue to process existing emails\n'
                '  • Use --auto-respond to enable automatic responses'
            )
        )
    
    def build_time_query(self, time_filter, base_query):
        """Build Gmail query with time filtering"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if time_filter == 'today':
            date_str = now.strftime('%Y/%m/%d')
            time_query = f'after:{date_str}'
        elif time_filter == 'yesterday':
            yesterday = now - timedelta(days=1)
            date_str = yesterday.strftime('%Y/%m/%d')
            today_str = now.strftime('%Y/%m/%d')
            time_query = f'after:{date_str} before:{today_str}'
        elif time_filter == 'this-week':
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            monday = now - timedelta(days=days_since_monday)
            date_str = monday.strftime('%Y/%m/%d')
            time_query = f'after:{date_str}'
        elif time_filter == 'this-month':
            # Start of current month
            first_day = now.replace(day=1)
            date_str = first_day.strftime('%Y/%m/%d')
            time_query = f'after:{date_str}'
        else:  # 'all'
            time_query = ''
        
        # Combine with base query
        if time_query and base_query:
            return f'({base_query}) AND {time_query}'
        elif time_query:
            return time_query
        else:
            return base_query
