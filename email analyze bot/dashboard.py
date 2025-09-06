#!/usr/bin/env python3
"""
Email Analyze Bot Dashboard
Main application that coordinates all modules and provides a dashboard interface.
"""

import os
import sys
import json
import time
from datetime import datetime, date
from typing import Dict, List
import traceback

# Import our custom modules
from email_retrieval import EmailRetriever
from email_analyzer import EmailAnalyzer
from response_generator import ResponseGenerator
from information_extractor import InformationExtractor
from database_manager import DatabaseManager

class EmailAnalyzeBotDashboard:
    def __init__(self):
        """Initialize the Email Analyze Bot with all components."""
        print("🤖 Initializing Email Analyze Bot Dashboard...")
        print("=" * 60)
        
        try:
            # Initialize all components
            self.email_retriever = EmailRetriever()
            self.email_analyzer = EmailAnalyzer()
            self.response_generator = ResponseGenerator()
            self.information_extractor = InformationExtractor()
            self.database_manager = DatabaseManager()
            
            print("✅ All components initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def run_complete_analysis(self):
        """Run the complete email analysis pipeline."""
        print(f"\n🚀 STARTING COMPLETE EMAIL ANALYSIS PIPELINE")
        print("=" * 60)
        print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Retrieve today's emails
            print(f"\n📧 STEP 1: EMAIL RETRIEVAL")
            print("-" * 40)
            
            all_emails = self.email_retriever.get_todays_emails()
            
            if not all_emails:
                print("📭 No emails found for today. Analysis complete.")
                return
            
            # Filter for support-related emails
            support_emails = self.email_retriever.filter_support_emails(all_emails)
            
            if not support_emails:
                print("📭 No support-related emails found for today.")
                return
            
            print(f"✅ Found {len(support_emails)} support-related emails to analyze")
            
            # Step 2: Analyze emails (sentiment, priority, categorization)
            print(f"\n🔍 STEP 2: EMAIL ANALYSIS & CATEGORIZATION")
            print("-" * 40)
            
            analyzed_emails = self.email_analyzer.batch_analyze_emails(support_emails)
            
            # Step 3: Extract information
            print(f"\n📊 STEP 3: INFORMATION EXTRACTION")
            print("-" * 40)
            
            emails_with_extraction = self.information_extractor.batch_extract_information(analyzed_emails)
            
            # Step 4: Generate auto-responses
            print(f"\n🤖 STEP 4: AUTO-RESPONSE GENERATION")
            print("-" * 40)
            
            complete_emails = self.response_generator.batch_generate_responses(emails_with_extraction)
            
            # Step 5: Store in database
            print(f"\n💾 STEP 5: DATABASE STORAGE")
            print("-" * 40)
            
            stored_ids = self.database_manager.batch_store_emails(complete_emails)
            
            # Step 6: Update daily statistics
            print(f"\n📈 STEP 6: UPDATING STATISTICS")
            print("-" * 40)
            
            self.database_manager.update_daily_stats()
            
            # Step 7: Generate summary report
            print(f"\n📋 STEP 7: GENERATING SUMMARY REPORT")
            print("-" * 40)
            
            self.generate_analysis_report(complete_emails, stored_ids)
            
            print(f"\n🎉 ANALYSIS PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error in analysis pipeline: {e}")
            traceback.print_exc()
    
    def generate_analysis_report(self, complete_emails: List[Dict], stored_ids: List[int]):
        """Generate a comprehensive analysis report."""
        try:
            report_data = {
                'analysis_date': date.today().isoformat(),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_emails_processed': len(complete_emails),
                'emails_stored': len(stored_ids),
                'statistics': self._calculate_analysis_statistics(complete_emails),
                'priority_breakdown': self._get_priority_breakdown(complete_emails),
                'sentiment_breakdown': self._get_sentiment_breakdown(complete_emails),
                'category_breakdown': self._get_category_breakdown(complete_emails),
                'top_issues': self._identify_top_issues(complete_emails),
                'response_summary': self._get_response_summary(complete_emails)
            }
            
            # Save report to file
            report_filename = f"email_analysis_report_{date.today().isoformat()}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Save detailed report as text
            text_report_filename = f"email_analysis_report_{date.today().isoformat()}.txt"
            self._save_text_report(report_data, complete_emails, text_report_filename)
            
            print(f"✅ Analysis report saved to:")
            print(f"   - JSON: {report_filename}")
            print(f"   - Text: {text_report_filename}")
            
            # Display summary
            self.display_analysis_summary(report_data)
            
        except Exception as e:
            print(f"⚠️ Error generating analysis report: {e}")
    
    def _calculate_analysis_statistics(self, emails: List[Dict]) -> Dict:
        """Calculate overall statistics from analyzed emails."""
        if not emails:
            return {}
        
        total = len(emails)
        urgent = sum(1 for email in emails if email.get('priority') == 'urgent')
        positive = sum(1 for email in emails if email.get('sentiment') == 'positive')
        negative = sum(1 for email in emails if email.get('sentiment') == 'negative')
        neutral = sum(1 for email in emails if email.get('sentiment') == 'neutral')
        
        # Calculate average sentiment score
        sentiment_scores = [email.get('sentiment_score', 0.5) for email in emails]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        
        # Count emails with contact info extracted
        with_phone = sum(1 for email in emails 
                        if email.get('extracted_info', {}).get('contact_details', {}).get('phone_numbers'))
        with_alt_email = sum(1 for email in emails 
                           if email.get('extracted_info', {}).get('contact_details', {}).get('alternate_emails'))
        
        return {
            'total_emails': total,
            'urgent_emails': urgent,
            'urgent_percentage': round(urgent / total * 100, 1) if total > 0 else 0,
            'positive_emails': positive,
            'negative_emails': negative,
            'neutral_emails': neutral,
            'average_sentiment_score': round(avg_sentiment, 2),
            'emails_with_phone': with_phone,
            'emails_with_alt_email': with_alt_email,
            'contact_extraction_rate': round((with_phone + with_alt_email) / total * 100, 1) if total > 0 else 0
        }
    
    def _get_priority_breakdown(self, emails: List[Dict]) -> Dict:
        """Get breakdown of emails by priority."""
        priorities = {}
        for email in emails:
            priority = email.get('priority', 'normal')
            priorities[priority] = priorities.get(priority, 0) + 1
        return priorities
    
    def _get_sentiment_breakdown(self, emails: List[Dict]) -> Dict:
        """Get breakdown of emails by sentiment."""
        sentiments = {}
        for email in emails:
            sentiment = email.get('sentiment', 'neutral')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        return sentiments
    
    def _get_category_breakdown(self, emails: List[Dict]) -> Dict:
        """Get breakdown of emails by category."""
        categories = {}
        for email in emails:
            category = email.get('category', 'General Support')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _identify_top_issues(self, emails: List[Dict]) -> List[Dict]:
        """Identify top issues based on keywords and categories."""
        issue_keywords = {}
        
        for email in emails:
            keywords = email.get('keywords', [])
            for keyword in keywords:
                if keyword not in issue_keywords:
                    issue_keywords[keyword] = {
                        'count': 0,
                        'urgent_count': 0,
                        'negative_count': 0
                    }
                
                issue_keywords[keyword]['count'] += 1
                
                if email.get('priority') == 'urgent':
                    issue_keywords[keyword]['urgent_count'] += 1
                
                if email.get('sentiment') == 'negative':
                    issue_keywords[keyword]['negative_count'] += 1
        
        # Sort by frequency and urgency
        top_issues = []
        for keyword, data in issue_keywords.items():
            score = data['count'] + (data['urgent_count'] * 2) + (data['negative_count'] * 1.5)
            top_issues.append({
                'keyword': keyword,
                'total_mentions': data['count'],
                'urgent_mentions': data['urgent_count'],
                'negative_mentions': data['negative_count'],
                'priority_score': round(score, 1)
            })
        
        # Return top 10 issues
        return sorted(top_issues, key=lambda x: x['priority_score'], reverse=True)[:10]
    
    def _get_response_summary(self, emails: List[Dict]) -> Dict:
        """Get summary of generated responses."""
        total_responses = sum(1 for email in emails if email.get('response_body'))
        context_used = sum(1 for email in emails if email.get('context_used', False))
        
        return {
            'total_responses_generated': total_responses,
            'responses_with_context': context_used,
            'context_usage_rate': round(context_used / total_responses * 100, 1) if total_responses > 0 else 0
        }
    
    def _save_text_report(self, report_data: Dict, complete_emails: List[Dict], filename: str):
        """Save a detailed text report."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("EMAIL ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Analysis Date: {report_data['analysis_date']}\n")
                f.write(f"Analysis Time: {report_data['analysis_time']}\n")
                f.write(f"Total Emails Processed: {report_data['total_emails_processed']}\n")
                f.write(f"Emails Stored in Database: {report_data['emails_stored']}\n\n")
                
                # Statistics
                stats = report_data['statistics']
                f.write("OVERALL STATISTICS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Urgent Emails: {stats.get('urgent_emails', 0)} ({stats.get('urgent_percentage', 0)}%)\n")
                f.write(f"Average Sentiment Score: {stats.get('average_sentiment_score', 0)}\n")
                f.write(f"Contact Extraction Rate: {stats.get('contact_extraction_rate', 0)}%\n\n")
                
                # Priority breakdown
                f.write("PRIORITY BREAKDOWN\n")
                f.write("-" * 40 + "\n")
                for priority, count in report_data['priority_breakdown'].items():
                    f.write(f"{priority.title()}: {count}\n")
                f.write("\n")
                
                # Sentiment breakdown
                f.write("SENTIMENT BREAKDOWN\n")
                f.write("-" * 40 + "\n")
                for sentiment, count in report_data['sentiment_breakdown'].items():
                    f.write(f"{sentiment.title()}: {count}\n")
                f.write("\n")
                
                # Category breakdown
                f.write("CATEGORY BREAKDOWN\n")
                f.write("-" * 40 + "\n")
                for category, count in report_data['category_breakdown'].items():
                    f.write(f"{category}: {count}\n")
                f.write("\n")
                
                # Top issues
                f.write("TOP ISSUES (by priority score)\n")
                f.write("-" * 40 + "\n")
                for i, issue in enumerate(report_data['top_issues'][:10], 1):
                    f.write(f"{i:2d}. {issue['keyword']} (Score: {issue['priority_score']}, " +
                           f"Total: {issue['total_mentions']}, Urgent: {issue['urgent_mentions']})\n")
                f.write("\n")
                
                # Detailed email list
                f.write("DETAILED EMAIL ANALYSIS\n")
                f.write("=" * 80 + "\n")
                
                # Sort emails by priority and sentiment
                sorted_emails = sorted(complete_emails, 
                                     key=lambda x: (0 if x.get('priority') == 'urgent' else 1,
                                                   1 if x.get('sentiment') == 'negative' else 2))
                
                for i, email in enumerate(sorted_emails, 1):
                    f.write(f"\nEMAIL #{i}\n")
                    f.write("-" * 50 + "\n")
                    f.write(f"From: {email.get('sender_name', 'Unknown')} <{email.get('sender_email', 'unknown@email.com')}>\n")
                    f.write(f"Subject: {email.get('subject', 'No Subject')}\n")
                    f.write(f"Priority: {email.get('priority', 'normal').upper()}\n")
                    f.write(f"Sentiment: {email.get('sentiment', 'neutral').upper()} (Score: {email.get('sentiment_score', 0.5)})\n")
                    f.write(f"Category: {email.get('category', 'Unknown')}\n")
                    
                    # Contact info
                    extracted = email.get('extracted_info', {})
                    contact = extracted.get('contact_details', {})
                    if contact.get('phone_numbers') or contact.get('alternate_emails'):
                        f.write(f"Contact Info: ")
                        if contact.get('phone_numbers'):
                            f.write(f"Phone: {', '.join(contact['phone_numbers'])} ")
                        if contact.get('alternate_emails'):
                            f.write(f"Alt Email: {', '.join(contact['alternate_emails'])}")
                        f.write("\n")
                    
                    # Requirements
                    requirements = extracted.get('customer_requirements', {})
                    if requirements.get('primary_request'):
                        f.write(f"Primary Request: {requirements['primary_request']}\n")
                    
                    # Response preview
                    if email.get('response_body'):
                        f.write(f"Response Generated: Yes (Subject: {email.get('response_subject', 'N/A')})\n")
                        f.write(f"Response Preview: {email.get('response_body', '')[:100]}...\n")
                    
                    f.write("-" * 50 + "\n")
                
        except Exception as e:
            print(f"⚠️ Error saving text report: {e}")
    
    def display_analysis_summary(self, report_data: Dict):
        """Display analysis summary on console."""
        print(f"\n📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        stats = report_data.get('statistics', {})
        
        print(f"📧 Total emails processed: {stats.get('total_emails', 0)}")
        print(f"🔥 Urgent emails: {stats.get('urgent_emails', 0)} ({stats.get('urgent_percentage', 0)}%)")
        print(f"📈 Average sentiment score: {stats.get('average_sentiment_score', 0)}")
        print(f"📞 Contact extraction rate: {stats.get('contact_extraction_rate', 0)}%")
        
        print(f"\n📊 Priority Distribution:")
        for priority, count in report_data.get('priority_breakdown', {}).items():
            print(f"   {priority.title()}: {count}")
        
        print(f"\n😊 Sentiment Distribution:")
        for sentiment, count in report_data.get('sentiment_breakdown', {}).items():
            print(f"   {sentiment.title()}: {count}")
        
        print(f"\n📋 Top Categories:")
        categories = report_data.get('category_breakdown', {})
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:5]:
            print(f"   {category}: {count}")
        
        print(f"\n🚨 Top Issues:")
        for i, issue in enumerate(report_data.get('top_issues', [])[:5], 1):
            print(f"   {i}. {issue['keyword']} (Priority Score: {issue['priority_score']})")
        
        print("=" * 60)
    
    def run_dashboard_viewer(self):
        """Run an interactive dashboard viewer."""
        while True:
            print(f"\n🖥️ EMAIL ANALYZE BOT DASHBOARD")
            print("=" * 50)
            print("1. Run Complete Analysis Pipeline")
            print("2. View Today's Dashboard Data")
            print("3. Search Emails")
            print("4. View Database Summary")
            print("5. Generate Reports Only")
            print("6. Exit")
            print("-" * 50)
            
            choice = input("Select an option (1-6): ").strip()
            
            if choice == '1':
                self.run_complete_analysis()
            elif choice == '2':
                self.view_dashboard_data()
            elif choice == '3':
                self.search_emails_interactive()
            elif choice == '4':
                self.database_manager.display_database_summary()
            elif choice == '5':
                self.generate_reports_only()
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def view_dashboard_data(self):
        """View dashboard data for today."""
        try:
            dashboard_data = self.database_manager.get_email_dashboard_data()
            
            print(f"\n📊 TODAY'S DASHBOARD DATA")
            print("=" * 50)
            print(f"Date: {dashboard_data['date']}")
            
            stats = dashboard_data['statistics']
            print(f"Total emails: {stats.get('total_emails', 0)}")
            print(f"Support emails: {stats.get('support_emails', 0)}")
            print(f"Urgent emails: {stats.get('urgent_emails', 0)}")
            print(f"Responses generated: {stats.get('responses_generated', 0)}")
            
            emails = dashboard_data['emails']
            if emails:
                print(f"\n📧 SUPPORT EMAILS ({len(emails)} total):")
                print("-" * 50)
                
                for i, email in enumerate(emails[:10], 1):  # Show first 10
                    priority_icon = "🔥" if email.get('priority') == 'urgent' else "📝"
                    sentiment_icon = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(email.get('sentiment'), '😐')
                    
                    print(f"{priority_icon}{sentiment_icon} {i:2d}. {email.get('sender_name', 'Unknown')[:20]:<20} | " +
                          f"{email.get('subject', 'No Subject')[:40]}")
                
                if len(emails) > 10:
                    print(f"... and {len(emails) - 10} more emails")
            else:
                print("📭 No support emails found for today.")
            
        except Exception as e:
            print(f"❌ Error viewing dashboard data: {e}")
    
    def search_emails_interactive(self):
        """Interactive email search."""
        try:
            search_term = input("Enter search term: ").strip()
            
            if not search_term:
                print("❌ Please enter a search term.")
                return
            
            results = self.database_manager.search_emails(search_term)
            
            if results:
                print(f"\n🔍 SEARCH RESULTS ({len(results)} found)")
                print("-" * 60)
                
                for i, email in enumerate(results[:20], 1):  # Show first 20
                    print(f"{i:2d}. From: {email.get('sender_name', 'Unknown')[:20]:<20} | " +
                          f"Subject: {email.get('subject', 'No Subject')[:35]}")
                    print(f"     Date: {email.get('received_date', 'Unknown')[:19]} | " +
                          f"Priority: {email.get('priority', 'normal')} | " +
                          f"Sentiment: {email.get('sentiment', 'neutral')}")
                    print()
                
                if len(results) > 20:
                    print(f"... and {len(results) - 20} more results")
            else:
                print(f"📭 No emails found matching '{search_term}'")
            
        except Exception as e:
            print(f"❌ Error searching emails: {e}")
    
    def generate_reports_only(self):
        """Generate reports from existing database data."""
        try:
            # Get today's data from database
            dashboard_data = self.database_manager.get_email_dashboard_data()
            emails = dashboard_data.get('emails', [])
            
            if not emails:
                print("📭 No email data found for today. Run the analysis pipeline first.")
                return
            
            print(f"📋 Generating reports for {len(emails)} emails...")
            
            # Generate analysis report
            self.generate_analysis_report(emails, list(range(len(emails))))
            
            print("✅ Reports generated successfully!")
            
        except Exception as e:
            print(f"❌ Error generating reports: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if hasattr(self, 'database_manager'):
                self.database_manager.disconnect()
            print("🧹 Cleanup completed.")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

def main():
    """Main function to run the Email Analyze Bot Dashboard."""
    print("🤖 EMAIL ANALYZE BOT DASHBOARD")
    print("=" * 60)
    print("Advanced Email Analysis System with AI-Powered Insights")
    print("Features: Retrieval, Analysis, Categorization, Auto-Response, Storage")
    print("=" * 60)
    
    dashboard = None
    
    try:
        # Initialize dashboard
        dashboard = EmailAnalyzeBotDashboard()
        
        # Run dashboard interface
        dashboard.run_dashboard_viewer()
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
    finally:
        if dashboard:
            dashboard.cleanup()

if __name__ == "__main__":
    main()
