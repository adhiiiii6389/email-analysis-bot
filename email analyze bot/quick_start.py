#!/usr/bin/env python3
"""
Quick Start Script for Email Analyze Bot
This script helps you get started quickly by checking prerequisites and running setup.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def check_files():
    """Check if required files exist."""
    required_files = [
        'client_secret.json',
        'database_setup.py',
        'email_retrieval.py',
        'email_analyzer.py',
        'response_generator.py',
        'information_extractor.py',
        'database_manager.py',
        'dashboard.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ {file} found")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def check_gmail_credentials():
    """Check if Gmail API credentials are valid."""
    try:
        with open('client_secret.json', 'r') as f:
            credentials = json.load(f)
        
        if 'installed' in credentials and 'client_id' in credentials['installed']:
            print("✅ Gmail API credentials found")
            return True
        else:
            print("❌ Invalid Gmail API credentials format")
            return False
    except Exception as e:
        print(f"❌ Error reading Gmail credentials: {e}")
        return False

def install_requirements():
    """Install Python requirements."""
    try:
        print("📦 Installing Python requirements...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Error installing requirements: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def test_postgresql():
    """Test PostgreSQL connection."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='Adhi.'
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except ImportError:
        print("❌ psycopg2 not installed. Installing requirements first...")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Please ensure PostgreSQL is running with correct credentials:")
        print("   - Host: localhost")
        print("   - User: postgres")
        print("   - Password: Adhi.")
        return False

def setup_database():
    """Setup the database."""
    try:
        print("🗄️ Setting up database...")
        result = subprocess.run([sys.executable, 'database_setup.py'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database setup completed")
            return True
        else:
            print(f"❌ Database setup failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def test_gemini_ai():
    """Test Gemini AI connection."""
    try:
        import google.generativeai as genai
        genai.configure(api_key="AIzaSyD_mF9dR6-5gD_3MU9fCP1yfi_kZVUq1YM")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Simple test
        response = model.generate_content("Hello, this is a test.")
        
        if response.text:
            print("✅ Gemini AI connection successful")
            return True
        else:
            print("❌ Gemini AI response empty")
            return False
    except ImportError:
        print("❌ google-generativeai not installed")
        return False
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {e}")
        return False

def run_dashboard():
    """Launch the dashboard."""
    try:
        print("🚀 Launching Email Analyze Bot Dashboard...")
        subprocess.run([sys.executable, 'dashboard.py'])
    except KeyboardInterrupt:
        print("\n⚠️ Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

def main():
    """Main setup function."""
    print("🤖 EMAIL ANALYZE BOT - QUICK START")
    print("=" * 60)
    
    # Check prerequisites
    print("\n🔍 CHECKING PREREQUISITES...")
    print("-" * 40)
    
    if not check_python_version():
        return
    
    if not check_files():
        return
    
    if not check_gmail_credentials():
        print("\n📧 Gmail API Setup Required:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable Gmail API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download as 'client_secret.json'")
        return
    
    # Install requirements
    print("\n📦 INSTALLING DEPENDENCIES...")
    print("-" * 40)
    
    if not install_requirements():
        return
    
    # Test connections
    print("\n🔌 TESTING CONNECTIONS...")
    print("-" * 40)
    
    if not test_postgresql():
        return
    
    if not test_gemini_ai():
        return
    
    # Setup database
    print("\n🗄️ SETTING UP DATABASE...")
    print("-" * 40)
    
    if not setup_database():
        return
    
    print("\n✅ SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    # Ask if user wants to run dashboard
    choice = input("\nWould you like to run the dashboard now? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        run_dashboard()
    else:
        print("\n🎉 Setup complete! You can run the dashboard anytime with:")
        print("   python dashboard.py")

if __name__ == "__main__":
    main()
