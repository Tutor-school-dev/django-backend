from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from config.logger import get_logger

from .models import OTP

logger = get_logger(__name__)
from .serializers import (
    GoogleSignInSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    TutorSerializer,
    LearnerSerializer,
    TokenResponseSerializer,
    TutorLoginSerializer
)
from .services import GoogleAuthService, OTPService, TokenService
from tutor.models import Teacher
from learner.models import Learner


class GoogleSignInView(APIView):
    """Handle Google Sign-In for both tutors and learners"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        logger.info(f"Google sign-in attempt for user_type: {request.data.get('user_type')}")
        
        serializer = GoogleSignInSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid Google sign-in data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        id_token = serializer.validated_data['id_token']
        user_type = serializer.validated_data['user_type']
        
        # Verify Google token
        google_service = GoogleAuthService()
        user_info = google_service.verify_google_token(id_token)
        
        if not user_info:
            logger.error(f"Invalid Google token for user_type: {user_type}")
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
        
        logger.info(f"Google authentication successful for email: {email}, user_type: {user_type}")
        
        # Check if user exists
        if user_type == 'tutor':
            user = Teacher.objects.filter(email=email).first()
            model_name = 'teacher'
        else:  # learner
            user = Learner.objects.filter(email=email).first()
            model_name = 'learner'
        
        # If user doesn't exist, create temporary user record and return access hash
        if not user:
            logger.info(f"New user detected - creating temporary {user_type} record for: {email}")
            # Create temporary user record
            if user_type == 'tutor':
                temp_user = Teacher.objects.create(
                    email=email,
                    name=name,
                    password=''  # Will be set during registration completion
                )
            else:
                temp_user = Learner.objects.create(
                    email=email,
                    name=name,
                    password=''
                )
            
            # Generate JWT-based access hash
            access_hash = TokenService.generate_access_hash(temp_user.id, user_type)
            logger.info(f"Access hash generated for new user: {email}")
            
            return Response({
                'message': 'Account creation required. Please complete registration.',
                'access_hash': access_hash,
                'user_type': user_type
            }, status=status.HTTP_200_OK)
        
        # Existing user - generate JWT token
        logger.info(f"Existing {user_type} found - generating JWT tokens for: {email}")
        
        tokens = TokenService.generate_tokens(user.id, user_type)
        
        if user_type == 'tutor':
            user_data = TutorSerializer(user).data
        else:
            user_data = LearnerSerializer(user).data
        
        logger.info(f"Login successful for {user_type}: {email}")
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
        logger.info(f"OTP request received for user_type: {request.data.get('user_type')}")
        
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid OTP request data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['phone_number']
        user_type = serializer.validated_data['user_type']
        use_for = serializer.validated_data['use_for']
        
        # Format phone number
        otp_service = OTPService()
        formatted_phone = otp_service.format_phone_number(phone_number)
        
        logger.info(f"Creating OTP for phone: {formatted_phone}, use_for: {use_for}")
        
        # Create OTP
        otp_obj = OTP.create_otp(formatted_phone, use_for)
        
        # Send OTP via SMS
        sms_sent = otp_service.send_otp_sms(formatted_phone, otp_obj.otp)
        
        if not sms_sent:
            logger.error(f"Failed to send OTP SMS to {formatted_phone}")
            return Response(
                {'error': 'Failed to send OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"OTP sent successfully to {formatted_phone}")
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
        logger.info(f"OTP verification attempt for user_type: {request.data.get('user_type')}")
        
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid OTP verification data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp']
        user_type = serializer.validated_data['user_type']
        use_for = serializer.validated_data['use_for']
        
        # Format phone number
        otp_service = OTPService()
        formatted_phone = otp_service.format_phone_number(phone_number)
        
        logger.info(f"Verifying OTP for phone: {formatted_phone}")
        
        # Verify OTP
        is_valid = OTP.verify_otp(formatted_phone, otp_code, use_for)
        
        if not is_valid:
            logger.warning(f"Invalid or expired OTP for phone: {formatted_phone}")
            return Response(
                {'error': 'Invalid or expired OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find or create user
        if user_type == 'tutor':
            user = Teacher.objects.filter(primary_contact=formatted_phone).first()
            
            if not user:
                logger.info(f"Creating new tutor account for phone: {formatted_phone}")
                user = Teacher.objects.create(
                    primary_contact=formatted_phone,
                    password=''  # OTP auth, no password initially
                )
                is_new_user = True
            else:
                logger.info(f"Existing tutor found for phone: {formatted_phone}")
                is_new_user = False
        
        else:  # learner
            user = Learner.objects.filter(primary_contact=formatted_phone).first()
            
            if not user:
                logger.info(f"Creating new learner account for phone: {formatted_phone}")
                user = Learner.objects.create(
                    primary_contact=formatted_phone,
                    password=''  # OTP auth, no password initially
                )
                is_new_user = True
            else:
                logger.info(f"Existing learner found for phone: {formatted_phone}")
                is_new_user = False
                    
        # If new user, return access hash for registration completion
        if is_new_user:
            # Generate JWT-based access hash
            access_hash = TokenService.generate_access_hash(user.id, user_type)
            logger.info(f"Access hash generated for new {user_type}: {formatted_phone}")
            
            return Response({
                'message': 'Account creation required. Please complete registration.',
                'access_hash': access_hash,
                'user_type': user_type
            }, status=status.HTTP_200_OK)
        
        logger.info(f"Generating JWT tokens for existing {user_type}: {formatted_phone}")
        # Generate JWT tokens for existing user
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

class TutorLoginView(APIView):
    """Handle tutor login via email and password"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Authenticate tutor with email and password
        
        Expected body:
        {
            "email": "tutor@example.com",
            "password": "SecurePass123@"
        }
        """
        serializer = TutorLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Find tutor by email
        try:
            teacher = Teacher.objects.get(email=email)
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not teacher.check_password(password):
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if account is fully set up
        if not teacher.password:
            return Response(
                {'error': 'Account not fully set up. Please complete registration.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate JWT tokens
        tokens = TokenService.generate_tokens(teacher.id, 'tutor')
        
        # Serialize teacher data
        teacher_data = TutorSerializer(teacher).data
        
        return Response({
            'message': 'Login successful',
            'jwt_token': tokens['access'],
            'refresh': tokens['refresh'],
            'user_type': 'tutor',
            'teacher': teacher_data
        }, status=status.HTTP_200_OK)
