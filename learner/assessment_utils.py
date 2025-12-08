"""
Cognitive Assessment Scoring Utilities with Granular 0-100 Performance Bands
"""
from .models import CognitiveAssessment
import re


# Scoring Constants for Maintainability
class ScoringConstants:
    """Constants for cognitive assessment scoring"""
    
    # Conservation Scoring
    CONSERVATION_CORRECT_BASE = (70, 85)  # Range for choice 'C'
    CONSERVATION_INCORRECT_BASE = {
        'A': (25, 35),  # Appearance-based (volume focus)
        'B': (30, 40),  # Appearance-based (height focus)
    }
    
    # Confidence adjustments
    CONFIDENCE_HIGH_THRESHOLD = 80
    CONFIDENCE_LOW_THRESHOLD = 40
    CONFIDENCE_CORRECT_HIGH_BONUS = (10, 15)
    CONFIDENCE_CORRECT_LOW_BONUS = (0, 5)
    CONFIDENCE_INCORRECT_HIGH_PENALTY = 10
    
    # Classification Scoring
    CLASSIFICATION_BASE_SCORES = {
        'shape': (75, 85),      # Abstract/functional criteria
        'mixed': (55, 70),      # Multiple criteria
        'color': (35, 50),      # Single surface feature
        'random': (0, 25)       # No discernible pattern
    }
    
    CLASSIFICATION_CORRECTION_PENALTIES = {
        (0, 1): 0,      # Good planning
        (2, 3): 5,      # Normal trial-error
        (4, 6): 10,     # Struggling with concept
        (7, 10): 15,    # Significant difficulty
        (11, float('inf')): 20  # Fundamental confusion
    }
    
    # Seriation Scoring
    SERIATION_CORRECT_SCORES = {
        (0, 3): (85, 100),     # Efficient planning
        (4, 7): (70, 84),      # Good strategy with adjustments
        (8, 12): (55, 69),     # Trial-error success
        (13, 20): (40, 54),    # Struggled but persisted
        (21, float('inf')): (30, 39)  # Correct by chance
    }
    
    SERIATION_INCORRECT_SCORES = {
        (0, 8): (25, 35),      # Gave up early
        (9, 15): (15, 24),     # Tried but lacks reasoning
        (16, float('inf')): (0, 14)  # Random attempts
    }
    
    # Reversibility Scoring
    REVERSIBILITY_SCORES = {
        'yes': (75, 85),       # Strong reversibility understanding
        'not_sure': (45, 60),  # Emerging understanding
        'no': (20, 35)         # Limited reversibility
    }
    
    # Hypothetical Thinking Scoring
    HYPOTHETICAL_SCORES = {
        'D': (85, 95),         # Strong abstract reasoning
        'B': (65, 78),         # Moderate hypothetical thinking
        'A': (38, 52),         # Concrete-bound thinking
        'C': (18, 32),         # Rejects hypothetical premise
        'other': (0, 15)       # No hypothetical reasoning
    }
    
    # Performance Bands
    PERFORMANCE_BANDS = [
        (0, 20),    # Band 1: Emerging
        (21, 40),   # Band 2: Developing
        (41, 60),   # Band 3: Progressing
        (61, 80),   # Band 4: Proficient
        (81, 100)   # Band 5: Advanced
    ]
    
    # Piaget Stage Thresholds
    PIAGET_THRESHOLDS = {
        (0, 30): 'preoperational',
        (31, 55): 'concrete',
        (56, 75): 'transition_formal',
        (76, 100): 'formal'
    }
    
    # Overall Score Weights
    PIAGET_WEIGHTS = {
        'conservation': 1.0,
        'classification': 1.0,
        'seriation': 1.0,
        'reversibility': 1.0,
        'hypothetical_thinking': 1.2
    }


def clamp_score(score: float) -> int:
    """Clamp score to 0-100 range and return as integer"""
    return max(0, min(100, int(round(score))))


def get_performance_band(score: int) -> int:
    """Get performance band (1-5) for a given score"""
    for band_num, (min_score, max_score) in enumerate(ScoringConstants.PERFORMANCE_BANDS, 1):
        if min_score <= score <= max_score:
            return band_num
    return 1  # Fallback to lowest band


def calculate_conservation_score(choice: str, confidence: int = None) -> int:
    """Calculate conservation score with granular 0-100 range"""
    
    if choice == 'C':  # Correct conservation understanding
        base_min, base_max = ScoringConstants.CONSERVATION_CORRECT_BASE
        base_score = (base_min + base_max) / 2
        
        # Adjust for confidence
        if confidence is not None:
            if confidence >= ScoringConstants.CONFIDENCE_HIGH_THRESHOLD:
                # High confidence with correct answer shows mastery
                bonus_min, bonus_max = ScoringConstants.CONFIDENCE_CORRECT_HIGH_BONUS
                base_score += (bonus_min + bonus_max) / 2
            elif confidence < ScoringConstants.CONFIDENCE_LOW_THRESHOLD:
                # Low confidence with correct answer shows uncertainty
                bonus_min, bonus_max = ScoringConstants.CONFIDENCE_CORRECT_LOW_BONUS
                base_score += (bonus_min + bonus_max) / 2
    else:
        # Incorrect answers - appearance-based thinking
        base_range = ScoringConstants.CONSERVATION_INCORRECT_BASE.get(choice, (20, 30))
        base_min, base_max = base_range
        base_score = (base_min + base_max) / 2
        
        # Adjust for confidence
        if confidence is not None and confidence >= ScoringConstants.CONFIDENCE_HIGH_THRESHOLD:
            # High confidence with wrong answer shows strong perceptual bias
            base_score -= ScoringConstants.CONFIDENCE_INCORRECT_HIGH_PENALTY
    
    return clamp_score(base_score)


def calculate_classification_score(rule: str, corrections: int) -> int:
    """Calculate classification score with granular 0-100 range"""
    
    # Base score from rule complexity
    base_range = ScoringConstants.CLASSIFICATION_BASE_SCORES.get(rule, (0, 25))
    base_min, base_max = base_range
    base_score = (base_min + base_max) / 2
    
    # Apply correction penalties
    penalty = 0
    for (min_corr, max_corr), pen in ScoringConstants.CLASSIFICATION_CORRECTION_PENALTIES.items():
        if min_corr <= corrections <= max_corr:
            penalty = pen
            break
    
    final_score = base_score - penalty
    return clamp_score(final_score)


def calculate_seriation_score(is_correct: bool, swap_count: int) -> int:
    """Calculate seriation score combining outcome and process efficiency"""
    
    if is_correct:
        # Find appropriate score range based on swap count
        for (min_swaps, max_swaps), (score_min, score_max) in ScoringConstants.SERIATION_CORRECT_SCORES.items():
            if min_swaps <= swap_count <= max_swaps:
                base_score = (score_min + score_max) / 2
                return clamp_score(base_score)
    else:
        # Incorrect ordering
        for (min_swaps, max_swaps), (score_min, score_max) in ScoringConstants.SERIATION_INCORRECT_SCORES.items():
            if min_swaps <= swap_count <= max_swaps:
                base_score = (score_min + score_max) / 2
                return clamp_score(base_score)
    
    # Fallback
    return clamp_score(20)


def calculate_reversibility_score(answer: str, explanation: str = None) -> int:
    """Calculate reversibility score with explanation analysis"""
    
    # Base score from answer
    base_range = ScoringConstants.REVERSIBILITY_SCORES.get(answer, (10, 25))
    base_min, base_max = base_range
    base_score = (base_min + base_max) / 2
    
    # Analyze explanation if provided
    if explanation:
        explanation_lower = explanation.lower()
        
        # Positive indicators in explanation
        positive_keywords = [
            'undo', 'reverse', 'back', 'opposite', 'cancel',
            'return', 'restore', 'original', 'same as before'
        ]
        
        negative_keywords = [
            'permanent', 'forever', 'cant', "can't", 'impossible',
            'never', 'always', 'stuck'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in explanation_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in explanation_lower)
        
        # Adjust score based on explanation quality
        if positive_count > negative_count:
            base_score += 5  # Good understanding in explanation
        elif negative_count > positive_count:
            base_score -= 5  # Shows misconceptions
    
    return clamp_score(base_score)


def calculate_hypothetical_thinking_score(choice: str) -> int:
    """Calculate hypothetical thinking score"""
    
    score_range = ScoringConstants.HYPOTHETICAL_SCORES.get(choice, ScoringConstants.HYPOTHETICAL_SCORES['other'])
    score_min, score_max = score_range
    base_score = (score_min + score_max) / 2
    
    return clamp_score(base_score)


def generate_granular_summary_points(scores_dict: dict, bands_dict: dict) -> list:
    """Generate detailed, granular summary points based on specific performance patterns"""
    
    points = []
    
    # Conservation-specific insights
    conservation_score = scores_dict['conservation']
    conservation_band = bands_dict['conservation']
    
    if conservation_band >= 4:
        points.append("Demonstrates solid understanding of conservation principles")
    elif conservation_band == 3:
        points.append("Shows emerging conservation understanding with some inconsistencies")
    else:
        points.append("Tends to focus on perceptual appearance rather than underlying quantities")
    
    # Classification insights
    classification_score = scores_dict['classification']
    classification_band = bands_dict['classification']
    
    if classification_band >= 4:
        points.append("Excels at pattern recognition and multi-criteria categorization")
    elif classification_band == 3:
        points.append("Can group objects but may need support with complex criteria")
    else:
        points.append("Works best with single, obvious classification features")
    
    # Seriation insights  
    seriation_score = scores_dict['seriation']
    seriation_band = bands_dict['seriation']
    
    if seriation_band >= 4:
        points.append("Shows strong planning and systematic ordering abilities")
    elif seriation_band == 3:
        points.append("Can create sequences but benefits from scaffolding for complex tasks")
    else:
        points.append("Learns sequencing best through hands-on trial and error")
    
    # Reversibility insights
    reversibility_score = scores_dict['reversibility']
    reversibility_band = bands_dict['reversibility']
    
    if reversibility_band >= 4:
        points.append("Routinely uses mental reversal as a problem-solving strategy")
    elif reversibility_band == 3:
        points.append("Understanding reversibility in familiar contexts, expanding to new areas")
    else:
        points.append("Benefits from concrete demonstrations of 'do-undo' operations")
    
    # Hypothetical thinking insights
    hypothetical_score = scores_dict['hypothetical_thinking']
    hypothetical_band = bands_dict['hypothetical_thinking']
    
    if hypothetical_band >= 4:
        points.append("Enjoys abstract scenarios and 'what-if' thinking exercises")
    elif hypothetical_band == 3:
        points.append("Handles simple hypotheticals best when connected to real experiences")
    else:
        points.append("Learns best through concrete, hands-on experiences before abstractions")
    
    # Learning style preferences based on score patterns
    structure_preference = seriation_score >= hypothetical_score
    if structure_preference:
        points.append("Thrives with structured, step-by-step learning progressions")
    else:
        points.append("Benefits from flexible, discovery-based learning approaches")
    
    # Overall cognitive profile
    avg_score = sum(scores_dict.values()) / len(scores_dict)
    if avg_score >= 75:
        points.append("Ready for advanced abstract concepts and independent reasoning tasks")
    elif avg_score >= 50:
        points.append("Developing strong cognitive foundations, ready for moderate challenges")
    else:
        points.append("Benefits from concrete, supportive learning environments with clear examples")
    
    return points


def compute_scores(assessment: CognitiveAssessment, payload: dict) -> None:
    """
    Compute granular cognitive assessment scores with 5-band performance system.
    
    Args:
        assessment: CognitiveAssessment model instance
        payload: Dictionary containing the raw assessment data from frontend
    """
    
    # Extract data from payload
    s2_data = payload['s2']
    s3_data = payload['s3']
    s4_data = payload['s4']
    s5_data = payload['s5']
    s6_data = payload['s6']
    
    # Populate raw answer fields
    assessment.s2_choice = s2_data['choice']
    assessment.s2_confidence = s2_data.get('confidence')
    
    assessment.s3_rule = s3_data['rule']
    assessment.s3_corrections = s3_data['corrections']
    
    assessment.s4_is_correct = s4_data['is_correct']
    assessment.s4_swap_count = s4_data['swap_count']
    
    assessment.s5_answer = s5_data['answer']
    assessment.s5_explanation = s5_data.get('explanation', '')
    
    assessment.s6_choice = s6_data['choice']
    
    # Calculate granular domain scores
    conservation_score = calculate_conservation_score(
        s2_data['choice'], 
        s2_data.get('confidence')
    )
    
    classification_score = calculate_classification_score(
        s3_data['rule'], 
        s3_data['corrections']
    )
    
    seriation_score = calculate_seriation_score(
        s4_data['is_correct'], 
        s4_data['swap_count']
    )
    
    reversibility_score = calculate_reversibility_score(
        s5_data['answer'], 
        s5_data.get('explanation')
    )
    
    hypothetical_thinking_score = calculate_hypothetical_thinking_score(
        s6_data['choice']
    )
    
    # Calculate performance bands
    scores_dict = {
        'conservation': conservation_score,
        'classification': classification_score,
        'seriation': seriation_score,
        'reversibility': reversibility_score,
        'hypothetical_thinking': hypothetical_thinking_score
    }
    
    bands_dict = {
        domain: get_performance_band(score) 
        for domain, score in scores_dict.items()
    }
    
    # Calculate overall Piaget construct score (weighted average)
    weights = ScoringConstants.PIAGET_WEIGHTS
    total_weighted_score = sum(score * weights[domain] for domain, score in scores_dict.items())
    total_weight = sum(weights.values())
    piaget_construct_score = clamp_score(total_weighted_score / total_weight)
    
    # Determine Piaget stage
    piaget_stage = 'preoperational'  # Default
    for (min_score, max_score), stage in ScoringConstants.PIAGET_THRESHOLDS.items():
        if min_score <= piaget_construct_score <= max_score:
            piaget_stage = stage
            break
    
    # Determine learning preferences
    primary_modality = 'visual'  # Default for now
    prefers_structure = seriation_score >= hypothetical_thinking_score
    
    # Generate granular summary points
    summary_points = generate_granular_summary_points(scores_dict, bands_dict)
    
    # Create detailed bands and scores data
    detailed_bands_and_scores = {}
    for domain, score in scores_dict.items():
        detailed_bands_and_scores[domain] = {
            'score': score,
            'band': bands_dict[domain]
        }
    
    # Add overall score and band
    detailed_bands_and_scores['overall'] = {
        'score': piaget_construct_score,
        'band': get_performance_band(piaget_construct_score)
    }
    
    # Set all computed fields on the assessment
    assessment.conservation_score = conservation_score
    assessment.classification_score = classification_score
    assessment.seriation_score = seriation_score
    assessment.reversibility_score = reversibility_score
    assessment.hypothetical_thinking_score = hypothetical_thinking_score
    assessment.piaget_construct_score = piaget_construct_score
    assessment.piaget_stage = piaget_stage
    assessment.primary_modality = primary_modality
    assessment.prefers_structure = prefers_structure
    assessment.summary_points = summary_points
    assessment.detailed_bands_and_scores = detailed_bands_and_scores
    
    # Save the assessment
    assessment.save()


def get_assessment_bands_and_scores(assessment: CognitiveAssessment) -> dict:
    """
    Get detailed bands and scores for an assessment.
    
    Returns:
        dict: Contains score and band for each cognitive parameter
    """
    
    # Return the stored detailed bands and scores if available
    if assessment.detailed_bands_and_scores:
        return assessment.detailed_bands_and_scores
    
    # Fallback: calculate if not stored (for backward compatibility)
    scores = {
        'conservation': assessment.conservation_score,
        'classification': assessment.classification_score,
        'seriation': assessment.seriation_score,
        'reversibility': assessment.reversibility_score,
        'hypothetical_thinking': assessment.hypothetical_thinking_score
    }
    
    result = {}
    for domain, score in scores.items():
        result[domain] = {
            'score': score,
            'band': get_performance_band(score)
        }
    
    # Add overall score
    result['overall'] = {
        'score': assessment.piaget_construct_score,
        'band': get_performance_band(assessment.piaget_construct_score)
    }
    
    return result