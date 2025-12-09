from django.core.management.base import BaseCommand
from learner.models import Learner, CognitiveAssessment
from tutor.models import Teacher, TeacherPedagogyProfile
from learner.services.matching_service import TutorMatchingService
import json


class Command(BaseCommand):
    help = 'Test the tutor matching system with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--learner-id',
            type=str,
            help='Specific learner ID to test matching for'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed matching information'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Tutor Matching System'))
        
        # Get test learner
        learner_id = options.get('learner_id')
        if learner_id:
            try:
                learner = Learner.objects.get(id=learner_id)
            except Learner.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Learner with ID {learner_id} not found')
                )
                return
        else:
            # Find first learner with cognitive assessment
            try:
                assessment = CognitiveAssessment.objects.select_related('learner').first()
                if not assessment:
                    self.stdout.write(
                        self.style.ERROR('No learners with cognitive assessments found')
                    )
                    return
                learner = assessment.learner
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error finding test learner: {e}')
                )
                return
        
        self.stdout.write(f'Testing with learner: {learner.name} ({learner.id})')
        
        # Check for cognitive assessment
        try:
            assessment = CognitiveAssessment.objects.get(learner=learner)
        except CognitiveAssessment.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Selected learner has no cognitive assessment')
            )
            return
        
        # Check available tutors
        qualified_tutors = Teacher.objects.filter(
            pedagogy_profile__tcs__isnull=False,
            pedagogy_profile__tspi__isnull=False, 
            pedagogy_profile__twmls__isnull=False,
            pedagogy_profile__tpo__isnull=False,
            pedagogy_profile__tecp__isnull=False,
            pedagogy_profile__tet__isnull=False,
            pedagogy_profile__tics__isnull=False,
            pedagogy_profile__trd__isnull=False,
        ).count()
        
        self.stdout.write(f'Available qualified tutors: {qualified_tutors}')
        
        if qualified_tutors == 0:
            self.stdout.write(
                self.style.WARNING('No tutors with complete pedagogy profiles found')
            )
            return
        
        # Display learner information
        if options.get('verbose'):
            self.stdout.write('\n=== LEARNER PROFILE ===')
            try:
                subjects = json.loads(learner.subjects) if learner.subjects else []
            except:
                subjects = []
            
            self.stdout.write(f'Name: {learner.name}')
            self.stdout.write(f'Subjects: {", ".join(subjects)}')
            self.stdout.write(f'Budget: ₹{learner.budget}')
            self.stdout.write(f'Location: {learner.area}, {learner.state}')
            
            self.stdout.write('\n=== COGNITIVE SCORES ===')
            self.stdout.write(f'Confidence: {assessment.confidence_score}/100')
            self.stdout.write(f'Anxiety: {assessment.anxiety_score}/100')
            self.stdout.write(f'Processing Speed: {assessment.processing_speed_score}/100')
            self.stdout.write(f'Working Memory: {assessment.working_memory_score}/100')
            self.stdout.write(f'Precision: {assessment.precision_score}/100')
            self.stdout.write(f'Error Correction: {assessment.error_correction_ability_score}/100')
            self.stdout.write(f'Exploration: {assessment.exploratory_nature_score}/100')
            self.stdout.write(f'Impulsivity: {assessment.impulsivity_score}/100')
            self.stdout.write(f'Logical Reasoning: {assessment.logical_reasoning_score}/100')
            self.stdout.write(f'Hypothetical Reasoning: {assessment.hypothetical_reasoning_score}/100')
        
        # Test matching service
        try:
            matching_service = TutorMatchingService()
            
            self.stdout.write('\n=== RUNNING MATCHING ALGORITHM ===')
            result = matching_service.get_best_matches(learner)
            
            if result.get('success'):
                matches = result.get('matches', [])
                self.stdout.write(
                    self.style.SUCCESS(f'\nFound {len(matches)} tutor matches:')
                )
                
                for i, match in enumerate(matches, 1):
                    tutor_data = match['tutor']
                    match_details = match['match_details']
                    
                    self.stdout.write(f'\n--- MATCH #{i} ---')
                    self.stdout.write(f'Tutor: {tutor_data["name"]}')
                    self.stdout.write(f'Price: ₹{tutor_data["lesson_price"]}/hour')
                    self.stdout.write(f'Subjects: {tutor_data.get("subjects", "N/A")}')
                    self.stdout.write(f'Location: {tutor_data.get("area", "N/A")}')
                    self.stdout.write(f'Compatibility Score: {match_details["compatibility_score"]:.1f}')
                    
                    if options.get('verbose'):
                        self.stdout.write(f'Reasoning: {match_details["reasoning"]}')
                        self.stdout.write(f'Subject Analysis: {match_details["subject_explanation"]}')
                
                processing_time = result.get('processing_time_ms', 0)
                self.stdout.write(f'\nProcessing completed in {processing_time}ms')
                
            else:
                self.stdout.write(
                    self.style.ERROR('Matching failed - no results returned')
                )
                
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'Matching validation error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Matching system error: {e}')
            )
            if options.get('verbose'):
                import traceback
                self.stdout.write(traceback.format_exc())
        
        self.stdout.write(
            self.style.SUCCESS('\nTutor matching test completed')
        )