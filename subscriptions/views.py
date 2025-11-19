from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import transaction
import logging

from auth_app.authentication import JWTAuthentication
from .models import Subscription, Payment, UserSubscription
from .serializers import (
    SubscriptionSerializer,
    StartPaymentSerializer,
    PaymentSerializer,
    UserSubscriptionSerializer,
    StartPaymentResponseSerializer,
    PaymentStatusSerializer
)
from .hdfc_service import HDFCPaymentService

logger = logging.getLogger(__name__)


class ListSubscriptionsView(APIView):
    """
    GET /api/subscriptions/
    List all available subscription plans
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all active subscription plans"""
        try:
            subscriptions = Subscription.objects.filter(is_active=True).order_by('id')
            serializer = SubscriptionSerializer(subscriptions, many=True)
            
            return Response({
                'success': True,
                'plans': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error fetching subscription plans")
            return Response({
                'error': 'Failed to fetch subscription plans',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StartPaymentView(APIView):
    """
    POST /api/subscriptions/start-payment/
    Initiate payment for a subscription
    
    Request body:
    {
        "sub_id": 1,  # 1=Basic, 2=Standard, 3=Pro
        "duration": 3  # 3, 6, or 12 months
    }
    """
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        """Start payment process"""
        try:
            # Validate request data
            serializer = StartPaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            sub_id = serializer.validated_data['sub_id']
            duration = serializer.validated_data['duration']
            
            # Get teacher from authenticated request
            teacher = request.user
            
            # Get subscription plan
            try:
                subscription = Subscription.objects.get(id=sub_id, is_active=True)
            except Subscription.DoesNotExist:
                return Response({
                    'error': f'Subscription plan {sub_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate amount
            amount = subscription.calculate_price(duration)
            
            # Generate order ID
            hdfc_service = HDFCPaymentService()
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            order_id = hdfc_service.generate_order_id(
                teacher_id=str(teacher.id),
                subscription_id=sub_id,
                timestamp=timestamp
            )
            
            # Create payment record
            with transaction.atomic():
                payment = Payment.objects.create(
                    order_id=order_id,
                    teacher=teacher,
                    subscription=subscription,
                    amount=amount,
                    duration_months=duration,
                    status=Payment.STATUS_PENDING
                )
            
            # Create payment session with HDFC
            payment_response = hdfc_service.create_payment_session(
                order_id=order_id,
                amount=amount,
                teacher_id=str(teacher.id),
                teacher_name=teacher.name or '',
                teacher_email=teacher.email or '',
                teacher_phone=teacher.phone or '',
                subscription_id=sub_id,
                duration_months=duration
            )
            
            if payment_response.get('success'):
                logger.info(f"Payment session created: order_id={order_id}, teacher={teacher.id}")
                
                return Response({
                    'success': True,
                    'payment_url': payment_response['payment_url'],
                    'order_id': order_id,
                    'amount': amount,
                    'subscription': subscription.name,
                    'duration_months': duration,
                    'message': 'Payment session created. Redirect user to payment_url'
                }, status=status.HTTP_200_OK)
            else:
                # Payment session creation failed
                logger.error(f"Failed to create payment session: {payment_response}")
                
                return Response({
                    'success': False,
                    'error': payment_response.get('error', 'Failed to initiate payment'),
                    'details': payment_response.get('details', '')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.exception("Error starting payment")
            return Response({
                'error': 'Failed to start payment',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(APIView):
    """
    GET /api/subscriptions/payment-status/{order_id}/
    Check payment status
    """
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, order_id):
        """Get payment status"""
        try:
            teacher = request.user
            
            # Get payment record
            try:
                payment = Payment.objects.get(order_id=order_id, teacher=teacher)
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # If already charged, return from database
            if payment.status == Payment.STATUS_CHARGED:
                return Response({
                    'success': True,
                    'order_id': payment.order_id,
                    'status': payment.status,
                    'amount': str(payment.amount),
                    'subscription': payment.subscription.name,
                    'duration_months': payment.duration_months,
                    'payment_date': payment.payment_date,
                    'tracking_id': payment.hdfc_tracking_id,
                    'bank_ref_no': payment.hdfc_bank_ref_no,
                    'message': 'Payment successful'
                }, status=status.HTTP_200_OK)
            
            # Check status from HDFC gateway
            hdfc_service = HDFCPaymentService()
            status_response = hdfc_service.verify_payment_status(order_id, str(teacher.id))
            
            if not status_response.get('success'):
                return Response({
                    'error': 'Failed to check payment status',
                    'details': status_response.get('error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            order_status = status_response.get('status', '').upper()
            
            # Update payment status if changed
            if order_status == 'CHARGED' and payment.status == Payment.STATUS_PENDING:
                with transaction.atomic():
                    # Mark payment as charged
                    payment.mark_as_charged({
                        'transaction_id': status_response.get('trn_id'),
                        'tracking_id': status_response.get('trn_id'),
                        'bank_ref_no': status_response.get('trn_id'),
                        'response_code': '',
                        'response_message': status_response.get('bank_error_message', ''),
                        'payment_method': status_response.get('payment_method_type'),
                    })
                    
                    # Create user subscription
                    start_date = timezone.now()
                    end_date = hdfc_service.calculate_subscription_end_date(
                        start_date, payment.duration_months
                    )
                    
                    # Deactivate previous subscriptions
                    UserSubscription.objects.filter(
                        teacher=teacher,
                        status=UserSubscription.STATUS_ACTIVE
                    ).update(status=UserSubscription.STATUS_EXPIRED)
                    
                    # Create new subscription
                    user_subscription = UserSubscription.objects.create(
                        teacher=teacher,
                        subscription=payment.subscription,
                        payment=payment,
                        duration_months=payment.duration_months,
                        amount_paid=payment.amount,
                        start_date=start_date,
                        end_date=end_date,
                        status=UserSubscription.STATUS_ACTIVE
                    )
                    
                    logger.info(f"Subscription activated: user_sub_id={user_subscription.id}, teacher={teacher.id}")
            
            elif order_status in ['AUTHORIZATION_FAILED', 'AUTHENTICATION_FAILED']:
                payment.status = Payment.STATUS_AUTHENTICATION_FAILED
                payment.hdfc_response_message = status_response.get('bank_error_message')
                payment.save()
            
            # Return current status
            return Response({
                'success': True,
                'order_id': order_id,
                'status': payment.status,
                'amount': str(payment.amount),
                'subscription': payment.subscription.name,
                'duration_months': payment.duration_months,
                'trn_id': status_response.get('trn_id'),
                'payment_method_type': status_response.get('payment_method_type'),
                'refunded': status_response.get('refunded', False),
                'bank_error_message': status_response.get('bank_error_message', '')
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"Error checking payment status for order_id: {order_id}")
            return Response({
                'error': 'Failed to check payment status',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSubscriptionsView(APIView):
    """
    GET /api/subscriptions/user-subscriptions/
    Get user's subscription history
    """
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """Get user's subscriptions"""
        try:
            teacher = request.user
            
            # Get all subscriptions for this user
            subscriptions = UserSubscription.objects.filter(
                teacher=teacher
            ).select_related('subscription', 'payment').order_by('-created_at')
            
            # Separate active and past subscriptions
            active_subscriptions = subscriptions.filter(status=UserSubscription.STATUS_ACTIVE)
            past_subscriptions = subscriptions.exclude(status=UserSubscription.STATUS_ACTIVE)
            
            active_serializer = UserSubscriptionSerializer(active_subscriptions, many=True)
            past_serializer = UserSubscriptionSerializer(past_subscriptions, many=True)
            
            return Response({
                'success': True,
                'active_subscriptions': active_serializer.data,
                'past_subscriptions': past_serializer.data,
                'total_count': subscriptions.count()
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"Error fetching user subscriptions for teacher: {teacher.id}")
            return Response({
                'error': 'Failed to fetch subscriptions',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentWebhookView(APIView):
    """
    POST /api/subscriptions/payment-webhook/
    Handle HDFC payment webhook notifications
    Webhook structure: {"event_name": "ORDER_CHARGED", "content": {"order": {...}}}
    """
    permission_classes = [AllowAny]  # Webhook from HDFC, no JWT required
    
    def post(self, request):
        """Process HDFC webhook"""
        try:
            webhook_data = request.data
            
            logger.info(f"Received HDFC webhook: {webhook_data.get('event_name')}")
            
            # Parse webhook data using service
            hdfc_service = HDFCPaymentService()
            parsed_data = hdfc_service.parse_webhook_data(webhook_data)
            
            if 'error' in parsed_data:
                logger.error(f"Webhook parsing error: {parsed_data}")
                return Response({
                    'error': parsed_data['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            order_id = parsed_data.get('order_id')
            order_status = parsed_data.get('status')
            event_name = parsed_data.get('event_name')
            
            # Get payment record
            try:
                payment = Payment.objects.select_related('teacher', 'subscription').get(order_id=order_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for webhook order_id: {order_id}")
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Process based on event
            if event_name == 'ORDER_CHARGED' and order_status == 'CHARGED':
                # Only process if payment is still pending
                if payment.status == Payment.STATUS_PENDING:
                    with transaction.atomic():
                        # Mark payment as charged
                        payment.mark_as_charged({
                            'transaction_id': parsed_data.get('trn_id'),
                            'tracking_id': parsed_data.get('trn_id'),
                            'bank_ref_no': parsed_data.get('trn_id'),
                            'response_code': '',
                            'response_message': parsed_data.get('bank_error_message', ''),
                            'payment_method': parsed_data.get('payment_method_type'),
                        })
                        
                        # Create user subscription
                        start_date = timezone.now()
                        end_date = hdfc_service.calculate_subscription_end_date(
                            start_date, payment.duration_months
                        )
                        
                        # Deactivate previous subscriptions
                        UserSubscription.objects.filter(
                            teacher=payment.teacher,
                            status=UserSubscription.STATUS_ACTIVE
                        ).update(status=UserSubscription.STATUS_EXPIRED)
                        
                        # Create new subscription
                        user_subscription = UserSubscription.objects.create(
                            teacher=payment.teacher,
                            subscription=payment.subscription,
                            payment=payment,
                            duration_months=payment.duration_months,
                            amount_paid=payment.amount,
                            start_date=start_date,
                            end_date=end_date,
                            status=UserSubscription.STATUS_ACTIVE
                        )
                        
                        logger.info(f"Webhook: Subscription activated - user_sub_id={user_subscription.id}, order_id={order_id}")
                
                return Response({
                    'success': True,
                    'message': 'Webhook processed successfully'
                }, status=status.HTTP_200_OK)
            
            elif event_name in ['AUTO_REFUND', 'ORDER_REFUNDED']:
                # Handle refund
                if payment.status == Payment.STATUS_CHARGED:
                    payment.status = Payment.STATUS_REFUNDED
                    payment.hdfc_response_message = f"Refunded: {parsed_data.get('amount_refunded')}"
                    payment.save()
                    
                    # Deactivate subscription if exists
                    UserSubscription.objects.filter(
                        payment=payment,
                        status=UserSubscription.STATUS_ACTIVE
                    ).update(status=UserSubscription.STATUS_CANCELLED)
                    
                    logger.info(f"Webhook: Payment refunded - order_id={order_id}")
                
                return Response({
                    'success': True,
                    'message': 'Refund processed'
                }, status=status.HTTP_200_OK)
            
            elif order_status in ['AUTHORIZATION_FAILED', 'AUTHENTICATION_FAILED']:
                # Handle failed payment
                payment.status = Payment.STATUS_AUTHENTICATION_FAILED
                payment.hdfc_response_message = parsed_data.get('bank_error_message', 'Payment failed')
                payment.save()
                
                logger.info(f"Webhook: Payment failed - order_id={order_id}, status={order_status}")
                
                return Response({
                    'success': True,
                    'message': 'Payment failure recorded'
                }, status=status.HTTP_200_OK)
            
            # Unknown event or status
            logger.warning(f"Webhook: Unhandled event - {event_name}, status={order_status}, order_id={order_id}")
            
            return Response({
                'success': True,
                'message': 'Webhook received'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error processing HDFC webhook")
            return Response({
                'error': 'Failed to process webhook',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
