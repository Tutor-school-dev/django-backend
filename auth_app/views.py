from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .models import OTP
from .serializers import (
    GoogleSignInSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    TutorSerializer,
    LearnerSerializer,
    TokenResponseSerializer
)
from .services import GoogleAuthService, OTPService, TokenService
from tutor.models import Teacher
from learner.models import Learner


class GoogleSignInView(APIView):
    """Handle Google Sign-In for both tutors and learners"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = GoogleSignInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        id_token = serializer.validated_data['id_token']
        user_type = serializer.validated_data['user_type']
        
        # Verify Google token
        google_service = GoogleAuthService()
        user_info = google_service.verify_google_token(id_token)
        
        if not user_info:
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user_info.get('email_verified'):
            return Response(
                {'error': 'Email not verified with Google'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user_info['email']
        name = user_info['name']
        
        # Check if user exists
        if user_type == 'tutor':
            user = Teacher.objects.filter(email=email).first()
            model_name = 'teacher'
        else:  # learner
            user = Learner.objects.filter(email=email).first()
            model_name = 'learner'
        
        # If user doesn't exist, create temporary access hash for registration
        if not user:
            # Generate temporary access hash
            import secrets
            access_hash = secrets.token_urlsafe(32)            
            
            return Response({
                'message': 'Account creation required. Please complete registration.',
                'access_hash': access_hash,
                'user_type': user_type
            }, status=status.HTTP_200_OK)
        
        # Existing user - generate JWT token

        tokens = TokenService.generate_tokens(user.id, user_type)
        
        if user_type == 'tutor':
            user_data = TutorSerializer(user).data
        else:
            user_data = LearnerSerializer(user).data
        
        return Response({
            'jwt_token': tokens['access'],
            'refresh': tokens['refresh'],
            'user_type': user_type,
            'user': user_data,
            'go_to_dashboard': True
        }, status=status.HTTP_200_OK)


class OTPRequestView(APIView):
    """Request OTP for phone verification/login"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['phone_number']
        user_type = serializer.validated_data['user_type']
        use_for = serializer.validated_data['use_for']
        
        # Format phone number
        otp_service = OTPService()
        formatted_phone = otp_service.format_phone_number(phone_number)
        
        # Create OTP
        otp_obj = OTP.create_otp(formatted_phone, use_for)
        
        # Send OTP via SMS
        sms_sent = otp_service.send_otp_sms(formatted_phone, otp_obj.otp)
        
        if not sms_sent:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': 'OTP sent successfully',
            'expires_at': otp_obj.expires_at,
            'phone_number': formatted_phone,
            'otp': otp_obj.otp
        }, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    """Verify OTP and login/register user"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp']
        user_type = serializer.validated_data['user_type']
        use_for = serializer.validated_data['use_for']
        
        # Format phone number
        otp_service = OTPService()
        formatted_phone = otp_service.format_phone_number(phone_number)
        
        # Verify OTP
        is_valid = OTP.verify_otp(formatted_phone, otp_code, use_for)
        
        if not is_valid:
            return Response(
                {'error': 'Invalid or expired OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find or create user
        if user_type == 'tutor':
            user = Teacher.objects.filter(primary_contact=formatted_phone).first()
            
            if not user:
                user = Teacher.objects.create(
                    primary_contact=formatted_phone,
                    password=''  # OTP auth, no password initially
                )
                is_new_user = True
            else:
                is_new_user = False
        
        else:  # learner
            user = Learner.objects.filter(primary_contact=formatted_phone).first()
            
            if not user:
                user = Learner.objects.create(
                    primary_contact=formatted_phone,
                    password=''  # OTP auth, no password initially
                )
                is_new_user = True
            else:
                is_new_user = False
                    
        # Generate JWT tokens
        tokens = TokenService.generate_tokens(user.id, user_type)

        # If user doesn't exist, create temporary access hash for registration
        if is_new_user:
            # Generate temporary access hash
            import secrets
            access_hash = secrets.token_urlsafe(32)            
            
            return Response({
                'message': 'Account creation required. Please complete registration.',
                'access_hash': access_hash,
                'user_type': user_type
            }, status=status.HTTP_200_OK)
        
        if user_type == 'tutor':
            user_data = TutorSerializer(user).data
        else:
            user_data = LearnerSerializer(user).data

        return Response({
            'jwt_token': tokens['access'],
            'refresh': tokens['refresh'],
            'user_type': user_type,
            'user': user_data,
            'go_to_dashboard': True
        }, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """Refresh JWT access token"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )