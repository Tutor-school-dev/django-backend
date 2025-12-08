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
        Submit cognitive assessment results
        
        Expected body format:
        {
          "s2": {
            "choice": "A" | "B" | "C",
            "confidence": number or null,
            "reaction_time_ms": number or null,
            "switch_count": number
          },
          "s3": {
            "rule": "shape" | "color" | "mixed",
            "corrections": number,
            "time_ms": number or null
          },
          "s4": {
            "is_correct": bool,
            "swap_count": number
          },
          "s5": {
            "answer": "yes" | "no" | "not_sure",
            "explanation": string
          },
          "s6": {
            "choice": "A" | "B" | "C" | "D",
            "reaction_time_ms": number or null
          }
        }
        """
        from auth_app.authentication import JWTAuthentication
        from .models import CognitiveAssessment
        from .serializers import CognitiveAssessmentInputSerializer, CognitiveAssessmentOutputSerializer
        from .assessment_utils import compute_scores
        
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
            
            # Compute scores and populate fields
            compute_scores(assessment, serializer.validated_data)
            
            # Get bands and detailed scores
            from .assessment_utils import get_assessment_bands_and_scores
            bands_and_scores = get_assessment_bands_and_scores(assessment)
            
            # Prepare response data
            response_data = {
                'conservation_score': assessment.conservation_score,
                'classification_score': assessment.classification_score,
                'seriation_score': assessment.seriation_score,
                'reversibility_score': assessment.reversibility_score,
                'hypothetical_thinking_score': assessment.hypothetical_thinking_score,
                'piaget_construct_score': assessment.piaget_construct_score,
                'piaget_stage': assessment.piaget_stage,
                'summary_points': assessment.summary_points,
                'detailed_bands_and_scores': bands_and_scores
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'detail': f'An error occurred while processing the assessment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
