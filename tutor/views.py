from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Teacher
from .serializers import CreateTutorAccountSerializer, TutorSerializer
from auth_app.services import TokenService


class CreateTutorAccountView(APIView):
    """Create a new tutor account with access hash verification"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Complete tutor registration with validated data
        
        Expected body:
        {
            "access_hash": "jwt_token_here",
            "email": "user@example.com",
            "name": "John Doe",
            "p_contact": "9876543210",
            "password": "SecurePass123@",
        }
        """
        serializer = CreateTutorAccountSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        access_hash = serializer.validated_data['access_hash']
        
        # Verify access hash JWT
        hash_payload = TokenService.verify_access_hash(access_hash)
        
        if not hash_payload:
            return Response(
                {'error': 'Invalid or expired access hash'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify it's for a tutor account
        if hash_payload.get('user_type') != 'tutor':
            return Response(
                {'error': 'Access hash is not valid for tutor account creation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = hash_payload.get('user_id')
        
        # Find the temporary user record
        try:
            teacher = Teacher.objects.get(id=user_id)
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'User record not found. Please restart registration process.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify the user hasn't already completed registration
        if teacher.password:
            return Response(
                {'error': 'Account already exists. Please login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update teacher record with complete information
        teacher.name = serializer.validated_data['name']
        teacher.email = serializer.validated_data['email']
        teacher.primary_contact = serializer.validated_data['p_contact']
        
        # Set password using the model's method (hashes password)
        teacher.set_password(serializer.validated_data['password'])
        
        # Mark basic onboarding as done
        teacher.basic_done = True
        
        teacher.save()
        
        # Generate JWT tokens for the newly created account
        tokens = TokenService.generate_tokens(teacher.id, 'tutor')
        
        # Serialize teacher data
        teacher_data = TutorSerializer(teacher).data
        
        return Response({
            'message': 'Teacher created successfully',
            'jwt_token': tokens['access'],
            'refresh': tokens['refresh'],
            'teacher': teacher_data
        }, status=status.HTTP_201_CREATED)
