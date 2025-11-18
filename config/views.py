from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection
from django.utils import timezone


class HealthCheckView(APIView):
    """Health check endpoint to verify service is running"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Returns health status of the service
        Checks:
        - API is responding
        - Database connectivity
        """
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'TutorSchool API',
            'checks': {}
        }
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'connected'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = f'error: {str(e)}'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)
