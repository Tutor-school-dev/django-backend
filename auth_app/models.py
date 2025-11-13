import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class OTP(models.Model):
    """OTP model for phone/email verification"""
    
    USE_CASES = (
        ('PHONE_VERIFICATION', 'Phone Verification'),
        ('RESET_PASSWORD', 'Reset Password'),
        ('LOGIN', 'Login'),
    )
    
    otp = models.CharField(max_length=6)
    verification_id = models.CharField(max_length=255)  # Phone number or email
    use_for = models.CharField(max_length=50, choices=USE_CASES)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'otp'
        indexes = [
            models.Index(fields=['otp', 'verification_id', 'use_for']),
            models.Index(fields=['verification_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.verification_id} - {self.use_for}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def create_otp(cls, verification_id, use_for):
        """Create new OTP"""
        import random
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(settings.OTP_LENGTH)])
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        return cls.objects.create(
            otp=otp_code,
            verification_id=verification_id,
            use_for=use_for,
            expires_at=expires_at
        )
    
    @classmethod
    def verify_otp(cls, verification_id, otp_code, use_for):
        """Verify OTP and mark as used"""
        try:
            otp_obj = cls.objects.get(
                verification_id=verification_id,
                otp=otp_code,
                use_for=use_for,
                is_used=False
            )
            if otp_obj.is_valid():
                otp_obj.is_used = True
                otp_obj.save()
                return True
            return False
        except cls.DoesNotExist:
            return False