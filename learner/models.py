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
    
    # Model now uses behavioral bands (0-4) and cognitive parameter scores (0-10)
    # No choice constants needed for the new system
    
    # One-to-one relationship with Learner
    learner = models.OneToOneField(
        Learner, 
        on_delete=models.CASCADE, 
        related_name='cognitive_assessment'
    )
    
    # Question 1 - Conservation Task
    q1_rt_band = models.PositiveSmallIntegerField(default=0)  # Reaction Time Band (0-2)
    q1_h_band = models.PositiveSmallIntegerField(default=0)   # Hover Time Band (0-2)
    q1_ac = models.PositiveSmallIntegerField(default=0)       # Answer Change Count (0-2+)
    q1_correctness = models.BooleanField(default=False)       # Is answer correct
    
    # Question 2 - Classification Task
    q2_corr_band = models.PositiveSmallIntegerField(default=0)  # Corrections Band (0-2)
    q2_idle_band = models.PositiveSmallIntegerField(default=0)  # Idle Time Band (0-2)
    q2_t_band = models.PositiveSmallIntegerField(default=0)     # Time Band (0-2)
    
    # Question 3 - Seriation Task
    q3_s_band = models.PositiveSmallIntegerField(default=0)   # Swaps Band (0-2)
    q3_m_band = models.PositiveSmallIntegerField(default=0)   # Misplacement Band (0-2)
    q3_tp_band = models.PositiveSmallIntegerField(default=0)  # Time to First Correct Band (0-2)
    q3_t_band = models.PositiveSmallIntegerField(default=0)   # Total Time Band (0-2)
    
    # Question 4 - Reversibility Task
    q4_rt_band = models.PositiveSmallIntegerField(default=0)  # Reaction Time Band (0-2)
    q4_h_band = models.PositiveSmallIntegerField(default=0)   # Hover Time Band (0-2)
    q4_ac = models.PositiveSmallIntegerField(default=0)       # Answer Change Count (0-2+)
    q4_correctness = models.BooleanField(default=False)       # Is answer correct
    
    # Question 5 - Hypothetical Task
    q5_rt_band = models.PositiveSmallIntegerField(default=0)  # Reaction Time Band (0-2)
    q5_h_band = models.PositiveSmallIntegerField(default=0)   # Hover Time Band (0-2)
    q5_ac = models.PositiveSmallIntegerField(default=0)       # Answer Change Count (0-2+)
    
    # Cognitive Parameters (0-10 raw scores)
    confidence_score = models.FloatField(default=0.0)
    working_memory_score = models.FloatField(default=0.0)
    anxiety_score = models.FloatField(default=0.0)
    precision_score = models.FloatField(default=0.0)
    error_correction_ability_score = models.FloatField(default=0.0)
    impulsivity_score = models.FloatField(default=0.0)
    working_memory_load_handling_score = models.FloatField(default=0.0)
    processing_speed_score = models.FloatField(default=0.0)
    exploratory_nature_score = models.FloatField(default=0.0)
    hypothetical_reasoning_score = models.FloatField(default=0.0)
    logical_reasoning_score = models.FloatField(default=0.0)
    flexibility_score = models.FloatField(default=0.0)
    
    # Cognitive Parameters Results (structured data for each parameter)
    cognitive_parameters = models.JSONField(default=dict)  # Complete parameter data
    
    # Final summary for parents
    final_summary = models.TextField(default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cognitive_assessments'
    
    def __str__(self):
        return f"Cognitive Assessment for {self.learner.name} - {self.created_at.strftime('%Y-%m-%d')}"