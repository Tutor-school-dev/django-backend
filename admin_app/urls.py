from django.urls import path
from .views import JobApplicationView, JobListingsView

app_name = 'admin_app'

urlpatterns = [
    path('jobs/', JobListingsView.as_view(), name='job-listings'),
    path('job-apply/', JobApplicationView.as_view(), name='job-apply'),
]