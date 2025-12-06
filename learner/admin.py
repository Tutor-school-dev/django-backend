from django.contrib import admin
from .models import Learner
from django.contrib.gis.admin import GISModelAdmin


@admin.register(Learner)
class LearnerAdmin(GISModelAdmin):
    list_display = ['name', 'email', 'primary_contact', 'educationLevel', 'board', 'state', 'created_at']
    list_filter = ['educationLevel', 'board', 'preferred_mode', 'state', 'created_at']
    search_fields = ['name', 'email', 'primary_contact', 'secondary_contact', 'guardian_name', 'area', 'pincode']
    readonly_fields = ['id', 'created_at', 'updated_at', 'password_last_modified']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'email', 'primary_contact', 'secondary_contact', 'zoho_id')
        }),
        ('Location', {
            'fields': ('state', 'area', 'pincode', 'location', 'latitude', 'longitude')
        }),
        ('Learner Details', {
            'fields': ('educationLevel', 'board', 'subjects', 'budget', 'preferred_mode')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_email')
        }),
        ('Security', {
            'fields': ('password', 'password_last_modified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    ordering = ['-created_at']
