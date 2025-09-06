#!/usr/bin/env python3
"""
Information Extraction Module
Extracts key information from emails including contact details, requirements, and metadata.
"""

import re
import json
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyD_mF9dR6-5gD_3MU9fCP1yfi_kZVUq1YM"
genai.configure(api_key=GEMINI_API_KEY)

class InformationExtractor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Regex patterns for different types of information
        self.patterns = {
            'phone_us': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'phone_international': r'\+[1-9]\d{1,14}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
            'ticket_number': r'(?:ticket|case|ref|reference)[\s#:]*([A-Z0-9-]{5,20})',
            'product_name': r'\b(?:product|software|application|app|service|platform)[\s:]*([A-Za-z0-9\s]{2,30})',
            'error_code': r'(?:error|code)[\s#:]*([A-Z0-9-]{3,15})',
            'version': r'(?:version|v\.?)[\s]*([0-9]+(?:\.[0-9]+)*)',
            'date_mention': r'\b(?:by|before|after|on|until)\s+([A-Za-z0-9\s,.-]{5,25})\b'
        }
        
        print("✅ Information Extractor initialized with Gemini AI and regex patterns.")
    
    def extract_information(self, email_data: Dict) -> Dict:
        """
        Extract comprehensive information from an email.
        
        Args:
            email_data: Dictionary containing email content and metadata
        
        Returns:
            Dictionary with extracted information
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender_email = email_data.get('sender_email', '')
        
        print(f"🔍 Extracting information from: {subject[:50]}...")
        
        # Combine subject and body for analysis
        full_text = f"{subject}\n\n{body}"
        
        # Extract different types of information
        contact_info = self._extract_contact_details(full_text, sender_email)
        requirements = self._extract_customer_requirements(subject, body)
        sentiment_indicators = self._extract_sentiment_indicators(full_text)
        technical_info = self._extract_technical_information(full_text)
        business_info = self._extract_business_information(full_text)
        
        # Combine all extracted information
        extracted_info = {
            'contact_details': contact_info,
            'customer_requirements': requirements,
            'sentiment_indicators': sentiment_indicators,
            'technical_information': technical_info,
            'business_information': business_info,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'extraction_methods': ['regex', 'ai_analysis'],
                'confidence_score': self._calculate_confidence_score(contact_info, requirements, technical_info)
            }
        }
        
        return extracted_info
    
    def _extract_contact_details(self, text: str, primary_email: str) -> Dict:
        """Extract contact information using regex patterns."""
        contact_info = {
            'phone_numbers': [],
            'alternate_emails': [],
            'social_media': [],
            'addresses': []
        }
        
        # Extract phone numbers
        us_phones = re.findall(self.patterns['phone_us'], text, re.IGNORECASE)
        for match in us_phones:
            if isinstance(match, tuple):
                phone = ''.join(match)
                # Clean and format phone number
                phone = re.sub(r'[^\d]', '', phone)
                if len(phone) == 10:
                    phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
                elif len(phone) == 11 and phone.startswith('1'):
                    phone = f"+1 ({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
                if phone not in contact_info['phone_numbers']:
                    contact_info['phone_numbers'].append(phone)
        
        # Extract international phone numbers
        intl_phones = re.findall(self.patterns['phone_international'], text)
        for phone in intl_phones:
            if phone not in contact_info['phone_numbers']:
                contact_info['phone_numbers'].append(phone)
        
        # Extract alternate email addresses
        emails = re.findall(self.patterns['email'], text, re.IGNORECASE)
        for email in emails:
            if email.lower() != primary_email.lower() and email not in contact_info['alternate_emails']:
                contact_info['alternate_emails'].append(email)
        
        # Extract social media handles (basic patterns)
        social_patterns = [
            r'@([A-Za-z0-9_]{1,15})',  # Twitter-style handles
            r'linkedin\.com/in/([A-Za-z0-9-]+)',
            r'facebook\.com/([A-Za-z0-9.]+)',
            r'github\.com/([A-Za-z0-9-]+)'
        ]
        
        for pattern in social_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contact_info['social_media'].extend(matches)
        
        return contact_info
    
    def _extract_customer_requirements(self, subject: str, body: str) -> Dict:
        """Extract customer requirements and requests using AI analysis."""
        try:
            prompt = f"""
            Analyze this customer email and extract their specific requirements, requests, and needs:

            Subject: {subject}
            Body: {body}

            Please identify and extract:
            1. Primary request or problem they need solved
            2. Specific features or services they're asking about
            3. Any deadlines or time constraints mentioned
            4. Business impact or urgency reasons
            5. Specific actions they want us to take
            6. Any technical specifications or requirements mentioned

            Provide your analysis in JSON format:
            {{
                "primary_request": "Main thing they need help with",
                "specific_features": ["feature1", "feature2"],
                "deadlines": ["deadline1", "deadline2"],
                "business_impact": "How this affects their business",
                "requested_actions": ["action1", "action2"],
                "technical_specs": ["spec1", "spec2"],
                "urgency_reasons": ["reason1", "reason2"],
                "additional_context": "Any other relevant information"
            }}

            Respond only with valid JSON.
            """
            
            response = self.model.generate_content(prompt)
            requirements = json.loads(response.text.strip())
            
            # Validate and clean the response
            return {
                'primary_request': requirements.get('primary_request', ''),
                'specific_features': requirements.get('specific_features', []),
                'deadlines': requirements.get('deadlines', []),
                'business_impact': requirements.get('business_impact', ''),
                'requested_actions': requirements.get('requested_actions', []),
                'technical_specs': requirements.get('technical_specs', []),
                'urgency_reasons': requirements.get('urgency_reasons', []),
                'additional_context': requirements.get('additional_context', '')
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting requirements: {e}")
            return self._fallback_requirements_extraction(subject, body)
    
    def _extract_sentiment_indicators(self, text: str) -> Dict:
        """Extract sentiment indicators and emotional cues."""
        sentiment_indicators = {
            'positive_words': [],
            'negative_words': [],
            'urgency_words': [],
            'frustration_indicators': [],
            'satisfaction_indicators': []
        }
        
        # Define word lists
        positive_words = [
            'thank', 'thanks', 'grateful', 'appreciate', 'excellent', 'great', 'amazing',
            'wonderful', 'fantastic', 'pleased', 'satisfied', 'happy', 'love', 'perfect'
        ]
        
        negative_words = [
            'problem', 'issue', 'error', 'bug', 'broken', 'failed', 'not working',
            'terrible', 'awful', 'horrible', 'disappointed', 'frustrated', 'angry',
            'upset', 'annoyed', 'useless', 'worst', 'hate'
        ]
        
        urgency_words = [
            'urgent', 'critical', 'emergency', 'asap', 'immediately', 'deadline',
            'time-sensitive', 'rush', 'priority', 'escalate', 'cannot wait'
        ]
        
        frustration_indicators = [
            'multiple times', 'again and again', 'still not working', 'same problem',
            'keep getting', 'over and over', 'repeatedly', 'countless times',
            'third time', 'several attempts', 'still having'
        ]
        
        satisfaction_indicators = [
            'solved', 'resolved', 'working now', 'fixed', 'much better',
            'improvement', 'helpful', 'quick response', 'professional'
        ]
        
        text_lower = text.lower()
        
        # Find positive words
        for word in positive_words:
            if word in text_lower:
                sentiment_indicators['positive_words'].append(word)
        
        # Find negative words
        for word in negative_words:
            if word in text_lower:
                sentiment_indicators['negative_words'].append(word)
        
        # Find urgency words
        for word in urgency_words:
            if word in text_lower:
                sentiment_indicators['urgency_words'].append(word)
        
        # Find frustration indicators
        for phrase in frustration_indicators:
            if phrase in text_lower:
                sentiment_indicators['frustration_indicators'].append(phrase)
        
        # Find satisfaction indicators
        for phrase in satisfaction_indicators:
            if phrase in text_lower:
                sentiment_indicators['satisfaction_indicators'].append(phrase)
        
        return sentiment_indicators
    
    def _extract_technical_information(self, text: str) -> Dict:
        """Extract technical information using regex patterns."""
        technical_info = {
            'error_codes': [],
            'product_versions': [],
            'urls_mentioned': [],
            'ticket_numbers': [],
            'browser_info': [],
            'operating_system': [],
            'file_names': []
        }
        
        # Extract error codes
        error_codes = re.findall(self.patterns['error_code'], text, re.IGNORECASE)
        technical_info['error_codes'] = list(set(error_codes))
        
        # Extract version numbers
        versions = re.findall(self.patterns['version'], text, re.IGNORECASE)
        technical_info['product_versions'] = list(set(versions))
        
        # Extract URLs
        urls = re.findall(self.patterns['url'], text)
        technical_info['urls_mentioned'] = list(set(urls))
        
        # Extract ticket numbers
        tickets = re.findall(self.patterns['ticket_number'], text, re.IGNORECASE)
        technical_info['ticket_numbers'] = list(set(tickets))
        
        # Extract browser information
        browser_patterns = [
            r'(chrome|firefox|safari|edge|internet explorer|ie)\s*(\d+(?:\.\d+)*)?',
            r'(mozilla|webkit)'
        ]
        
        for pattern in browser_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    browser_info = ' '.join(filter(None, match))
                else:
                    browser_info = match
                if browser_info not in technical_info['browser_info']:
                    technical_info['browser_info'].append(browser_info)
        
        # Extract operating system information
        os_patterns = [
            r'(windows|mac|macos|linux|ubuntu|android|ios)\s*(\d+(?:\.\d+)*)?',
            r'(win\d+|osx)'
        ]
        
        for pattern in os_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    os_info = ' '.join(filter(None, match))
                else:
                    os_info = match
                if os_info not in technical_info['operating_system']:
                    technical_info['operating_system'].append(os_info)
        
        # Extract file names and extensions
        file_patterns = [
            r'([A-Za-z0-9_-]+\.[a-z]{2,4})',  # filename.ext
            r'([A-Za-z0-9_/-]+\.(?:jpg|png|pdf|doc|docx|xls|xlsx|txt|csv|log))'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technical_info['file_names'].extend(matches)
        
        technical_info['file_names'] = list(set(technical_info['file_names']))
        
        return technical_info
    
    def _extract_business_information(self, text: str) -> Dict:
        """Extract business-related information."""
        business_info = {
            'company_mentioned': [],
            'dates_mentioned': [],
            'money_amounts': [],
            'departments': [],
            'roles_titles': [],
            'business_processes': []
        }
        
        # Extract company names (basic pattern)
        company_patterns = [
            r'at\s+([A-Z][A-Za-z\s&.,-]{2,30}(?:Inc|Corp|LLC|Ltd|Co)\.?)',
            r'([A-Z][A-Za-z\s&.,-]{2,30}(?:Inc|Corp|LLC|Ltd|Co)\.?)',
            r'work(?:ing)?\s+(?:at|for)\s+([A-Z][A-Za-z\s&.-]{2,30})'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            business_info['company_mentioned'].extend(matches)
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})',
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            business_info['dates_mentioned'].extend(matches)
        
        # Extract money amounts
        money_patterns = [
            r'\$([0-9,]+(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?)',
            r'(USD\s*\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            business_info['money_amounts'].extend(matches)
        
        # Extract departments
        departments = [
            'sales', 'marketing', 'support', 'engineering', 'finance', 'hr',
            'human resources', 'it', 'legal', 'operations', 'development',
            'customer service', 'billing', 'accounting'
        ]
        
        text_lower = text.lower()
        for dept in departments:
            if dept in text_lower:
                business_info['departments'].append(dept)
        
        # Extract job titles/roles
        role_patterns = [
            r'\b(manager|director|ceo|cto|cfo|president|vp|vice president|coordinator|analyst|specialist|lead|senior|junior)\b'
        ]
        
        for pattern in role_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            business_info['roles_titles'].extend(matches)
        
        # Remove duplicates
        for key in business_info:
            if isinstance(business_info[key], list):
                business_info[key] = list(set(business_info[key]))
        
        return business_info
    
    def _fallback_requirements_extraction(self, subject: str, body: str) -> Dict:
        """Fallback method for requirements extraction when AI fails."""
        requirements = {
            'primary_request': subject,
            'specific_features': [],
            'deadlines': [],
            'business_impact': '',
            'requested_actions': [],
            'technical_specs': [],
            'urgency_reasons': [],
            'additional_context': 'Fallback extraction used due to AI analysis error'
        }
        
        # Simple keyword-based extraction
        text_lower = f"{subject} {body}".lower()
        
        # Check for common requests
        if any(word in text_lower for word in ['help', 'support', 'assistance']):
            requirements['requested_actions'].append('Provide assistance')
        
        if any(word in text_lower for word in ['fix', 'resolve', 'solve']):
            requirements['requested_actions'].append('Fix issue')
        
        if any(word in text_lower for word in ['information', 'details', 'explain']):
            requirements['requested_actions'].append('Provide information')
        
        # Check for deadlines
        deadline_words = ['deadline', 'by', 'before', 'urgent', 'asap', 'immediately']
        if any(word in text_lower for word in deadline_words):
            requirements['urgency_reasons'].append('Time-sensitive request')
        
        return requirements
    
    def _calculate_confidence_score(self, contact_info: Dict, requirements: Dict, technical_info: Dict) -> float:
        """Calculate a confidence score for the extraction."""
        score = 0.0
        
        # Contact information found
        if contact_info['phone_numbers']:
            score += 0.2
        if contact_info['alternate_emails']:
            score += 0.1
        
        # Requirements extracted
        if requirements['primary_request']:
            score += 0.3
        if requirements['requested_actions']:
            score += 0.2
        
        # Technical information found
        if technical_info['error_codes'] or technical_info['product_versions']:
            score += 0.2
        
        return min(1.0, score)
    
    def batch_extract_information(self, emails: List[Dict]) -> List[Dict]:
        """Extract information from multiple emails."""
        print(f"🔍 Starting information extraction for {len(emails)} emails...")
        
        emails_with_extraction = []
        
        for i, email in enumerate(emails, 1):
            print(f"📊 Extracting from email {i}/{len(emails)}: {email.get('subject', 'No Subject')[:30]}...")
            
            try:
                extracted_info = self.extract_information(email)
                
                # Add extraction to email data
                email_with_extraction = email.copy()
                email_with_extraction['extracted_info'] = extracted_info
                
                emails_with_extraction.append(email_with_extraction)
                
            except Exception as e:
                print(f"⚠️ Error extracting information from email {i}: {e}")
                # Add email with minimal extraction
                email_with_extraction = email.copy()
                email_with_extraction['extracted_info'] = {
                    'contact_details': {'phone_numbers': [], 'alternate_emails': []},
                    'customer_requirements': {'primary_request': email.get('subject', ''), 'requested_actions': []},
                    'sentiment_indicators': {},
                    'technical_information': {},
                    'business_information': {},
                    'extraction_metadata': {
                        'extracted_at': datetime.now().isoformat(),
                        'extraction_methods': ['fallback'],
                        'confidence_score': 0.1
                    }
                }
                emails_with_extraction.append(email_with_extraction)
        
        print(f"✅ Information extraction completed! {len(emails_with_extraction)} emails processed.")
        return emails_with_extraction
    
    def display_extraction_summary(self, emails_with_extraction: List[Dict]):
        """Display a summary of extracted information."""
        if not emails_with_extraction:
            print("📭 No extraction data to display.")
            return
        
        print(f"\n🔍 INFORMATION EXTRACTION SUMMARY")
        print("=" * 80)
        
        # Calculate statistics
        total_emails = len(emails_with_extraction)
        phones_found = sum(1 for email in emails_with_extraction 
                          if email.get('extracted_info', {}).get('contact_details', {}).get('phone_numbers'))
        alt_emails_found = sum(1 for email in emails_with_extraction 
                              if email.get('extracted_info', {}).get('contact_details', {}).get('alternate_emails'))
        technical_info_found = sum(1 for email in emails_with_extraction 
                                  if any(email.get('extracted_info', {}).get('technical_information', {}).values()))
        
        avg_confidence = sum(email.get('extracted_info', {}).get('extraction_metadata', {}).get('confidence_score', 0)
                           for email in emails_with_extraction) / total_emails if total_emails > 0 else 0
        
        print(f"Total emails processed: {total_emails}")
        print(f"Phone numbers found: {phones_found} ({phones_found/total_emails*100:.1f}%)")
        print(f"Alternate emails found: {alt_emails_found} ({alt_emails_found/total_emails*100:.1f}%)")
        print(f"Technical information found: {technical_info_found} ({technical_info_found/total_emails*100:.1f}%)")
        print(f"Average extraction confidence: {avg_confidence:.2f}")
        
        print(f"\n📋 EXTRACTED INFORMATION PREVIEW:")
        print("-" * 80)
        
        for i, email in enumerate(emails_with_extraction[:5], 1):  # Show first 5
            extracted = email.get('extracted_info', {})
            contact = extracted.get('contact_details', {})
            requirements = extracted.get('customer_requirements', {})
            confidence = extracted.get('extraction_metadata', {}).get('confidence_score', 0)
            
            sender = email.get('sender_name') or email.get('sender_email', 'Unknown')
            subject = email.get('subject', 'No Subject')[:40]
            
            print(f"📧 {i}. {sender[:25]:<25} | {subject}")
            print(f"     Confidence: {confidence:.2f} | Phones: {len(contact.get('phone_numbers', []))} | " +
                  f"Alt Emails: {len(contact.get('alternate_emails', []))}")
            print(f"     Request: {requirements.get('primary_request', 'N/A')[:60]}...")
            print()
        
        if len(emails_with_extraction) > 5:
            print(f"... and {len(emails_with_extraction) - 5} more emails")
        
        print("-" * 80)

def main():
    """Main function for testing information extraction."""
    print("🔍 Information Extraction Test")
    print("=" * 50)
    
    # Test with sample email data
    sample_emails = [
        {
            'subject': 'URGENT: Cannot access my account - need immediate help!',
            'body': '''Hi there,
            
            I cannot access my account john.doe@mycompany.com and I have an important deadline today at 5 PM. 
            This is critical for my business as we have a client presentation.
            
            My phone number is (555) 123-4567 if you need to call me directly.
            I'm using Chrome version 91.2 on Windows 10.
            
            Error code: AUTH_FAILED_2023
            
            Please help immediately!
            
            John Doe
            Project Manager
            TechCorp Inc.''',
            'sender_email': 'john@example.com',
            'sender_name': 'John Doe'
        },
        {
            'subject': 'Question about product features and pricing',
            'body': '''Hello,
            
            I'm interested in learning more about your software features, specifically:
            1. User management capabilities
            2. API integration options
            3. Reporting and analytics tools
            
            Our company (DataSolutions LLC) is looking for a solution that can handle 500+ users.
            We'd also like to know about enterprise pricing for our Q2 budget planning.
            
            You can reach me at mike.johnson@datasolutions.com or call me at +1-800-555-0199.
            
            Thanks,
            Mike Johnson
            IT Director''',
            'sender_email': 'mike@example.com',
            'sender_name': 'Mike Johnson'
        }
    ]
    
    # Initialize extractor
    extractor = InformationExtractor()
    
    # Extract information
    emails_with_extraction = extractor.batch_extract_information(sample_emails)
    
    # Display summary
    extractor.display_extraction_summary(emails_with_extraction)
    
    # Show detailed extraction for first email
    if emails_with_extraction:
        print(f"\n🔍 DETAILED EXTRACTION EXAMPLE:")
        print("=" * 80)
        
        first_email = emails_with_extraction[0]
        extracted = first_email.get('extracted_info', {})
        
        print(f"Email: {first_email.get('subject', 'No Subject')}")
        print(f"Sender: {first_email.get('sender_name', 'Unknown')}")
        print("\nExtracted Information:")
        print(json.dumps(extracted, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
