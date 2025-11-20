from django.db import models
from learner.models import Learner
from tutor.models import Teacher

# Create your models here.
class JobListing(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='job_listings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"JobListing for {self.learner.name} - {self.learner.email}"
    

class JobApplication(models.Model):
    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    tutor = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='job_applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"Application by {self.tutor.name} for {self.job_listing}"