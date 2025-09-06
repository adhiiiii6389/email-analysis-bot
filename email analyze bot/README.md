# Email Analyze Bot

Advanced AI-powered email analysis system that automatically retrieves, analyzes, categorizes, and generates responses for support emails using Gmail API, Gemini AI, and PostgreSQL.

## Features

### 🔄 Email Retrieval & Filtering
- Fetches all incoming emails from Gmail account (today's emails only)
- Filters emails with support-related keywords ("Support", "Query", "Request", "Help", etc.)
- Extracts and displays relevant details:
  - Sender's email address and name
  - Subject line
  - Email body content
  - Date/time received

### 📊 Categorization & Prioritization
- **Sentiment Analysis**: Positive / Negative / Neutral using Gemini AI
- **Priority Classification**: Urgent / Normal based on keywords and AI analysis
- **Automatic Categorization**: Technical Issue, Account Support, Product Inquiry, etc.
- **Priority Queue**: Urgent emails processed first

### 🤖 Context-Aware Auto-Responses
- Uses Gemini AI (google-generativeai) to generate professional draft replies
- **RAG (Retrieval-Augmented Generation)** with built-in knowledge base
- Maintains professional and friendly tone
- Context-aware responses based on:
  - Customer sentiment (acknowledges frustration empathetically)
  - Email category and content
  - Extracted customer requirements
- **Responses are stored, not sent automatically**

### 🔍 Information Extraction
- **Contact Details**: Phone numbers, alternate emails, social media
- **Customer Requirements**: Primary requests, deadlines, business impact
- **Technical Information**: Error codes, product versions, browser info
- **Sentiment Indicators**: Positive/negative words, urgency indicators
- **Business Information**: Company mentions, departments, roles

### 💾 PostgreSQL Database Storage
- Comprehensive email storage with full analysis results
- Extracted information with JSONB fields for flexible queries
- Auto-generated responses storage
- Daily statistics tracking
- Optimized with indexes for fast retrieval

## Installation

### Prerequisites
1. **PostgreSQL** installed and running
   - Username: `postgres`
   - Password: `Adhi.`
   - Default database: `postgres`

2. **Gmail API Credentials**
   - Google Cloud Console project with Gmail API enabled
   - Download `client_secret.json` and place in project directory

3. **Python 3.8+**

### Setup Steps

1. **Clone/Download the project**
   ```bash
   cd "email analyze bot"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Gmail API credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create credentials (OAuth 2.0) for desktop application
   - Download as `client_secret.json` and place in project folder

4. **Setup PostgreSQL database**
   ```bash
   python database_setup.py
   ```
   This will:
   - Create `email_analyzer` database
   - Create all required tables with proper schema
   - Set up indexes for performance

5. **Test individual components** (optional)
   ```bash
   # Test email retrieval
   python email_retrieval.py
   
   # Test email analysis
   python email_analyzer.py
   
   # Test response generation
   python response_generator.py
   
   # Test information extraction
   python information_extractor.py
   
   # Test database operations
   python database_manager.py
   ```

## Usage

### Run the Complete Dashboard
```bash
python dashboard.py
```

The dashboard provides:
1. **Complete Analysis Pipeline** - Full automated processing
2. **View Dashboard Data** - Today's email summary
3. **Search Emails** - Search stored emails
4. **Database Summary** - Statistics and overview
5. **Generate Reports** - Create detailed analysis reports

### Manual Component Usage

#### Email Retrieval Only
```bash
python email_retrieval.py
```

#### Analysis Only (requires email data)
```bash
python email_analyzer.py
```

#### Response Generation Only
```bash
python response_generator.py
```

## Configuration

### Database Configuration
Edit `database_manager.py` to change database settings:
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'proj1',
    'user': 'postgres',
    'password': 'Adhi.'
}
```

### Gemini AI Configuration
The Gemini AI API key is already configured in the code:
```python
GEMINI_API_KEY = "AIzaSyD_mF9dR6-5gD_3MU9fCP1yfi_kZVUq1YM"
```

### Support Keywords
Modify `SUPPORT_KEYWORDS` in `email_retrieval.py` to customize filtering:
```python
SUPPORT_KEYWORDS = [
    'support', 'query', 'request', 'help', 'issue', 'problem',
    'assistance', 'trouble', 'error', 'bug', 'complaint'
]
```

## Database Schema

### Tables Created
- **emails**: Main email storage with analysis results
- **extracted_info**: Detailed extracted information (contact, requirements)
- **auto_responses**: Generated AI responses
- **email_stats**: Daily statistics

### Key Features
- JSONB fields for flexible data storage
- Optimized indexes for fast queries
- Foreign key relationships for data integrity
- Automatic timestamp tracking

## File Structure

```
email analyze bot/
├── dashboard.py                 # Main dashboard application
├── email_retrieval.py          # Gmail API email fetching
├── email_analyzer.py           # AI-powered sentiment & categorization
├── response_generator.py       # Context-aware response generation
├── information_extractor.py    # Information extraction from emails
├── database_manager.py         # PostgreSQL database operations
├── database_setup.py           # Database initialization
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── client_secret.json          # Gmail API credentials (you provide)
└── token.json                  # Auto-generated Gmail token
```

## Reports Generated

The system generates comprehensive reports:

### JSON Report
- Complete analysis statistics
- Priority and sentiment breakdowns
- Category distribution
- Top issues identification
- Response generation summary

### Text Report
- Human-readable summary
- Detailed email analysis
- Contact information extracted
- Generated responses preview

## API Usage

### Gemini AI Features Used
- Sentiment analysis with reasoning
- Priority classification
- Email categorization
- Keyword extraction
- Context-aware response generation
- Information extraction

### Gmail API Features Used
- Email retrieval with date filtering
- Header parsing for metadata
- Body content extraction (text/html)
- OAuth 2.0 authentication

## Performance Considerations

- **Batch Processing**: Emails processed in batches for efficiency
- **Database Indexing**: Optimized queries with proper indexes
- **Error Handling**: Robust error handling with fallback methods
- **Rate Limiting**: Respects Gmail API rate limits
- **Memory Management**: Efficient processing of large email volumes

## Security Features

- OAuth 2.0 for Gmail authentication
- Secure database connections
- Input validation and sanitization
- Error logging without sensitive data exposure

## Troubleshooting

### Common Issues

1. **Gmail API Authentication**
   - Ensure `client_secret.json` is correct
   - Check Gmail API is enabled in Google Cloud Console
   - Verify OAuth consent screen is configured

2. **Database Connection**
   - Confirm PostgreSQL is running
   - Check username/password in `DB_CONFIG`
   - Ensure database exists (run `database_setup.py`)

3. **Gemini AI Errors**
   - Verify API key is valid
   - Check internet connection
   - Monitor API quota limits

4. **No Emails Found**
   - System only processes today's emails
   - Ensure there are support-related emails in inbox
   - Check support keywords configuration

## License

This project is created for educational and business automation purposes. Please ensure compliance with Gmail API terms of service and data privacy regulations.

## Support

For issues or questions, please check:
1. Error logs in console output
2. Database connection status
3. Gmail API quotas and limits
4. Gemini AI API status
