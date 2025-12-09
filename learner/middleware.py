import time
from django.core.cache import cache
from django.http import JsonResponse
from config.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware for tutor matching API
    Limits requests per user to prevent abuse and control costs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limiting configuration
        self.rate_limits = {
            '/api/learner/match-tutors/': {
                'requests': 5,     # Max requests
                'window': 300,     # Time window in seconds (5 minutes)
                'message': 'Too many matching requests. Please wait 5 minutes.'
            }
        }
    
    def __call__(self, request):
        # Check rate limits before processing request
        rate_limit_response = self.check_rate_limit(request)
        if rate_limit_response:
            return rate_limit_response
        
        response = self.get_response(request)
        return response
    
    def check_rate_limit(self, request):
        """
        Check if request should be rate limited
        
        Returns:
            JsonResponse if rate limited, None otherwise
        """
        
        # Only check specific endpoints
        path = request.path_info
        if path not in self.rate_limits:
            return None
        
        # Get user identifier (require authentication)
        user_id = self.get_user_identifier(request)
        if not user_id:
            return None  # Let authentication middleware handle this
        
        # Get rate limit config
        config = self.rate_limits[path]
        
        # Check rate limit
        cache_key = f"rate_limit:{path}:{user_id}"
        current_time = int(time.time())
        
        # Get current request timestamps
        requests = cache.get(cache_key, [])
        
        # Filter out old requests outside the window
        window_start = current_time - config['window']
        requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if limit exceeded
        if len(requests) >= config['requests']:
            oldest_request = min(requests)
            retry_after = oldest_request + config['window'] - current_time
            
            logger.warning(f"Rate limit exceeded for user {user_id} on {path}")
            
            return JsonResponse({
                'error': config['message'],
                'retry_after': max(retry_after, 0)
            }, status=429)
        
        # Add current request
        requests.append(current_time)
        
        # Update cache
        cache.set(cache_key, requests, config['window'])
        
        return None
    
    def get_user_identifier(self, request):
        """
        Get user identifier from request
        
        Returns:
            str: User identifier or None if not authenticated
        """
        
        # Check for authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        
        # Check for JWT token (manual authentication)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from auth_app.authentication import JWTAuthentication
                auth = JWTAuthentication()
                user, _ = auth.authenticate_credentials(token)
                if user:
                    return str(user.id)
            except Exception:
                pass
        
        return None