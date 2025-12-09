# Tutor Matching System - API Documentation

## Overview
The Tutor Matching System provides AI-powered matching between learners and tutors based on cognitive compatibility analysis. It combines cognitive assessment scores with pedagogy profiles to find the most compatible tutors for each learner.

## Endpoint

```
GET /api/learner/match-tutors/
```

### Authentication
- **Required**: JWT token in Authorization header
- **Format**: `Authorization: Bearer <jwt_token>`
- **User Type**: Must be a learner (user_type: 'learner')

### Rate Limiting
- **Limit**: 5 requests per 5 minutes per user
- **Purpose**: Control OpenAI API costs and prevent abuse
- **Response**: HTTP 429 with retry_after field when exceeded

### Prerequisites
1. **Cognitive Assessment**: Learner must have completed cognitive assessment
2. **Qualified Tutors**: System requires tutors with complete pedagogy profiles
3. **OpenAI Configuration**: OPENAI_API_KEY must be set in environment

### Request
No request body required. All matching is based on authenticated learner's profile and cognitive assessment.

### Response Format

#### Success Response (200 OK)
```json
{
    "success": true,
    "matches": [
        {
            "tutor": {
                "id": "uuid-string",
                "name": "Tutor Name",
                "lesson_price": 500.0,
                "subjects": "Math, Science, Physics",
                "area": "Location Area",
                "state": "State Name",
                "phone": "+91XXXXXXXXXX",
                "email": "tutor@example.com",
                // ... other tutor fields from TutorSerializer
            },
            "match_details": {
                "compatibility_score": 85.5,
                "reasoning": "High confidence support (TCS) matches learner's low confidence. Slow processing support (TSPI) suits learner's processing speed. Strong subject overlap in Mathematics.",
                "subject_explanation": "Perfect match: Learner's Math request matches tutor's Mathematics specialization. Good overlap in Science subjects."
            }
        },
        // ... up to 3 matches total
    ],
    "processing_time_ms": 1250
}
```

#### Error Responses

**Authentication Required (401)**
```json
{
    "error": "Authentication credentials were not provided"
}
```

**Wrong User Type (403)**
```json
{
    "error": "This endpoint is only accessible to learners"
}
```

**Missing Assessment (400)**
```json
{
    "error": "Cognitive assessment required"
}
```

**No Tutors Available (400)**
```json
{
    "error": "No qualified tutors available"
}
```

**Rate Limit Exceeded (429)**
```json
{
    "error": "Too many matching requests. Please wait 5 minutes.",
    "retry_after": 180
}
```

**Server Error (500)**
```json
{
    "error": "An error occurred while finding tutor matches. Please try again."
}
```

## Matching Algorithm

### 1. Cognitive Compatibility Scoring
The system uses 8 pedagogy traits matched against 10 cognitive parameters:

#### Trait Mapping Rules
- **TCS (Confidence Support)**: Matches confidence/anxiety levels
- **TSPI (Slow Processing Instructions)**: Matches processing speed
- **TWMLS (Working Memory Learning Support)**: Matches working memory
- **TPO (Precision Orientation)**: Matches precision scores
- **TECP (Error Correction Practices)**: Matches error correction ability
- **TET (Exploration Teaching)**: Matches exploration tendency
- **TICS (Impulsivity Control Strategies)**: Matches impulsivity levels
- **TRD (Reasoning Development)**: Matches logical/hypothetical reasoning

#### Scoring Logic
For each trait, compatibility is determined by:
- **Low score (≤40)**: Needs HIGH support
- **High score (≥70)**: Needs LOW support
- **Medium score (40-70)**: Benefits from HIGH support

Score: +1 point per compatible trait (max 8 points)

### 2. Subject Compatibility
- Basic string matching with semantic understanding
- Handles variations (Math = Mathematics, Science = Physics/Chemistry/Biology)
- Weighted by subject overlap percentage

### 3. AI Ranking (OpenAI Integration)
- **Model**: GPT-4o-mini for cost efficiency
- **Token Optimization**: Compact prompt format
- **Fallback**: Rule-based ranking when AI unavailable
- **Caching**: 1-hour cache TTL for identical requests

### 4. Final Ranking Criteria
1. Cognitive compatibility score (primary)
2. Subject overlap score (secondary)  
3. Price (tiebreaker - lower preferred)

## Configuration

### Environment Variables
```bash
# Required for AI matching
OPENAI_API_KEY=your_openai_api_key_here

# Optional OpenAI settings
OPENAI_MODEL=gpt-4o-mini           # Default model
OPENAI_MAX_TOKENS=1000             # Token limit per request  
OPENAI_TIMEOUT=30                  # Request timeout seconds
```

### Django Settings
The system automatically configures:
- Rate limiting middleware
- Database caching for AI responses
- Logging for matching requests and errors

## Testing

### Management Command
```bash
python manage.py test_matching --verbose
python manage.py test_matching --learner-id <uuid>
```

### API Testing
```bash
curl -X GET \
  http://localhost:8000/api/learner/match-tutors/ \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json"
```

## Performance & Costs

### Caching Strategy
- **Cache Key**: Combines learner_id + tutors_hash + cognitive_hash
- **TTL**: 1 hour for stable results
- **Invalidation**: Automatic when tutor pool or assessment changes

### Cost Control
- **Rate Limiting**: 5 requests per 5 minutes per user
- **Token Optimization**: Compact prompts (~400 tokens)
- **Model Choice**: GPT-4o-mini for 60x cost reduction vs GPT-4
- **Fallback**: Rule-based matching when AI fails

### Expected Performance
- **AI Response**: 1-3 seconds
- **Fallback Response**: <100ms  
- **Cache Hit**: <50ms
- **Cost per Request**: ~$0.002 (with GPT-4o-mini)

## Error Handling

### Graceful Degradation
1. **OpenAI Unavailable**: Falls back to rule-based matching
2. **API Quota Exceeded**: Returns fallback results with warning
3. **Invalid AI Response**: Logs error, returns rule-based results
4. **Network Timeout**: Automatic fallback after 30 seconds

### Monitoring & Logging
All matching requests, errors, and performance metrics are logged to:
- `logs/application-logs.log` (INFO level)
- `logs/error-logs.log` (ERROR level)

## Future Enhancements

### Planned Features
1. **Location-based filtering**: PostGIS radius matching
2. **Availability checking**: Real-time tutor schedule integration  
3. **Price range filtering**: Budget-based tutor filtering
4. **Learning style preferences**: Extended cognitive profiling
5. **Review system integration**: Include tutor ratings in matching

### Scaling Considerations
1. **Redis caching**: For high-traffic scenarios
2. **Async processing**: Background matching for large tutor pools
3. **Model fine-tuning**: Custom models trained on matching success rates
4. **A/B testing**: Compare different matching algorithms

## Security & Privacy

### Data Protection
- No personal data sent to OpenAI (only scores and IDs)
- JWT token validation for all requests
- Rate limiting prevents enumeration attacks
- Error messages don't expose internal system details

### API Security
- Authentication required for all requests
- User type validation (learners only)
- Input sanitization and validation
- Comprehensive error logging for security monitoring