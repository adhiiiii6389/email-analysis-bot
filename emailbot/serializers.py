from rest_framework import serializers
from .models import Email, DailyStats, APIKey

class EmailSerializer(serializers.ModelSerializer):
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Email
        fields = [
            'id', 'sender_email', 'subject', 'body', 'received_at', 'processed_at',
            'sentiment', 'sentiment_display', 'sentiment_confidence',
            'priority', 'priority_display', 'category', 'category_display',
            'extracted_info', 'ai_response', 'response_generated_at',
            'is_responded', 'is_urgent'
        ]
        read_only_fields = ['id', 'processed_at', 'response_generated_at']

class EmailListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Email
        fields = [
            'id', 'sender_email', 'subject', 'received_at',
            'sentiment', 'sentiment_display', 'priority', 'priority_display',
            'category', 'category_display', 'is_responded', 'is_urgent'
        ]

class DailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStats
        fields = [
            'id', 'date', 'total_emails', 'urgent_emails', 'responded_emails', 'pending_emails',
            'positive_emails', 'negative_emails', 'neutral_emails',
            'technical_issues', 'account_support', 'product_inquiries', 
            'billing_issues', 'general_inquiries', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailResponseSerializer(serializers.Serializer):
    """Serializer for generating AI responses"""
    email_id = serializers.IntegerField()
    regenerate = serializers.BooleanField(default=False)

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard overview"""
    today_stats = DailyStatsSerializer()
    recent_emails = EmailListSerializer(many=True)
    urgent_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    sentiment_breakdown = serializers.DictField()
    category_breakdown = serializers.DictField()
