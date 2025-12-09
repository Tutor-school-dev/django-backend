# Step-by-Step Testing Guide for Tutor Matching API

## Prerequisites
Make sure you have the Django server environment set up and running.

## Step 1: Navigate to Project Directory
```bash
cd /Users/gbhinda/gaurav/django-backend
```

## Step 2: Start Django Server
```bash
python manage.py runserver
```
*Keep this terminal open - the server should run on http://localhost:8000*

## Step 3: Create Test Data (New Terminal)
Open a new terminal and run:

```bash
cd /Users/gbhinda/gaurav/django-backend
python manage.py create_test_data
```

**Expected Output:**
```
Creating test data for matching system...
✓ Created learner: Test Student (ID: <uuid>)
✓ Created cognitive assessment with low confidence profile
✓ Created tutor: Perfect Match Tutor (ID: <uuid>)
✓ Created tutor: Good Match Tutor (ID: <uuid>)
✓ Created tutor: Poor Match Tutor (ID: <uuid>)

==================================================
TEST DATA CREATED SUCCESSFULLY!
==================================================

LEARNER INFO:
Name: Test Student
ID: <learner-uuid>
Subjects: ["Mathematics", "Physics", "Chemistry"]
Cognitive Profile: Low confidence, high anxiety, needs support

JWT TOKEN (copy this for API testing):
<jwt-token-here>

TUTORS CREATED:
1. Perfect Match Tutor - ₹800/hr (Expected Score: 8/8)
2. Good Match Tutor - ₹600/hr (Expected Score: 4/8)
3. Poor Match Tutor - ₹400/hr (Expected Score: 0/8)

API TESTING COMMAND:
curl -X GET http://localhost:8000/api/learner/match-tutors/ \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json"
```

## Step 4: Copy the JWT Token
From the output above, copy the JWT token that appears after "JWT TOKEN (copy this for API testing):"

## Step 5: Test the API Endpoint
Use the curl command provided in the output, or manually construct it:

```bash
curl -X GET http://localhost:8000/api/learner/match-tutors/ \
  -H "Authorization: Bearer <PASTE_JWT_TOKEN_HERE>" \
  -H "Content-Type: application/json"
```

**Replace `<PASTE_JWT_TOKEN_HERE>` with the actual token from Step 4.**

## Step 6: Expected Response
You should get a response like this:

```json
{
    "success": true,
    "matches": [
        {
            "tutor": {
                "id": "<tutor-uuid>",
                "name": "Perfect Match Tutor",
                "lesson_price": 800.0,
                "subjects": "[\"Mathematics\", \"Physics\", \"Algebra\"]",
                "area": "Indiranagar",
                "state": "Karnataka",
                "phone": "+919876543200",
                "email": "tutor0@example.com"
            },
            "match_details": {
                "compatibility_score": 85.5,
                "reasoning": "High confidence support (TCS) matches learner's low confidence. Slow processing support (TSPI) suits learner's processing speed...",
                "subject_explanation": "Strong subject overlap: Mathematics matches perfectly..."
            }
        },
        {
            "tutor": {
                "id": "<tutor-uuid>",
                "name": "Good Match Tutor",
                "lesson_price": 600.0,
                "subjects": "[\"Mathematics\", \"Chemistry\", \"Science\"]",
                // ... more tutor data
            },
            "match_details": {
                "compatibility_score": 65.0,
                // ... match analysis
            }
        },
        {
            "tutor": {
                "id": "<tutor-uuid>", 
                "name": "Poor Match Tutor",
                "lesson_price": 400.0,
                // ... more data
            },
            "match_details": {
                "compatibility_score": 25.0,
                // ... match analysis
            }
        }
    ],
    "processing_time_ms": 1250
}
```

## Step 7: Test Different Scenarios

### 7a. Test Rate Limiting
Run the same curl command 6 times quickly:
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -X GET http://localhost:8000/api/learner/match-tutors/ \
    -H "Authorization: Bearer <TOKEN>" \
    -H "Content-Type: application/json"
  echo -e "\n---"
done
```

**Expected:** First 5 requests succeed, 6th returns HTTP 429 (Too Many Requests)

### 7b. Test Without Authentication
```bash
curl -X GET http://localhost:8000/api/learner/match-tutors/ \
  -H "Content-Type: application/json"
```

**Expected:** HTTP 401 Unauthorized

### 7c. Test with Invalid Token
```bash
curl -X GET http://localhost:8000/api/learner/match-tutors/ \
  -H "Authorization: Bearer invalid-token-here" \
  -H "Content-Type: application/json"
```

**Expected:** HTTP 401 Unauthorized

## Step 8: Verify Matching Logic

### Check Cognitive Compatibility Scores
The test data is designed with:
- **Perfect Match Tutor**: All 8 pedagogy traits match learner's needs = 8/8 score
- **Good Match Tutor**: 4 traits match = 4/8 score  
- **Poor Match Tutor**: 0 traits match = 0/8 score

### Subject Matching
- **Learner subjects**: Mathematics, Physics, Chemistry
- **Perfect Match**: Mathematics, Physics, Algebra (good overlap)
- **Good Match**: Mathematics, Chemistry, Science (moderate overlap)
- **Poor Match**: Biology, English, History (no overlap)

## Step 9: Test Management Command
```bash
python manage.py test_matching --verbose
```

This should show detailed matching information and verify the system works end-to-end.

## Troubleshooting

### If you get "No module named 'openai'":
```bash
pip install openai==1.58.1
```

### If you get "OPENAI_API_KEY not set":
Add to your `.env` file:
```
OPENAI_API_KEY=your_openai_key_here
```

### If you get database errors:
```bash
python manage.py makemigrations
python manage.py migrate
```

### If you get "No qualified tutors available":
Run the test data creation command again:
```bash
python manage.py create_test_data
```

## Expected Performance
- **With OpenAI**: 1-3 second response time, detailed AI reasoning
- **Without OpenAI**: <100ms response time, rule-based fallback reasoning
- **Cached results**: <50ms response time for repeated requests

## Cleanup (Optional)
To remove test data:
```bash
python manage.py shell
>>> from learner.models import Learner
>>> from tutor.models import Teacher
>>> Learner.objects.filter(name="Test Student").delete()
>>> Teacher.objects.filter(name__contains="Match Tutor").delete()
>>> exit()
```