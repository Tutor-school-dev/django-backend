from rest_framework import serializers
from .models import Learner
import re
import json


class CreateLearnerAccountSerializer(serializers.Serializer):
    """Serializer for creating a learner account with validation"""
    
    PREFERRED_MODES = ['Online', 'Offline', 'Both']
    
    access_hash = serializers.CharField(required=True, max_length=500)
    data = serializers.DictField(required=True)
    
    def validate_data(self, value):
        """Validate the nested data object"""
        required_fields = [
            'studentName', 'studentBoard', 'parentName', 'parentEmail',
            'grade', 'subjects', 'budget', 'preferredMode',
            'area', 'state', 'pincode', 'position'
        ]
        
        # Check all required fields are present
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        
        # Validate studentName
        student_name = value.get('studentName', '').strip()
        if not student_name or len(student_name) < 2:
            raise serializers.ValidationError("Student name must be at least 2 characters")
        if not re.match(r'^[a-zA-Z\s]+$', student_name):
            raise serializers.ValidationError("Student name should contain only letters and spaces")
        
        # Validate parentName
        parent_name = value.get('parentName', '').strip()
        if not parent_name or len(parent_name) < 2:
            raise serializers.ValidationError("Parent name must be at least 2 characters")
        if not re.match(r'^[a-zA-Z\s]+$', parent_name):
            raise serializers.ValidationError("Parent name should contain only letters and spaces")
        
        # Validate parentEmail
        parent_email = value.get('parentEmail', '').strip().lower()
        value['parentEmail'] = parent_email
        if not parent_email:
            raise serializers.ValidationError("Parent email is required")
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, parent_email):
            raise serializers.ValidationError("Invalid parent email format")
        
        # Validate studentBoard
        if not value.get('studentBoard', '').strip():
            raise serializers.ValidationError("Student board is required")
        
        # Validate grade
        grade = value.get('grade', '').strip()
        if not grade:
            raise serializers.ValidationError("Grade is required")
        
        # Validate subjects (should be a list)
        subjects = value.get('subjects')
        if not isinstance(subjects, list) or len(subjects) == 0:
            raise serializers.ValidationError("Subjects must be a non-empty list")
        
        # Validate budget
        try:
            budget = float(value.get('budget', 0))
            if budget < 0:
                raise serializers.ValidationError("Budget must be a positive number")
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid budget value")
        
        # Validate preferredMode
        preferred_mode = value.get('preferredMode')
        if preferred_mode not in self.PREFERRED_MODES:
            raise serializers.ValidationError(f"Preferred mode must be one of: {', '.join(self.PREFERRED_MODES)}")
        
        # Validate pincode
        pincode = value.get('pincode', '').strip()
        if not re.match(r'^\d{6}$', pincode):
            raise serializers.ValidationError("Pincode must be exactly 6 digits")
        
        # Validate area and state
        if not value.get('area', '').strip():
            raise serializers.ValidationError("Area is required")
        if not value.get('state', '').strip():
            raise serializers.ValidationError("State is required")
        
        # Validate position (lat/lng)
        position = value.get('position')
        if not isinstance(position, dict):
            raise serializers.ValidationError("Position must be an object with lat and lng")
        
        if 'lat' not in position or 'lng' not in position:
            raise serializers.ValidationError("Position must contain lat and lng fields")
        
        try:
            lat = float(position['lat'])
            lng = float(position['lng'])
            if not (-90 <= lat <= 90):
                raise serializers.ValidationError("Latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                raise serializers.ValidationError("Longitude must be between -180 and 180")
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid latitude or longitude values")
        
        return value


class LearnerSerializer(serializers.ModelSerializer):
    """Serializer for Learner model"""
    
    class Meta:
        model = Learner
        fields = [
            'id', 'name', 'email', 'primary_contact', 'secondary_contact',
            'state', 'area', 'pincode', 'latitude', 'longitude',
            'grade', 'board', 'guardian_name', 'guardian_email',
            'subjects', 'budget', 'preferred_mode',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
