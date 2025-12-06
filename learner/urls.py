from django.urls import path
from .views import CreateLearnerAccountView, CognitiveAssessmentView

urlpatterns = [
    path('create-account/', CreateLearnerAccountView.as_view(), name='create-learner-account'),
    path('cognitive-assessment/', CognitiveAssessmentView.as_view(), name='cognitive-assessment'),
]
