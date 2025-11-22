from django.contrib import admin
from .models import Teacher
from django.contrib.gis.admin import GISModelAdmin


@admin.register(Teacher)
class TeacherAdmin(GISModelAdmin):
    list_display = ['name', 'email', 'primary_contact', 'teaching_mode', 'state', 'created_at', 'subjects']
    list_filter = ['teaching_mode', 'state', 'basic_done', 'location_done', 'later_onboarding_done', 'created_at']
    search_fields = ['name', 'email', 'primary_contact', 'secondary_contact', 'area', 'pincode']
    readonly_fields = ['id', 'created_at', 'updated_at', 'password_last_modified']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'email', 'primary_contact', 'secondary_contact', 'zoho_id')
        }),
        ('Location', {
            'fields': ('state', 'area', 'pincode', 'location', 'latitude', 'longitude')
        }),
        ('Profile', {
            'fields': ('profile_pic', 'introduction', 'teaching_desc', 'video_url', 'lesson_price', 
                      'current_status', 'teaching_mode', 'university', 'class_level', 'degree')
        }),
        ('Onboarding Status', {
            'fields': ('basic_done', 'location_done', 'later_onboarding_done')
        }),
        ('Security & Subscription', {
            'fields': ('password', 'password_last_modified', 'subscription_validity', 'referral')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    ordering = ['-created_at']
