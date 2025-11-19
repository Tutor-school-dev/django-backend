from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Teacher
from .serializers import CreateTutorAccountSerializer, TutorSerializer, AddTutorDetailsSerializer
from auth_app.services import TokenService

from auth_app.authentication import JWTAuthentication
from django.contrib.gis.geos import Point


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


class TutorDetailsView(APIView):
    """Protected endpoint to add additional tutor details"""

    authentication_classes = []  # Will use custom authentication
    permission_classes = []  # Will handle permissions manually

    def get(self, request):
        """
        Get details of the authenticated tutor
        """        
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        
        # Verify it's a tutor
        if not hasattr(user, 'user_type') or user.user_type != 'tutor':
            return Response(
                {'error': 'This endpoint is only accessible to tutors'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return tutor data
        teacher = user
        teacher_data = TutorSerializer(teacher).data
        
        return Response({
            'teacher': teacher_data
        }, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        """
        Add additional details for an authenticated tutor
        """
        
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        
        # Verify it's a tutor
        if not hasattr(user, 'user_type') or user.user_type != 'tutor':
            return Response(
                {'error': 'This endpoint is only accessible to tutors'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request data
        serializer = AddTutorDetailsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get the teacher object (already fetched during authentication)
        teacher = user
        
        # Update teacher details
        teacher.class_level = validated_data['class']
        teacher.current_status = validated_data['current_status']
        teacher.degree = validated_data['degree']
        teacher.university = validated_data['university']
        teacher.referral = validated_data['referral']
        teacher.teaching_mode = validated_data['teaching_mode']
        teacher.area = validated_data['area']
        teacher.state = validated_data['state']
        teacher.pincode = validated_data['pincode']
        teacher.latitude = str(validated_data['latitude'])
        teacher.longitude = str(validated_data['longitude'])
        
        # Create PostGIS Point for location
        teacher.location = Point(
            float(validated_data['longitude']),
            float(validated_data['latitude']),
            srid=4326
        )
        
        # Mark location onboarding as done
        teacher.location_done = True
        
        teacher.save()
        
        # Serialize and return complete teacher data
        teacher_data = TutorSerializer(teacher).data
        
        return Response({
            'message': 'Tutor details updated successfully',
            'teacher': teacher_data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        Update tutor details for an authenticated tutor
        """
        
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        
        # Verify it's a tutor
        if not hasattr(user, 'user_type') or user.user_type != 'tutor':
            return Response(
                {'error': 'This endpoint is only accessible to tutors'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the teacher object
        teacher = user
        
        # Update teacher with partial data (only fields provided)
        data = request.data
        
        simple_fields = [
            'name', 'email', 'primary_contact', 'secondary_contact',
            'state', 'area', 'pincode', 'introduction', 'teaching_desc',
            'lesson_price', 'teaching_mode', 'class_level', 'current_status',
            'degree', 'university', 'referral'
        ]
        
        # Update simple fields
        for field in simple_fields:
            if field in data:
                setattr(teacher, field, data[field])
        
        # Update location if both latitude and longitude provided
        if 'latitude' in data and 'longitude' in data:
            teacher.latitude = str(data['latitude'])
            teacher.longitude = str(data['longitude'])
            teacher.location = Point(
                float(data['longitude']),
                float(data['latitude']),
                srid=4326
            )
        
        teacher.save()
        
        # Serialize and return complete teacher data
        teacher_data = TutorSerializer(teacher).data
        
        return Response({
            'message': 'Tutor details updated successfully',
            'teacher': teacher_data
        }, status=status.HTTP_200_OK)
