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
    """Serializer for cognitive assessment input with new behavioral band format"""
    
    # Question 1 - Conservation
    question1_conservation = serializers.DictField(required=True)
    
    # Question 2 - Classification
    question2_classification = serializers.DictField(required=True)
    
    # Question 3 - Seriation
    question3_seriation = serializers.DictField(required=True)
    
    # Question 4 - Reversibility
    question4_reversibility = serializers.DictField(required=True)
    
    # Question 5 - Hypothetical Thinking
    question5_hypothetical = serializers.DictField(required=True)
    
    def validate_question1_conservation(self, value):
        """Validate question 1 behavioral bands"""
        required_fields = ['rt_band', 'h_band', 'ac', 'correctness']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing '{field}' field in question1_conservation")
        
        # Validate band values (0-4 for bands, 0-1 for ac, boolean for correctness)
        rt_band = value['rt_band']
        h_band = value['h_band']
        if not (0 <= rt_band <= 4) or not (0 <= h_band <= 4):
            raise serializers.ValidationError("Band values must be between 0-4")
        
        ac = value['ac']
        if not (0 <= ac <= 2):
            raise serializers.ValidationError("ac must be between 0-2")
            
        if not isinstance(value['correctness'], bool):
            raise serializers.ValidationError("correctness must be boolean")
        
        return value
    
    def validate_question2_classification(self, value):
        """Validate question 2 behavioral bands"""
        required_fields = ['corr_band', 'idle_band', 't_band']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing '{field}' field in question2_classification")
        
        # All should be 0-4 band values
        for field in required_fields:
            band_value = value[field]
            if not (0 <= band_value <= 4):
                raise serializers.ValidationError(f"{field} must be between 0-4")
        
        return value
    
    def validate_question3_seriation(self, value):
        """Validate question 3 behavioral bands"""
        required_fields = ['s_band', 'm_band', 'tp_band', 't_band']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing '{field}' field in question3_seriation")
        
        # All should be 0-4 band values
        for field in required_fields:
            band_value = value[field]
            if not (0 <= band_value <= 4):
                raise serializers.ValidationError(f"{field} must be between 0-4")
        
        return value
    
    def validate_question4_reversibility(self, value):
        """Validate question 4 behavioral bands"""
        required_fields = ['rt_band', 'h_band', 'ac', 'correctness']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing '{field}' field in question4_reversibility")
        
        # Validate band values and other fields
        rt_band = value['rt_band']
        h_band = value['h_band']
        if not (0 <= rt_band <= 4) or not (0 <= h_band <= 4):
            raise serializers.ValidationError("Band values must be between 0-4")
        
        ac = value['ac']
        if not (0 <= ac <= 2):
            raise serializers.ValidationError("ac must be between 0-2")
            
        if not isinstance(value['correctness'], bool):
            raise serializers.ValidationError("correctness must be boolean")
        
        return value
    
    def validate_question5_hypothetical(self, value):
        """Validate question 5 behavioral bands"""
        required_fields = ['rt_band', 'h_band', 'ac']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing '{field}' field in question5_hypothetical")
        
        # Validate band values
        rt_band = value['rt_band']
        h_band = value['h_band']
        if not (0 <= rt_band <= 4) or not (0 <= h_band <= 4):
            raise serializers.ValidationError("Band values must be between 0-4")
        
        ac = value['ac']
        if not (0 <= ac <= 2):
            raise serializers.ValidationError("ac must be between 0-2")
        
        return value


class CognitiveParameterSerializer(serializers.Serializer):
    """Serializer for individual cognitive parameter"""
    raw_score = serializers.FloatField()
    band = serializers.CharField()
    score_range = serializers.CharField()
    label = serializers.CharField()
    interpretation = serializers.CharField()
    final_score = serializers.IntegerField()


class CognitiveAssessmentOutputSerializer(serializers.Serializer):
    """Serializer for cognitive assessment output with 11 parameters"""
    
    # 11 Cognitive Parameters
    confidence = CognitiveParameterSerializer()
    working_memory = CognitiveParameterSerializer()
    anxiety = CognitiveParameterSerializer()
    precision = CognitiveParameterSerializer()
    error_correction_ability = CognitiveParameterSerializer()
    impulsivity = CognitiveParameterSerializer()
    working_memory_load_handling = CognitiveParameterSerializer()
    processing_speed = CognitiveParameterSerializer()
    exploratory_nature = CognitiveParameterSerializer()
    hypothetical_reasoning = CognitiveParameterSerializer()
    logical_reasoning = CognitiveParameterSerializer()
    flexibility = CognitiveParameterSerializer()
    
    # Final summary
    final_summary = serializers.CharField()
