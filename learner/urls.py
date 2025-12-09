from django.urls import path
from .views import CreateLearnerAccountView, CognitiveAssessmentView, TutorMatchingView

urlpatterns = [
    path('create-account/', CreateLearnerAccountView.as_view(), name='create-learner-account'),
    path('cognitive-assessment/', CognitiveAssessmentView.as_view(), name='cognitive-assessment'),
    path('match-tutors/', TutorMatchingView.as_view(), name='match-tutors'),
]
