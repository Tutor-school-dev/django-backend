from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from tutor.models import Teacher
from learner.models import Learner


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class that can be reused across the application.
    Extracts JWT from Authorization header and authenticates the user.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        
        Args:
            request: The request object
            
        Returns:
            tuple: (user, token) if authentication successful
            None: if no authentication credentials provided
            
        Raises:
            AuthenticationFailed: if authentication fails
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        # Check if it's a Bearer token
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise AuthenticationFailed('Invalid authorization header format. Expected: Bearer <token>')
        
        token = parts[1]
        
        try:
            # Decode and verify the JWT token
            access_token = AccessToken(token)
            
            user_id = access_token.get('user_id')
            user_type = access_token.get('user_type')
            
            if not user_id or not user_type:
                raise AuthenticationFailed('Invalid token payload')
            
            # Fetch the user based on user_type
            if user_type == 'tutor':
                try:
                    user = Teacher.objects.get(id=user_id)
                except Teacher.DoesNotExist:
                    raise AuthenticationFailed('Tutor not found')
            elif user_type == 'learner':
                try:
                    user = Learner.objects.get(id=user_id)
                except Learner.DoesNotExist:
                    raise AuthenticationFailed('Learner not found')
            else:
                raise AuthenticationFailed('Invalid user type in token')
            
            # Attach user_type to user object for easy access in views
            user.user_type = user_type
            
            return (user, token)
            
        except TokenError as e:
            raise AuthenticationFailed(f'Invalid or expired token: {str(e)}')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Bearer'
