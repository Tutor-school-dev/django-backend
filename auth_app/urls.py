from django.urls import path
from .views import (
    GoogleSignInView,
    OTPRequestView,
    OTPVerifyView,
    TokenRefreshView,
    TutorLoginView
)

urlpatterns = [
    path('google/', GoogleSignInView.as_view(), name='google-signin'),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('tutor/login/', TutorLoginView.as_view(), name='tutor-login'), # password based login for tutors
]