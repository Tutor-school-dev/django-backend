import json
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from config.logger import get_logger

logger = get_logger(__name__)

# Try to import AI packages
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available.")
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI package not available.")
    GEMINI_AVAILABLE = False


class AIMatchingService:
    """Generic AI service for tutor-learner matching using OpenAI or Gemini"""
    
    def __init__(self):
        """Initialize AI client based on GEN_AI setting"""
        logger.info("Initializing AIMatchingService...")
        
        self.ai_provider = getattr(settings, 'GEN_AI', 'openai').lower()
        logger.info(f"AI Provider selected: {self.ai_provider}")
        
        self.client = None
        self.model = None
        self.max_tokens = 800
        self.timeout = 30
        
        if self.ai_provider == 'gemini':
            self._init_gemini()
        else:
            self._init_openai()
        
        logger.info(f"AI Service config - Provider: {self.ai_provider}, Model: {self.model}, Max tokens: {self.max_tokens}, Timeout: {self.timeout}s")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        if OPENAI_AVAILABLE:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            if api_key:
                logger.info(f"OpenAI package available, API key provided (length: {len(api_key)})")
                self.client = openai.OpenAI(api_key=api_key)
                self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
                self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 800)
                self.timeout = getattr(settings, 'OPENAI_TIMEOUT', 30)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI package available but no API key provided")
        else:
            logger.warning("OpenAI package not available")
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        if GEMINI_AVAILABLE:
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            if api_key:
                logger.info(f"Gemini package available, API key provided (length: {len(api_key)})")
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel('gemini-2.5-flash-lite')
                self.model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
                self.max_tokens = getattr(settings, 'GEMINI_MAX_TOKENS', 800)
                self.timeout = getattr(settings, 'GEMINI_TIMEOUT', 30)
                logger.info("Gemini client initialized successfully")
            else:
                logger.warning("Gemini package available but no API key provided")
        else:
            logger.warning("Gemini package not available")
        
    def get_tutor_matches(self, learner_profile, tutors_data, cache_key=None):
        """
        Get top 3 tutor matches using AI (OpenAI or Gemini)
        
        Args:
            learner_profile (dict): Learner's cognitive profile and subjects
            tutors_data (list): Pre-processed tutor compatibility data
            cache_key (str): Cache key for storing results
            
        Returns:
            dict: AI response with ranked tutors
        """
        
        logger.info(f"Starting AI matching for {len(tutors_data)} tutors using {self.ai_provider}")
        
        # Check cache first
        if cache_key:
            logger.debug(f"Checking cache with key: {cache_key}")
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for matching request: {cache_key}")
                return cached_result
            logger.debug("No cached result found")
        
        try:
            # Check if AI client is available
            logger.debug(f"AI availability check - Provider: {self.ai_provider}, client: {self.client is not None}")
            
            if not self.client:
                if self.ai_provider == 'gemini' and not GEMINI_AVAILABLE:
                    logger.error("Gemini package not installed or not imported successfully")
                    raise Exception("Gemini package not available")
                elif self.ai_provider == 'openai' and not OPENAI_AVAILABLE:
                    logger.error("OpenAI package not installed or not imported successfully") 
                    raise Exception("OpenAI package not available")
                else:
                    logger.error(f"{self.ai_provider.title()} client not initialized (likely missing API key)")
                    raise Exception(f"{self.ai_provider.title()} client not initialized")
            
            # Prepare token-optimized prompt
            logger.debug("Building matching prompt...")
            prompt = self._build_matching_prompt(learner_profile, tutors_data)
            logger.info(f"Prompt built - length: {len(prompt)} characters")
            
            # Call AI API based on provider
            logger.info(f"Calling {self.ai_provider.title()} API - Model: {self.model}, Max tokens: {self.max_tokens}")
            start_time = timezone.now()
            
            if self.ai_provider == 'gemini':
                ai_content = self._call_gemini_api(prompt)
            else:
                ai_content = self._call_openai_api(prompt)
            
            processing_time = (timezone.now() - start_time).total_seconds() * 1000
            logger.info(f"{self.ai_provider.title()} API call completed in {processing_time}ms")
            
            # Parse AI response
            logger.debug(f"AI response length: {len(ai_content)} characters")
            logger.debug(f"AI response preview: {ai_content[:200]}...")
            
            # Clean AI response (remove markdown code blocks if present)
            cleaned_content = self._clean_ai_response(ai_content)
            logger.debug(f"Cleaned response length: {len(cleaned_content)} characters")
            
            result = json.loads(cleaned_content)
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
            logger.error(f"Original AI response: {ai_content if 'ai_content' in locals() else 'No original response'}")
            logger.error(f"Cleaned AI response: {cleaned_content if 'cleaned_content' in locals() else 'No cleaned response'}")
            raise Exception("AI returned invalid response format")
        except Exception as e:
            # Handle specific AI provider errors
            if self.ai_provider == 'openai' and 'openai' in str(type(e).__module__):
                logger.error(f"OpenAI API error: {e}")
                raise Exception(f"OpenAI API error: {str(e)}")
            elif self.ai_provider == 'gemini' and ('google' in str(type(e).__module__) or 'genai' in str(type(e).__module__)):
                logger.error(f"Gemini API error: {e}")
                raise Exception(f"Gemini API error: {str(e)}")
            else:
                logger.error(f"AI matching failed with unexpected error: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                raise Exception(f"AI service error: {str(e)}")
    
    def _call_openai_api(self, prompt):
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a tutor-student matching expert. Return ONLY valid JSON - no markdown, no code blocks, no explanations. Just pure JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=self.max_tokens,
            temperature=0.4,  # Moderate temperature for varied but sensible results
        )
        return response.choices[0].message.content.strip()
    
    def _call_gemini_api(self, prompt):
        """Call Gemini API"""
        full_prompt = f"""You are a tutor-student matching expert. Return ONLY valid JSON - no markdown, no code blocks, no explanations. Just pure JSON.

{prompt}"""
        
        response = self.client.generate_content(
            full_prompt,
            generation_config={
                'max_output_tokens': self.max_tokens,
                'temperature': 0.4,
            }
        )
        return response.text.strip()
    
    def _clean_ai_response(self, ai_content):
        """Clean AI response by removing markdown code blocks and extra formatting"""
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        cleaned = ai_content.strip()
        
        # Check for markdown code blocks
        if cleaned.startswith('```'):
            # Find the first newline after ```
            first_newline = cleaned.find('\n')
            if first_newline != -1:
                # Remove the opening ```json or ```
                cleaned = cleaned[first_newline + 1:]
            
            # Remove closing ```
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
        
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Log the cleaning process for debugging
        if cleaned != ai_content.strip():
            logger.debug("AI response contained markdown formatting - cleaned successfully")
        
        return cleaned
    
    def _build_matching_prompt(self, learner_profile, tutors_data):
        """Build token-optimized prompt for AI models"""
        
        # Extract learner data
        subjects = learner_profile['subjects']
        cognitive = learner_profile['cognitive']
        
        # Build tutor list (compact format)
        tutors_str = []
        for tutor in tutors_data:
            # Compact pedagogy format
            pedagogy = ','.join([f"{k}:{v}" for k, v in tutor['pedagogy'].items()])
            
            tutors_str.append(
                f"{tutor['id']} (cog:{tutor['cognitive_score']}/10, "
                f"subj:{tutor['subject_score']}/10, price:{tutor.get('price_score', 5)}/10, ₹{tutor['price']}) "
                f"subjects:\"{tutor['subjects']}\" pedagogy:\"{pedagogy}\""
            )
        
        tutors_list = '\n'.join([f"{i+1}. {t}" for i, t in enumerate(tutors_str)])
        
        # Token-optimized prompt
        prompt = f"""You are a tutor-student matching expert. Rank tutors by cognitive+subject compatibility+price.

Student: confidence={cognitive['confidence']}, anxiety={cognitive['anxiety']}, processing_speed={cognitive['processing_speed']}, working_memory={cognitive['working_memory']}, precision={cognitive['precision']}, error_correction={cognitive['error_correction']}, exploration={cognitive['exploration']}, impulsivity={cognitive['impulsivity']}, logical_reasoning={cognitive['logical_reasoning']}, hypothetical_reasoning={cognitive['hypothetical_reasoning']}
Subjects: {json.dumps(subjects)}

Tutors (cognitive_score/10, subject_score/10, price_score/10):
{tutors_list}

Matching Priority:
1. Cognitive compatibility (most important)
2. Subject overlap 
3. Price competitiveness
4. Introduce slight variation in similar matches

Subject matching rules:
- Handle variations: Maths=Mathematics, Science=Physics/Chemistry/Biology
- Partial overlap allowed, reward close matches
- Consider semantic similarity

IMPORTANT: 
- Return ONLY valid JSON - no markdown blocks, no code formatting, no explanations
- Avoid always picking the same tutors - consider subtle differences
- When scores are very close, factor in price and minor pedagogical differences

Required JSON format:
{{"matches":[{{"tutor_id":"id","final_score":85,"reasoning":"Strong cognitive match (8.2/10): TCS-HIGH suits low confidence. Good subject overlap. Competitive pricing.","subject_explanation":"Mathematics expertise matches Maths requirement"}}]}}

Return top 3 VARIED matches - avoid repetitive selections."""

        return prompt
    
    @staticmethod  
    def generate_cache_key(learner_id, tutors_hash, cognitive_hash):
        """Generate cache key for matching results"""
        from django.utils import timezone
        
        # Add hour component to introduce some cache variation
        hour_component = timezone.now().strftime("%Y%m%d%H")
        key_data = f"match_{learner_id}_{tutors_hash}_{cognitive_hash}_{hour_component}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]