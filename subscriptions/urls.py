from django.urls import path
from .views import (
    ListSubscriptionsView,
    StartPaymentView,
    PaymentStatusView,
    UserSubscriptionsView,
    PaymentWebhookView
)

urlpatterns = [
    # List all subscription plans (public)
    path('', ListSubscriptionsView.as_view(), name='list-subscriptions'),
    
    # Start payment for a subscription (protected)
    path('start-payment/', StartPaymentView.as_view(), name='start-payment'),
    
    # Check payment status (protected)
    path('payment-status/<str:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
    
    # Get user's subscription history (protected)
    path('user-subscriptions/', UserSubscriptionsView.as_view(), name='user-subscriptions'),
    
    # HDFC webhook endpoint (public - receives from HDFC)
    path('payment-webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
