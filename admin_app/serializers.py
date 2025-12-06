from rest_framework import serializers
from .models import JobListing

class JobListingSerializer(serializers.ModelSerializer):
    """Serializer for JobListing model"""
    learner_name = serializers.CharField(source='learner.name', read_only=True)
    learner_phone = serializers.CharField(source='learner.primary_contact', read_only=True)
    learner_email = serializers.EmailField(source='learner.email', read_only=True)
    educationLevel = serializers.CharField(source='learner.educationLevel', read_only=True)
    board = serializers.CharField(source='learner.board', read_only=True)
    state = serializers.CharField(source='learner.state', read_only=True)
    area = serializers.CharField(source='learner.area', read_only=True)
    subjects = serializers.CharField(source='learner.subjects', read_only=True)

    class Meta:
        model = JobListing
        fields = ['id', 'created_at', 'learner_name', 'learner_phone', 'learner_email', 'educationLevel', 'board', 'state', 'area', 'subjects']


