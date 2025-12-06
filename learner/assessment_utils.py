"""
Cognitive Assessment Scoring Utilities
"""
from .models import CognitiveAssessment


def compute_scores(assessment: CognitiveAssessment, payload: dict) -> None:
    """
    Compute cognitive assessment scores from raw answers and update the assessment instance.
    
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
    
    # Compute domain scores
    
    # Conservation (Screen 2)
    if s2_data['choice'] == 'C':  # Same amount
        conservation_score = 100
    else:
        conservation_score = 40
    
    # Optionally adjust using confidence and other factors
    confidence = s2_data.get('confidence')
    if confidence is not None:
        if confidence >= 80:
            conservation_score = min(100, conservation_score + 5)
        elif confidence <= 30:
            conservation_score = max(0, conservation_score - 10)
    
    # Classification (Screen 3)
    rule = s3_data['rule']
    if rule == 'shape':
        classification_score = 90
    elif rule == 'mixed':
        classification_score = 75
    else:  # color
        classification_score = 65
    
    # Subtract corrections penalty
    corrections_penalty = min(s3_data['corrections'] * 5, 20)
    classification_score = max(0, classification_score - corrections_penalty)
    
    # Seriation (Screen 4)
    if s4_data['is_correct']:
        seriation_score = 80
    else:
        seriation_score = 50
    
    # Adjust for swap count
    swap_count = s4_data['swap_count']
    if swap_count <= 5:
        seriation_score += 10
    elif swap_count > 15:
        seriation_score -= 10
    
    # Reversibility (Screen 5)
    answer = s5_data['answer']
    if answer == 'yes':
        reversibility_score = 80
    elif answer == 'not_sure':
        reversibility_score = 50
    else:  # no
        reversibility_score = 30
    
    # Hypothetical Thinking (Screen 6)
    choice = s6_data['choice']
    if choice == 'D':
        hypothetical_thinking_score = 85
    elif choice == 'B':
        hypothetical_thinking_score = 70
    elif choice == 'A':
        hypothetical_thinking_score = 50
    else:  # C
        hypothetical_thinking_score = 40
    
    # Clamp all scores to [0, 100]
    conservation_score = max(0, min(100, conservation_score))
    classification_score = max(0, min(100, classification_score))
    seriation_score = max(0, min(100, seriation_score))
    reversibility_score = max(0, min(100, reversibility_score))
    hypothetical_thinking_score = max(0, min(100, hypothetical_thinking_score))
    
    # Overall piaget_construct_score (weighted average)
    piaget_construct_score = round(
        (conservation_score + classification_score + seriation_score + 
         reversibility_score + 1.3 * hypothetical_thinking_score) / 5.3
    )
    piaget_construct_score = max(0, min(100, piaget_construct_score))
    
    # Determine Piaget stage
    if piaget_construct_score < 40:
        piaget_stage = 'preoperational'
    elif piaget_construct_score < 65:
        piaget_stage = 'concrete'
    elif piaget_construct_score < 80:
        piaget_stage = 'transition_formal'
    else:
        piaget_stage = 'formal'
    
    # Learning style
    primary_modality = 'visual'  # Set to visual for now as specified
    prefers_structure = seriation_score >= hypothetical_thinking_score
    
    # Generate summary points
    summary_points = []
    
    # Always include
    summary_points.append("Strong visual learner")
    
    # Conditional points
    if classification_score >= 75:
        summary_points.append("Good at grouping and pattern recognition")
    
    if prefers_structure:
        summary_points.append("Benefits from structured, step-by-step explanations")
    
    if hypothetical_thinking_score < 60:
        summary_points.append("Still building hypothetical reasoning — needs concrete examples")
    
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
    
    # Save the assessment
    assessment.save()