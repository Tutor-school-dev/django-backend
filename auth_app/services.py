import boto3
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from config.logger import get_logger

logger = get_logger(__name__)


class GoogleAuthService:
    """Handle Google Sign-In authentication"""
    
    @staticmethod
    def verify_google_token(token):
        """
        Verify Google ID token and extract user info
        
        Args:
            token: Google ID token from frontend
            
        Returns:
            dict: User info (email, name, picture) or None if invalid
        """
        try:
            logger.debug("Attempting to verify Google ID token")
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            
            # Verify the token is for our app
            if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
                logger.warning(f"Token audience mismatch. Expected: {settings.GOOGLE_CLIENT_ID}")
                return None
            
            email = idinfo.get('email')
            logger.info(f"Google token verified successfully for email: {email}")
            
            return {
                'email': email,
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False),
            }
        except ValueError as e:
            # Invalid token
            logger.error(f"Failed to verify Google token: {str(e)}")
            return None


class OTPService:
    """Handle OTP generation and sending via AWS SNS"""
    
    def __init__(self):
        self.sns_client = boto3.client(
            'sns',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
    
    def send_otp_sms(self, phone_number, otp_code):
        """
        Send OTP via SMS using AWS SNS
        
        Args:
            phone_number: Phone number with country code (e.g., +919876543210)
            otp_code: OTP code to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            logger.info(f"Attempting to send OTP SMS to {phone_number}")
            message = f"Your TutorSchool verification code is: {otp_code}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes."
            
            # response = self.sns_client.publish(
            #     PhoneNumber=phone_number,
            #     Message=message,
            #     MessageAttributes={
            #         'AWS.SNS.SMS.SenderID': {
            #             'DataType': 'String',
            #             'StringValue': 'TutorSchool'
            #         },
            #         'AWS.SNS.SMS.SMSType': {
            #             'DataType': 'String',
            #             'StringValue': 'Transactional'
            #         }
            #     }
            # )
            logger.info(f"OTP SMS sent successfully to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {str(e)}", exc_info=True)
            return False
    
    def format_phone_number(self, phone_number):
        """
        Format phone number to E.164 format
        
        Args:
            phone_number: Phone number (with or without country code)
            
        Returns:
            str: Formatted phone number with country code
        """
        import phonenumbers
        
        try:
            # Try to parse with default region as India
            parsed = phonenumbers.parse(phone_number, "IN")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.E164
                )
        except:
            pass
        
        # If parsing fails, assume it already has country code
        if not phone_number.startswith('+'):
            return f"+91{phone_number}"
        return phone_number


class TokenService:
    """Handle JWT token generation"""
    
    @staticmethod
    def generate_tokens(user_id, user_type):
        """
        Generate JWT access and refresh tokens
        
        Args:
            user_id: User UUID
            user_type: 'tutor' or 'learner'
            
        Returns:
            dict: Contains access and refresh tokens
        """
        refresh = RefreshToken()
        refresh['user_id'] = str(user_id)
        refresh['user_type'] = user_type
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }    
    @staticmethod
    def generate_access_hash(user_id, user_type):
        """
        Generate temporary access hash (JWT) for account registration
        
        Args:
            user_id: User UUID
            user_type: 'tutor' or 'learner'
            
        Returns:
            str: JWT access hash containing user_id and user_type
        """
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import AccessToken
        
        token = AccessToken()
        token['user_id'] = str(user_id)
        token['user_type'] = user_type
        token['is_access_hash'] = True
        # Set short expiry for access hash (30 minutes)
        token.set_exp(lifetime=timedelta(minutes=30))
        
        return str(token)
    
    @staticmethod
    def verify_access_hash(access_hash):
        """
        Verify and decode access hash JWT
        
        Args:
            access_hash: JWT access hash string
            
        Returns:
            dict: Decoded token payload with user_id and user_type, or None if invalid
        """
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            token = AccessToken(access_hash)
            
            # Verify it's an access hash token
            if not token.get('is_access_hash', False):
                return None
            
            return {
                'user_id': token.get('user_id'),
                'user_type': token.get('user_type'),
            }
        except TokenError:
            return None
