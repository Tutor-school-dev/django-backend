from django.urls import path
from .views import CreateTutorAccountView, AddTutorDetailsView

urlpatterns = [
    path('create-account/', CreateTutorAccountView.as_view(), name='create-tutor-account'),
    path('add-details/', AddTutorDetailsView.as_view(), name='add-tutor-details'),
]
