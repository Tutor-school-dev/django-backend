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
    Cognitive Assessment Results
    
    Shows how well learners think and solve problems across 5 key areas:
    • Conservation - Understanding amounts stay the same
    • Classification - Grouping things that belong together
    • Seriation - Putting things in order
    • Reversibility - Understanding things can be undone
    • Hypothetical Thinking - Imagining "what if" situations
    """
    
    # Display key info in the list view
    list_display = [
        'learner_name_and_email',
        'piaget_stage_display',
        'overall_score_display',
        'learning_style_summary',
        'assessment_completion_date',
    ]

    list_filter = [
        'piaget_stage',
        'primary_modality', 
        'prefers_structure',
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
        'detailed_scores',
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
        ('Screen 2: Conservation Task', {
            'fields': (
                's2_choice',
                's2_confidence',
            ),
            'description': 'Tests understanding that quantity remains constant despite changes in appearance. Choice C indicates correct conservation understanding.'
        }),
        ('Screen 3: Classification Task', {
            'fields': (
                's3_rule',
                's3_corrections',
            ),
            'description': 'Evaluates ability to group objects by shared characteristics (shape, color, or mixed rules). Fewer corrections indicate better classification skills.'
        }),
        ('Screen 4: Seriation Task', {
            'fields': (
                's4_is_correct',
                's4_swap_count',
            ),
            'description': 'Tests ability to arrange objects in logical sequence. Lower swap counts with correct answers indicate stronger seriation skills.'
        }),
        ('Screen 5: Reversibility Task', {
            'fields': (
                's5_answer',
                's5_explanation',
            ),
            'description': 'Assesses understanding that mental operations can be undone or reversed. "Yes" answers typically indicate mature reversibility thinking.'
        }),
        ('Screen 6: Hypothetical Thinking', {
            'fields': (
                's6_choice',
            ),
            'description': 'Evaluates ability to reason about abstract "what if" scenarios. Choice D typically indicates strongest hypothetical reasoning.'
        }),
        ('Cognitive Domain Scores (0-100)', {
            'fields': (
                'detailed_scores',
            ),
            'description': 'Computed scores for each cognitive domain based on the learner\'s responses. Higher scores indicate stronger abilities in that domain.'
        }),
        ('Performance Bands & Analysis', {
            'fields': (
                'detailed_bands_and_scores',
            ),
            'description': 'Detailed performance bands (1-5) and scores for each cognitive domain, stored as structured data for analysis and reporting.'
        }),
        ('Piaget Stage & Learning Profile', {
            'fields': (
                'piaget_stage',
                'primary_modality',
                'prefers_structure', 
                'summary_points',
            ),
            'description': 'Overall developmental stage classification and personalized learning recommendations based on assessment results.'
        }),
    )

    ordering = ['-created_at']
    
    def learner_name_and_email(self, obj):
        """Display learner name and email for easy identification"""
        return f"{obj.learner.name} ({obj.learner.email})"
    learner_name_and_email.short_description = "Learner"
    learner_name_and_email.admin_order_field = "learner__name"
    
    def piaget_stage_display(self, obj):
        """Display Piaget stage with color coding"""
        stage_colors = {
            'preoperational': '🔴',
            'concrete': '🟡', 
            'transition_formal': '🟠',
            'formal': '🟢'
        }
        color = stage_colors.get(obj.piaget_stage, '')
        return f"{color} {obj.get_piaget_stage_display()}"
    piaget_stage_display.short_description = "Piaget Stage"
    piaget_stage_display.admin_order_field = "piaget_stage"
    
    def overall_score_display(self, obj):
        """Display overall construct score with performance indicator"""
        score = obj.piaget_construct_score
        if score >= 80:
            indicator = "🟢 Excellent"
        elif score >= 65:
            indicator = "🟡 Good" 
        elif score >= 40:
            indicator = "🟠 Developing"
        else:
            indicator = "🔴 Emerging"
        return f"{score}/100 {indicator}"
    overall_score_display.short_description = "Overall Score"
    overall_score_display.admin_order_field = "piaget_construct_score"
    
    def learning_style_summary(self, obj):
        """Display key learning style preferences"""
        structure = "Structured" if obj.prefers_structure else "Flexible"
        return f"{obj.primary_modality.title()}, {structure}"
    learning_style_summary.short_description = "Learning Style"
    
    def assessment_completion_date(self, obj):
        """Display when the assessment was completed"""
        return obj.created_at.strftime("%b %d, %Y at %I:%M %p")
    assessment_completion_date.short_description = "Completed"
    assessment_completion_date.admin_order_field = "created_at"
    
    def assessment_summary(self, obj):
        """Simple summary of learner's cognitive abilities"""
        
        # Get performance level description
        score = obj.piaget_construct_score
        if score >= 75:
            level = "Advanced thinking skills"
        elif score >= 60:
            level = "Good thinking skills"
        elif score >= 40:
            level = "Developing thinking skills"
        else:
            level = "Early thinking skills"
            
        # Get strongest and weakest areas
        scores = {
            'Conservation': obj.conservation_score,
            'Classification': obj.classification_score, 
            'Seriation': obj.seriation_score,
            'Reversibility': obj.reversibility_score,
            'Hypothetical Thinking': obj.hypothetical_thinking_score
        }
        
        strongest = max(scores, key=scores.get)
        weakest = min(scores, key=scores.get)
        
        return f"""
        📊 Overall: {score}/100 - {level}
        🎯 Cognitive Stage: {obj.get_piaget_stage_display()}
        
        💪 Strongest Area: {strongest} ({scores[strongest]}/100)
        📈 Growing Area: {weakest} ({scores[weakest]}/100)
        
        🎨 Learning Style: {obj.primary_modality.title()} learner, {'structured' if obj.prefers_structure else 'flexible'} approach
        """
    assessment_summary.short_description = "Quick Summary"
    
    def detailed_scores(self, obj):
        """Show scores for each thinking skill area"""
        
        def get_level(score):
            if score >= 80: return "🟢 Strong"
            elif score >= 60: return "🟡 Good"
            elif score >= 40: return "🟠 Fair"
            else: return "🔴 Developing"
            
        return f"""
        Conservation (understanding amounts): {obj.conservation_score}/100 {get_level(obj.conservation_score)}
        Classification (grouping things): {obj.classification_score}/100 {get_level(obj.classification_score)}
        Seriation (putting in order): {obj.seriation_score}/100 {get_level(obj.seriation_score)}
        Reversibility (undoing actions): {obj.reversibility_score}/100 {get_level(obj.reversibility_score)}
        Hypothetical Thinking (what if): {obj.hypothetical_thinking_score}/100 {get_level(obj.hypothetical_thinking_score)}
        """
    detailed_scores.short_description = "Thinking Skills Breakdown"
