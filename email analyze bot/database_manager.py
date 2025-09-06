#!/usr/bin/env python3
"""
Database Manager Module
Handles all database operations for storing email data and analysis results.
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime, date
import json
from typing import Dict, List, Optional, Tuple

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'proj1',
    'user': 'postgres',
    'password': 'Adhi'
}

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected to PostgreSQL database successfully!")
        except psycopg2.Error as e:
            print(f"❌ Error connecting to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed.")
    
    def execute_query(self, query: str, params: Tuple = None, fetch: bool = True) -> Optional[List]:
        """Execute a database query and return results."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                if fetch and cursor.description:
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return None
                    
        except psycopg2.Error as e:
            print(f"❌ Database query error: {e}")
            self.connection.rollback()
            raise
    
    def store_email(self, email_data: Dict) -> Optional[int]:
        """
        Store email data in the database.
        
        Args:
            email_data: Dictionary containing email information
        
        Returns:
            Email ID if successful, None otherwise
        """
        try:
            query = """
                INSERT INTO emails (
                    message_id, sender_email, sender_name, subject, body,
                    received_date, is_support_related, priority, sentiment,
                    sentiment_score, category, keywords
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
            """
            
            params = (
                email_data.get('message_id'),
                email_data.get('sender_email'),
                email_data.get('sender_name'),
                email_data.get('subject'),
                email_data.get('body'),
                email_data.get('received_date'),
                email_data.get('is_support_related', False),
                email_data.get('priority', 'normal'),
                email_data.get('sentiment', 'neutral'),
                email_data.get('sentiment_score', 0.5),
                email_data.get('category', 'General Support'),
                email_data.get('keywords', [])
            )
            
            result = self.execute_query(query, params, fetch=True)
            
            if result:
                email_id = result[0]['id']
                print(f"✅ Email stored with ID: {email_id}")
                return email_id
            
        except Exception as e:
            print(f"⚠️ Error storing email: {e}")
            return None
    
    def store_extracted_info(self, email_id: int, extracted_info: Dict) -> bool:
        """
        Store extracted information for an email.
        
        Args:
            email_id: ID of the email
            extracted_info: Dictionary containing extracted information
        
        Returns:
            True if successful, False otherwise
        """
        try:
            contact_details = extracted_info.get('contact_details', {})
            requirements = extracted_info.get('customer_requirements', {})
            sentiment_indicators = extracted_info.get('sentiment_indicators', {})
            technical_info = extracted_info.get('technical_information', {})
            business_info = extracted_info.get('business_information', {})
            metadata = extracted_info.get('extraction_metadata', {})
            
            query = """
                INSERT INTO extracted_info (
                    email_id, phone_numbers, alternate_emails, customer_requirements,
                    sentiment_indicators, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
            """
            
            # Combine all metadata
            combined_metadata = {
                'technical_information': technical_info,
                'business_information': business_info,
                'extraction_metadata': metadata
            }
            
            params = (
                email_id,
                contact_details.get('phone_numbers', []),
                contact_details.get('alternate_emails', []),
                requirements.get('primary_request', ''),
                Json(sentiment_indicators),
                Json(combined_metadata)
            )
            
            self.execute_query(query, params, fetch=False)
            print(f"✅ Extracted info stored for email ID: {email_id}")
            return True
            
        except Exception as e:
            print(f"⚠️ Error storing extracted info: {e}")
            return False
    
    def store_auto_response(self, email_id: int, response_data: Dict) -> bool:
        """
        Store auto-generated response for an email.
        
        Args:
            email_id: ID of the email
            response_data: Dictionary containing response information
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO auto_responses (
                    email_id, response_subject, response_body, generated_at,
                    is_sent, model_used
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
            """
            
            generated_at = response_data.get('generated_at')
            if isinstance(generated_at, str):
                generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            elif generated_at is None:
                generated_at = datetime.now()
            
            params = (
                email_id,
                response_data.get('response_subject'),
                response_data.get('response_body'),
                generated_at,
                False,  # is_sent - we don't send, just store
                response_data.get('model_used', 'gemini-2.5-flash')
            )
            
            self.execute_query(query, params, fetch=False)
            print(f"✅ Auto-response stored for email ID: {email_id}")
            return True
            
        except Exception as e:
            print(f"⚠️ Error storing auto-response: {e}")
            return False
    
    def store_complete_email_analysis(self, email_data: Dict) -> Optional[int]:
        """
        Store complete email analysis including all related data.
        
        Args:
            email_data: Complete email data with analysis and extraction
        
        Returns:
            Email ID if successful, None otherwise
        """
        try:
            # Store main email data
            email_id = self.store_email(email_data)
            
            if not email_id:
                return None
            
            # Store extracted information if available
            if 'extracted_info' in email_data:
                self.store_extracted_info(email_id, email_data['extracted_info'])
            
            # Store auto-response if available
            if 'response_subject' in email_data and 'response_body' in email_data:
                response_data = {
                    'response_subject': email_data.get('response_subject'),
                    'response_body': email_data.get('response_body'),
                    'generated_at': email_data.get('generated_at'),
                    'model_used': email_data.get('model_used')
                }
                self.store_auto_response(email_id, response_data)
            
            return email_id
            
        except Exception as e:
            print(f"⚠️ Error storing complete email analysis: {e}")
            return None
    
    def batch_store_emails(self, emails_data: List[Dict]) -> List[int]:
        """
        Store multiple emails in batch.
        
        Args:
            emails_data: List of email data dictionaries
        
        Returns:
            List of email IDs that were successfully stored
        """
        print(f"💾 Storing {len(emails_data)} emails to database...")
        
        stored_ids = []
        
        for i, email_data in enumerate(emails_data, 1):
            print(f"💾 Storing email {i}/{len(emails_data)}: {email_data.get('subject', 'No Subject')[:30]}...")
            
            email_id = self.store_complete_email_analysis(email_data)
            
            if email_id:
                stored_ids.append(email_id)
            else:
                print(f"⚠️ Failed to store email {i}")
        
        print(f"✅ Successfully stored {len(stored_ids)} out of {len(emails_data)} emails.")
        return stored_ids
    
    def update_daily_stats(self, analysis_date: date = None) -> bool:
        """
        Update daily email statistics.
        
        Args:
            analysis_date: Date for which to update stats (default: today)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # Get statistics for the date
            stats_query = """
                SELECT 
                    COUNT(*) as total_emails,
                    COUNT(*) FILTER (WHERE is_support_related = true) as support_emails,
                    COUNT(*) FILTER (WHERE priority = 'urgent') as urgent_emails,
                    COUNT(*) FILTER (WHERE sentiment = 'positive') as positive_sentiment,
                    COUNT(*) FILTER (WHERE sentiment = 'negative') as negative_sentiment,
                    COUNT(*) FILTER (WHERE sentiment = 'neutral') as neutral_sentiment
                FROM emails 
                WHERE DATE(received_date) = %s
            """
            
            stats_result = self.execute_query(stats_query, (analysis_date,), fetch=True)
            
            if not stats_result:
                return False
            
            stats = stats_result[0]
            
            # Count generated responses
            responses_query = """
                SELECT COUNT(*) as responses_generated
                FROM auto_responses ar
                JOIN emails e ON ar.email_id = e.id
                WHERE DATE(e.received_date) = %s
            """
            
            responses_result = self.execute_query(responses_query, (analysis_date,), fetch=True)
            responses_count = responses_result[0]['responses_generated'] if responses_result else 0
            
            # Insert or update daily stats
            upsert_query = """
                INSERT INTO email_stats (
                    date, total_emails, support_emails, urgent_emails,
                    positive_sentiment, negative_sentiment, neutral_sentiment,
                    responses_generated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (date) DO UPDATE SET
                    total_emails = EXCLUDED.total_emails,
                    support_emails = EXCLUDED.support_emails,
                    urgent_emails = EXCLUDED.urgent_emails,
                    positive_sentiment = EXCLUDED.positive_sentiment,
                    negative_sentiment = EXCLUDED.negative_sentiment,
                    neutral_sentiment = EXCLUDED.neutral_sentiment,
                    responses_generated = EXCLUDED.responses_generated
            """
            
            params = (
                analysis_date,
                stats['total_emails'],
                stats['support_emails'],
                stats['urgent_emails'],
                stats['positive_sentiment'],
                stats['negative_sentiment'],
                stats['neutral_sentiment'],
                responses_count
            )
            
            self.execute_query(upsert_query, params, fetch=False)
            print(f"✅ Daily stats updated for {analysis_date}")
            return True
            
        except Exception as e:
            print(f"⚠️ Error updating daily stats: {e}")
            return False
    
    def get_email_dashboard_data(self, analysis_date: date = None) -> Dict:
        """
        Get dashboard data for email analysis.
        
        Args:
            analysis_date: Date for which to get data (default: today)
        
        Returns:
            Dictionary containing dashboard data
        """
        try:
            if analysis_date is None:
                analysis_date = date.today()
            
            # Get emails for the date
            emails_query = """
                SELECT 
                    e.id, e.sender_email, e.sender_name, e.subject, e.body,
                    e.received_date, e.is_support_related, e.priority, e.sentiment,
                    e.sentiment_score, e.category, e.keywords,
                    ei.phone_numbers, ei.alternate_emails, ei.customer_requirements,
                    ar.response_subject, ar.response_body, ar.generated_at as response_generated_at
                FROM emails e
                LEFT JOIN extracted_info ei ON e.id = ei.email_id
                LEFT JOIN auto_responses ar ON e.id = ar.email_id
                WHERE DATE(e.received_date) = %s AND e.is_support_related = true
                ORDER BY 
                    CASE WHEN e.priority = 'urgent' THEN 0 ELSE 1 END,
                    e.received_date DESC
            """
            
            emails_data = self.execute_query(emails_query, (analysis_date,), fetch=True)
            
            # Get daily statistics
            stats_query = """
                SELECT * FROM email_stats WHERE date = %s
            """
            
            stats_data = self.execute_query(stats_query, (analysis_date,), fetch=True)
            stats = stats_data[0] if stats_data else {}
            
            # Prepare dashboard data
            dashboard_data = {
                'date': analysis_date.isoformat(),
                'statistics': {
                    'total_emails': stats.get('total_emails', 0),
                    'support_emails': stats.get('support_emails', 0),
                    'urgent_emails': stats.get('urgent_emails', 0),
                    'positive_sentiment': stats.get('positive_sentiment', 0),
                    'negative_sentiment': stats.get('negative_sentiment', 0),
                    'neutral_sentiment': stats.get('neutral_sentiment', 0),
                    'responses_generated': stats.get('responses_generated', 0)
                },
                'emails': []
            }
            
            # Process email data for dashboard
            for email in emails_data or []:
                email_dict = dict(email)
                # Convert datetime objects to strings
                if email_dict.get('received_date'):
                    email_dict['received_date'] = email_dict['received_date'].isoformat()
                if email_dict.get('response_generated_at'):
                    email_dict['response_generated_at'] = email_dict['response_generated_at'].isoformat()
                
                dashboard_data['emails'].append(email_dict)
            
            return dashboard_data
            
        except Exception as e:
            print(f"⚠️ Error getting dashboard data: {e}")
            return {'date': analysis_date.isoformat(), 'statistics': {}, 'emails': []}
    
    def search_emails(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search emails by subject, body, or sender.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
        
        Returns:
            List of matching emails
        """
        try:
            query = """
                SELECT 
                    e.id, e.sender_email, e.sender_name, e.subject, e.body,
                    e.received_date, e.priority, e.sentiment, e.category
                FROM emails e
                WHERE 
                    e.subject ILIKE %s OR 
                    e.body ILIKE %s OR 
                    e.sender_email ILIKE %s OR
                    e.sender_name ILIKE %s
                ORDER BY e.received_date DESC
                LIMIT %s
            """
            
            search_pattern = f"%{search_term}%"
            params = (search_pattern, search_pattern, search_pattern, search_pattern, limit)
            
            results = self.execute_query(query, params, fetch=True)
            
            # Convert to list of dictionaries
            emails = []
            for email in results or []:
                email_dict = dict(email)
                if email_dict.get('received_date'):
                    email_dict['received_date'] = email_dict['received_date'].isoformat()
                emails.append(email_dict)
            
            return emails
            
        except Exception as e:
            print(f"⚠️ Error searching emails: {e}")
            return []
    
    def get_email_by_id(self, email_id: int) -> Optional[Dict]:
        """
        Get complete email data by ID.
        
        Args:
            email_id: Email ID
        
        Returns:
            Complete email data or None
        """
        try:
            query = """
                SELECT 
                    e.*, 
                    ei.phone_numbers, ei.alternate_emails, ei.customer_requirements,
                    ei.sentiment_indicators, ei.metadata,
                    ar.response_subject, ar.response_body, ar.generated_at as response_generated_at
                FROM emails e
                LEFT JOIN extracted_info ei ON e.id = ei.email_id
                LEFT JOIN auto_responses ar ON e.id = ar.email_id
                WHERE e.id = %s
            """
            
            result = self.execute_query(query, (email_id,), fetch=True)
            
            if result:
                email_data = dict(result[0])
                # Convert datetime objects to strings
                for key in ['received_date', 'processed_date', 'created_at', 'response_generated_at']:
                    if email_data.get(key):
                        email_data[key] = email_data[key].isoformat()
                return email_data
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting email by ID: {e}")
            return None
    
    def display_database_summary(self):
        """Display a summary of database contents."""
        try:
            print(f"\n💾 DATABASE SUMMARY")
            print("=" * 50)
            
            # Get total counts
            counts_query = """
                SELECT 
                    (SELECT COUNT(*) FROM emails) as total_emails,
                    (SELECT COUNT(*) FROM emails WHERE is_support_related = true) as support_emails,
                    (SELECT COUNT(*) FROM emails WHERE priority = 'urgent') as urgent_emails,
                    (SELECT COUNT(*) FROM extracted_info) as extracted_records,
                    (SELECT COUNT(*) FROM auto_responses) as auto_responses
            """
            
            counts = self.execute_query(counts_query, fetch=True)[0]
            
            print(f"Total emails: {counts['total_emails']}")
            print(f"Support emails: {counts['support_emails']}")
            print(f"Urgent emails: {counts['urgent_emails']}")
            print(f"Extracted info records: {counts['extracted_records']}")
            print(f"Auto-responses generated: {counts['auto_responses']}")
            
            # Get recent activity
            recent_query = """
                SELECT DATE(received_date) as date, COUNT(*) as count
                FROM emails 
                WHERE received_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(received_date)
                ORDER BY date DESC
                LIMIT 7
            """
            
            recent_data = self.execute_query(recent_query, fetch=True)
            
            if recent_data:
                print(f"\nRecent activity (last 7 days):")
                for row in recent_data:
                    print(f"  {row['date']}: {row['count']} emails")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"⚠️ Error displaying database summary: {e}")

def main():
    """Main function for testing database operations."""
    print("💾 Database Manager Test")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Display current database summary
    db_manager.display_database_summary()
    
    # Test with sample data
    sample_email = {
        'message_id': 'test_message_123',
        'sender_email': 'test@example.com',
        'sender_name': 'Test User',
        'subject': 'Test Email Subject',
        'body': 'This is a test email body for database testing.',
        'received_date': datetime.now(),
        'is_support_related': True,
        'priority': 'normal',
        'sentiment': 'neutral',
        'sentiment_score': 0.5,
        'category': 'General Support',
        'keywords': ['test', 'email', 'database'],
        'extracted_info': {
            'contact_details': {
                'phone_numbers': ['(555) 123-4567'],
                'alternate_emails': ['alt@example.com']
            },
            'customer_requirements': {
                'primary_request': 'Test request',
                'requested_actions': ['Test action']
            },
            'sentiment_indicators': {},
            'technical_information': {},
            'business_information': {},
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'confidence_score': 0.8
            }
        },
        'response_subject': 'Re: Test Email Subject',
        'response_body': 'Thank you for your test email. This is an automated response.',
        'generated_at': datetime.now().isoformat(),
        'model_used': 'gemini-2.5-flash'
    }
    
    print(f"\nTesting database operations...")
    
    # Store test email
    email_id = db_manager.store_complete_email_analysis(sample_email)
    
    if email_id:
        print(f"✅ Test email stored with ID: {email_id}")
        
        # Update daily stats
        db_manager.update_daily_stats()
        
        # Get dashboard data
        dashboard_data = db_manager.get_email_dashboard_data()
        print(f"✅ Dashboard data retrieved: {len(dashboard_data['emails'])} emails")
        
        # Search for the test email
        search_results = db_manager.search_emails('test')
        print(f"✅ Search completed: {len(search_results)} results found")
    
    # Close connection
    db_manager.disconnect()

if __name__ == "__main__":
    main()
