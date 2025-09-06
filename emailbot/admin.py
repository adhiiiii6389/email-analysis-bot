from django.contrib import admin
from .models import Email, DailyStats, APIKey

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['sender_email', 'subject_truncated', 'sentiment', 'priority', 'category', 'received_at', 'is_responded']
    list_filter = ['sentiment', 'priority', 'category', 'is_responded', 'is_urgent', 'received_at']
    search_fields = ['sender_email', 'subject', 'body']
    readonly_fields = ['processed_at', 'response_generated_at']
    list_per_page = 25
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Email Information', {
            'fields': ('sender_email', 'subject', 'body', 'received_at')
        }),
        ('Analysis Results', {
            'fields': ('sentiment', 'sentiment_confidence', 'priority', 'category', 'is_urgent')
        }),
        ('Extracted Information', {
            'fields': ('extracted_info',)
        }),
        ('AI Response', {
            'fields': ('ai_response', 'response_generated_at', 'is_responded')
        }),
        ('Timestamps', {
            'fields': ('processed_at',),
            'classes': ('collapse',)
        }),
    )
    
    def subject_truncated(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
    subject_truncated.short_description = 'Subject'

@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_emails', 'urgent_emails', 'responded_emails', 'pending_emails']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'key_prefix', 'is_active', 'usage_count', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['usage_count', 'last_used', 'created_at']
