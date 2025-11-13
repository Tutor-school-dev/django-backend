from django.urls import path
from .views import (
    GoogleSignInView,
    OTPRequestView,
    OTPVerifyView,
    TokenRefreshView
)

urlpatterns = [
    path('google/', GoogleSignInView.as_view(), name='google-signin'),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]