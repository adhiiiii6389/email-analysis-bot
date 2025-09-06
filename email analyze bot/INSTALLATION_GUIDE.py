#!/usr/bin/env python3
"""
Installation Guide and Setup Instructions
Complete step-by-step guide to set up the Email Analyze Bot
"""

print("""
🤖 EMAIL ANALYZE BOT - INSTALLATION GUIDE
=" * 60)

📋 WHAT WE'VE CREATED FOR YOU:
================================

✅ Complete Email Analysis System with:
   • Email Retrieval & Filtering (Gmail API)
   • AI-Powered Sentiment Analysis (Gemini AI)
   • Priority Classification (Urgent/Normal)
   • Context-Aware Response Generation
   • Information Extraction (contacts, requirements)
   • PostgreSQL Database Storage
   • Interactive Dashboard

📁 PROJECT STRUCTURE:
===================
email analyze bot/
├── dashboard.py                 # 🖥️ Main dashboard application
├── email_retrieval.py          # 📧 Gmail API email fetching
├── email_analyzer.py           # 🧠 AI sentiment & categorization
├── response_generator.py       # 🤖 Context-aware responses
├── information_extractor.py    # 🔍 Extract contacts & requirements
├── database_manager.py         # 💾 PostgreSQL operations
├── database_setup.py           # ⚙️ Database initialization
├── quick_start.py              # 🚀 Automated setup script
├── requirements.txt            # 📦 Python dependencies
├── client_secret.json          # 🔑 Gmail API credentials
└── README.md                   # 📖 Complete documentation

🔧 SETUP INSTRUCTIONS:
=====================

STEP 1: PostgreSQL Setup
------------------------
1. Install PostgreSQL from https://www.postgresql.org/download/
2. During installation, set a password for the 'postgres' user
3. Update the password in database_manager.py (line 15):
   
   DB_CONFIG = {
       'host': 'localhost',
       'database': 'proj1',
       'user': 'postgres',
       'password': 'YOUR_PASSWORD_HERE'  # Change this
   }

STEP 2: Install Python Dependencies
----------------------------------
Run: pip install -r requirements.txt

This installs:
• google-api-python-client (Gmail API)
• google-generativeai (Gemini AI)
• psycopg2-binary (PostgreSQL)
• python-dateutil (Date handling)

STEP 3: Setup Database
---------------------
Run: python database_setup.py

This creates:
• proj1 database
• All required tables with proper schema
• Indexes for performance

STEP 4: Test Components (Optional)
---------------------------------
• python email_retrieval.py     # Test Gmail connection
• python email_analyzer.py      # Test AI analysis
• python response_generator.py  # Test response generation
• python information_extractor.py  # Test extraction
• python database_manager.py    # Test database

STEP 5: Run the Dashboard
------------------------
Run: python dashboard.py

🎯 MAIN FEATURES:
================

1️⃣ EMAIL RETRIEVAL & FILTERING
   • Fetches today's emails from Gmail
   • Filters support-related emails by keywords
   • Extracts sender, subject, body, timestamps

2️⃣ AI-POWERED ANALYSIS
   • Sentiment: Positive/Negative/Neutral
   • Priority: Urgent/Normal (keyword + AI analysis)
   • Category: Technical Issue, Account Support, etc.
   • Keywords extraction

3️⃣ CONTEXT-AWARE RESPONSES
   • Professional, empathetic responses
   • Knowledge base integration (RAG)
   • Adapts tone based on sentiment
   • Prioritizes urgent emails

4️⃣ INFORMATION EXTRACTION
   • Contact details (phone, alternate emails)
   • Customer requirements and deadlines
   • Technical information (error codes, versions)
   • Business context (company, departments)

5️⃣ DATABASE STORAGE
   • PostgreSQL with optimized schema
   • Full email analysis storage
   • Generated responses (not sent)
   • Daily statistics tracking

📊 DASHBOARD FEATURES:
=====================
• Complete Analysis Pipeline (automated)
• View Today's Email Summary
• Search Stored Emails
• Database Statistics
• Generate Detailed Reports

🔑 API CONFIGURATIONS:
=====================
• Gmail API: Pre-configured with your credentials
• Gemini AI: Using provided API key
• PostgreSQL: Connects to local instance

📈 REPORTS GENERATED:
====================
• JSON report with complete statistics
• Text report with email details
• Priority queue with urgent emails first
• Contact extraction summary
• Response generation summary

🚀 QUICK START:
==============
1. Fix PostgreSQL password in database_manager.py
2. Run: python database_setup.py
3. Run: python dashboard.py
4. Select "Run Complete Analysis Pipeline"

💡 TIPS:
========
• System only processes TODAY'S emails
• Responses are generated but NOT sent automatically
• All data is stored in PostgreSQL for analysis
• Dashboard provides real-time insights
• Urgent emails are prioritized automatically

🛠️ TROUBLESHOOTING:
==================
• Gmail API: Ensure client_secret.json is valid
• PostgreSQL: Check service is running and password is correct
• Gemini AI: Verify internet connection
• No emails: System only checks today's support emails

🎉 YOU'RE ALL SET!
=================
This advanced email analysis system will help you:
• Automatically categorize support emails
• Generate professional responses
• Extract customer information
• Prioritize urgent requests
• Track daily email statistics
• Provide actionable insights

For detailed documentation, see README.md
""")

if __name__ == "__main__":
    pass
