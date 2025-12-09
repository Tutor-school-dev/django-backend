"""
New Cognitive Assessment Scoring System - 9 Parameter Analysis
"""
from .models import CognitiveAssessment


class CognitiveScoring:    
    # Band mapping for 0-10 scores to B1-B5
    BAND_MAPPING = [
        {"range": (0, 2.0), "band": "B1", "score_range": "0–20", "label": "Very Low", 
         "interpretation": "Needs intensive scaffolding, highly concrete, step-by-step", "final_score": 10},
        {"range": (2.1, 4.0), "band": "B2", "score_range": "21–40", "label": "Emerging", 
         "interpretation": "Can perform with support, inconsistent performance", "final_score": 30},
        {"range": (4.1, 6.0), "band": "B3", "score_range": "41–60", "label": "Developing", 
         "interpretation": "Basic competence, still needs some structure / examples", "final_score": 50},
        {"range": (6.1, 8.0), "band": "B4", "score_range": "61–80", "label": "Proficient", 
         "interpretation": "Can learn with standard instruction, light scaffolding", "final_score": 70},
        {"range": (8.1, 10.0), "band": "B5", "score_range": "81–100", "label": "Advanced", 
         "interpretation": "Ready for challenge, independence, higher abstraction", "final_score": 90}
    ]
    
    @staticmethod
    def get_band_info(raw_score):
        """Convert 0-10 raw score to band information"""
        for band_info in CognitiveScoring.BAND_MAPPING:
            min_score, max_score = band_info["range"]
            if min_score <= raw_score <= max_score:
                return band_info
        # Fallback for edge cases
        return CognitiveScoring.BAND_MAPPING[0] if raw_score < 2.1 else CognitiveScoring.BAND_MAPPING[-1]
    
    @staticmethod
    def clamp_score(score):
        """Clamp score to 0-10 range"""
        return max(0, min(10, score))
    
    # Question-specific scoring functions
    @staticmethod
    def calculate_q1_scores(rt_band, h_band, ac, correctness):
        """Question 1 - Conservation Task scoring"""
        confidence = CognitiveScoring.clamp_score(10 - (0.4 * h_band) - (0.3 * ac) - (0.3 * rt_band))
        anxiety = CognitiveScoring.clamp_score((0.5 * h_band * 3) + (0.3 * ac * 2) + (0.2 * rt_band * 3))
        impulsivity = CognitiveScoring.clamp_score((0 if correctness else 1) * 5 + (5 if rt_band == 0 else 0))
        processing_speed = CognitiveScoring.clamp_score(10 - (rt_band * 4))
        
        return {
            'confidence': confidence,
            'anxiety': anxiety,
            'impulsivity': impulsivity,
            'processing_speed': processing_speed
        }
    
    @staticmethod
    def calculate_q2_scores(corr_band, idle_band, t_band):
        """Question 2 - Classification Task scoring"""
        working_memory = CognitiveScoring.clamp_score(10 - (0.5 * corr_band) - (0.5 * idle_band))
        precision = CognitiveScoring.clamp_score(10 - (0.5 * corr_band) - (0.2 * idle_band))
        exploration = CognitiveScoring.clamp_score((corr_band * 3) + (idle_band * 2))
        processing_speed = CognitiveScoring.clamp_score(10 - (t_band * 3))
        
        return {
            'working_memory': working_memory,
            'precision': precision,
            'exploratory_nature': exploration,
            'processing_speed': processing_speed
        }
    
    @staticmethod
    def calculate_q3_scores(s_band, m_band, tp_band, t_band):
        """Question 3 - Seriation Task scoring"""
        load_handling = CognitiveScoring.clamp_score(10 - (0.4 * m_band) - (0.3 * s_band) - (0.3 * tp_band))
        precision = CognitiveScoring.clamp_score(10 - (0.5 * m_band) - (0.3 * s_band))
        error_correction = CognitiveScoring.clamp_score(10 - (0.6 * m_band) - (0.4 * s_band))
        impulsivity = CognitiveScoring.clamp_score((5 if tp_band == 0 else 0) + (3 if s_band == 2 else 0))
        processing_speed = CognitiveScoring.clamp_score(10 - (t_band * 3))
        
        return {
            'working_memory_load_handling': load_handling,
            'precision': precision,
            'error_correction_ability': error_correction,
            'impulsivity': impulsivity,
            'processing_speed': processing_speed
        }
    
    @staticmethod
    def calculate_q4_scores(rt_band, h_band, ac, correctness):
        """Question 4 - Reversibility Task scoring"""
        confidence = CognitiveScoring.clamp_score(10 - (0.4 * h_band) - (0.3 * ac) - (0.3 * rt_band))
        anxiety = CognitiveScoring.clamp_score((0.5 * h_band * 3) + (0.3 * ac * 3) + (0.2 * rt_band * 2))
        reasoning = CognitiveScoring.clamp_score((8 if correctness else 4) - rt_band - (h_band * 0.5))
        processing_speed = CognitiveScoring.clamp_score(10 - (rt_band * 3))
        
        return {
            'confidence': confidence,
            'anxiety': anxiety,
            'logical_reasoning': reasoning,
            'processing_speed': processing_speed
        }
    
    @staticmethod
    def calculate_q5_scores(rt_band, h_band, ac):
        """Question 5 - Hypothetical Thinking Task scoring"""
        hypothetical_reasoning = CognitiveScoring.clamp_score(10 - (0.4 * rt_band) - (0.4 * h_band) - (0.2 * ac))
        flexibility = CognitiveScoring.clamp_score(10 - (0.5 * h_band * 2) - (ac * 2))
        confidence = CognitiveScoring.clamp_score(10 - (0.3 * h_band) - (0.3 * ac) - (0.4 * rt_band))
        processing_speed = CognitiveScoring.clamp_score(10 - (rt_band * 2.5))
        
        return {
            'hypothetical_reasoning': hypothetical_reasoning,
            'flexibility': flexibility,
            'confidence': confidence,
            'processing_speed': processing_speed
        }


def compute_scores(assessment: CognitiveAssessment, payload: dict) -> None:
    """
    Compute cognitive assessment scores using new 9-parameter system.
    
    Args:
        assessment: CognitiveAssessment model instance
        payload: Dictionary containing behavioral bands from frontend
    """
    
    # Extract question data from payload
    q1_data = payload['question1_conservation']
    q2_data = payload['question2_classification']
    q3_data = payload['question3_seriation']
    q4_data = payload['question4_reversibility']
    q5_data = payload['question5_hypothetical']
    
    # Store raw behavioral data in model
    assessment.q1_rt_band = q1_data['rt_band']
    assessment.q1_h_band = q1_data['h_band']
    assessment.q1_ac = q1_data['ac']
    assessment.q1_correctness = q1_data['correctness']
    
    assessment.q2_corr_band = q2_data['corr_band']
    assessment.q2_idle_band = q2_data['idle_band']
    assessment.q2_t_band = q2_data['t_band']
    
    assessment.q3_s_band = q3_data['s_band']
    assessment.q3_m_band = q3_data['m_band']
    assessment.q3_tp_band = q3_data['tp_band']
    assessment.q3_t_band = q3_data['t_band']
    
    assessment.q4_rt_band = q4_data['rt_band']
    assessment.q4_h_band = q4_data['h_band']
    assessment.q4_ac = q4_data['ac']
    assessment.q4_correctness = q4_data['correctness']
    
    assessment.q5_rt_band = q5_data['rt_band']
    assessment.q5_h_band = q5_data['h_band']
    assessment.q5_ac = q5_data['ac']
    
    # Calculate scores for each question
    q1_scores = CognitiveScoring.calculate_q1_scores(
        q1_data['rt_band'], q1_data['h_band'], q1_data['ac'], q1_data['correctness']
    )
    q2_scores = CognitiveScoring.calculate_q2_scores(
        q2_data['corr_band'], q2_data['idle_band'], q2_data['t_band']
    )
    q3_scores = CognitiveScoring.calculate_q3_scores(
        q3_data['s_band'], q3_data['m_band'], q3_data['tp_band'], q3_data['t_band']
    )
    q4_scores = CognitiveScoring.calculate_q4_scores(
        q4_data['rt_band'], q4_data['h_band'], q4_data['ac'], q4_data['correctness']
    )
    q5_scores = CognitiveScoring.calculate_q5_scores(
        q5_data['rt_band'], q5_data['h_band'], q5_data['ac']
    )
    
    # Aggregate scores across questions for each parameter
    parameter_scores = {}
    
    # Confidence (Q1, Q4, Q5)
    confidence_scores = [q1_scores['confidence'], q4_scores['confidence'], q5_scores['confidence']]
    parameter_scores['confidence'] = sum(confidence_scores) / len(confidence_scores)
    
    # Working Memory (Q2 only)
    parameter_scores['working_memory'] = q2_scores['working_memory']
    
    # Anxiety (Q1, Q4)
    anxiety_scores = [q1_scores['anxiety'], q4_scores['anxiety']]
    parameter_scores['anxiety'] = sum(anxiety_scores) / len(anxiety_scores)
    
    # Precision (Q2, Q3)
    precision_scores = [q2_scores['precision'], q3_scores['precision']]
    parameter_scores['precision'] = sum(precision_scores) / len(precision_scores)
    
    # Error Correction Ability (Q3 only)
    parameter_scores['error_correction_ability'] = q3_scores['error_correction_ability']
    
    # Impulsivity (Q1, Q3)
    impulsivity_scores = [q1_scores['impulsivity'], q3_scores['impulsivity']]
    parameter_scores['impulsivity'] = sum(impulsivity_scores) / len(impulsivity_scores)
    
    # Working Memory Load Handling (Q3 only)
    parameter_scores['working_memory_load_handling'] = q3_scores['working_memory_load_handling']
    
    # Processing Speed (Q1, Q2, Q3, Q4, Q5)
    processing_speed_scores = [
        q1_scores['processing_speed'], q2_scores['processing_speed'], 
        q3_scores['processing_speed'], q4_scores['processing_speed'], 
        q5_scores['processing_speed']
    ]
    parameter_scores['processing_speed'] = sum(processing_speed_scores) / len(processing_speed_scores)
    
    # Exploratory Nature (Q2 only)
    parameter_scores['exploratory_nature'] = q2_scores['exploratory_nature']
    
    # Hypothetical Reasoning (Q5 only)
    parameter_scores['hypothetical_reasoning'] = q5_scores['hypothetical_reasoning']
    
    # Logical Reasoning (Q4 only)
    parameter_scores['logical_reasoning'] = q4_scores['logical_reasoning']
    
    # Flexibility (Q5 only) 
    parameter_scores['flexibility'] = q5_scores['flexibility']
    
    # Store raw parameter scores in model
    assessment.confidence_score = parameter_scores['confidence']
    assessment.working_memory_score = parameter_scores['working_memory']
    assessment.anxiety_score = parameter_scores['anxiety']
    assessment.precision_score = parameter_scores['precision']
    assessment.error_correction_ability_score = parameter_scores['error_correction_ability']
    assessment.impulsivity_score = parameter_scores['impulsivity']
    assessment.working_memory_load_handling_score = parameter_scores['working_memory_load_handling']
    assessment.processing_speed_score = parameter_scores['processing_speed']
    assessment.exploratory_nature_score = parameter_scores['exploratory_nature']
    assessment.hypothetical_reasoning_score = parameter_scores['hypothetical_reasoning']
    assessment.logical_reasoning_score = parameter_scores['logical_reasoning']
    assessment.flexibility_score = parameter_scores['flexibility']
    
    # Create cognitive parameters structure for API response
    cognitive_parameters = {}
    for param_name, raw_score in parameter_scores.items():
        band_info = CognitiveScoring.get_band_info(raw_score)
        cognitive_parameters[param_name] = {
            'raw_score': round(raw_score, 2),
            'band': band_info['band'],
            'score_range': band_info['score_range'],
            'label': band_info['label'],
            'interpretation': band_info['interpretation'],
            'final_score': band_info['final_score']
        }
    
    # Generate final summary
    final_summary = generate_parent_summary(cognitive_parameters)
    
    # Store in model
    assessment.cognitive_parameters = cognitive_parameters
    assessment.final_summary = final_summary
    
    # Save the assessment
    assessment.save()


def generate_parent_summary(cognitive_parameters: dict) -> str:
    """Generate parent-friendly summary from cognitive parameters"""
    
    # Extract key parameters for summary
    working_memory = cognitive_parameters['working_memory']
    processing_speed = cognitive_parameters['processing_speed']
    hypothetical_reasoning = cognitive_parameters['hypothetical_reasoning']
    logical_reasoning = cognitive_parameters['logical_reasoning']
    
    # Determine thinking pace
    if processing_speed['final_score'] >= 70:
        pace = "quick"
    elif processing_speed['final_score'] >= 50:
        pace = "steady"
    else:
        pace = "developing"
    
    # Determine working memory ability
    if working_memory['final_score'] >= 70:
        memory_ability = "well"
    elif working_memory['final_score'] >= 50:
        memory_ability = "moderately"
    else:
        memory_ability = "with support needed"
    
    # Determine reasoning ability (average of hypothetical and logical)
    avg_reasoning = (hypothetical_reasoning['final_score'] + logical_reasoning['final_score']) / 2
    if avg_reasoning >= 70:
        reasoning_level = "strong"
    elif avg_reasoning >= 50:
        reasoning_level = "growing"
    else:
        reasoning_level = "emerging"
    
    # Generate summary
    summary = f"""🧠 How Your Child Thinks:

Your child understands ideas at a {pace} pace. They can hold information in mind {memory_ability} while doing a task. They show signs of {reasoning_level} reasoning when thinking about 'why' or 'what might happen' questions.

This assessment shows your child's natural thinking patterns and helps us understand how they learn best."""
    
    return summary


def get_assessment_response(assessment: CognitiveAssessment) -> dict:
    """
    Get complete assessment response in new format.
    
    Returns:
        dict: Complete cognitive assessment response
    """
    
    if assessment.cognitive_parameters:
        # Add final_summary to the response
        response = dict(assessment.cognitive_parameters)
        response['final_summary'] = assessment.final_summary
        return response
    
    # Fallback for backward compatibility (shouldn't be needed with new system)
    return {
        'final_summary': 'Assessment data not available in new format.'
    }