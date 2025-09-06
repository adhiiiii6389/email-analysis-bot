#!/usr/bin/env python3
"""
Context-Aware Auto-Response Generation Module
Generates professional, context-aware responses using Perplexity AI with RAG capabilities.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerplexityAI:
    """Perplexity AI API client for response generation"""
    
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
            "max_tokens": 1500,
            "temperature": 0.3
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

# Knowledge base for common support scenarios
KNOWLEDGE_BASE = {
    "account_issues": {
        "password_reset": {
            "solution": "To reset your password, please visit our password reset page at [company-url]/reset-password and follow the instructions. You'll receive an email with reset instructions within 5 minutes.",
            "steps": [
                "Go to the login page",
                "Click 'Forgot Password'",
                "Enter your email address",
                "Check your email for reset instructions",
                "Create a new password"
            ]
        },
        "account_locked": {
            "solution": "Your account may be temporarily locked for security reasons. This usually happens after multiple failed login attempts. Please wait 30 minutes and try again, or contact our support team for immediate assistance.",
            "escalation": "If the issue persists, please contact our technical team."
        }
    },
    "technical_issues": {
        "login_problems": {
            "solution": "For login issues, please clear your browser cache and cookies, try a different browser, or check if you're using the correct credentials.",
            "troubleshooting": [
                "Clear browser cache and cookies",
                "Try using an incognito/private browser window",
                "Verify your username and password",
                "Check if Caps Lock is enabled",
                "Try a different browser or device"
            ]
        },
        "system_errors": {
            "solution": "We're aware of occasional system errors and our technical team is working to resolve them. Please try refreshing the page or logging out and back in.",
            "escalation": "If the error persists, please provide the error message details and we'll investigate further."
        }
    },
    "billing_issues": {
        "payment_failed": {
            "solution": "If your payment failed, please check that your payment method is valid and has sufficient funds. You can update your payment information in your account settings.",
            "steps": [
                "Log into your account",
                "Go to Account Settings > Billing",
                "Update your payment method",
                "Retry the payment"
            ]
        },
        "invoice_questions": {
            "solution": "For invoice-related questions, please check your account's billing section where you can download past invoices and view payment history.",
            "escalation": "For specific billing disputes, please contact our billing department."
        }
    },
    "general_support": {
        "how_to_questions": {
            "solution": "For how-to questions, please check our comprehensive documentation and tutorial section. If you need specific guidance, our support team is happy to help.",
            "resources": ["Documentation", "Video tutorials", "FAQ section", "Community forum"]
        },
        "feature_requests": {
            "solution": "Thank you for your feature suggestion! We value customer feedback and all suggestions are reviewed by our product team.",
            "process": "Feature requests are evaluated quarterly and prioritized based on customer demand and technical feasibility."
        }
    }
}

# Response templates based on priority and category
RESPONSE_TEMPLATES = {
    "urgent": {
        "greeting": "Thank you for contacting us urgently.",
        "acknowledgment": "I understand this is a critical issue that needs immediate attention.",
        "action": "I'm escalating this to our priority support team and you should hear back within 2 hours.",
        "contact": "For immediate assistance, please call our emergency support line at [emergency-number]."
    },
    "high": {
        "greeting": "Thank you for reaching out to us.",
        "acknowledgment": "I understand this issue is impacting your work.",
        "action": "I'm prioritizing your request and will ensure you receive a response within 4 hours.",
        "contact": "If you need faster assistance, please don't hesitate to call our support line."
    },
    "normal": {
        "greeting": "Thank you for contacting our support team.",
        "acknowledgment": "I'm here to help you with your inquiry.",
        "action": "I'll review your request and get back to you within 24 hours with a solution.",
        "contact": "Feel free to reply to this email if you have any additional questions."
    },
    "low": {
        "greeting": "Thank you for your message.",
        "acknowledgment": "I appreciate you taking the time to reach out.",
        "action": "I'll look into this and respond within 48 hours.",
        "contact": "Thank you for your patience."
    }
}

class ResponseGenerator:
    def __init__(self):
        # Initialize Perplexity AI
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY', 'your-perplexity-api-key-here')
        self.ai_client = PerplexityAI(self.perplexity_api_key)
        print("✅ Response Generator initialized with Perplexity AI.")
    
    def generate_response(self, email_data: Dict, analysis_data: Dict) -> Dict:
        """
        Generate a context-aware response based on email content and analysis.
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('sender_email', '')
        
        # Extract analysis results
        priority = analysis_data.get('priority', 'normal')
        category = analysis_data.get('category', 'General Support')
        sentiment = analysis_data.get('sentiment', 'neutral')
        
        print(f"📝 Generating response for {priority} priority {category} email...")
        
        # Try AI-powered response first
        ai_response = self._generate_ai_response(email_data, analysis_data)
        
        if ai_response:
            response_data = {
                'response_text': ai_response,
                'response_type': 'ai_generated',
                'priority': priority,
                'category': category,
                'generated_at': datetime.now().isoformat(),
                'confidence': 0.9
            }
        else:
            # Fallback to template-based response
            template_response = self._generate_template_response(email_data, analysis_data)
            response_data = {
                'response_text': template_response,
                'response_type': 'template_based',
                'priority': priority,
                'category': category,
                'generated_at': datetime.now().isoformat(),
                'confidence': 0.7
            }
        
        return response_data
    
    def _generate_ai_response(self, email_data: Dict, analysis_data: Dict) -> Optional[str]:
        """Generate response using Perplexity AI."""
        try:
            # Get relevant knowledge base information
            kb_context = self._get_relevant_knowledge(analysis_data)
            
            # Prepare the prompt
            messages = [
                {
                    "role": "user",
                    "content": f"""
                    Generate a professional customer support response for this email:

                    Original Email:
                    Subject: {email_data.get('subject', '')}
                    From: {email_data.get('sender_email', '')}
                    Body: {email_data.get('body', '')}

                    Analysis Results:
                    - Priority: {analysis_data.get('priority', 'normal')}
                    - Category: {analysis_data.get('category', 'General Support')}
                    - Sentiment: {analysis_data.get('sentiment', 'neutral')}
                    - Reasoning: {analysis_data.get('priority_reasoning', '')}

                    Relevant Knowledge Base Information:
                    {kb_context}

                    Please generate a professional, empathetic, and helpful response that:
                    1. Acknowledges the customer's concern appropriately
                    2. Addresses their specific issue based on the category and priority
                    3. Provides helpful information or next steps
                    4. Maintains a tone appropriate to the priority level
                    5. Is concise but comprehensive (200-500 words)
                    6. Includes a professional closing

                    Response Guidelines:
                    - For URGENT: Show immediate concern, offer escalation, provide emergency contact
                    - For HIGH: Express understanding of impact, commit to fast resolution
                    - For NORMAL: Be helpful and thorough, standard response time
                    - For LOW: Be polite and informative, acknowledge their patience

                    Use a professional customer service tone throughout.
                    """
                }
            ]
            
            response = self.ai_client.make_request(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    def _generate_template_response(self, email_data: Dict, analysis_data: Dict) -> str:
        """Generate response using templates as fallback."""
        priority = analysis_data.get('priority', 'normal')
        category = analysis_data.get('category', 'General Support')
        sender_name = self._extract_sender_name(email_data.get('sender_email', ''))
        
        # Get appropriate template
        template = RESPONSE_TEMPLATES.get(priority, RESPONSE_TEMPLATES['normal'])
        
        # Get relevant knowledge
        kb_info = self._get_relevant_knowledge(analysis_data)
        
        # Build response
        response_parts = []
        
        # Greeting
        if sender_name:
            response_parts.append(f"Dear {sender_name},")
        else:
            response_parts.append("Dear Customer,")
        
        response_parts.append("")
        response_parts.append(template['greeting'])
        response_parts.append("")
        response_parts.append(template['acknowledgment'])
        
        # Add specific content based on category
        if kb_info:
            response_parts.append("")
            response_parts.append("Here's what I can help you with:")
            response_parts.append(kb_info)
        
        response_parts.append("")
        response_parts.append(template['action'])
        
        if 'contact' in template:
            response_parts.append("")
            response_parts.append(template['contact'])
        
        # Closing
        response_parts.append("")
        response_parts.append("Best regards,")
        response_parts.append("Customer Support Team")
        response_parts.append("[Company Name]")
        
        return "\n".join(response_parts)
    
    def _get_relevant_knowledge(self, analysis_data: Dict) -> str:
        """Extract relevant information from knowledge base."""
        category = analysis_data.get('category', '').lower()
        priority = analysis_data.get('priority', 'normal')
        
        relevant_info = []
        
        # Map categories to knowledge base sections
        if 'account' in category.lower():
            if 'login' in analysis_data.get('priority_reasoning', '').lower():
                kb_section = KNOWLEDGE_BASE.get('account_issues', {}).get('password_reset')
                if kb_section:
                    relevant_info.append(f"Solution: {kb_section['solution']}")
            
        elif 'technical' in category.lower():
            kb_section = KNOWLEDGE_BASE.get('technical_issues', {}).get('login_problems')
            if kb_section:
                relevant_info.append(f"Troubleshooting: {kb_section['solution']}")
                if 'troubleshooting' in kb_section:
                    steps = "\n".join([f"- {step}" for step in kb_section['troubleshooting']])
                    relevant_info.append(f"Steps to try:\n{steps}")
        
        elif 'billing' in category.lower():
            kb_section = KNOWLEDGE_BASE.get('billing_issues', {}).get('payment_failed')
            if kb_section:
                relevant_info.append(f"Solution: {kb_section['solution']}")
        
        elif 'sales' in category.lower():
            relevant_info.append("Our sales team will provide detailed pricing information and help you choose the best plan for your needs.")
        
        else:
            # General support
            kb_section = KNOWLEDGE_BASE.get('general_support', {}).get('how_to_questions')
            if kb_section:
                relevant_info.append(f"Resources: {kb_section['solution']}")
        
        return "\n".join(relevant_info) if relevant_info else "Our support team will provide personalized assistance for your specific needs."
    
    def _extract_sender_name(self, email: str) -> str:
        """Extract sender name from email address."""
        if '@' in email:
            local_part = email.split('@')[0]
            # Common patterns for names in email addresses
            if '.' in local_part:
                parts = local_part.split('.')
                if len(parts) >= 2:
                    return f"{parts[0].capitalize()} {parts[1].capitalize()}"
            else:
                return local_part.capitalize()
        return ""
    
    def get_response_templates(self) -> Dict:
        """Return available response templates."""
        return RESPONSE_TEMPLATES
    
    def get_knowledge_base(self) -> Dict:
        """Return the knowledge base."""
        return KNOWLEDGE_BASE

# Example usage and testing
if __name__ == "__main__":
    generator = ResponseGenerator()
    
    # Test email data
    test_email = {
        'subject': 'URGENT: Cannot access my account',
        'body': 'Hi, I cannot log into my account and have an important deadline today. Please help immediately.',
        'sender_email': 'john.doe@example.com'
    }
    
    # Test analysis data
    test_analysis = {
        'priority': 'urgent',
        'category': 'Account Support',
        'sentiment': 'negative',
        'priority_reasoning': 'Account access issue with business impact and deadline'
    }
    
    print("🧪 Testing Response Generation with Perplexity AI...")
    result = generator.generate_response(test_email, test_analysis)
    
    print("\n📧 Generated Response:")
    print(f"Type: {result['response_type']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Priority: {result['priority']}")
    print(f"Category: {result['category']}")
    print("\nResponse Text:")
    print("-" * 50)
    print(result['response_text'])
    print("-" * 50)
