from django.urls import path
from .views import CreateTutorAccountView, TutorDetailsView

urlpatterns = [
    path('create-account/', CreateTutorAccountView.as_view(), name='create-tutor-account'),
    path('add-details/', TutorDetailsView.as_view(), name='add-tutor-details'),
    path('/', TutorDetailsView.as_view(), name='get-tutor-details'),
    
]
