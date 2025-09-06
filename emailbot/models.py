from django.db import models
from django.utils import timezone

from django.db import models
from django.utils import timezone

class Email(models.Model):
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('normal', 'Normal'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical_issue', 'Technical Issue'),
        ('account_support', 'Account Support'),
        ('product_inquiry', 'Product Inquiry'),
        ('billing', 'Billing'),
        ('general', 'General'),
    ]
    
    # Gmail specific fields
    message_id = models.CharField(max_length=200, unique=True, null=True, blank=True)
    thread_id = models.CharField(max_length=200, null=True, blank=True)
    snippet = models.TextField(null=True, blank=True)
    
    # Email metadata
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    received_at = models.DateTimeField()
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis results
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, null=True, blank=True)
    sentiment_confidence = models.FloatField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    
    # Extracted information
    extracted_info = models.JSONField(default=dict, blank=True)  # Phone, alternate email, requirements, etc.
    
    # AI response
    ai_response = models.TextField(null=True, blank=True)
    response_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    is_responded = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_urgent', '-received_at']
        indexes = [
            models.Index(fields=['received_at']),
            models.Index(fields=['priority']),
            models.Index(fields=['sentiment']),
            models.Index(fields=['is_urgent']),
            models.Index(fields=['message_id']),
        ]
    
    def __str__(self):
        return f"{self.sender_email} - {self.subject[:50]}"
    
    def save(self, *args, **kwargs):
        if self.priority == 'urgent':
            self.is_urgent = True
        super().save(*args, **kwargs)


class DailyStats(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    total_emails = models.IntegerField(default=0)
    urgent_emails = models.IntegerField(default=0)
    responded_emails = models.IntegerField(default=0)
    pending_emails = models.IntegerField(default=0)
    
    # Sentiment breakdown
    positive_emails = models.IntegerField(default=0)
    negative_emails = models.IntegerField(default=0)
    neutral_emails = models.IntegerField(default=0)
    
    # Category breakdown
    technical_issues = models.IntegerField(default=0)
    account_support = models.IntegerField(default=0)
    product_inquiries = models.IntegerField(default=0)
    billing_issues = models.IntegerField(default=0)
    general_inquiries = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date}"


class APIKey(models.Model):
    name = models.CharField(max_length=100)
    key_prefix = models.CharField(max_length=20)  # Store only first few characters for identification
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
