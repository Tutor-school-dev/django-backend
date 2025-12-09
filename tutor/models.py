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


class TeacherPedagogyProfile(models.Model):
    """
    Teacher Pedagogy Fingerprint - stores cognitive teaching traits.
    Each trait represents how the teacher approaches different aspects of teaching.
    """
    
    # Trait segment choices
    SEGMENT_CHOICES = [
        ('HIGH', 'High'),
        ('LOW', 'Low'),
    ]
    
    # Primary relationship
    teacher = models.OneToOneField(
        Teacher,
        on_delete=models.CASCADE,
        related_name='pedagogy_profile',
        primary_key=True
    )
    
    # Teaching Pedagogy Traits (8 binary traits)
    
    tcs = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Confidence Support (TCS)",
        help_text="Measures how the teacher supports student confidence when they make errors. HIGH: Encourages and uses reflective questions. LOW: Direct or neutral corrections."
    )
    
    tspi = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Speed Regulation (TSPI)",
        help_text="Indicates the teacher's natural teaching pace and speed regulation. HIGH: Moderate to slow pace with checkpoints or adaptive speed. LOW: Fast and concise teaching."
    )
    
    twmls = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Working Memory Support (TWMLS)",
        help_text="Shows how the teacher manages cognitive load in multi-step concepts. HIGH: Breaks content into chunks or micro-steps. LOW: Explains full concepts at once or lets child attempt first."
    )
    
    tpo = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Precision Focus (TPO)",
        help_text="Reflects which types of errors the teacher prioritizes. HIGH: Focuses on conceptual and procedural errors. LOW: Focuses on accuracy or only repeated errors."
    )
    
    tecp = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Error Regulation (TECP)",
        help_text="Defines the teacher's approach to repeated student mistakes. HIGH: Re-explains, shows counterexamples, or rebuilds from basics. LOW: Allows more exploration."
    )
    
    tet = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Exploration Control (TET)",
        help_text="Measures the teacher's tolerance for student experimentation. HIGH: Prefers single methods or strict structure. LOW: Encourages or allows experimentation."
    )
    
    tics = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Impulse Regulation (TICS)",
        help_text="Shows how the teacher handles impulsive student responses. HIGH: Slows down students or asks for explanations. LOW: Lets them try first or doesn't interfere."
    )
    
    trd = models.CharField(
        max_length=4,
        choices=SEGMENT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Reasoning Depth (TRD)",
        help_text="Indicates frequency of deep reasoning questions ('why', 'what if'). HIGH: Always or often asks reasoning questions. LOW: Rarely or never asks them."
    )
    
    # Metadata
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the pedagogy profile was completed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teacher_pedagogy_profile'
        verbose_name = 'Teacher Pedagogy Profile'
        verbose_name_plural = 'Teacher Pedagogy Profiles'
    
    def __str__(self):
        return f"Pedagogy Profile: {self.teacher.name}"
    
    def get_pedagogy_fingerprint(self):
        """
        Returns the complete Teacher Pedagogy Fingerprint as a dict
        """
        return {
            'TCS': self.tcs,
            'TSPI': self.tspi,
            'TWMLS': self.twmls,
            'TPO': self.tpo,
            'TECP': self.tecp,
            'TET': self.tet,
            'TICS': self.tics,
            'TRD': self.trd,
        }