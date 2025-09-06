#!/usr/bin/env python3
"""
Email Categorization and Prioritization Module
Performs sentiment analysis and priority classification using Perplexity AI.
"""

import requests
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Priority keywords
URGENT_KEYWORDS = [
    'urgent', 'critical', 'emergency', 'immediately', 'asap', 'cannot access',
    'broken', 'not working', 'down', 'crashed', 'failed', 'error',
    'deadline', 'important', 'escalate', 'priority', 'escalation'
]

class PerplexityAI:
    """Perplexity AI API client for email analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, messages: List[Dict], model: str = "sonar-pro") -> str:
        """Make a request to Perplexity API"""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            return None

class EmailAnalyzer:
    def __init__(self):
        # Initialize Perplexity AI
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY', 'your-perplexity-api-key-here')
        self.ai_client = PerplexityAI(self.perplexity_api_key)
        print("✅ Email Analyzer initialized with Perplexity AI.")
    
    def analyze_email(self, email_data: Dict) -> Dict:
        """
        Perform comprehensive analysis on an email.
        Returns analysis results including sentiment, priority, and category.
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('sender_email', '')
        
        print(f"🔍 Analyzing email: {subject[:50]}...")
        
        # Perform different types of analysis
        sentiment_result = self.analyze_sentiment(subject, body)
        priority_result = self.analyze_priority(subject, body)
        category_result = self.categorize_email(subject, body)
        keywords = self.extract_keywords(subject, body)
        
        # Combine results
        analysis = {
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'sentiment_reasoning': sentiment_result['reasoning'],
            'priority': priority_result['priority'],
            'priority_reasoning': priority_result['reasoning'],
            'category': category_result['category'],
            'category_reasoning': category_result['reasoning'],
            'keywords': keywords,
            'analyzed_at': datetime.now().isoformat()
        }
        
        return analysis
    
    def analyze_sentiment(self, subject: str, body: str) -> Dict:
        """Analyze sentiment of email content using Perplexity AI."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Analyze the sentiment of this email and provide a detailed assessment:

                    Subject: {subject}
                    Body: {body}

                    Please provide your analysis in the following JSON format:
                    {{
                        "sentiment": "positive|negative|neutral",
                        "score": 0.0-1.0,
                        "reasoning": "Brief explanation of why you classified it this way",
                        "key_indicators": ["list", "of", "words", "or", "phrases", "that", "influenced", "decision"]
                    }}

                    Consider:
                    - Overall tone and language used
                    - Emotional indicators (frustration, satisfaction, neutrality)
                    - Urgency and stress levels
                    - Politeness and professionalism
                    - Problem severity if mentioned

                    Respond only with valid JSON.
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Validate and normalize
                    sentiment = result.get('sentiment', 'neutral').lower()
                    if sentiment not in ['positive', 'negative', 'neutral']:
                        sentiment = 'neutral'
                    
                    score = float(result.get('score', 0.5))
                    score = max(0.0, min(1.0, score))  # Clamp between 0 and 1
                    
                    return {
                        'sentiment': sentiment,
                        'score': score,
                        'reasoning': result.get('reasoning', 'No reasoning provided'),
                        'key_indicators': result.get('key_indicators', [])
                    }
            
            # Fallback analysis
            return self._fallback_sentiment_analysis(subject, body)
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._fallback_sentiment_analysis(subject, body)
    
    def analyze_priority(self, subject: str, body: str) -> Dict:
        """Analyze priority level of email using Perplexity AI."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Analyze the priority level of this support email:

                    Subject: {subject}
                    Body: {body}

                    Please classify the priority and provide analysis in this JSON format:
                    {{
                        "priority": "urgent|high|normal|low",
                        "confidence": 0.0-1.0,
                        "reasoning": "Detailed explanation of priority classification",
                        "urgency_indicators": ["list", "of", "factors", "that", "indicate", "urgency"]
                    }}

                    Priority Guidelines:
                    - URGENT: System down, cannot access account, security issues, business-critical deadlines
                    - HIGH: Major functionality impaired, significant business impact, urgent but not critical
                    - NORMAL: General questions, minor issues, feature requests, standard support
                    - LOW: Documentation requests, general inquiries, non-time-sensitive items

                    Consider:
                    - Business impact mentioned
                    - Time sensitivity and deadlines
                    - Keywords indicating urgency
                    - Problem severity
                    - User frustration level

                    Respond only with valid JSON.
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Validate priority
                    priority = result.get('priority', 'normal').lower()
                    if priority not in ['urgent', 'high', 'normal', 'low']:
                        priority = 'normal'
                    
                    confidence = float(result.get('confidence', 0.5))
                    confidence = max(0.0, min(1.0, confidence))
                    
                    return {
                        'priority': priority,
                        'confidence': confidence,
                        'reasoning': result.get('reasoning', 'No reasoning provided'),
                        'urgency_indicators': result.get('urgency_indicators', [])
                    }
            
            # Fallback analysis
            return self._fallback_priority_analysis(subject, body)
            
        except Exception as e:
            logger.error(f"Error in priority analysis: {e}")
            return self._fallback_priority_analysis(subject, body)
    
    def categorize_email(self, subject: str, body: str) -> Dict:
        """Categorize email using Perplexity AI."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Categorize this customer support email:

                    Subject: {subject}
                    Body: {body}

                    Please categorize and provide analysis in this JSON format:
                    {{
                        "category": "category_name",
                        "confidence": 0.0-1.0,
                        "reasoning": "Explanation of why this category was chosen",
                        "subcategory": "specific_subcategory_if_applicable"
                    }}

                    Available Categories:
                    - Technical Support: Bug reports, system errors, functionality issues
                    - Account Support: Login issues, password resets, account access
                    - Sales Inquiry: Pricing questions, feature requests, upgrade inquiries
                    - General Support: How-to questions, general information requests
                    - Complaint: Service dissatisfaction, negative feedback
                    - Feature Request: Suggestions for new features or improvements
                    - Billing Support: Payment issues, invoice questions, subscription matters

                    Consider:
                    - Main intent of the email
                    - Specific problems or requests mentioned
                    - Type of assistance needed
                    - Department that should handle this

                    Respond only with valid JSON.
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    valid_categories = [
                        'Technical Support', 'Account Support', 'Sales Inquiry',
                        'General Support', 'Complaint', 'Feature Request', 'Billing Support'
                    ]
                    
                    category = result.get('category', 'General Support')
                    if category not in valid_categories:
                        category = 'General Support'
                    
                    confidence = float(result.get('confidence', 0.5))
                    confidence = max(0.0, min(1.0, confidence))
                    
                    return {
                        'category': category,
                        'confidence': confidence,
                        'reasoning': result.get('reasoning', 'No reasoning provided'),
                        'subcategory': result.get('subcategory', '')
                    }
            
            # Fallback analysis
            return self._fallback_categorization(subject, body)
            
        except Exception as e:
            logger.error(f"Error in categorization: {e}")
            return self._fallback_categorization(subject, body)
    
    def extract_keywords(self, subject: str, body: str) -> List[str]:
        """Extract relevant keywords from email content."""
        text = f"{subject} {body}".lower()
        
        # Common stop words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
            'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'should'
        }
        
        # Extract words (alphanumeric + some special chars)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', text)
        
        # Filter and deduplicate
        keywords = []
        seen = set()
        
        for word in words:
            word_lower = word.lower()
            if (len(word) >= 3 and 
                word_lower not in stop_words and 
                word_lower not in seen and
                not word_lower.isdigit()):
                keywords.append(word)
                seen.add(word_lower)
        
        return keywords[:20]  # Return top 20 keywords
    
    def _fallback_sentiment_analysis(self, subject: str, body: str) -> Dict:
        """Fallback sentiment analysis using keyword matching."""
        text = f"{subject} {body}".lower()
        
        positive_words = ['thank', 'great', 'excellent', 'good', 'appreciate', 'love', 'perfect', 'awesome']
        negative_words = ['urgent', 'critical', 'problem', 'issue', 'error', 'broken', 'fail', 'cannot', 'wrong']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return {
                'sentiment': 'positive',
                'score': 0.7,
                'reasoning': 'Fallback analysis detected positive keywords',
                'key_indicators': [word for word in positive_words if word in text]
            }
        elif negative_count > positive_count:
            return {
                'sentiment': 'negative',
                'score': 0.7,
                'reasoning': 'Fallback analysis detected negative keywords',
                'key_indicators': [word for word in negative_words if word in text]
            }
        else:
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'reasoning': 'Fallback analysis - no clear sentiment indicators',
                'key_indicators': []
            }
    
    def _fallback_priority_analysis(self, subject: str, body: str) -> Dict:
        """Fallback priority analysis using keyword matching."""
        text = f"{subject} {body}".lower()
        
        urgent_found = [keyword for keyword in URGENT_KEYWORDS if keyword in text]
        
        if urgent_found:
            return {
                'priority': 'urgent',
                'confidence': 0.8,
                'reasoning': f'Fallback analysis found urgent keywords: {", ".join(urgent_found)}',
                'urgency_indicators': urgent_found
            }
        else:
            return {
                'priority': 'normal',
                'confidence': 0.6,
                'reasoning': 'Fallback analysis - no urgent keywords detected',
                'urgency_indicators': []
            }
    
    def _fallback_categorization(self, subject: str, body: str) -> Dict:
        """Fallback categorization using keyword matching."""
        text = f"{subject} {body}".lower()
        
        # Simple keyword-based categorization
        if any(word in text for word in ['login', 'password', 'access', 'account', 'sign in']):
            return {
                'category': 'Account Support',
                'confidence': 0.7,
                'reasoning': 'Fallback analysis detected account-related keywords',
                'subcategory': 'Access Issue'
            }
        elif any(word in text for word in ['price', 'pricing', 'cost', 'plan', 'upgrade', 'subscription']):
            return {
                'category': 'Sales Inquiry',
                'confidence': 0.7,
                'reasoning': 'Fallback analysis detected pricing-related keywords',
                'subcategory': 'Pricing Question'
            }
        elif any(word in text for word in ['bug', 'error', 'broken', 'not working', 'crash']):
            return {
                'category': 'Technical Support',
                'confidence': 0.7,
                'reasoning': 'Fallback analysis detected technical issue keywords',
                'subcategory': 'Bug Report'
            }
        else:
            return {
                'category': 'General Support',
                'confidence': 0.5,
                'reasoning': 'Fallback analysis - no specific category indicators found',
                'subcategory': 'General Inquiry'
            }
    
    def batch_analyze_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Analyze multiple emails in batch.
        Returns a list of analyzed email data with analysis results.
        """
        analyzed_emails = []
        total_emails = len(emails)
        
        print(f"🔄 Starting batch analysis of {total_emails} emails...")
        
        for i, email in enumerate(emails, 1):
            try:
                print(f"📧 Analyzing email {i}/{total_emails}: {email.get('subject', 'No Subject')[:50]}...")
                
                # Perform analysis
                analysis = self.analyze_email(email)
                
                # Combine email data with analysis
                analyzed_email = {
                    **email,  # Original email data
                    'analysis': analysis  # Analysis results
                }
                
                analyzed_emails.append(analyzed_email)
                
            except Exception as e:
                logger.error(f"Error analyzing email {i}: {e}")
                # Add email with error status
                analyzed_email = {
                    **email,
                    'analysis': {
                        'sentiment': 'neutral',
                        'sentiment_score': 0.5,
                        'sentiment_reasoning': f'Analysis failed: {str(e)}',
                        'priority': 'normal',
                        'priority_reasoning': 'Default priority due to analysis failure',
                        'category': 'General Support',
                        'category_reasoning': 'Default category due to analysis failure',
                        'keywords': [],
                        'analyzed_at': datetime.now().isoformat(),
                        'error': str(e)
                    }
                }
                analyzed_emails.append(analyzed_email)
        
        print(f"✅ Batch analysis completed. {len(analyzed_emails)} emails analyzed.")
        return analyzed_emails

# Example usage and testing
if __name__ == "__main__":
    analyzer = EmailAnalyzer()
    
    # Test email
    test_email = {
        'subject': 'URGENT: Cannot access my account',
        'body': 'Hi, I cannot log into my account and have an important deadline today. Please help immediately.',
        'sender_email': 'john@example.com'
    }
    
    print("🧪 Testing Email Analysis with Perplexity AI...")
    result = analyzer.analyze_email(test_email)
    
    print("\n📊 Analysis Results:")
    for key, value in result.items():
        print(f"{key}: {value}")
