from django.urls import path
from .views import CreateTutorAccountView

urlpatterns = [
    path('create-account/', CreateTutorAccountView.as_view(), name='create-tutor-account'),
]
