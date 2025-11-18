from rest_framework import serializers
from .models import Teacher
import re


class CreateTutorAccountSerializer(serializers.Serializer):
    """Serializer for creating a tutor account with validation"""
    
    access_hash = serializers.CharField(required=True, max_length=500)
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True, max_length=255, min_length=2)
    p_contact = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, min_length=8, max_length=128, write_only=True)
    
    def validate_name(self, value):
        """Validate name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Name should contain only letters and spaces")
        return value.strip()
    
    def validate_p_contact(self, value):
        """Validate primary contact number format"""
        # Remove any spaces or dashes
        cleaned = re.sub(r'[\s\-]', '', value)
        
        # Check if it's a valid phone number (10 digits or with country code)
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise serializers.ValidationError("Invalid phone number format")
        
        return cleaned
    
    def validate_password(self, value):
        """
        Validate password strength:
        - At least 8 characters
        - Contains uppercase and lowercase
        - Contains at least one number
        - Contains at least one special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Check if email already exists for a different user
        email = data.get('email')
        if Teacher.objects.filter(email=email).exclude(password='').exists():
            raise serializers.ValidationError({
                'email': 'A tutor account with this email already exists'
            })
        
        # Check if primary contact already exists for a different user
        p_contact = data.get('p_contact')
        if Teacher.objects.filter(primary_contact=p_contact).exclude(password='').exists():
            raise serializers.ValidationError({
                'p_contact': 'A tutor account with this phone number already exists'
            })
        
        return data


class TutorSerializer(serializers.ModelSerializer):
    """Serializer for Tutor/Teacher model"""
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'name', 'email', 'primary_contact', 'secondary_contact',
            'state', 'area', 'pincode', 'latitude', 'longitude',
            'profile_pic', 'introduction', 'teaching_desc', 'lesson_price',
            'teaching_mode', 'subscription_validity',
            'basic_done', 'location_done', 'later_onboarding_done',
            'class_level', 'current_status', 'degree', 'university', 'referral',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AddTutorDetailsSerializer(serializers.Serializer):
    """Serializer for adding additional tutor details"""
    
    TEACHING_MODES = ['ONLINE', 'OFFLINE', 'BOTH']
    
    # Academic details
    class_field = serializers.CharField(
        required=True, 
        max_length=50,
        source='class'  # Maps to 'class' field in request but uses different name to avoid Python keyword
    )
    current_status = serializers.CharField(required=True, max_length=255)
    degree = serializers.CharField(required=True, max_length=255)
    university = serializers.CharField(required=True, max_length=255)
    
    # Teaching preferences
    referral = serializers.CharField(required=True, max_length=255)
    teaching_mode = serializers.ChoiceField(
        required=True,
        choices=TEACHING_MODES,
        error_messages={'invalid_choice': 'Teaching mode must be one of: ONLINE, OFFLINE, BOTH'}
    )
    
    # Location details
    area = serializers.CharField(required=True, max_length=255)
    state = serializers.CharField(required=True, max_length=255)
    pincode = serializers.CharField(required=True, max_length=10)
    latitude = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=7,
        min_value=-90,
        max_value=90
    )
    longitude = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=7,
        min_value=-180,
        max_value=180
    )
    
    def validate_pincode(self, value):
        """Validate pincode format"""
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("Pincode must be exactly 6 digits")
        return value
    
    def validate_class_field(self, value):
        """Validate class field"""
        if not value.strip():
            raise serializers.ValidationError("Class cannot be empty")
        return value.strip()
    
    def validate_current_status(self, value):
        """Validate current status"""
        if not value.strip():
            raise serializers.ValidationError("Current status cannot be empty")
        return value.strip()
    
    def validate_degree(self, value):
        """Validate degree"""
        if not value.strip():
            raise serializers.ValidationError("Degree cannot be empty")
        return value.strip()
    
    def validate_university(self, value):
        """Validate university"""
        if not value.strip():
            raise serializers.ValidationError("University cannot be empty")
        return value.strip()
