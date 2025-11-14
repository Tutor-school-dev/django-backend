from rest_framework import serializers
from tutor.models import Teacher
from learner.models import Learner


class GoogleSignInSerializer(serializers.Serializer):
    """Serializer for Google Sign-In"""
    id_token = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(choices=['tutor', 'learner'], required=True)


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request"""
    phone_number = serializers.CharField(required=True, max_length=20)
    user_type = serializers.ChoiceField(choices=['tutor', 'learner'], required=False)
    use_for = serializers.ChoiceField(
        choices=['PHONE_VERIFICATION', 'LOGIN', 'RESET_PASSWORD'],
        default='LOGIN',
        required=False
    )


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone_number = serializers.CharField(required=True, max_length=20)
    otp = serializers.CharField(required=True, max_length=6)
    user_type = serializers.ChoiceField(choices=['tutor', 'learner'], required=True)
    use_for = serializers.ChoiceField(
        choices=['PHONE_VERIFICATION', 'LOGIN', 'RESET_PASSWORD'],
        default='LOGIN'
    )
    # Optional fields for new user registration
    name = serializers.CharField(required=False, max_length=255)
    email = serializers.EmailField(required=False)


class TutorSerializer(serializers.ModelSerializer):
    """Serializer for Tutor/Teacher"""
    class Meta:
        model = Teacher
        fields = [
            'id', 'name', 'email', 'primary_contact', 'secondary_contact',
            'state', 'area', 'pincode', 'latitude', 'longitude',
            'profile_pic', 'introduction', 'teaching_desc', 'lesson_price',
            'teaching_mode', 'subscription_validity',
            'basic_done', 'location_done', 'later_onboarding_done',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LearnerSerializer(serializers.ModelSerializer):
    """Serializer for Learner/Learner"""
    class Meta:
        model = Learner
        fields = [
            'id', 'name', 'email', 'primary_contact', 'secondary_contact',
            'state', 'area', 'pincode', 'latitude', 'longitude',
            'grade', 'board', 'guardian_name', 'guardian_email',
            'subjects', 'budget', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_type = serializers.CharField()
    user = serializers.DictField()