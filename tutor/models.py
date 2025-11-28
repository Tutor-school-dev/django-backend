import uuid
from django.db import models
from django.contrib.gis.db.models import PointField
from django.utils import timezone
from config.constants import CLASS_LEVEL_CHOICES, TEACHING_MODE_CHOICES


class Teacher(models.Model):
    """Teacher/Tutor model"""
    
    TEACHING_MODES = TEACHING_MODE_CHOICES
    
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
    city = models.CharField(max_length=255, null=True, blank=True)
    area = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    location = PointField(geography=True, null=True, blank=True)
    latitude = models.CharField(max_length=50, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)
    
    # Profile fields
    profile_pic = models.CharField(max_length=255, null=True, blank=True)  # S3 key
    introduction = models.TextField(null=True, blank=True)
    teaching_desc = models.TextField(null=True, blank=True)
    video_url = models.CharField(max_length=255, null=True, blank=True)  # S3 key
    lesson_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_status = models.CharField(max_length=255, null=True, blank=True)
    teaching_mode = models.CharField(max_length=10, choices=TEACHING_MODES, default='BOTH')
    referral = models.CharField(max_length=255, null=True, blank=True)
    university = models.CharField(max_length=255, null=True, blank=True)
    class_level = models.CharField(max_length=255, choices=CLASS_LEVEL_CHOICES, null=True, blank=True)
    degree = models.CharField(max_length=255, null=True, blank=True)
    subjects = models.TextField(null=True, blank=True, default='')  # JSON string or comma-separated
    
    # Subscription & security
    subscription_validity = models.DateTimeField(null=True, blank=True)
    password_last_modified = models.DateTimeField(null=True, blank=True)
    
    # Onboarding flags
    basic_done = models.BooleanField(default=False)
    location_done = models.BooleanField(default=False)
    later_onboarding_done = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teachers'
        indexes = [
            models.Index(fields=['zoho_id']),
            models.Index(fields=['primary_contact']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase"""
        if self.email:
            self.email = self.email.lower().strip()
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
    
    def has_active_subscription(self):
        """Check if subscription is active"""
        if not self.subscription_validity:
            return False
        return timezone.now() < self.subscription_validity