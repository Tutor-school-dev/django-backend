import json
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from config.logger import get_logger

logger = get_logger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available. AI matching will use fallback.")
    OPENAI_AVAILABLE = False


class AIMatchingService:
    """Generic AI service for tutor-learner matching using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        logger.info("Initializing AIMatchingService...")
        
        if OPENAI_AVAILABLE:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            if api_key:
                logger.info(f"OpenAI package available, API key provided (length: {len(api_key)})")
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI package available but no API key provided")
                self.client = None
        else:
            logger.warning("OpenAI package not available - will use fallback matching")
            self.client = None
            
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 800)
        self.timeout = getattr(settings, 'OPENAI_TIMEOUT', 30)
        
        logger.info(f"AI Service config - Model: {self.model}, Max tokens: {self.max_tokens}, Timeout: {self.timeout}s")
        
    def get_tutor_matches(self, learner_profile, tutors_data, cache_key=None):
        """
        Get top 3 tutor matches using OpenAI
        
        Args:
            learner_profile (dict): Learner's cognitive profile and subjects
            tutors_data (list): Pre-processed tutor compatibility data
            cache_key (str): Cache key for storing results
            
        Returns:
            dict: AI response with ranked tutors
        """
        
        logger.info(f"Starting AI matching for {len(tutors_data)} tutors")
        
        # Check cache first
        if cache_key:
            logger.debug(f"Checking cache with key: {cache_key}")
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for matching request: {cache_key}")
                return cached_result
            logger.debug("No cached result found")
        
        try:
            # Check if OpenAI is available
            logger.debug(f"OpenAI availability check - OPENAI_AVAILABLE: {OPENAI_AVAILABLE}, client: {self.client is not None}")
            if not OPENAI_AVAILABLE:
                logger.error("OpenAI package not installed or not imported successfully")
                raise Exception("OpenAI package not available")
            
            if not self.client:
                logger.error("OpenAI client not initialized (likely missing API key)")
                raise Exception("OpenAI client not initialized")
            
            # Prepare token-optimized prompt
            logger.debug("Building matching prompt...")
            prompt = self._build_matching_prompt(learner_profile, tutors_data)
            logger.info(f"Prompt built - length: {len(prompt)} characters")
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API - Model: {self.model}, Max tokens: {self.max_tokens}")
            start_time = timezone.now()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a tutor-student matching expert. Return only valid JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,  # Limit tokens for cost control
                temperature=0.1,  # Low temperature for consistent results
            )
            
            processing_time = (timezone.now() - start_time).total_seconds() * 1000
            logger.info(f"OpenAI API call completed in {processing_time}ms")
            
            # Parse AI response
            ai_content = response.choices[0].message.content.strip()
            logger.debug(f"AI response length: {len(ai_content)} characters")
            logger.debug(f"AI response preview: {ai_content[:200]}...")
            
            result = json.loads(ai_content)
            logger.info(f"AI response parsed successfully - found {len(result.get('matches', []))} matches")
            
            # Add metadata
            result['ai_processing_time_ms'] = processing_time
            result['cache_hit'] = False
            
            # Cache result for 1 hour
            if cache_key:
                cache.set(cache_key, result, 3600)
                logger.info(f"Cached matching result: {cache_key}")
            
            logger.info(f"AI matching completed successfully in {processing_time}ms")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"AI response content: {ai_content if 'ai_content' in locals() else 'No response content'}")
            raise Exception("AI returned invalid response format")
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"AI matching failed with unexpected error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise Exception(f"AI service error: {str(e)}")
    
    def _build_matching_prompt(self, learner_profile, tutors_data):
        """Build token-optimized prompt for OpenAI"""
        
        # Extract learner data
        subjects = learner_profile['subjects']
        cognitive = learner_profile['cognitive']
        
        # Build tutor list (compact format)
        tutors_str = []
        for tutor in tutors_data:
            # Compact pedagogy format
            pedagogy = ','.join([f"{k}:{v}" for k, v in tutor['pedagogy'].items()])
            
            tutors_str.append(
                f"{tutor['id']} (cog:{tutor['cognitive_score']}/8, "
                f"subj:{tutor['subject_score']}/10, ₹{tutor['price']}) "
                f"subjects:\"{tutor['subjects']}\" pedagogy:\"{pedagogy}\""
            )
        
        tutors_list = '\n'.join([f"{i+1}. {t}" for i, t in enumerate(tutors_str)])
        
        # Token-optimized prompt
        prompt = f"""You are a tutor-student matching expert. Rank tutors by cognitive+subject compatibility+price.

Student: confidence={cognitive['confidence']}, anxiety={cognitive['anxiety']}, processing_speed={cognitive['processing_speed']}, working_memory={cognitive['working_memory']}, precision={cognitive['precision']}, error_correction={cognitive['error_correction']}, exploration={cognitive['exploration']}, impulsivity={cognitive['impulsivity']}, logical_reasoning={cognitive['logical_reasoning']}, hypothetical_reasoning={cognitive['hypothetical_reasoning']}
Subjects: {json.dumps(subjects)}

Tutors (cognitive_score/8, subject_score/10):
{tutors_list}

Subject matching rules:
- Handle variations: Maths=Mathematics, Science=Physics/Chemistry/Biology
- Partial overlap allowed, reward close matches
- Consider semantic similarity

Return top 3 as JSON:
{{"matches":[{{"tutor_id":"id","final_score":85,"reasoning":"High TCS matches low confidence (3). TSPI suits slow processing (2). Strong subject match.","subject_explanation":"Maths matches Mathematics expertise"}}]}}

Rank by: 1)Cognitive compatibility 2)Subject overlap 3)Lower price for ties. Be concise but clear."""

        return prompt
    
    @staticmethod  
    def generate_cache_key(learner_id, tutors_hash, cognitive_hash):
        """Generate cache key for matching results"""
        key_data = f"match_{learner_id}_{tutors_hash}_{cognitive_hash}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]