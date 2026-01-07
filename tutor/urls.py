from django.urls import path
from .views import CreateTutorAccountView, TutorDetailsView, TutorGenericDetailsView, TutorJobDetails, TutorPublicGenericDetailsView

urlpatterns = [
    path('', TutorDetailsView.as_view(), name='get-tutor-details'),
    path('all/', TutorGenericDetailsView.as_view(), name='get-all-tutors'),
    path('public/all/', TutorPublicGenericDetailsView.as_view(), name='get-public-tutors'),
    path('create-account/', CreateTutorAccountView.as_view(), name='create-tutor-account'),
    path('add-details/', TutorDetailsView.as_view(), name='add-tutor-details'),
    path('applied-jobs/', TutorJobDetails.as_view(), name='get-tutor-applications')
]
