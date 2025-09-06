from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import datetime, timedelta

from .models import Email, DailyStats
from .serializers import (
    EmailSerializer, EmailListSerializer, DailyStatsSerializer,
    EmailResponseSerializer, DashboardStatsSerializer
)
from .services import EmailAnalysisService, PerplexityService

@method_decorator(csrf_exempt, name='dispatch')
class EmailViewSet(viewsets.ModelViewSet):
    """ViewSet for managing emails"""
    queryset = Email.objects.all()
    permission_classes = [AllowAny]  # Allow public access for demo
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmailListSerializer
        return EmailSerializer
    
    def get_queryset(self):
        queryset = Email.objects.all()
        
        # Time-based filtering (default to today)
        time_filter = self.request.query_params.get('time_filter', 'today')
        queryset = self.apply_time_filter(queryset, time_filter)
        
        # Filter by query parameters
        priority = self.request.query_params.get('priority')
        sentiment = self.request.query_params.get('sentiment')
        category = self.request.query_params.get('category')
        is_urgent = self.request.query_params.get('is_urgent')
        is_responded = self.request.query_params.get('is_responded')
        search = self.request.query_params.get('search')
        
        if priority:
            queryset = queryset.filter(priority=priority)
        if sentiment:
            queryset = queryset.filter(sentiment=sentiment)
        if category:
            queryset = queryset.filter(category=category)
        if is_urgent is not None:
            queryset = queryset.filter(is_urgent=is_urgent.lower() == 'true')
        if is_responded is not None:
            queryset = queryset.filter(is_responded=is_responded.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(sender_email__icontains=search) |
                Q(subject__icontains=search) |
                Q(body__icontains=search)
            )
        
        return queryset
    
    def apply_time_filter(self, queryset, time_filter):
        """Apply time-based filtering to queryset"""
        now = timezone.now()
        
        if time_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(received_at__gte=start_date)
        elif time_filter == 'yesterday':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(received_at__gte=start_date, received_at__lt=end_date)
        elif time_filter == 'this-week':
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(received_at__gte=start_date)
        elif time_filter == 'this-month':
            # Start of current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            queryset = queryset.filter(received_at__gte=start_date)
        # 'all' or invalid filter - return all emails
        
        return queryset.order_by('-is_urgent', '-received_at')
    
    @action(detail=True, methods=['post'])
    def generate_response(self, request, pk=None):
        """Generate or regenerate AI response for an email"""
        email = self.get_object()
        
        try:
            perplexity = PerplexityService()
            
            # Prepare sentiment analysis data - handle both dict and string cases
            sentiment_data = {}
            if hasattr(email, 'sentiment_analysis') and email.sentiment_analysis:
                if isinstance(email.sentiment_analysis, dict):
                    sentiment_data = email.sentiment_analysis
                elif isinstance(email.sentiment_analysis, str):
                    try:
                        import json
                        sentiment_data = json.loads(email.sentiment_analysis)
                    except (json.JSONDecodeError, TypeError):
                        # If parsing fails, create basic sentiment data
                        sentiment_data = {
                            'sentiment': email.sentiment or 'neutral',
                            'empathy_required': email.sentiment == 'negative',
                            'emotional_tone': email.sentiment or 'neutral',
                            'customer_mood': f"Customer appears {email.sentiment or 'neutral'}"
                        }
            else:
                # Create basic sentiment data from existing fields
                sentiment_data = {
                    'sentiment': email.sentiment or 'neutral',
                    'empathy_required': email.sentiment == 'negative',
                    'emotional_tone': email.sentiment or 'neutral',
                    'customer_mood': f"Customer appears {email.sentiment or 'neutral'}"
                }
            
            email.ai_response = perplexity.generate_response(
                email.body, email.subject, email.sender_email,
                sentiment_data, email.category or 'general'
            )
            email.response_generated_at = timezone.now()
            email.save()
            
            return Response({
                'success': True,
                'response': email.ai_response,
                'generated_at': email.response_generated_at
            })
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating response: {str(e)}")
            print(f"Full traceback: {error_details}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def mark_responded(self, request, pk=None):
        """Mark email as responded"""
        email = self.get_object()
        email.is_responded = True
        email.save()
        
        # Update daily stats
        today = timezone.now().date()
        if hasattr(email, 'received_at') and email.received_at.date() == today:
            try:
                stats = DailyStats.objects.get(date=today)
                stats.responded_emails = Email.objects.filter(
                    received_at__date=today,
                    is_responded=True
                ).count()
                stats.pending_emails = Email.objects.filter(
                    received_at__date=today,
                    is_responded=False
                ).count()
                stats.save()
            except DailyStats.DoesNotExist:
                pass
        
        return Response({'success': True, 'message': 'Email marked as responded'})
    
    @action(detail=False, methods=['get'])
    def by_time(self, request):
        """Get emails filtered by time period"""
        time_filter = request.query_params.get('period', 'today')
        
        # Get emails for the specified time period
        queryset = Email.objects.all()
        queryset = self.apply_time_filter(queryset, time_filter)
        
        # Get statistics for the period
        total_count = queryset.count()
        urgent_count = queryset.filter(is_urgent=True).count()
        responded_count = queryset.filter(is_responded=True).count()
        pending_count = queryset.filter(is_responded=False).count()
        
        # Get sentiment breakdown
        sentiment_stats = queryset.values('sentiment').annotate(count=Count('sentiment'))
        sentiment_breakdown = {item['sentiment']: item['count'] for item in sentiment_stats if item['sentiment']}
        
        # Get category breakdown
        category_stats = queryset.values('category').annotate(count=Count('category'))
        category_breakdown = {item['category']: item['count'] for item in category_stats if item['category']}
        
        # Serialize emails
        page = self.paginate_queryset(queryset.order_by('-is_urgent', '-received_at'))
        if page is not None:
            serializer = EmailListSerializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            
            # Add statistics to response
            result.data['statistics'] = {
                'period': time_filter,
                'total_emails': total_count,
                'urgent_emails': urgent_count,
                'responded_emails': responded_count,
                'pending_emails': pending_count,
                'sentiment_breakdown': sentiment_breakdown,
                'category_breakdown': category_breakdown
            }
            
            return result
        
        serializer = EmailListSerializer(queryset.order_by('-is_urgent', '-received_at'), many=True)
        return Response({
            'emails': serializer.data,
            'statistics': {
                'period': time_filter,
                'total_emails': total_count,
                'urgent_emails': urgent_count,
                'responded_emails': responded_count,
                'pending_emails': pending_count,
                'sentiment_breakdown': sentiment_breakdown,
                'category_breakdown': category_breakdown
            }
        })
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get all urgent emails"""
        urgent_emails = self.get_queryset().filter(is_urgent=True)
        serializer = EmailListSerializer(urgent_emails, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending (unresponded) emails"""
        pending_emails = self.get_queryset().filter(is_responded=False)
        serializer = EmailListSerializer(pending_emails, many=True)
        return Response(serializer.data)

class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for daily statistics"""
    queryset = DailyStats.objects.all()
    serializer_class = DailyStatsSerializer
    permission_classes = [AllowAny]  # Allow public access for demo
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's statistics"""
        today = timezone.now().date()
        try:
            stats = DailyStats.objects.get(date=today)
            serializer = DailyStatsSerializer(stats)
            return Response(serializer.data)
        except DailyStats.DoesNotExist:
            return Response({
                'date': today,
                'total_emails': 0,
                'urgent_emails': 0,
                'responded_emails': 0,
                'pending_emails': 0,
                'positive_emails': 0,
                'negative_emails': 0,
                'neutral_emails': 0,
                'technical_issues': 0,
                'account_support': 0,
                'product_inquiries': 0,
                'billing_issues': 0,
                'general_inquiries': 0
            })
    
    @action(detail=False, methods=['get'])
    def last_7_days(self, request):
        """Get statistics for the last 7 days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        stats = DailyStats.objects.filter(date__range=[start_date, end_date])
        serializer = DailyStatsSerializer(stats, many=True)
        return Response(serializer.data)

class DashboardViewSet(viewsets.ViewSet):
    """ViewSet for dashboard data"""
    permission_classes = [AllowAny]  # Allow public access for demo
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview data with time filtering (default: today)"""
        time_filter = request.query_params.get('time_filter', 'today')
        
        # Apply time filter to get relevant emails
        today = timezone.now().date()
        all_emails = Email.objects.all()
        
        # Filter emails by time period
        if time_filter == 'today':
            start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            filtered_emails = all_emails.filter(received_at__gte=start_date)
            period_label = "Today"
        elif time_filter == 'yesterday':
            start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            filtered_emails = all_emails.filter(received_at__gte=start_date, received_at__lt=end_date)
            period_label = "Yesterday"
        elif time_filter == 'this-week':
            days_since_monday = timezone.now().weekday()
            start_date = (timezone.now() - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            filtered_emails = all_emails.filter(received_at__gte=start_date)
            period_label = "This Week"
        elif time_filter == 'this-month':
            start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filtered_emails = all_emails.filter(received_at__gte=start_date)
            period_label = "This Month"
        else:  # 'all'
            filtered_emails = all_emails
            period_label = "All Time"
        
        # Today's stats (always show today's stats)
        try:
            today_stats = DailyStats.objects.get(date=today)
        except DailyStats.DoesNotExist:
            today_stats = DailyStats(date=today)
        
        # Recent emails from filtered period (last 10)
        recent_emails = filtered_emails.order_by('-received_at')[:10]
        
        # Counts for filtered period
        total_count = filtered_emails.count()
        urgent_count = filtered_emails.filter(is_urgent=True).count()
        pending_count = filtered_emails.filter(is_responded=False).count()
        responded_count = filtered_emails.filter(is_responded=True).count()
        
        # Sentiment breakdown for filtered period
        sentiment_breakdown = filtered_emails.values('sentiment').annotate(count=Count('sentiment'))
        sentiment_dict = {item['sentiment']: item['count'] for item in sentiment_breakdown if item['sentiment']}
        
        # Category breakdown for filtered period
        category_breakdown = filtered_emails.values('category').annotate(count=Count('category'))
        category_dict = {item['category']: item['count'] for item in category_breakdown if item['category']}
        
        data = {
            'time_filter': {
                'period': time_filter,
                'label': period_label,
                'total_emails': total_count,
                'urgent_emails': urgent_count,
                'pending_emails': pending_count,
                'responded_emails': responded_count
            },
            'today_stats': DailyStatsSerializer(today_stats).data,
            'recent_emails': EmailListSerializer(recent_emails, many=True).data,
            'urgent_count': urgent_count,
            'pending_count': pending_count,
            'sentiment_breakdown': sentiment_dict,
            'category_breakdown': category_dict
        }
        
        return Response(data)

def dashboard_view(request):
    """Render the main dashboard template"""
    return render(request, 'emailbot/dashboard.html')
