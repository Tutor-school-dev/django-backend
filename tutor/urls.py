from django.urls import path
from .views import CreateTutorAccountView, TutorDetailsView

urlpatterns = [
    path('', TutorDetailsView.as_view(), name='get-tutor-details'),
    path('create-account/', CreateTutorAccountView.as_view(), name='create-tutor-account'),
    path('add-details/', TutorDetailsView.as_view(), name='add-tutor-details'),
]
