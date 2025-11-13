import boto3
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


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
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            
            # Verify the token is for our app
            if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
                return None
            
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False),
            }
        except ValueError:
            # Invalid token
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
            message = f"Your TutorSchool verification code is: {otp_code}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes."
            
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'TutorSchool'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            return response.get('MessageId') is not None
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
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