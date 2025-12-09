from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from learner.models import Learner, CognitiveAssessment
from tutor.models import Teacher, TeacherPedagogyProfile
from auth_app.services import TokenService
import json
import uuid


class Command(BaseCommand):
    help = 'Create comprehensive test data for tutor matching system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data for matching system...'))
        
        # Create test learner
        learner_id = uuid.uuid4()
        learner = Learner.objects.create(
            id=learner_id,
            name="Test Student",
            primary_contact="+919876543210",
            email="teststudent@example.com",
            board="CBSE",
            guardian_name="Test Parent",
            guardian_email="testparent@example.com",
            educationLevel="12",
            budget=1000.0,
            preferred_mode="Online",
            area="Koramangala",
            state="Karnataka",
            pincode="560034",
            latitude="12.9279",
            longitude="77.6271",
            location=Point(77.6271, 12.9279, srid=4326),
            subjects=json.dumps(["Mathematics", "Physics", "Chemistry"])
        )
        
        # Create cognitive assessment for learner
        assessment = CognitiveAssessment.objects.create(
            learner=learner,
            # Low confidence student who needs support
            confidence_score=25,      # Low confidence
            anxiety_score=75,         # High anxiety
            processing_speed_score=30, # Slow processing
            working_memory_score=40,   # Below average
            precision_score=35,        # Needs precision support
            error_correction_ability_score=45, # Needs error correction help
            exploratory_nature_score=60,       # Moderate exploration
            impulsivity_score=70,              # High impulsivity
            logical_reasoning_score=55,        # Average reasoning
            hypothetical_reasoning_score=50,   # Average hypothetical thinking
            
            # Store behavioral bands (not used in matching but required)
            q1_rt_band=2, q1_h_band=3, q1_ac=0,
            q2_corr_band=2, q2_idle_band=1, q2_t_band=3,
            q3_s_band=2, q3_m_band=3, q3_tp_band=2, q3_t_band=3,
            q4_rt_band=3, q4_h_band=2, q4_ac=1,
            q5_rt_band=2, q5_h_band=3, q5_ac=0,
            
            # Cognitive parameters JSON (backup)
            cognitive_parameters={
                "confidence_score": 25,
                "anxiety_score": 75,
                "processing_speed_score": 30,
                "working_memory_score": 40,
                "precision_score": 35,
                "error_correction_ability_score": 45,
                "exploratory_nature_score": 60,
                "impulsivity_score": 70,
                "logical_reasoning_score": 55,
                "hypothetical_reasoning_score": 50
            }
        )
        
        self.stdout.write(f'✓ Created learner: {learner.name} (ID: {learner.id})')
        self.stdout.write(f'✓ Created cognitive assessment with low confidence profile')
        
        # Create test tutors with different pedagogy profiles
        tutors_data = [
            {
                'name': 'Perfect Match Tutor',
                'subjects': '["Mathematics", "Physics", "Algebra"]',
                'price': 800,
                'pedagogy': {
                    'tcs': 'HIGH',    # High confidence support - matches low confidence
                    'tspi': 'HIGH',   # Slow processing support - matches slow processing
                    'twmls': 'HIGH',  # Working memory support - matches low WM
                    'tpo': 'HIGH',    # Precision orientation - matches low precision
                    'tecp': 'HIGH',   # Error correction - matches low error correction
                    'tet': 'LOW',     # Low exploration teaching - moderate exploration ok
                    'tics': 'HIGH',   # Impulsivity control - matches high impulsivity
                    'trd': 'HIGH',    # Reasoning development - matches average reasoning
                }
            },
            {
                'name': 'Good Match Tutor',
                'subjects': '["Mathematics", "Chemistry", "Science"]',
                'price': 600,
                'pedagogy': {
                    'tcs': 'HIGH',    # Matches low confidence
                    'tspi': 'LOW',    # Doesn\'t match slow processing
                    'twmls': 'HIGH',  # Matches low working memory
                    'tpo': 'HIGH',    # Matches low precision
                    'tecp': 'LOW',    # Doesn\'t match error correction needs
                    'tet': 'LOW',     # Matches moderate exploration
                    'tics': 'HIGH',   # Matches high impulsivity
                    'trd': 'LOW',     # Doesn\'t match reasoning needs
                }
            },
            {
                'name': 'Poor Match Tutor',
                'subjects': '["Biology", "English", "History"]',
                'price': 400,
                'pedagogy': {
                    'tcs': 'LOW',     # Doesn\'t match low confidence
                    'tspi': 'LOW',    # Doesn\'t match slow processing
                    'twmls': 'LOW',   # Doesn\'t match low working memory
                    'tpo': 'LOW',     # Doesn\'t match low precision
                    'tecp': 'LOW',    # Doesn\'t match error correction needs
                    'tet': 'HIGH',    # Doesn\'t match exploration level
                    'tics': 'LOW',    # Doesn\'t match high impulsivity
                    'trd': 'LOW',     # Doesn\'t match reasoning needs
                }
            }
        ]
        
        created_tutors = []
        for tutor_data in tutors_data:
            tutor_id = uuid.uuid4()
            tutor = Teacher.objects.create(
                id=tutor_id,
                name=tutor_data['name'],
                primary_contact=f"+9198765432{len(created_tutors)}0",
                email=f"tutor{len(created_tutors)}@example.com",
                lesson_price=tutor_data['price'],
                subjects=tutor_data['subjects'],
                area="Indiranagar",
                state="Karnataka",
                pincode="560038",
                latitude="12.9784",
                longitude="77.6408",
                location=Point(77.6408, 12.9784, srid=4326),
                basic_done=True,
                location_done=True,
                later_onboarding_done=True
            )
            
            # Create pedagogy profile
            TeacherPedagogyProfile.objects.create(
                teacher=tutor,
                **tutor_data['pedagogy']
            )
            
            created_tutors.append(tutor)
            self.stdout.write(f'✓ Created tutor: {tutor.name} (ID: {tutor.id})')
        
        # Generate JWT token for the learner
        tokens = TokenService.generate_tokens(learner.id, 'learner')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('TEST DATA CREATED SUCCESSFULLY!'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'\nLEARNER INFO:')
        self.stdout.write(f'Name: {learner.name}')
        self.stdout.write(f'ID: {learner.id}')
        self.stdout.write(f'Subjects: {learner.subjects}')
        self.stdout.write(f'Cognitive Profile: Low confidence, high anxiety, needs support')
        
        self.stdout.write(f'\nJWT TOKEN (copy this for API testing):')
        self.stdout.write(f'{tokens["access"]}')
        
        self.stdout.write(f'\nTUTORS CREATED:')
        for i, tutor in enumerate(created_tutors):
            expected_score = [8, 4, 0][i]  # Expected cognitive compatibility scores
            self.stdout.write(f'{i+1}. {tutor.name} - ₹{tutor.lesson_price}/hr (Expected Score: {expected_score}/8)')
        
        self.stdout.write(f'\nAPI TESTING COMMAND:')
        self.stdout.write(f'curl -X GET http://localhost:8000/api/learner/match-tutors/ \\')
        self.stdout.write(f'  -H "Authorization: Bearer {tokens["access"]}" \\')
        self.stdout.write(f'  -H "Content-Type: application/json"')
        
        return {
            'learner_id': str(learner.id),
            'jwt_token': tokens['access'],
            'tutors_created': len(created_tutors)
        }