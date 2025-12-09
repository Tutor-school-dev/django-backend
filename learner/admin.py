from django.contrib import admin
from .models import CognitiveAssessment, Learner
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

from django.contrib import admin
from .models import CognitiveAssessment


@admin.register(CognitiveAssessment)
class CognitiveAssessmentAdmin(admin.ModelAdmin):
    """
    Cognitive Assessment Results - New 12-Parameter System
    
    Measures cognitive abilities through behavioral analysis across 12 parameters:
    • Confidence, Working Memory, Anxiety, Precision
    • Error Correction, Impulsivity, Processing Speed
    • Exploratory Nature, Hypothetical & Logical Reasoning
    • Working Memory Load Handling, Flexibility
    """
    
    # Display key info in the list view
    list_display = [
        'learner_name_and_email',
        'top_parameters_display',
        'assessment_completion_date',
    ]

    list_filter = [
        'created_at',
    ]

    search_fields = [
        'learner__name',
        'learner__email',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'assessment_summary',
        'parameter_scores_display',
    ]

    fieldsets = (
        ('Assessment Overview', {
            'fields': (
                'id',
                'learner',
                'created_at',
                'assessment_summary',
            ),
            'description': 'Basic information about this cognitive assessment completion.'
        }),
        ('Question 1: Conservation Behavioral Data', {
            'fields': (
                'q1_rt_band',
                'q1_h_band',
                'q1_ac',
                'q1_correctness',
            ),
            'description': 'Behavioral bands from conservation task: reaction time, hover time, answer changes, correctness.'
        }),
        ('Question 2: Classification Behavioral Data', {
            'fields': (
                'q2_corr_band',
                'q2_idle_band',
                'q2_t_band',
            ),
            'description': 'Behavioral bands from classification task: corrections, idle time, total time.'
        }),
        ('Question 3: Seriation Behavioral Data', {
            'fields': (
                'q3_s_band',
                'q3_m_band',
                'q3_tp_band',
                'q3_t_band',
            ),
            'description': 'Behavioral bands from seriation task: swaps, misplacements, time to first correct, total time.'
        }),
        ('Question 4: Reversibility Behavioral Data', {
            'fields': (
                'q4_rt_band',
                'q4_h_band',
                'q4_ac',
                'q4_correctness',
            ),
            'description': 'Behavioral bands from reversibility task: reaction time, hover time, answer changes, correctness.'
        }),
        ('Question 5: Hypothetical Behavioral Data', {
            'fields': (
                'q5_rt_band',
                'q5_h_band',
                'q5_ac',
            ),
            'description': 'Behavioral bands from hypothetical task: reaction time, hover time, answer changes.'
        }),
        ('Cognitive Parameter Scores', {
            'fields': (
                'parameter_scores_display',
            ),
            'description': '12 cognitive parameters derived from behavioral analysis.'
        }),
        ('Assessment Results', {
            'fields': (
                'cognitive_parameters',
                'final_summary',
            ),
            'description': 'Complete cognitive parameters structure and parent-friendly summary.'
        }),
    )

    ordering = ['-created_at']
    
    def learner_name_and_email(self, obj):
        """Display learner name and email for easy identification"""
        return f"{obj.learner.name} ({obj.learner.email})"
    learner_name_and_email.short_description = "Learner"
    learner_name_and_email.admin_order_field = "learner__name"
    
    def top_parameters_display(self, obj):
        """Display top cognitive parameters"""
        if not obj.cognitive_parameters:
            return "No data"
        
        # Get top 3 parameters by final_score
        params = []
        for param_name, param_data in obj.cognitive_parameters.items():
            if param_name != 'final_summary':
                params.append((param_name, param_data.get('final_score', 0)))
        
        top_params = sorted(params, key=lambda x: x[1], reverse=True)[:3]
        return " | ".join([f"{name.replace('_', ' ').title()}: {score}" for name, score in top_params])
    top_parameters_display.short_description = "Top Parameters"
    
    def assessment_completion_date(self, obj):
        """Display when the assessment was completed"""
        return obj.created_at.strftime("%b %d, %Y at %I:%M %p")
    assessment_completion_date.short_description = "Completed"
    assessment_completion_date.admin_order_field = "created_at"
    
    def assessment_summary(self, obj):
        """Simple summary of learner's cognitive abilities"""
        if obj.final_summary:
            return obj.final_summary
        return "Assessment data not available"
    assessment_summary.short_description = "Parent Summary"
    
    def parameter_scores_display(self, obj):
        """Show all 12 cognitive parameter scores"""
        if not obj.cognitive_parameters:
            return "No parameter data available"
        
        def get_level_emoji(score):
            if score >= 80: return "🟢"
            elif score >= 60: return "🟡"
            elif score >= 40: return "🟠"
            else: return "🔴"
            
        result = []
        for param_name, param_data in obj.cognitive_parameters.items():
            if param_name != 'final_summary':
                score = param_data.get('final_score', 0)
                band = param_data.get('band', 'N/A')
                emoji = get_level_emoji(score)
                display_name = param_name.replace('_', ' ').title()
                result.append(f"{emoji} {display_name}: {score} ({band})")
        
        return "\n".join(result)
    parameter_scores_display.short_description = "12 Cognitive Parameters"
