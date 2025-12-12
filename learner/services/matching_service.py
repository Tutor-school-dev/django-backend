import json
import hashlib
from django.core.cache import cache
from tutor.models import Teacher, TeacherPedagogyProfile
from learner.models import CognitiveAssessment
from .ai_service import AIMatchingService
from config.logger import get_logger

logger = get_logger(__name__)


class TutorMatchingService:
    """Service for matching tutors with learners based on cognitive compatibility"""
    
    def __init__(self):
        self.ai_service = AIMatchingService()
    
    def get_best_matches(self, learner):
        """
        Get top 3 tutor matches for a learner
        
        Args:
            learner: Learner model instance
            
        Returns:
            dict: Matching results with tutor data and scores
        """
        
        logger.info(f"Starting tutor matching for learner: {learner.id} ({learner.name})")
        
        # 1. Validate learner has cognitive assessment
        try:
            assessment = CognitiveAssessment.objects.get(learner=learner)
            logger.info(f"Found cognitive assessment for learner {learner.id}")
        except CognitiveAssessment.DoesNotExist:
            logger.error(f"No cognitive assessment found for learner {learner.id}")
            raise ValueError("Cognitive assessment required")
        
        # 2. Get available tutors with complete pedagogy profiles
        logger.info("Fetching qualified tutors...")
        tutors = self._get_qualified_tutors()
        logger.info(f"Found {tutors.count()} qualified tutors")
        if not tutors:
            logger.warning("No qualified tutors available in database")
            raise ValueError("No qualified tutors available")
        
        # 3. Prepare learner profile
        learner_profile = self._prepare_learner_profile(learner, assessment)
        
        # 4. Calculate compatibility scores
        logger.info("Calculating cognitive compatibility scores...")
        tutors_data = self._calculate_compatibility_scores(tutors, learner_profile)
        logger.info(f"Compatibility scores calculated for {len(tutors_data)} tutors")
        
        for i, tutor in enumerate(tutors_data[:3]):  # Log top 3 scores
            logger.debug(f"Tutor {i+1}: {tutor['name']} - Cognitive: {tutor['cognitive_score']}/8, Subject: {tutor['subject_score']:.1f}/10")
        
        # 5. Generate cache key
        tutors_hash = self._generate_tutors_hash(tutors)
        cognitive_hash = self._generate_cognitive_hash(assessment)
        cache_key = AIMatchingService.generate_cache_key(
            str(learner.id), tutors_hash, cognitive_hash
        )
        logger.info(f"Generated cache key: {cache_key}")
        
        # 6. Get AI ranking
        logger.info("Attempting AI-powered ranking...")
        try:
            ai_result = self.ai_service.get_tutor_matches(
                learner_profile, tutors_data, cache_key
            )
            logger.info("AI ranking completed successfully")
        except Exception as e:
            logger.warning(f"AI matching failed, using fallback: {e}")
            logger.info("Switching to rule-based fallback matching")
            ai_result = self._fallback_matching(tutors_data)
        
        # 7. Prepare final response with full tutor data
        logger.info("Preparing final response with tutor details...")
        final_response = self._prepare_response(ai_result, tutors)
        logger.info(f"Matching completed - returning {len(final_response.get('matches', []))} matches")
        return final_response
    
    def _get_qualified_tutors(self):
        """Get tutors with complete pedagogy profiles"""
        return Teacher.objects.filter(
            pedagogy_profile__tcs__isnull=False,
            pedagogy_profile__tspi__isnull=False, 
            pedagogy_profile__twmls__isnull=False,
            pedagogy_profile__tpo__isnull=False,
            pedagogy_profile__tecp__isnull=False,
            pedagogy_profile__tet__isnull=False,
            pedagogy_profile__tics__isnull=False,
            pedagogy_profile__trd__isnull=False,
        ).select_related('pedagogy_profile')
    
    def _prepare_learner_profile(self, learner, assessment):
        """Prepare learner profile for matching"""
        
        # Parse subjects
        try:
            subjects = json.loads(learner.subjects) if learner.subjects else []
        except (json.JSONDecodeError, TypeError):
            subjects = []
        
        # Scale cognitive scores from 0-100 to 0-10
        cognitive = {
            'confidence': assessment.confidence_score / 10,
            'anxiety': assessment.anxiety_score / 10,
            'processing_speed': assessment.processing_speed_score / 10,
            'working_memory': assessment.working_memory_score / 10,
            'precision': assessment.precision_score / 10,
            'error_correction': assessment.error_correction_ability_score / 10,
            'exploration': assessment.exploratory_nature_score / 10,
            'impulsivity': assessment.impulsivity_score / 10,
            'logical_reasoning': assessment.logical_reasoning_score / 10,
            'hypothetical_reasoning': assessment.hypothetical_reasoning_score / 10,
        }
        
        return {
            'subjects': subjects,
            'cognitive': cognitive
        }
    
    def _calculate_compatibility_scores(self, tutors, learner_profile):
        """Calculate pre-compatibility scores for tutors"""
        
        tutors_data = []
        cognitive = learner_profile['cognitive']
        learner_subjects = learner_profile['subjects']
        
        for tutor in tutors:
            # Calculate cognitive compatibility score (more granular)
            cognitive_score = self._calculate_enhanced_cognitive_score(cognitive, tutor.pedagogy_profile)
            
            # Calculate subject compatibility score  
            subject_score = self._calculate_subject_score(learner_subjects, tutor.subjects)
            
            # Calculate price competitiveness (0-10 scale, lower price = higher score)
            max_price = 2000  # Assuming max reasonable price
            price_score = max(0, 10 - (float(tutor.lesson_price) / max_price * 10))
            
            tutors_data.append({
                'id': str(tutor.id),
                'name': tutor.name,
                'price': float(tutor.lesson_price),
                'subjects': tutor.subjects or "",
                'cognitive_score': cognitive_score,
                'subject_score': subject_score,
                'price_score': price_score,
                'pedagogy': tutor.pedagogy_profile.get_pedagogy_fingerprint()
            })
        
        return tutors_data
    
    def _calculate_cognitive_score(self, cognitive, pedagogy_profile):
        """Calculate cognitive compatibility score using matching logic"""
        
        score = 0
        
        # Confidence/Anxiety matching
        conf = cognitive['confidence']
        anx = cognitive['anxiety']
        if (conf <= 4 or anx >= 7) and pedagogy_profile.tcs == 'HIGH':
            score += 1
        elif conf >= 7 and anx <= 4 and pedagogy_profile.tcs == 'LOW':
            score += 1
        elif 4 < conf < 7 and 4 < anx < 7 and pedagogy_profile.tcs == 'HIGH':
            score += 1
        
        # Processing Speed matching
        ps = cognitive['processing_speed']
        if ps <= 4 and pedagogy_profile.tspi == 'HIGH':
            score += 1
        elif ps >= 7 and pedagogy_profile.tspi == 'LOW':
            score += 1
        elif 4 < ps < 7 and pedagogy_profile.tspi == 'HIGH':
            score += 1
        
        # Working Memory matching
        wm = cognitive['working_memory']
        if wm <= 4 and pedagogy_profile.twmls == 'HIGH':
            score += 1
        elif wm >= 7 and pedagogy_profile.twmls == 'LOW':
            score += 1
        elif 4 < wm < 7 and pedagogy_profile.twmls == 'HIGH':
            score += 1
        
        # Precision matching
        prec = cognitive['precision']
        if prec <= 4 and pedagogy_profile.tpo == 'HIGH':
            score += 1
        elif prec >= 7 and pedagogy_profile.tpo == 'LOW':
            score += 1
        elif 4 < prec < 7 and pedagogy_profile.tpo == 'HIGH':
            score += 1
        
        # Error Correction matching
        ec = cognitive['error_correction']
        if ec <= 4 and pedagogy_profile.tecp == 'HIGH':
            score += 1
        elif ec >= 7 and pedagogy_profile.tecp == 'LOW':
            score += 1
        elif 4 < ec < 7 and pedagogy_profile.tecp == 'HIGH':
            score += 1
        
        # Exploration matching
        exp = cognitive['exploration']
        if exp >= 7 and pedagogy_profile.tet == 'LOW':
            score += 1
        elif exp <= 4 and pedagogy_profile.tet == 'HIGH':
            score += 1
        elif 4 < exp < 7:
            # Depends on precision
            if prec <= 4 and pedagogy_profile.tet == 'HIGH':
                score += 1
            elif prec > 4 and pedagogy_profile.tet == 'LOW':
                score += 1
        
        # Impulsivity matching
        imp = cognitive['impulsivity']
        if imp >= 7 and pedagogy_profile.tics == 'HIGH':
            score += 1
        elif imp <= 4 and pedagogy_profile.tics == 'LOW':
            score += 1
        elif 4 < imp < 7 and pedagogy_profile.tics == 'HIGH':
            score += 1
        
        # Reasoning matching (composite of logical + hypothetical)
        reasoning = (cognitive['logical_reasoning'] + cognitive['hypothetical_reasoning']) / 2
        if reasoning >= 7 and pedagogy_profile.trd == 'HIGH':
            score += 1
        elif reasoning <= 4 and pedagogy_profile.trd == 'LOW':
            score += 1
        elif 4 < reasoning < 7 and pedagogy_profile.trd == 'HIGH':
            score += 1
        
        return score
    
    def _calculate_enhanced_cognitive_score(self, cognitive, pedagogy_profile):
        """Enhanced cognitive compatibility scoring with decimal precision"""
        
        total_score = 0.0
        
        # Confidence/Anxiety matching (weighted by strength of match)
        conf = cognitive['confidence']
        anx = cognitive['anxiety']
        if conf <= 4 or anx >= 7:
            if pedagogy_profile.tcs == 'HIGH':
                total_score += 1.0 + (0.2 if anx >= 8 else 0.1)  # Bonus for severe cases
            else:
                total_score += 0.3  # Partial match
        elif conf >= 7 and anx <= 4:
            if pedagogy_profile.tcs == 'LOW':
                total_score += 1.0 + (0.2 if conf >= 8 else 0.1)
            else:
                total_score += 0.3
        elif 4 < conf < 7 and 4 < anx < 7:
            if pedagogy_profile.tcs == 'HIGH':
                total_score += 0.8
            else:
                total_score += 0.5
        
        # Processing Speed matching
        ps = cognitive['processing_speed']
        if ps <= 4 and pedagogy_profile.tspi == 'HIGH':
            total_score += 1.0 + (0.2 if ps <= 2 else 0.1)
        elif ps >= 7 and pedagogy_profile.tspi == 'LOW':
            total_score += 1.0 + (0.2 if ps >= 8 else 0.1)
        elif 4 < ps < 7 and pedagogy_profile.tspi == 'HIGH':
            total_score += 0.8
        elif 4 < ps < 7 and pedagogy_profile.tspi == 'LOW':
            total_score += 0.5
        
        # Working Memory matching
        wm = cognitive['working_memory']
        if wm <= 4 and pedagogy_profile.twmls == 'HIGH':
            total_score += 1.0 + (0.2 if wm <= 2 else 0.1)
        elif wm >= 7 and pedagogy_profile.twmls == 'LOW':
            total_score += 1.0 + (0.2 if wm >= 8 else 0.1)
        elif 4 < wm < 7 and pedagogy_profile.twmls == 'HIGH':
            total_score += 0.8
        elif 4 < wm < 7 and pedagogy_profile.twmls == 'LOW':
            total_score += 0.5
        
        # Precision matching
        prec = cognitive['precision']
        if prec <= 4 and pedagogy_profile.tpo == 'HIGH':
            total_score += 1.0 + (0.2 if prec <= 2 else 0.1)
        elif prec >= 7 and pedagogy_profile.tpo == 'LOW':
            total_score += 1.0 + (0.2 if prec >= 8 else 0.1)
        elif 4 < prec < 7 and pedagogy_profile.tpo == 'HIGH':
            total_score += 0.8
        elif 4 < prec < 7 and pedagogy_profile.tpo == 'LOW':
            total_score += 0.5
        
        # Error Correction matching
        ec = cognitive['error_correction']
        if ec <= 4 and pedagogy_profile.tecp == 'HIGH':
            total_score += 1.0 + (0.2 if ec <= 2 else 0.1)
        elif ec >= 7 and pedagogy_profile.tecp == 'LOW':
            total_score += 1.0 + (0.2 if ec >= 8 else 0.1)
        elif 4 < ec < 7 and pedagogy_profile.tecp == 'HIGH':
            total_score += 0.8
        elif 4 < ec < 7 and pedagogy_profile.tecp == 'LOW':
            total_score += 0.5
        
        # Exploration matching
        exp = cognitive['exploration']
        if exp >= 7 and pedagogy_profile.tet == 'LOW':
            total_score += 1.0 + (0.2 if exp >= 8 else 0.1)
        elif exp <= 4 and pedagogy_profile.tet == 'HIGH':
            total_score += 1.0 + (0.2 if exp <= 2 else 0.1)
        elif 4 < exp < 7:
            if prec <= 4 and pedagogy_profile.tet == 'HIGH':
                total_score += 0.8
            elif prec > 4 and pedagogy_profile.tet == 'LOW':
                total_score += 0.8
            else:
                total_score += 0.4
        
        # Impulsivity matching
        imp = cognitive['impulsivity']
        if imp >= 7 and pedagogy_profile.tics == 'HIGH':
            total_score += 1.0 + (0.2 if imp >= 8 else 0.1)
        elif imp <= 4 and pedagogy_profile.tics == 'LOW':
            total_score += 1.0 + (0.2 if imp <= 2 else 0.1)
        elif 4 < imp < 7 and pedagogy_profile.tics == 'HIGH':
            total_score += 0.8
        elif 4 < imp < 7 and pedagogy_profile.tics == 'LOW':
            total_score += 0.5
        
        # Reasoning matching (composite of logical + hypothetical)
        reasoning = (cognitive['logical_reasoning'] + cognitive['hypothetical_reasoning']) / 2
        if reasoning >= 7 and pedagogy_profile.trd == 'HIGH':
            total_score += 1.0 + (0.2 if reasoning >= 8 else 0.1)
        elif reasoning <= 4 and pedagogy_profile.trd == 'LOW':
            total_score += 1.0 + (0.2 if reasoning <= 2 else 0.1)
        elif 4 < reasoning < 7 and pedagogy_profile.trd == 'HIGH':
            total_score += 0.8
        elif 4 < reasoning < 7 and pedagogy_profile.trd == 'LOW':
            total_score += 0.5
        
        # Return score with 1 decimal precision, max 10.0
        return round(min(total_score, 10.0), 1)
    
    def _calculate_subject_score(self, learner_subjects, tutor_subjects_str):
        """Calculate subject compatibility score (basic overlap check)"""
        
        if not learner_subjects or not tutor_subjects_str:
            return 0
        
        try:
            tutor_subjects = json.loads(tutor_subjects_str) if tutor_subjects_str else []
        except (json.JSONDecodeError, TypeError):
            tutor_subjects = []
        
        if not tutor_subjects:
            return 0
        
        # Simple overlap calculation (AI will handle semantic matching)
        learner_set = set(s.lower().strip() for s in learner_subjects)
        tutor_set = set(s.lower().strip() for s in tutor_subjects)
        
        overlap = len(learner_set.intersection(tutor_set))
        total = len(learner_set)
        
        return (overlap / total * 10) if total > 0 else 0
    
    def _fallback_matching(self, tutors_data):
        """Fallback matching when AI fails"""
        
        logger.info("Using rule-based fallback matching algorithm")
        
        import random
        
        # Add small random factor to break ties and create variation
        for tutor in tutors_data:
            tutor['random_factor'] = random.random() * 0.5  # 0.0-0.5 bonus
            
        # Sort by cognitive score, then subject score, then random factor, then price
        sorted_tutors = sorted(
            tutors_data,
            key=lambda t: (-t['cognitive_score'], -t['subject_score'], -t['random_factor'], t['price'])
        )
        
        logger.debug(f"Fallback ranking: {[(t['name'], t['cognitive_score'], t['subject_score']) for t in sorted_tutors[:3]]}")
        
        matches = []
        for i, tutor in enumerate(sorted_tutors[:3]):
            matches.append({
                'tutor_id': tutor['id'],
                'final_score': tutor['cognitive_score'] * 10 + tutor['subject_score'],
                'reasoning': f"Cognitive compatibility: {tutor['cognitive_score']}/8. Subject match: {tutor['subject_score']:.1f}/10.",
                'subject_explanation': "Basic subject overlap analysis"
            })
        
        return {
            'matches': matches,
            'ai_processing_time_ms': 0,
            'cache_hit': False
        }
    
    def _prepare_response(self, ai_result, tutors):
        """Prepare final response with full tutor data"""
        
        # Create tutor lookup
        tutors_dict = {str(t.id): t for t in tutors}
        
        response_matches = []
        
        for match in ai_result.get('matches', []):
            tutor_id = match['tutor_id']
            tutor = tutors_dict.get(tutor_id)
            
            if tutor:
                from tutor.serializers import TutorSerializer
                
                response_matches.append({
                    'tutor': TutorSerializer(tutor).data,
                    'match_details': {
                        'compatibility_score': match.get('final_score', 0),
                        'reasoning': match.get('reasoning', ''),
                        'subject_explanation': match.get('subject_explanation', '')
                    }
                })
        
        return {
            'success': True,
            'matches': response_matches
        }
    
    def _generate_tutors_hash(self, tutors):
        """Generate hash of current tutors for cache invalidation"""
        tutor_ids = sorted([str(t.id) for t in tutors])
        return hashlib.md5('|'.join(tutor_ids).encode()).hexdigest()[:8]
    
    def _generate_cognitive_hash(self, assessment):
        """Generate hash of cognitive assessment for cache key"""
        scores = [
            assessment.confidence_score,
            assessment.anxiety_score,
            assessment.processing_speed_score,
            assessment.working_memory_score,
            assessment.precision_score,
            assessment.error_correction_ability_score,
            assessment.exploratory_nature_score,
            assessment.impulsivity_score,
            assessment.logical_reasoning_score,
            assessment.hypothetical_reasoning_score
        ]
        score_str = '|'.join([str(s) for s in scores])
        return hashlib.md5(score_str.encode()).hexdigest()[:8]