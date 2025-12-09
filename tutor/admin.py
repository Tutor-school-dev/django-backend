from django.contrib import admin
from .models import Teacher, TeacherPedagogyProfile
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


@admin.register(TeacherPedagogyProfile)
class TeacherPedagogyProfileAdmin(admin.ModelAdmin):
    """Admin interface for Teacher Pedagogy Profiles"""
    
    list_display = [
        'teacher_name',
        'pedagogy_fingerprint_display',
        'profile_completion_status',
        'completed_at',
    ]
    
    list_filter = [
        'tcs', 'tspi', 'twmls', 'tpo', 'tecp', 'tet', 'tics', 'trd',
        'completed_at', 'created_at'
    ]
    
    search_fields = [
        'teacher__name',
        'teacher__email',
        'teacher__primary_contact'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('teacher',)
        }),
        ('Pedagogy Traits', {
            'fields': (
                ('tcs', 'tspi'),
                ('twmls', 'tpo'), 
                ('tecp', 'tet'),
                ('tics', 'trd')
            ),
            'description': 'Eight binary teaching traits that define the teacher\'s pedagogical approach'
        }),
        ('Metadata', {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def teacher_name(self, obj):
        """Display teacher name for easy identification"""
        return obj.teacher.name
    teacher_name.short_description = "Teacher"
    teacher_name.admin_order_field = "teacher__name"
    
    def pedagogy_fingerprint_display(self, obj):
        """Display the complete pedagogy fingerprint"""
        fingerprint = obj.get_pedagogy_fingerprint()
        return ' | '.join([f'{trait}:{value}' for trait, value in fingerprint.items() if value])
    pedagogy_fingerprint_display.short_description = "Pedagogy Fingerprint"
    
    def profile_completion_status(self, obj):
        """Show completion status of the profile"""
        fingerprint = obj.get_pedagogy_fingerprint()
        completed_traits = sum(1 for value in fingerprint.values() if value)
        total_traits = len(fingerprint)
        
        if completed_traits == total_traits:
            return f"✅ Complete ({completed_traits}/{total_traits})"
        elif completed_traits > 0:
            return f"🟡 Partial ({completed_traits}/{total_traits})"
        else:
            return f"❌ Empty ({completed_traits}/{total_traits})"
    profile_completion_status.short_description = "Status"
