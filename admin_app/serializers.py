from rest_framework import serializers
from .models import JobListing

class JobListingSerializer(serializers.ModelSerializer):
    """Serializer for JobListing model"""
    class Meta:
        model = JobListing
        fields = ['id', 'learner', 'created_at']




        