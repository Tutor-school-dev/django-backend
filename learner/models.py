import uuid
from django.db import models
from django.contrib.gis.db.models import PointField
from django.utils import timezone


class Learner(models.Model):
    """Learner/Learner model"""
    
    PREFERRED_MODES = (
        ('Online', 'Online'),
        ('Offline', 'Offline'),
        ('Both', 'Both'),
    )
    
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
    grade = models.CharField(max_length=50, null=True, blank=True)
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