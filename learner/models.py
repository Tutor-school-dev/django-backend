import uuid
from django.db import models
from django.contrib.gis.db.models import PointField
from django.utils import timezone
from config.constants import CLASS_LEVEL_CHOICES, PREFERRED_MODE_CHOICES


class Learner(models.Model):
    """Learner/Learner model"""
    
    PREFERRED_MODES = PREFERRED_MODE_CHOICES
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zoho_id = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    primary_contact = models.CharField(max_length=20, unique=True, null=True, blank=True)
    secondary_contact = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    password = models.CharField(max_length=255)
    
    # Location fields
    state = models.CharField(max_length=255, null=True, blank=True)
    area = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    location = PointField(geography=True, null=True, blank=True)
    latitude = models.CharField(max_length=50, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)
    
    # Learner-specific fields
    educationLevel = models.CharField(max_length=255, choices=CLASS_LEVEL_CHOICES, null=True, blank=True)
    board = models.CharField(max_length=100, null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)
    guardian_email = models.EmailField(null=True, blank=True)
    subjects = models.TextField(null=True, blank=True)  # JSON string or comma-separated
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_mode = models.CharField(max_length=10, choices=PREFERRED_MODES, null=True, blank=True)
    
    # Security
    password_last_modified = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learners'
        indexes = [
            models.Index(fields=['zoho_id']),
            models.Index(fields=['primary_contact']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.primary_contact})"
    
    def save(self, *args, **kwargs):
        """Override save to ensure emails are lowercase"""
        if self.email:
            self.email = self.email.lower().strip()
        if self.guardian_email:
            self.guardian_email = self.guardian_email.lower().strip()
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """Hash and set password"""
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
        self.password_last_modified = timezone.now()
    
    def check_password(self, raw_password):
        """Check if password is correct"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)
    
    @property
    def is_authenticated(self):
        """Always return True for authenticated users"""
        return True
    
    @property
    def is_anonymous(self):
        """Always return False for authenticated users"""
        return False


class CognitiveAssessment(models.Model):
    """Cognitive assessment model for learners - one assessment per learner"""
    
    # Choice constants
    S2_CHOICES = [
        ('A', 'A'),
        ('B', 'B'), 
        ('C', 'C')
    ]
    
    S3_RULE_CHOICES = [
        ('shape', 'Shape'),
        ('color', 'Color'),
        ('mixed', 'Mixed')
    ]
    
    S5_ANSWER_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_sure', 'Not Sure')
    ]
    
    S6_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D')
    ]
    
    PIAGET_STAGE_CHOICES = [
        ('preoperational', 'Preoperational'),
        ('concrete', 'Concrete operational'),
        ('transition_formal', 'Transition to formal'),
        ('formal', 'Formal operational')
    ]
    
    PRIMARY_MODALITY_CHOICES = [
        ('visual', 'Visual'),
        ('verbal', 'Verbal'),
        ('mixed', 'Mixed')
    ]
    
    # One-to-one relationship with Learner
    learner = models.OneToOneField(
        Learner, 
        on_delete=models.CASCADE, 
        related_name='cognitive_assessment'
    )
    
    # Raw answer fields
    s2_choice = models.CharField(max_length=1, choices=S2_CHOICES)
    s2_confidence = models.PositiveSmallIntegerField(null=True, blank=True)
    
    s3_rule = models.CharField(max_length=10, choices=S3_RULE_CHOICES)
    s3_corrections = models.PositiveSmallIntegerField(default=0)
    
    s4_is_correct = models.BooleanField()
    s4_swap_count = models.PositiveSmallIntegerField(default=0)
    
    s5_answer = models.CharField(max_length=10, choices=S5_ANSWER_CHOICES)
    s5_explanation = models.TextField(null=True, blank=True)
    
    s6_choice = models.CharField(max_length=1, choices=S6_CHOICES)
    
    # Computed scores (0-100)
    conservation_score = models.PositiveSmallIntegerField()
    classification_score = models.PositiveSmallIntegerField() 
    seriation_score = models.PositiveSmallIntegerField()
    reversibility_score = models.PositiveSmallIntegerField()
    hypothetical_thinking_score = models.PositiveSmallIntegerField()
    piaget_construct_score = models.PositiveSmallIntegerField()
    
    # Piaget stage label
    piaget_stage = models.CharField(max_length=20, choices=PIAGET_STAGE_CHOICES)
    
    # Learning style summary
    primary_modality = models.CharField(
        max_length=10, 
        choices=PRIMARY_MODALITY_CHOICES, 
        default='visual'
    )
    prefers_structure = models.BooleanField(default=True)
    summary_points = models.JSONField(default=list)  # list of bullet point strings
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cognitive_assessments'
    
    def __str__(self):
        return f"Cognitive Assessment for {self.learner.name} - {self.piaget_stage}"