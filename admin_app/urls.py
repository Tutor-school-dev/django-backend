from django.urls import path
from .views import JobListingsView

app_name = 'admin_app'

urlpatterns = [
    path('jobs/', JobListingsView.as_view(), name='job-listings'),
]