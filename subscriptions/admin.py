from django.contrib import admin
from .models import Subscription, Payment, UserSubscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price', 'annual_price', 'tuition_applications', 'is_active']
    list_filter = ['is_active', 'verified_badge', 'priority_listing']
    search_fields = ['name', 'description']
    ordering = ['id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'teacher', 'subscription', 'amount', 'status', 'created_at']
    list_filter = ['status', 'subscription', 'created_at']
    search_fields = ['order_id', 'teacher__name', 'teacher__email', 'hdfc_transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subscription', 'duration_months', 'status', 'start_date', 'end_date', 'applications_used']
    list_filter = ['status', 'subscription', 'start_date', 'end_date']
    search_fields = ['teacher__name', 'teacher__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
