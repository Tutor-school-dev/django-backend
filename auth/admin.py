from django.contrib import admin
from .models import OTP


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['verification_id', 'otp', 'use_for', 'is_used', 'expires_at', 'created_at']
    list_filter = ['use_for', 'is_used', 'created_at']
    search_fields = ['verification_id', 'otp']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual OTP creation through admin