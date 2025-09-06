# Email Assistant - AI-Powered Communication Assistant

A comprehensive Django-based email management system that intelligently filters, categorizes, prioritizes, and generates responses for support emails using AI.

## 🌟 Features

### ✅ Core Requirements Met

- **Email Retrieval & Filtering**: Fetches emails from Gmail API and filters by support keywords
- **Categorization & Prioritization**: AI-powered sentiment analysis and urgency detection
- **Context-Aware Auto-Responses**: Professional AI-generated responses using Perplexity API
- **Information Extraction**: Extracts contact details, requirements, and technical information
- **Web Dashboard**: Clean, interactive dashboard with real-time analytics

### 🔧 Technical Stack

- **Backend**: Django 5.2.6 + Django REST Framework
- **Database**: PostgreSQL (configurable via environment variables)
- **AI/LLM**: Perplexity API for intelligent email analysis and response generation
- **Frontend**: Bootstrap 5 + Chart.js for interactive dashboard
- **Email API**: Gmail API for email retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Perplexity API key
- Gmail API credentials (optional, for email fetching)

### 1. Installation

```bash
# Clone or download the project
cd email-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here

# PostgreSQL
POSTGRES_DB=email_assistant_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Perplexity API
PERPLEXITY_API_KEY=your-perplexity-api-key

# Gmail API (optional)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
```

### 3. Database Setup

```bash
# Create PostgreSQL database (ensure PostgreSQL is running)
createdb email_assistant_db

# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 4. Run the Application

```bash
# Start development server
python manage.py runserver

# Access the application
# Dashboard: http://localhost:8000/
# Admin Panel: http://localhost:8000/admin/
# API: http://localhost:8000/api/
```

## 📧 Email Processing

### Manual Email Processing (for Testing)

You can manually add emails through the Django admin or API for testing:

1. Go to http://localhost:8000/admin/
2. Add emails in the "Emails" section
3. The system will automatically analyze them

### Gmail Integration (Optional)

For automatic email fetching:

1. Set up Gmail API credentials:
   ```bash
   python manage.py process_emails --setup-gmail
   ```

2. Fetch and analyze emails:
   ```bash
   python manage.py process_emails --fetch-emails --days 1
   ```

## 🎯 API Endpoints

### Emails
- `GET /api/emails/` - List all emails (with filtering)
- `GET /api/emails/{id}/` - Get email details
- `POST /api/emails/{id}/generate_response/` - Generate AI response
- `POST /api/emails/{id}/mark_responded/` - Mark as responded
- `GET /api/emails/urgent/` - Get urgent emails
- `GET /api/emails/pending/` - Get pending emails

### Statistics
- `GET /api/stats/` - List daily statistics
- `GET /api/stats/today/` - Today's statistics
- `GET /api/stats/last_7_days/` - Last 7 days statistics

### Dashboard
- `GET /api/dashboard/overview/` - Complete dashboard data

### Query Parameters (for filtering)
- `priority=urgent|normal`
- `sentiment=positive|negative|neutral`
- `category=technical_issue|account_support|product_inquiry|billing|general`
- `is_urgent=true|false`
- `is_responded=true|false`
- `search=query` (searches sender, subject, body)

## 🎨 Dashboard Features

### Overview Cards
- Total emails received today
- Urgent emails requiring attention
- Pending emails awaiting response
- Responded emails count

### Analytics Charts
- **Sentiment Analysis Pie Chart**: Distribution of positive/negative/neutral emails
- **Category Bar Chart**: Breakdown by email categories

### Email Management
- **Email List**: Recent emails with priority indicators
- **Email Details Modal**: Complete email information with extracted data
- **AI Response**: View and regenerate AI-generated responses
- **Status Management**: Mark emails as responded

### Real-time Features
- Automatic refresh functionality
- Interactive email details
- Dynamic filtering and search

## 🤖 AI Features

### Sentiment Analysis
- Classifies emails as positive, negative, or neutral
- Provides confidence scores
- Uses context-aware analysis

### Priority Detection
- Identifies urgent emails based on keywords and context
- Considers tone and business impact
- Automatic priority queue management

### Category Classification
- Technical Issue
- Account Support
- Product Inquiry
- Billing
- General

### Information Extraction
- Phone numbers
- Alternate email addresses
- Customer requirements
- Deadlines and urgency indicators
- Technical details
- Business context

### Response Generation
- Professional and friendly tone
- Context-aware responses
- Acknowledges customer sentiment
- Provides helpful next steps
- Customizable based on category and priority

## 🔒 Security Features

- Environment variable management for API keys
- Django's built-in security features
- Session-based authentication for dashboard
- API authentication via Django REST Framework

## 📊 Database Schema

### Email Model
- Email metadata (sender, subject, body, timestamp)
- Analysis results (sentiment, priority, category)
- Extracted information (JSON field)
- AI-generated response
- Status tracking

### DailyStats Model
- Daily email counts and breakdowns
- Sentiment and category statistics
- Response tracking

### APIKey Model
- API key management and usage tracking

## 🚀 Deployment

### Environment Variables for Production
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DJANGO_SECRET_KEY=secure-production-key
# ... other production settings
```

### For GitHub Deployment
- All sensitive data is in `.env` file (not committed)
- Add `.env` to `.gitignore`
- Use environment variables in production

## 🛠️ Development

### Adding New Features
1. Extend models in `emailbot/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Update serializers in `emailbot/serializers.py`
4. Add views in `emailbot/views.py`
5. Update templates and JavaScript as needed

### Customizing AI Responses
Modify prompts in `emailbot/services.py`:
- `analyze_email_sentiment()`
- `determine_priority()`
- `categorize_email()`
- `generate_response()`

## 📝 License

This project is developed for the Linkenite Hackathon Challenge.

## 🤝 Support

For issues and questions, please check the admin panel logs or Django debug output when running in development mode.

---

## 🎯 Hackathon Requirements Compliance

✅ **Email Retrieval & Filtering**: Gmail API integration with keyword filtering  
✅ **Categorization & Prioritization**: AI-powered sentiment and priority analysis  
✅ **Context-Aware Auto-Responses**: Perplexity API for professional responses  
✅ **Information Extraction**: Comprehensive data extraction from emails  
✅ **Dashboard Interface**: Modern web dashboard with analytics  
✅ **Django + PostgreSQL**: As requested technology stack  
✅ **API Security**: Environment variable management for GitHub deployment  
✅ **Priority Queue**: Urgent emails processed and displayed first
