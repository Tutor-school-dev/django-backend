from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.gis.geos import Point
import json

from admin_app.models import JobListing

from .models import Learner
from .serializers import CreateLearnerAccountSerializer, LearnerSerializer
from auth_app.services import TokenService


class CreateLearnerAccountView(APIView):
    """Create a new learner account with access hash verification"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Complete learner registration with validated data
        
        Expected body:
        {
            "access_hash": "jwt_token_here",
            "data": {
                "studentName": "John Doe",
                "studentBoard": "CBSE",
                "parentName": "Parent Name",
                "parentEmail": "parent@example.com",
                "educationLevel": "12",
                "subjects": ["Maths", "Science"],
                "budget": "1000",
                "preferredMode": "Offline",
                "area": "Area Name",
                "state": "State Name",
                "pincode": "302039",
                "position": {
                    "lat": 22.553962779580214,
                    "lng": 88.35566958253622
                }
            }
        }
        """
        serializer = CreateLearnerAccountSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        access_hash = serializer.validated_data['access_hash']
        data = serializer.validated_data['data']
        
        # Verify access hash JWT
        hash_payload = TokenService.verify_access_hash(access_hash)
        
        if not hash_payload:
            return Response(
                {'error': 'Invalid or expired access hash'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify it's for a learner account
        if hash_payload.get('user_type') != 'learner':
            return Response(
                {'error': 'Access hash is not valid for learner account creation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = hash_payload.get('user_id')
        
        # Find the temporary user record
        try:
            learner = Learner.objects.get(id=user_id)
        except Learner.DoesNotExist:
            return Response(
                {'error': 'User record not found. Please restart registration process.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify the user hasn't already completed registration
        if learner.name and learner.name != '':
            return Response(
                {'error': 'Account already exists. Please login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map payload fields to learner model
        learner.name = data['studentName'].strip()
        learner.board = data['studentBoard'].strip()
        learner.guardian_name = data['parentName'].strip()
        learner.guardian_email = data['parentEmail'].strip().lower()
        learner.educationLevel = data['educationLevel'].strip()
        learner.budget = float(data['budget'])
        learner.preferred_mode = data['preferredMode']
        learner.area = data['area'].strip()
        learner.state = data['state'].strip()
        learner.pincode = data['pincode'].strip()
        
        # Store subjects as JSON string
        learner.subjects = json.dumps(data['subjects'])
        
        # Store location data
        position = data['position']
        learner.latitude = str(position['lat'])
        learner.longitude = str(position['lng'])
        
        # Create PostGIS Point for location
        learner.location = Point(
            float(position['lng']),
            float(position['lat']),
            srid=4326
        )
        
        learner.save()
        
        # Generate JWT tokens for the newly created account
        tokens = TokenService.generate_tokens(learner.id, 'learner')
        
        # Serialize learner data
        learner_data = LearnerSerializer(learner).data

        # Create a job listing for the learner
        try:
            JobListing.objects.create(learner=learner)
        except Exception as e:
            print("Error creating job listing for learner:")
        
        return Response({
            'message': 'Learner account created successfully',
            'jwt_token': tokens['access'],
            'refresh': tokens['refresh'],
            'learner': learner_data
        }, status=status.HTTP_201_CREATED)


class CognitiveAssessmentView(APIView):
    """Handle cognitive assessment submission for learners"""
    
    def post(self, request):
        """
        Submit cognitive assessment results with new 11-parameter system
        
        Expected body format:
        {
          "question1_conservation": {
            "rt_band": 0-4,
            "h_band": 0-4,
            "ac": 0-1,
            "correctness": boolean
          },
          "question2_classification": {
            "corr_band": 0-4,
            "idle_band": 0-4,
            "t_band": 0-4
          },
          "question3_seriation": {
            "s_band": 0-4,
            "m_band": 0-4,
            "tp_band": 0-4,
            "t_band": 0-4
          },
          "question4_reversibility": {
            "rt_band": 0-4,
            "h_band": 0-4,
            "ac": 0-1,
            "correctness": boolean
          },
          "question5_hypothetical": {
            "rt_band": 0-4,
            "h_band": 0-4,
            "ac": 0-1
          }
        }
        """
        from auth_app.authentication import JWTAuthentication
        from .models import CognitiveAssessment
        from .serializers import CognitiveAssessmentInputSerializer, CognitiveAssessmentOutputSerializer
        from .assessment_utils import compute_scores, get_assessment_response
        
        # Authenticate learner
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        if not auth_result:
            return Response(
                {'detail': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        if not hasattr(user, 'user_type') or user.user_type != 'learner':
            return Response(
                {'detail': 'This endpoint is only accessible to learners'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if learner already has a cognitive assessment
        try:
            existing_assessment = CognitiveAssessment.objects.get(learner=user)
            return Response(
                {'detail': 'Assessment already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CognitiveAssessment.DoesNotExist:
            pass  # Good, no existing assessment
        
        # Validate input data
        serializer = CognitiveAssessmentInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create new assessment instance
            assessment = CognitiveAssessment(learner=user)
            
            # Compute scores and populate fields using new system
            compute_scores(assessment, serializer.validated_data)
            
            # Get complete assessment response in new format
            response_data = get_assessment_response(assessment)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'detail': f'An error occurred while processing the assessment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TutorMatchingView(APIView):
    """
    AI-powered tutor matching endpoint
    Returns top 3 tutor matches based on cognitive compatibility and subject overlap
    """
    
    def get(self, request):
        """
        Get best tutor matches for authenticated learner
        
        Returns:
        {
            "success": true,
            "matches": [
                {
                    "tutor": {
                        "id": "uuid",
                        "name": "Tutor Name",
                        "lesson_price": 500.0,
                        "subjects": "Math, Science",
                        "area": "Location",
                        // ... other tutor fields
                    },
                    "match_details": {
                        "compatibility_score": 85.5,
                        "reasoning": "AI explanation of why this tutor matches",
                        "subject_explanation": "Subject compatibility analysis"
                    }
                }
            ]
        }
        """
        from auth_app.authentication import JWTAuthentication
        from .services.matching_service import TutorMatchingService
        import time
        
        start_time = time.time()
        
        # Authenticate learner
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        if not hasattr(user, 'user_type') or user.user_type != 'learner':
            return Response(
                {'error': 'This endpoint is only accessible to learners'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Initialize matching service
            matching_service = TutorMatchingService()
            
            # Get matches
            result = matching_service.get_best_matches(user)
            
            # Add timing information
            processing_time = int((time.time() - start_time) * 1000)
            result['processing_time_ms'] = processing_time
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Handle business logic errors (no assessment, no tutors, etc.)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Handle unexpected errors
            from config.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Tutor matching error for learner {user.id}: {str(e)}")
            
            return Response(
                {'error': 'An error occurred while finding tutor matches. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
