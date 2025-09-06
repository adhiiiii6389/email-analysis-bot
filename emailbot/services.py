import os
import re
import json
import requests
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Email, DailyStats

class PerplexityAI:
    """Perplexity AI API client for email analysis and response generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, messages, model="sonar-pro"):
        """Make a request to Perplexity API"""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling Perplexity API: {e}")
            return None

class PerplexityService:
    """Enhanced service for interacting with Perplexity API with improved analysis"""
    
    def __init__(self):
        # Use environment variable for API key
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        self.ai_client = PerplexityAI(self.api_key)
        
        # Enhanced filtering keywords for support emails
        self.support_keywords = [
            'support', 'query', 'request', 'help', 'assistance', 'issue', 'problem',
            'question', 'inquiry', 'ticket', 'bug', 'error', 'feature', 'feedback'
        ]
        
        # Enhanced priority keywords with categories
        self.urgent_keywords = [
            'urgent', 'critical', 'emergency', 'immediately', 'asap', 'cannot access',
            'broken', 'not working', 'down', 'crashed', 'failed', 'error',
            'deadline', 'important', 'escalate', 'priority', 'escalation',
            'production', 'outage', 'security', 'breach', 'hack', 'compromised'
        ]
        
        # Sentiment indicators for enhanced analysis
        self.positive_indicators = [
            'thank', 'thanks', 'grateful', 'appreciate', 'excellent', 'great',
            'good', 'satisfied', 'happy', 'pleased', 'wonderful', 'awesome',
            'love', 'perfect', 'amazing', 'fantastic'
        ]
        
        self.negative_indicators = [
            'frustrated', 'angry', 'disappointed', 'upset', 'annoyed', 'terrible',
            'awful', 'horrible', 'hate', 'worst', 'useless', 'broken', 'failed',
            'crash', 'bug', 'error', 'problem', 'issue', 'complaint'
        ]
        
        # Knowledge base for context-aware responses
        self.knowledge_base = {
            'account_support': {
                'common_issues': ['password reset', 'login problems', 'account locked', 'two-factor authentication'],
                'solutions': {
                    'password': 'You can reset your password by clicking the "Forgot Password" link on our login page.',
                    'login': 'Please clear your browser cache and cookies, then try logging in again.',
                    'locked': 'Your account may be temporarily locked for security. Please wait 15 minutes and try again.',
                    '2fa': 'If you\'re having trouble with two-factor authentication, please contact our security team.'
                }
            },
            'technical_issue': {
                'common_issues': ['server errors', 'loading problems', 'feature not working', 'data sync'],
                'solutions': {
                    'server': 'We\'re aware of intermittent server issues and our team is working on a fix.',
                    'loading': 'Try refreshing the page or clearing your browser cache.',
                    'feature': 'Please provide specific details about which feature isn\'t working.',
                    'sync': 'Data synchronization can take up to 15 minutes. Please wait and try again.'
                }
            },
            'billing': {
                'common_issues': ['payment failed', 'refund request', 'subscription changes', 'invoice questions'],
                'solutions': {
                    'payment': 'Please check that your payment method is valid and has sufficient funds.',
                    'refund': 'Refund requests are processed within 5-7 business days.',
                    'subscription': 'You can change your subscription plan in your account settings.',
                    'invoice': 'All invoices are available in your account dashboard under Billing.'
                }
            },
            'product_inquiry': {
                'common_issues': ['pricing questions', 'feature requests', 'upgrade options', 'comparisons'],
                'solutions': {
                    'pricing': 'Our pricing plans are available on our website with detailed feature comparisons.',
                    'feature': 'We appreciate your feedback and will consider this for future updates.',
                    'upgrade': 'You can upgrade your plan anytime from your account settings.',
                    'comparison': 'Please visit our pricing page for a detailed feature comparison.'
                }
            }
        }
    
    def is_support_email(self, subject, body):
        """Check if email qualifies as a support email based on keywords"""
        full_text = f"{subject} {body}".lower()
        return any(keyword in full_text for keyword in self.support_keywords)
    
    def analyze_email_sentiment(self, email_text, sender_email="", enhanced=True):
        """Enhanced sentiment analysis with context awareness"""
        try:
            if enhanced:
                # Enhanced prompt with better context
                messages = [
                    {
                        "role": "user",
                        "content": f"""
                        Analyze the sentiment and emotional tone of this customer support email with high accuracy:

                        Email: {email_text}
                        From: {sender_email}

                        Please provide detailed analysis in this JSON format:
                        {{
                            "sentiment": "positive|negative|neutral",
                            "confidence": 0.0-1.0,
                            "emotional_tone": "frustrated|satisfied|confused|urgent|polite|angry|grateful",
                            "intensity": "low|medium|high",
                            "key_indicators": ["word1", "word2"],
                            "customer_mood": "Brief description of customer's mood",
                            "empathy_required": true|false,
                            "reasoning": "Detailed explanation of analysis"
                        }}

                        Consider:
                        - Overall tone, language patterns, and emotional indicators
                        - Level of frustration, satisfaction, or urgency
                        - Politeness vs aggressiveness
                        - Whether empathetic response is needed
                        - Context clues about customer's experience

                        Respond only with valid JSON.
                        """
                    }
                ]
            else:
                # Fallback to original prompt
                messages = [
                    {
                        "role": "user",
                        "content": f"""
                        Analyze the sentiment of this email and provide a detailed assessment:

                        Email: {email_text}

                        Please provide your analysis in the following JSON format:
                        {{
                            "sentiment": "positive|negative|neutral",
                            "score": 0.0-1.0,
                            "reasoning": "Brief explanation of why you classified it this way"
                        }}

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
                    
                    # Normalize sentiment
                    sentiment = result.get('sentiment', 'neutral').lower()
                    if sentiment not in ['positive', 'negative', 'neutral']:
                        sentiment = 'neutral'
                    
                    # Get confidence score
                    confidence = result.get('confidence') or result.get('score', 0.5)
                    confidence = max(0.0, min(1.0, float(confidence)))
                    
                    # Enhanced response
                    if enhanced and 'emotional_tone' in result:
                        return {
                            "sentiment": sentiment,
                            "confidence": confidence,
                            "emotional_tone": result.get('emotional_tone', 'neutral'),
                            "intensity": result.get('intensity', 'medium'),
                            "key_indicators": result.get('key_indicators', []),
                            "customer_mood": result.get('customer_mood', ''),
                            "empathy_required": result.get('empathy_required', False),
                            "reasoning": result.get('reasoning', '')
                        }
                    else:
                        return {"sentiment": sentiment, "confidence": confidence}
            
            return self._fallback_sentiment_analysis(email_text)
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return self._fallback_sentiment_analysis(email_text)
    
    def determine_priority(self, email_text, subject):
        """Determine priority using your working implementation"""
        try:
            full_text = f"{subject} {email_text}".lower()
            
            # First check for urgent keywords
            urgent_found = [keyword for keyword in self.urgent_keywords if keyword in full_text]
            
            if urgent_found:
                return "urgent"
            
            # Use AI for more nuanced analysis
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Analyze the priority level of this support email:

                    Subject: {subject}
                    Body: {email_text}

                    Please classify the priority and provide analysis in this JSON format:
                    {{
                        "priority": "urgent|normal",
                        "reasoning": "Explanation of priority classification"
                    }}

                    Priority Guidelines:
                    - URGENT: System down, cannot access account, security issues, business-critical deadlines
                    - NORMAL: General questions, minor issues, feature requests, standard support

                    Respond only with valid JSON.
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    priority = result.get('priority', 'normal').lower()
                    return "urgent" if priority == "urgent" else "normal"
            
            return "normal"
            
        except Exception as e:
            print(f"Error determining priority: {e}")
            return "normal"
    
    def categorize_email(self, email_text, subject):
        """Categorize email using your working implementation"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Categorize this customer support email:

                    Subject: {subject}
                    Body: {email_text}

                    Available Categories:
                    - technical_issue: Bug reports, system errors, functionality issues
                    - account_support: Login issues, password resets, account access
                    - product_inquiry: Pricing questions, feature requests, upgrade inquiries
                    - billing: Payment issues, invoice questions, subscription matters
                    - general: How-to questions, general information requests

                    Please respond with only the category name (e.g., "technical_issue")
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                categories = ['technical_issue', 'account_support', 'product_inquiry', 'billing', 'general']
                response_lower = response.lower().strip()
                
                for category in categories:
                    if category in response_lower:
                        return category
                
                # Fallback based on keywords
                return self._categorize_by_keywords(subject, email_text)
            
            return self._categorize_by_keywords(subject, email_text)
            
        except Exception as e:
            print(f"Error categorizing email: {e}")
            return self._categorize_by_keywords(subject, email_text)
    
    def generate_response(self, email_text, subject, sender_email, sentiment_analysis, category, enhanced=True):
        """Enhanced response generation with knowledge base and context awareness"""
        try:
            # Get enhanced sentiment info
            sentiment = sentiment_analysis.get('sentiment', 'neutral')
            empathy_required = sentiment_analysis.get('empathy_required', False)
            emotional_tone = sentiment_analysis.get('emotional_tone', 'neutral')
            customer_mood = sentiment_analysis.get('customer_mood', '')
            
            # Get relevant knowledge base info
            kb_info = self.knowledge_base.get(category, {})
            common_issues = kb_info.get('common_issues', [])
            solutions = kb_info.get('solutions', {})
            
            # Build context-aware prompt
            context_info = ""
            if empathy_required or sentiment == 'negative':
                context_info = f"""
                IMPORTANT: The customer appears {emotional_tone} and may be {customer_mood}. 
                Show genuine empathy and acknowledge their frustration appropriately.
                Use phrases like "I understand how frustrating this must be" or "I sincerely apologize for the inconvenience."
                """
            elif sentiment == 'positive':
                context_info = "The customer has a positive tone. Maintain their positivity and thank them for their patience/feedback."
            
            # Add knowledge base context
            if common_issues:
                context_info += f"\nCommon {category} issues include: {', '.join(common_issues[:3])}"
            
            # Enhanced response generation prompt
            if enhanced:
                messages = [
                    {
                        "role": "user",
                        "content": f"""
                        Generate a professional, empathetic, and helpful customer support response for this email:

                        From: {sender_email}
                        Subject: {subject}
                        Body: {email_text}

                        Customer Analysis:
                        - Category: {category}
                        - Sentiment: {sentiment} ({emotional_tone})
                        - Mood: {customer_mood}
                        - Requires empathy: {empathy_required}

                        {context_info}

                        Response Requirements:
                        1. **Greeting**: Professional and warm greeting using their email/name if appropriate
                        2. **Acknowledgment**: Acknowledge their specific concern/request clearly
                        3. **Empathy**: {('Show genuine empathy for their frustration' if empathy_required else 'Maintain professional, helpful tone')}
                        4. **Solution**: Provide specific, actionable steps or information
                        5. **Knowledge**: {('Reference relevant solutions: ' + str(list(solutions.keys())[:2]) if solutions else 'Provide helpful guidance')}
                        6. **Next Steps**: Clear next steps or escalation path
                        7. **Closing**: Professional closing with contact information

                        Style Guidelines:
                        - Length: 200-400 words
                        - Tone: Professional, empathetic, solution-focused
                        - Avoid: Generic responses, technical jargon, dismissive language
                        - Include: Specific details from their email, relevant solutions

                        Generate only the email body response (no subject line).
                        """
                    }
                ]
            else:
                # Fallback to original prompt
                messages = [
                    {
                        "role": "user",
                        "content": f"""
                        Generate a professional customer support response for this email:

                        From: {sender_email}
                        Subject: {subject}
                        Body: {email_text}

                        Context:
                        - Category: {category}
                        - Customer sentiment: {sentiment}
                        - {context_info}

                        Please generate a professional, empathetic, and helpful response.
                        Generate only the email body response, no subject line.
                        """
                    }
                ]
            
            response = self.ai_client.make_request(messages)
            
            if response:
                return response.strip()
            else:
                return self._generate_fallback_response(category, sentiment, enhanced=True)
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._generate_fallback_response(category, sentiment, enhanced=True)
    
    def extract_information(self, email_text, subject="", enhanced=True):
        """Enhanced information extraction with better accuracy"""
        try:
            if enhanced:
                # Enhanced extraction with AI
                messages = [
                    {
                        "role": "user",
                        "content": f"""
                        Extract detailed information from this customer support email:

                        Subject: {subject}
                        Body: {email_text}

                        Please extract and return information in this JSON format:
                        {{
                            "contact_details": {{
                                "phone_numbers": ["list of phone numbers found"],
                                "alternate_emails": ["list of email addresses mentioned"],
                                "social_media": ["any social handles mentioned"]
                            }},
                            "customer_request": {{
                                "main_request": "primary thing customer wants",
                                "specific_requirements": ["detailed requirements"],
                                "products_mentioned": ["any products/services mentioned"],
                                "account_info": "any account details mentioned"
                            }},
                            "urgency_indicators": {{
                                "deadlines": "any deadlines mentioned",
                                "urgency_level": "low|medium|high",
                                "time_sensitive": true|false,
                                "business_impact": "description of business impact"
                            }},
                            "sentiment_indicators": {{
                                "positive_words": ["positive words found"],
                                "negative_words": ["negative words found"],
                                "emotional_language": ["emotional expressions"]
                            }},
                            "technical_details": {{
                                "error_messages": ["any error messages"],
                                "system_info": "browser, OS, device info",
                                "steps_taken": ["what customer already tried"]
                            }},
                            "context": {{
                                "customer_type": "new|existing|premium",
                                "previous_interactions": "any mentions of past support",
                                "relationship_duration": "how long they've been a customer"
                            }}
                        }}

                        Be thorough and accurate. If information is not found, use empty strings or arrays.
                        Respond only with valid JSON.
                        """
                    }
                ]
                
                response = self.ai_client.make_request(messages)
                
                if response:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        return result
            
            # Fallback to regex-based extraction
            return self._regex_extraction(email_text, subject)
            
        except Exception as e:
            print(f"Error extracting information: {e}")
            return self._regex_extraction(email_text, subject)
    
    def _regex_extraction(self, email_text, subject=""):
        """Fallback regex-based information extraction"""
        try:
            # Use regex patterns for basic extraction
            phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            
            phones = re.findall(phone_pattern, email_text)
            emails = re.findall(email_pattern, email_text)
            
            # Clean phone numbers
            clean_phones = [re.sub(r'[^\d+]', '', phone) for phone in phones if len(re.sub(r'[^\d]', '', phone)) >= 10]
            
            # Extract basic requirements using keywords
            requirements = ""
            full_text = f"{subject} {email_text}"
            if any(word in full_text.lower() for word in ['need', 'want', 'require', 'request']):
                # Extract sentence containing requirement keywords
                sentences = email_text.split('.')
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['need', 'want', 'require', 'request']):
                        requirements = sentence.strip()
                        break
            
            # Extract deadlines and urgency
            deadlines = ""
            urgency_words = ['deadline', 'urgent', 'today', 'tomorrow', 'asap', 'immediately']
            urgency_found = [word for word in urgency_words if word in full_text.lower()]
            if urgency_found:
                deadlines = f"Urgency indicators: {', '.join(urgency_found)}"
            
            # Extract sentiment indicators
            positive_found = [word for word in self.positive_indicators if word in full_text.lower()]
            negative_found = [word for word in self.negative_indicators if word in full_text.lower()]
            
            return {
                "contact_details": {
                    "phone_numbers": clean_phones,
                    "alternate_emails": [email for email in emails],
                    "social_media": []
                },
                "customer_request": {
                    "main_request": requirements,
                    "specific_requirements": [],
                    "products_mentioned": [],
                    "account_info": ""
                },
                "urgency_indicators": {
                    "deadlines": deadlines,
                    "urgency_level": "high" if urgency_found else "medium",
                    "time_sensitive": bool(urgency_found),
                    "business_impact": ""
                },
                "sentiment_indicators": {
                    "positive_words": positive_found[:5],
                    "negative_words": negative_found[:5],
                    "emotional_language": []
                },
                "technical_details": {
                    "error_messages": [],
                    "system_info": "",
                    "steps_taken": []
                },
                "context": {
                    "customer_type": "",
                    "previous_interactions": "",
                    "relationship_duration": ""
                }
            }
            
        except Exception as e:
            print(f"Error in regex extraction: {e}")
            return {
                "contact_details": {"phone_numbers": [], "alternate_emails": [], "social_media": []},
                "customer_request": {"main_request": "", "specific_requirements": [], "products_mentioned": [], "account_info": ""},
                "urgency_indicators": {"deadlines": "", "urgency_level": "medium", "time_sensitive": False, "business_impact": ""},
                "sentiment_indicators": {"positive_words": [], "negative_words": [], "emotional_language": []},
                "technical_details": {"error_messages": [], "system_info": "", "steps_taken": []},
                "context": {"customer_type": "", "previous_interactions": "", "relationship_duration": ""}
            }
    
    def _fallback_sentiment_analysis(self, text):
        """Fallback sentiment analysis using keyword matching"""
        text_lower = text.lower()
        
        positive_words = ['thank', 'great', 'excellent', 'good', 'appreciate', 'love', 'perfect', 'awesome']
        negative_words = ['urgent', 'critical', 'problem', 'issue', 'error', 'broken', 'fail', 'cannot', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {"sentiment": "positive", "confidence": 0.7}
        elif negative_count > positive_count:
            return {"sentiment": "negative", "confidence": 0.7}
        else:
            return {"sentiment": "neutral", "confidence": 0.5}
    
    def _categorize_by_keywords(self, subject, body):
        """Fallback categorization using keywords"""
        text = f"{subject} {body}".lower()
        
        if any(word in text for word in ['login', 'password', 'access', 'account', 'sign in']):
            return 'account_support'
        elif any(word in text for word in ['price', 'pricing', 'cost', 'plan', 'upgrade', 'subscription']):
            return 'product_inquiry'
        elif any(word in text for word in ['bug', 'error', 'broken', 'not working', 'crash']):
            return 'technical_issue'
        elif any(word in text for word in ['bill', 'payment', 'invoice', 'charge']):
            return 'billing'
        else:
            return 'general'
    
    def _generate_fallback_response(self, category, sentiment, enhanced=False):
        """Enhanced fallback response generation with knowledge base"""
        
        # Get knowledge base info
        kb_info = self.knowledge_base.get(category, {})
        solutions = kb_info.get('solutions', {})
        
        if enhanced and solutions:
            # Use knowledge base for better responses
            base_responses = {
                'account_support': f"Thank you for contacting us about your account issue. {list(solutions.values())[0] if solutions else 'Our account team will help you resolve this.'} Please let us know if you need further assistance.",
                'technical_issue': f"Thank you for reporting this technical issue. {list(solutions.values())[0] if solutions else 'Our technical team will investigate this promptly.'} We appreciate your patience.",
                'product_inquiry': f"Thank you for your interest in our products. {list(solutions.values())[0] if solutions else 'Our sales team will provide detailed information.'} Please don't hesitate to ask any questions.",
                'billing': f"Thank you for contacting us about billing. {list(solutions.values())[0] if solutions else 'Our billing team will review your account.'} We'll ensure this is resolved quickly.",
                'general': "Thank you for contacting our support team. We've received your inquiry and will provide you with the assistance you need promptly."
            }
        else:
            # Original fallback responses
            base_responses = {
                'account_support': "Thank you for contacting us about your account. We'll help you resolve this access issue. Please verify your email address and we'll send you password reset instructions if needed.",
                'technical_issue': "Thank you for reporting this technical issue. Our technical team will investigate and provide a resolution. We appreciate your patience as we work to fix this.",
                'product_inquiry': "Thank you for your interest in our products. Our sales team will provide you with detailed information about pricing and features that best fit your needs.",
                'billing': "Thank you for contacting us about billing. Our billing department will review your account and provide clarification on any charges or payment issues.",
                'general': "Thank you for contacting our support team. We'll review your inquiry and provide you with the assistance you need."
            }
        
        base_response = base_responses.get(category, base_responses['general'])
        
        # Add sentiment-appropriate opening
        if sentiment == 'negative':
            base_response = "I understand your frustration and apologize for any inconvenience you've experienced. " + base_response
        elif sentiment == 'positive':
            base_response = "Thank you for your positive feedback and for choosing our services! " + base_response
        
        return base_response + "\n\nBest regards,\nCustomer Support Team"


class EmailAnalysisService:
    """Enhanced service for analyzing emails end-to-end with priority queue and auto-respond"""
    
    def __init__(self):
        self.perplexity = PerplexityService()
    
    def analyze_email(self, email_obj, enhanced=True):
        """Perform enhanced analysis on an email"""
        try:
            # Check if this is a support email first
            is_support = self.perplexity.is_support_email(email_obj.subject, email_obj.body)
            
            if not is_support:
                print(f"⏭️ Skipping non-support email: {email_obj.subject[:50]}...")
                return email_obj
            
            # Combine subject and body for analysis
            full_text = f"{email_obj.subject} {email_obj.body}"
            
            print(f"🔍 Analyzing support email: {email_obj.subject[:50]}...")
            
            # Enhanced sentiment analysis
            sentiment_result = self.perplexity.analyze_email_sentiment(
                full_text, email_obj.sender_email, enhanced=enhanced
            )
            
            email_obj.sentiment = sentiment_result.get('sentiment', 'neutral')
            email_obj.sentiment_confidence = sentiment_result.get('confidence', 0.5)
            
            # Store enhanced sentiment data
            if enhanced and 'emotional_tone' in sentiment_result:
                email_obj.extracted_info['sentiment_analysis'] = {
                    'emotional_tone': sentiment_result.get('emotional_tone', ''),
                    'intensity': sentiment_result.get('intensity', ''),
                    'key_indicators': sentiment_result.get('key_indicators', []),
                    'customer_mood': sentiment_result.get('customer_mood', ''),
                    'empathy_required': sentiment_result.get('empathy_required', False),
                    'reasoning': sentiment_result.get('reasoning', '')
                }
            
            # Priority determination
            email_obj.priority = self.perplexity.determine_priority(email_obj.body, email_obj.subject)
            if email_obj.priority == 'urgent':
                email_obj.is_urgent = True
            
            # Categorization
            email_obj.category = self.perplexity.categorize_email(email_obj.body, email_obj.subject)
            
            # Enhanced information extraction
            extracted_info = self.perplexity.extract_information(
                email_obj.body, email_obj.subject, enhanced=enhanced
            )
            
            # Merge with existing extracted_info
            if hasattr(email_obj, 'extracted_info') and email_obj.extracted_info:
                email_obj.extracted_info.update(extracted_info)
            else:
                email_obj.extracted_info = extracted_info
            
            # Generate enhanced AI response
            email_obj.ai_response = self.perplexity.generate_response(
                email_obj.body, email_obj.subject, email_obj.sender_email,
                sentiment_result, email_obj.category, enhanced=enhanced
            )
            email_obj.response_generated_at = timezone.now()
            
            email_obj.save()
            
            print(f"✅ Enhanced analysis complete:")
            print(f"   Priority: {email_obj.priority}")
            print(f"   Sentiment: {email_obj.sentiment}")
            print(f"   Category: {email_obj.category}")
            if enhanced and 'sentiment_analysis' in email_obj.extracted_info:
                print(f"   Emotional tone: {email_obj.extracted_info['sentiment_analysis'].get('emotional_tone', 'N/A')}")
                print(f"   Empathy required: {email_obj.extracted_info['sentiment_analysis'].get('empathy_required', 'N/A')}")
            
            # Update daily stats
            self.update_daily_stats(email_obj)
            
            return email_obj
            
        except Exception as e:
            print(f"Error analyzing email {email_obj.id}: {e}")
            return email_obj
    
    def process_priority_queue(self, max_emails=50, auto_respond=False):
        """Process emails in priority order (urgent first)"""
        try:
            print(f"🚀 Processing email priority queue...")
            
            # Get unprocessed emails ordered by priority
            unprocessed_emails = Email.objects.filter(
                ai_response__isnull=True
            ).order_by('-is_urgent', '-received_at')[:max_emails]
            
            if not unprocessed_emails:
                print("📭 No emails to process")
                return []
            
            processed_emails = []
            
            for i, email in enumerate(unprocessed_emails, 1):
                priority_icon = "🚨" if email.is_urgent else "📝"
                print(f"{priority_icon} Processing email {i}/{len(unprocessed_emails)}: {email.subject[:50]}...")
                
                # Analyze email
                analyzed_email = self.analyze_email(email, enhanced=True)
                processed_emails.append(analyzed_email)
                
                # Auto-respond if enabled and email was analyzed
                if auto_respond and analyzed_email.ai_response:
                    try:
                        self.send_auto_response(analyzed_email)
                    except Exception as e:
                        print(f"   ⚠️ Auto-response failed: {e}")
                
                # Small delay to avoid rate limiting
                time.sleep(1)
            
            print(f"✅ Processed {len(processed_emails)} emails")
            return processed_emails
            
        except Exception as e:
            print(f"Error processing priority queue: {e}")
            return []
    
    def send_auto_response(self, email_obj):
        """Send automatic response (placeholder - would integrate with email service)"""
        try:
            print(f"📧 Sending auto-response to {email_obj.sender_email}...")
            
            # In a real implementation, this would:
            # 1. Use Gmail API or SMTP to send the response
            # 2. Update email status to 'responded'
            # 3. Log the sent response
            
            # For now, just mark as responded
            email_obj.is_responded = True
            email_obj.save()
            
            print(f"✅ Auto-response sent successfully")
            
            # Update daily stats
            today = timezone.now().date()
            stats, created = DailyStats.objects.get_or_create(date=today)
            stats.responded_emails += 1
            stats.pending_emails = max(0, stats.pending_emails - 1)
            stats.save()
            
        except Exception as e:
            print(f"Error sending auto-response: {e}")
            raise
    
    def get_priority_statistics(self):
        """Get detailed priority and processing statistics"""
        try:
            today = timezone.now().date()
            
            stats = {
                'total_emails': Email.objects.count(),
                'urgent_emails': Email.objects.filter(is_urgent=True).count(),
                'pending_urgent': Email.objects.filter(is_urgent=True, is_responded=False).count(),
                'processed_today': Email.objects.filter(processed_at__date=today).count(),
                'responded_today': Email.objects.filter(
                    response_generated_at__date=today,
                    is_responded=True
                ).count(),
                'avg_response_time': self._calculate_avg_response_time(),
                'category_breakdown': self._get_category_breakdown(),
                'sentiment_breakdown': self._get_sentiment_breakdown()
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting priority statistics: {e}")
            return {}
    
    def _calculate_avg_response_time(self):
        """Calculate average response time for processed emails"""
        try:
            from django.db.models import Avg, F
            
            avg_time = Email.objects.filter(
                response_generated_at__isnull=False
            ).aggregate(
                avg_time=Avg(F('response_generated_at') - F('received_at'))
            )['avg_time']
            
            if avg_time:
                return str(avg_time).split('.')[0]  # Remove microseconds
            return "N/A"
            
        except Exception:
            return "N/A"
    
    def _get_category_breakdown(self):
        """Get breakdown of emails by category"""
        try:
            from django.db.models import Count
            
            categories = Email.objects.values('category').annotate(
                count=Count('category')
            ).order_by('-count')
            
            return {cat['category']: cat['count'] for cat in categories if cat['category']}
            
        except Exception:
            return {}
    
    def _get_sentiment_breakdown(self):
        """Get breakdown of emails by sentiment"""
        try:
            from django.db.models import Count
            
            sentiments = Email.objects.values('sentiment').annotate(
                count=Count('sentiment')
            ).order_by('-count')
            
            return {sent['sentiment']: sent['count'] for sent in sentiments if sent['sentiment']}
            
        except Exception:
            return {}
    
    def update_daily_stats(self, email_obj):
        """Update daily statistics"""
        today = timezone.now().date()
        stats, created = DailyStats.objects.get_or_create(date=today)
        
        if created:
            stats.total_emails = 1
        else:
            stats.total_emails += 1
        
        # Update sentiment counts
        if email_obj.sentiment == 'positive':
            stats.positive_emails += 1
        elif email_obj.sentiment == 'negative':
            stats.negative_emails += 1
        else:
            stats.neutral_emails += 1
        
        # Update priority counts
        if email_obj.priority == 'urgent':
            stats.urgent_emails += 1
        
        # Update category counts
        category_mapping = {
            'technical_issue': 'technical_issues',
            'account_support': 'account_support', 
            'product_inquiry': 'product_inquiries',
            'billing': 'billing_issues',
            'general': 'general_inquiries',
        }
        
        if email_obj.category in category_mapping:
            current_count = getattr(stats, category_mapping[email_obj.category])
            setattr(stats, category_mapping[email_obj.category], current_count + 1)
        
        # Update pending count
        pending_count = Email.objects.filter(
            received_at__date=today,
            is_responded=False
        ).count()
        stats.pending_emails = pending_count
        
        # Update responded count
        responded_count = Email.objects.filter(
            received_at__date=today,
            is_responded=True
        ).count()
        stats.responded_emails = responded_count
        
        stats.save()
