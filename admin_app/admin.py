from django.contrib import admin
from .models import JobListing, JobApplication


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ['learner', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['learner__name', 'learner__email', 'learner__primary_contact']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job_listing', 'tutor', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['tutor__name', 'tutor__email', 'job_listing__learner__name']
    readonly_fields = ['applied_at']
    ordering = ['-applied_at']