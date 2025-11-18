from django.urls import path
from .views import CreateLearnerAccountView

urlpatterns = [
    path('create-account/', CreateLearnerAccountView.as_view(), name='create-learner-account'),
]
