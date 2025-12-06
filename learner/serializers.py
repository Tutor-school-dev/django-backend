from rest_framework import serializers
from .models import Learner
from config.constants import CLASS_LEVEL_CHOICES, PREFERRED_MODE_CHOICES
import re
import json


class CreateLearnerAccountSerializer(serializers.Serializer):
    """Serializer for creating a learner account with validation"""
    
    PREFERRED_MODES = ['Online', 'Offline', 'Both']
    VALID_CLASS_LEVELS = [choice[0] for choice in CLASS_LEVEL_CHOICES]
    
    access_hash = serializers.CharField(required=True, max_length=500)
    data = serializers.DictField(required=True)
    
    def validate_data(self, value):
        """Validate the nested data object"""
        required_fields = [
            'studentName', 'studentBoard', 'parentName', 'parentEmail',
            'educationLevel', 'subjects', 'budget', 'preferredMode',
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
        
        # Validate educationLevel against class level choices
        educationLevel = value.get('educationLevel', '').strip()
        if not educationLevel:
            raise serializers.ValidationError("educationLevel/Class level is required")
        
        # Validate against predefined class levels
        if educationLevel not in self.VALID_CLASS_LEVELS:
            raise serializers.ValidationError(
                "Invalid educationLevel/class level. Must be one of the predefined class levels."
            )
        
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
            'educationLevel', 'board', 'guardian_name', 'guardian_email',
            'subjects', 'budget', 'preferred_mode',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_educationLevel(self, value):
        """Validate educationLevel against allowed class level choices"""
        if value and value not in [choice[0] for choice in CLASS_LEVEL_CHOICES]:
            raise serializers.ValidationError(
                "Invalid educationLevel. Must be one of the predefined class levels."
            )
        return value


class CognitiveAssessmentInputSerializer(serializers.Serializer):
    """Serializer for cognitive assessment input from frontend"""
    
    # Screen 2 - Conservation
    s2 = serializers.DictField(required=True)
    
    # Screen 3 - Classification 
    s3 = serializers.DictField(required=True)
    
    # Screen 4 - Seriation
    s4 = serializers.DictField(required=True)
    
    # Screen 5 - Reversibility
    s5 = serializers.DictField(required=True)
    
    # Screen 6 - Hypothetical Thinking
    s6 = serializers.DictField(required=True)
    
    def validate_s2(self, value):
        """Validate screen 2 data"""
        if 'choice' not in value:
            raise serializers.ValidationError("Missing 'choice' field in s2")
        
        choice = value['choice']
        if choice not in ['A', 'B', 'C']:
            raise serializers.ValidationError("s2.choice must be 'A', 'B', or 'C'")
        
        # Confidence is optional but should be a number if present
        if 'confidence' in value and value['confidence'] is not None:
            try:
                confidence = int(value['confidence'])
                if confidence < 0 or confidence > 100:
                    raise serializers.ValidationError("s2.confidence must be between 0 and 100")
            except (ValueError, TypeError):
                raise serializers.ValidationError("s2.confidence must be a number")
        
        return value
    
    def validate_s3(self, value):
        """Validate screen 3 data"""
        if 'rule' not in value:
            raise serializers.ValidationError("Missing 'rule' field in s3")
        
        rule = value['rule']
        if rule not in ['shape', 'color', 'mixed']:
            raise serializers.ValidationError("s3.rule must be 'shape', 'color', or 'mixed'")
        
        if 'corrections' not in value:
            raise serializers.ValidationError("Missing 'corrections' field in s3")
        
        try:
            corrections = int(value['corrections'])
            if corrections < 0:
                raise serializers.ValidationError("s3.corrections must be non-negative")
        except (ValueError, TypeError):
            raise serializers.ValidationError("s3.corrections must be a number")
        
        return value
    
    def validate_s4(self, value):
        """Validate screen 4 data"""
        if 'is_correct' not in value:
            raise serializers.ValidationError("Missing 'is_correct' field in s4")
        
        if not isinstance(value['is_correct'], bool):
            raise serializers.ValidationError("s4.is_correct must be boolean")
        
        if 'swap_count' not in value:
            raise serializers.ValidationError("Missing 'swap_count' field in s4")
        
        try:
            swap_count = int(value['swap_count'])
            if swap_count < 0:
                raise serializers.ValidationError("s4.swap_count must be non-negative")
        except (ValueError, TypeError):
            raise serializers.ValidationError("s4.swap_count must be a number")
        
        return value
    
    def validate_s5(self, value):
        """Validate screen 5 data"""
        if 'answer' not in value:
            raise serializers.ValidationError("Missing 'answer' field in s5")
        
        answer = value['answer']
        if answer not in ['yes', 'no', 'not_sure']:
            raise serializers.ValidationError("s5.answer must be 'yes', 'no', or 'not_sure'")
        
        # Explanation is optional
        return value
    
    def validate_s6(self, value):
        """Validate screen 6 data"""
        if 'choice' not in value:
            raise serializers.ValidationError("Missing 'choice' field in s6")
        
        choice = value['choice']
        if choice not in ['A', 'B', 'C', 'D']:
            raise serializers.ValidationError("s6.choice must be 'A', 'B', 'C', or 'D'")
        
        return value


class CognitiveAssessmentOutputSerializer(serializers.Serializer):
    """Serializer for cognitive assessment output/results"""
    
    conservation_score = serializers.IntegerField()
    classification_score = serializers.IntegerField()
    seriation_score = serializers.IntegerField()
    reversibility_score = serializers.IntegerField()
    hypothetical_thinking_score = serializers.IntegerField()
    piaget_construct_score = serializers.IntegerField()
    piaget_stage = serializers.CharField()
    summary_points = serializers.ListField(child=serializers.CharField())
