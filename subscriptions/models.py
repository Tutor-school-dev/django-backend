import uuid
from django.db import models
from django.utils import timezone
from tutor.models import Teacher


class Subscription(models.Model):
    """Subscription plans for tutors"""
    
    PLAN_BASIC = 1
    PLAN_STANDARD = 2
    PLAN_PRO = 3
    
    PLAN_CHOICES = (
        (PLAN_BASIC, 'Basic'),
        (PLAN_STANDARD, 'Standard'),
        (PLAN_PRO, 'Pro'),
    )
    
    id = models.IntegerField(primary_key=True, choices=PLAN_CHOICES)
    name = models.CharField(max_length=50)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Benefits
    tuition_applications = models.IntegerField(help_text="Number of tuition applications allowed")
    verified_badge = models.BooleanField(default=False)
    priority_listing = models.BooleanField(default=False)
    mock_interviews = models.BooleanField(default=False)
    fast_track_support = models.BooleanField(default=False)
    workshops = models.BooleanField(default=False)
    health_insurance = models.BooleanField(default=False)
    pedagogy_training = models.BooleanField(default=False)
    profile_listing = models.BooleanField(default=True)
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.name} - ₹{self.monthly_price}/month"
    
    def calculate_price(self, duration_months: int) -> float:
        """Calculate price based on duration"""
        duration_months = min(duration_months, 12)
        if duration_months >= 12:
            return float(self.annual_price)
        return float(self.monthly_price * duration_months)
    
    def get_benefits_list(self) -> list:
        """Get list of benefits for this plan"""
        benefits = []
        if self.tuition_applications:
            benefits.append(f"{self.tuition_applications} tuition applications")
        if self.pedagogy_training:
            benefits.append("Pedagogy training")
        if self.profile_listing:
            benefits.append("Profile listing")
        if self.verified_badge:
            benefits.append("Verified badge")
        if self.priority_listing:
            benefits.append("Priority listing")
        if self.mock_interviews:
            benefits.append("Mock interviews")
        if self.fast_track_support:
            benefits.append("Fast-track support")
        if self.workshops:
            benefits.append("Workshops")
        if self.health_insurance:
            benefits.append("Health insurance")
        return benefits


class Payment(models.Model):
    """Payment transaction records"""
    
    STATUS_PENDING = 'PENDING'
    STATUS_CHARGED = 'CHARGED'
    STATUS_AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_REFUNDED = 'REFUNDED'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_CHARGED, 'Charged'),
        (STATUS_AUTHENTICATION_FAILED, 'Authentication Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REFUNDED, 'Refunded'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.CharField(max_length=100, unique=True, db_index=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField()
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # HDFC Gateway fields
    hdfc_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    hdfc_tracking_id = models.CharField(max_length=255, blank=True, null=True)
    hdfc_bank_ref_no = models.CharField(max_length=255, blank=True, null=True)
    hdfc_response_code = models.CharField(max_length=50, blank=True, null=True)
    hdfc_response_message = models.TextField(blank=True, null=True)
    
    # Additional metadata
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.order_id} - {self.status}"
    
    def mark_as_charged(self, transaction_data: dict):
        """Mark payment as successfully charged"""
        self.status = self.STATUS_CHARGED
        self.payment_date = timezone.now()
        self.hdfc_transaction_id = transaction_data.get('transaction_id')
        self.hdfc_tracking_id = transaction_data.get('tracking_id')
        self.hdfc_bank_ref_no = transaction_data.get('bank_ref_no')
        self.hdfc_response_code = transaction_data.get('response_code')
        self.hdfc_response_message = transaction_data.get('response_message')
        self.payment_method = transaction_data.get('payment_method')
        self.save()


class UserSubscription(models.Model):
    """User's active and historical subscriptions"""
    
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='user_subscriptions')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='user_subscriptions')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='user_subscription', null=True, blank=True)
    
    duration_months = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    
    # Usage tracking
    applications_used = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.teacher.name} - {self.subscription.name} ({self.status})"
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status == self.STATUS_ACTIVE and self.end_date > timezone.now()
    
    def deactivate(self):
        """Deactivate subscription"""
        self.status = self.STATUS_EXPIRED
        self.save()
    
    def cancel(self):
        """Cancel subscription"""
        self.status = self.STATUS_CANCELLED
        self.save()
    
    def can_apply(self) -> bool:
        """Check if user can still apply for tuitions"""
        if not self.is_active():
            return False
        return self.applications_used < self.subscription.tuition_applications
    
    def increment_applications(self):
        """Increment application count"""
        if self.can_apply():
            self.applications_used += 1
            self.save()
            return True
        return False
