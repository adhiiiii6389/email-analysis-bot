#!/usr/bin/env python3
"""
Database Setup for Email Analyzer Bot
Creates PostgreSQL tables for storing email data and analysis results.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Adhi'
}

def create_connection():
    """Create a connection to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def create_database():
    """Create the email_analyzer database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'proj1'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE proj1')
            print("✅ Database 'proj1' created successfully!")
        else:
            print("ℹ️ Database 'proj1' already exists.")
        
        cursor.close()
        conn.close()
        
        # Update DB_CONFIG to use the new database
        DB_CONFIG['database'] = 'proj1'
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def create_tables():
    """Create all necessary tables for the email analyzer."""
    
    tables = {
        'emails': '''
            CREATE TABLE IF NOT EXISTS emails (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR(255) UNIQUE NOT NULL,
                sender_email VARCHAR(255) NOT NULL,
                sender_name VARCHAR(255),
                subject TEXT NOT NULL,
                body TEXT,
                received_date TIMESTAMP WITH TIME ZONE NOT NULL,
                processed_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_support_related BOOLEAN DEFAULT FALSE,
                priority VARCHAR(20) DEFAULT 'normal',
                sentiment VARCHAR(20),
                sentiment_score FLOAT,
                category VARCHAR(100),
                keywords TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        'extracted_info': '''
            CREATE TABLE IF NOT EXISTS extracted_info (
                id SERIAL PRIMARY KEY,
                email_id INTEGER REFERENCES emails(id) ON DELETE CASCADE,
                phone_numbers TEXT[],
                alternate_emails TEXT[],
                customer_requirements TEXT,
                sentiment_indicators JSONB,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        'auto_responses': '''
            CREATE TABLE IF NOT EXISTS auto_responses (
                id SERIAL PRIMARY KEY,
                email_id INTEGER REFERENCES emails(id) ON DELETE CASCADE,
                response_subject TEXT NOT NULL,
                response_body TEXT NOT NULL,
                generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_sent BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP WITH TIME ZONE,
                model_used VARCHAR(50) DEFAULT 'gemini-2.5-flash'
            )
        ''',
        
        'email_stats': '''
            CREATE TABLE IF NOT EXISTS email_stats (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_emails INTEGER DEFAULT 0,
                support_emails INTEGER DEFAULT 0,
                urgent_emails INTEGER DEFAULT 0,
                positive_sentiment INTEGER DEFAULT 0,
                negative_sentiment INTEGER DEFAULT 0,
                neutral_sentiment INTEGER DEFAULT 0,
                responses_generated INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        '''
    }
    
    conn = create_connection()
    if not conn:
        print("❌ Failed to connect to database.")
        return False
    
    try:
        cursor = conn.cursor()
        
        for table_name, table_sql in tables.items():
            cursor.execute(table_sql)
            print(f"✅ Table '{table_name}' created/verified successfully!")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_emails_received_date ON emails(received_date)",
            "CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email)",
            "CREATE INDEX IF NOT EXISTS idx_emails_priority ON emails(priority)",
            "CREATE INDEX IF NOT EXISTS idx_emails_sentiment ON emails(sentiment)",
            "CREATE INDEX IF NOT EXISTS idx_emails_support ON emails(is_support_related)",
            "CREATE INDEX IF NOT EXISTS idx_email_stats_date ON email_stats(date)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Database indexes created successfully!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False

def test_connection():
    """Test the database connection."""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL connection successful!")
            print(f"📊 Database version: {version[0]}")
            cursor.close()
            conn.close()
            return True
        except psycopg2.Error as e:
            print(f"❌ Error testing connection: {e}")
            return False
    return False

def main():
    """Main function to set up the database."""
    print("🗄️ Email Analyzer Database Setup")
    print("=" * 50)
    
    # Test initial connection
    print("1. Testing PostgreSQL connection...")
    if not test_connection():
        print("❌ Please check your PostgreSQL installation and credentials.")
        return
    
    # Create database
    print("\n2. Creating email_analyzer database...")
    create_database()
    
    # Create tables
    print("\n3. Creating database tables...")
    if create_tables():
        print("\n🎉 Database setup completed successfully!")
        print("The following tables were created:")
        print("  - emails: Main email storage")
        print("  - extracted_info: Extracted information from emails")
        print("  - auto_responses: Generated AI responses")
        print("  - email_stats: Daily email statistics")
    else:
        print("❌ Database setup failed!")

if __name__ == "__main__":
    main()
