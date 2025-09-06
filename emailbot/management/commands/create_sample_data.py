from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from emailbot.models import Email
from emailbot.services import EmailAnalysisService

class Command(BaseCommand):
    help = 'Create sample emails for testing the system'
    
    def handle(self, *args, **options):
        analysis_service = EmailAnalysisService()
        
        sample_emails = [
            {
                'sender_email': 'john.doe@company.com',
                'subject': 'Urgent Support Request - Cannot Access Account',
                'body': 'Hi, I am unable to access my account since yesterday. This is critical as I have an important presentation today. Please help me immediately! My phone number is +1-555-0123.',
                'received_at': timezone.now() - timedelta(hours=2)
            },
            {
                'sender_email': 'sarah.smith@business.org',
                'subject': 'Query about Premium Features',
                'body': 'Hello, I would like to know more about your premium features and pricing. Could you please send me detailed information? Thank you for your excellent service!',
                'received_at': timezone.now() - timedelta(hours=5)
            },
            {
                'sender_email': 'angry.customer@email.com',
                'subject': 'Help - Technical Issue with API',
                'body': 'I am extremely frustrated! Your API has been down for 3 hours and my application is not working. This is causing major issues for my business. Please fix this ASAP! Contact me at +1-555-9876 or backup@email.com',
                'received_at': timezone.now() - timedelta(hours=1)
            },
            {
                'sender_email': 'happy.user@domain.com',
                'subject': 'Request for Documentation',
                'body': 'Hi team! I love using your platform. Could you please provide me with the latest API documentation? I am planning to integrate more features into my application.',
                'received_at': timezone.now() - timedelta(hours=8)
            },
            {
                'sender_email': 'billing.inquiry@corp.com',
                'subject': 'Support - Billing Question',
                'body': 'Hello, I have a question about my recent invoice. The amount seems incorrect. Could someone from billing help me understand the charges? My account number is AC12345.',
                'received_at': timezone.now() - timedelta(hours=12)
            },
            {
                'sender_email': 'tech.admin@startup.io',
                'subject': 'Critical Query - Server Integration',
                'body': 'Urgent: We are experiencing issues with server integration. Our production environment is affected and we need immediate assistance. Please contact me at +1-555-7890. This cannot wait!',
                'received_at': timezone.now() - timedelta(minutes=30)
            }
        ]
        
        created_count = 0
        for email_data in sample_emails:
            # Check if email already exists
            existing = Email.objects.filter(
                sender_email=email_data['sender_email'],
                subject=email_data['subject']
            ).first()
            
            if not existing:
                # Create email
                email_obj = Email.objects.create(**email_data)
                
                # Analyze email
                analysis_service.analyze_email(email_obj)
                
                created_count += 1
                self.stdout.write(f'Created and analyzed: {email_obj.sender_email} - {email_obj.subject}')
            else:
                self.stdout.write(f'Skipped (already exists): {email_data["sender_email"]}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample emails.')
        )
