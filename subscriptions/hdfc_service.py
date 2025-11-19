"""
HDFC Payment Gateway Integration Service
"""
import base64
import json
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class HDFCPaymentService:
    """Service class for HDFC payment gateway integration"""
    
    def __init__(self):
        self.api_key = settings.HDFC_API_KEY
        self.payment_url = settings.HDFC_PAYMENT_URL
        self.merchant_id = settings.HDFC_MERCHANT_ID
        self.client_id = settings.HDFC_CLIENT_ID
        self.return_url = settings.HDFC_RETURN_URL
        self.client_return_url = settings.HDFC_CLIENT_RETURN_URL
    
    def _get_auth_header(self):
        """Generate Base64 encoded Authorization header"""
        # HDFC expects: 'Basic {BASE64_ENCODED_API_KEY}:'
        credentials = f"{self.api_key}:"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def generate_order_id(self, teacher_id: str, subscription_id: int, timestamp: str) -> str:
        """
        Generate unique order ID for payment
        Format: TS_{teacher_id[:8]}_{sub_id}_{timestamp}
        """
        short_teacher_id = str(teacher_id).replace('-', '')[:8]
        return f"TS_{short_teacher_id}_{subscription_id}_{timestamp}"
    
    def create_payment_session(
        self,
        order_id: str,
        amount: Decimal,
        teacher_id: str,
        teacher_name: str,
        teacher_email: str,
        teacher_phone: str,
        subscription_id: int,
        duration_months: int
    ) -> dict:
        """
        Create payment session with HDFC gateway
        
        Args:
            order_id: Unique order identifier
            amount: Payment amount in INR
            teacher_id: Teacher UUID
            teacher_name: Teacher full name
            teacher_email: Teacher email
            teacher_phone: Teacher phone number
            subscription_id: Subscription plan ID (1/2/3)
            duration_months: Subscription duration (3/6/12)
        
        Returns:
            dict: Payment session details with redirect URL or error
        """
        try:
            # Validate required fields
            if not all([teacher_id, amount, order_id, teacher_email, teacher_phone]):
                return {
                    'success': False,
                    'error': 'Missing required fields'
                }
            
            # Prepare headers as per HDFC API documentation
            headers = {
                'Authorization': self._get_auth_header(),
                'Content-Type': 'application/json',
                'x-merchantid': self.merchant_id,
                'x-customerid': str(teacher_id),
            }
            
            # Mandatory fields to initiate payment session
            # Following HDFC API structure with UDF fields
            payment_data = {
                'order_id': order_id,
                'amount': float(amount),  # HDFC expects numeric value
                'customer_id': str(teacher_id),
                'customer_email': teacher_email,
                'customer_phone': teacher_phone,
                'payment_page_client_id': self.client_id,
                'action': 'paymentPage',
                'return_url': self.return_url,
                
                # User Defined Fields (UDF) - custom data
                'udf1': str(duration_months),  # Duration in months (12/6/3)
                'udf2': 'TEACHER',  # Model type (TEACHER/LEARNER)
                'udf3': str(subscription_id),  # Subscription plan ID (1/2/3)
                'udf4': 'SUBSCRIPTION',  # Payment type
                'udf5': teacher_name,  # Teacher name (optional)
            }
            
            logger.info(f"Creating HDFC payment session for order_id: {order_id}")
            
            # Make request to HDFC gateway session endpoint
            response = requests.post(
                f"{self.payment_url}/session",
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            if response.ok:
                response_data = response.json()
                
                # Extract payment link from response
                if 'payment_links' in response_data and 'web' in response_data['payment_links']:
                    payment_url = response_data['payment_links']['web']
                    
                    logger.info(f"Payment session created successfully for order_id: {order_id}")
                    
                    return {
                        'success': True,
                        'url': payment_url,
                        'order_id': order_id,
                        'amount': float(amount),
                        'message': 'Payment session created successfully'
                    }
                else:
                    logger.error(f"No payment URL in HDFC response: {response_data}")
                    return {
                        'success': False,
                        'error': 'Payment URL not received from gateway',
                        'details': response_data
                    }
            else:
                # Log error details from HDFC
                try:
                    error_data = response.json()
                    error_fields = error_data.get('error_info', {}).get('fields', {})
                    logger.error(f"HDFC API error - Status: {response.status_code}, Error: {error_fields}")
                except:
                    logger.error(f"HDFC API error - Status: {response.status_code}, Response: {response.text}")
                
                return {
                    'success': False,
                    'error': 'Failed to start payment session',
                    'details': response.text
                }
        
        except requests.exceptions.Timeout:
            logger.error(f"HDFC API timeout for order_id: {order_id}")
            return {
                'success': False,
                'error': 'Payment gateway timeout. Please try again.'
            }
        
        except Exception as e:
            logger.exception(f"Error creating payment session for order_id: {order_id}")
            return {
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            }
    
    def verify_payment_status(self, order_id: str, teacher_id: str) -> dict:
        """
        Check payment status from HDFC gateway
        Endpoint: GET {BASE_URL}/orders/{order_id}
        
        Args:
            order_id: Order ID to check status for
            teacher_id: Teacher UUID for x-customerid header
        
        Returns:
            dict: Payment status details
        """
        try:
            # Prepare headers as per HDFC API documentation
            headers = {
                'Authorization': self._get_auth_header(),
                'Content-Type': 'application/json',
                'x-merchantid': self.merchant_id,
                'x-customerid': str(teacher_id),
            }
            
            logger.info(f"Checking payment status for order_id: {order_id}")
            
            response = requests.get(
                f"{self.payment_url}/orders/{order_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Parse status - HDFC returns: NEW, CHARGED, AUTHORIZATION_FAILED, AUTHENTICATION_FAILED
                order_status = response_data.get('status', '').upper()
                
                result = {
                    'success': True,
                    'order_id': order_id,
                    'status': order_status,
                    'amount': response_data.get('amount', ''),
                    'payment_method_type': response_data.get('payment_method_type', ''),
                    'refunded': response_data.get('refunded', False),
                    'amount_refunded': response_data.get('amount_refunded', 0),
                    'trn_id': response_data.get('trn_id', ''),
                    'bank_error_message': response_data.get('bank_error_message', ''),
                    'customer_id': response_data.get('customer_id', ''),
                    'customer_email': response_data.get('customer_email', ''),
                    'customer_phone': response_data.get('customer_phone', ''),
                    
                    # UDF fields echoed back
                    'udf1': response_data.get('udf1', ''),  # Duration
                    'udf2': response_data.get('udf2', ''),  # TEACHER
                    'udf3': response_data.get('udf3', ''),  # Subscription ID
                    'udf4': response_data.get('udf4', ''),  # SUBSCRIPTION
                    'udf5': response_data.get('udf5', ''),  # Teacher name
                }
                
                # Get transaction ID from txn_detail if available
                txn_detail = response_data.get('txn_detail', {})
                if txn_detail and 'trn_id' in txn_detail:
                    result['transaction_id'] = txn_detail['trn_id']
                
                logger.info(f"Payment status retrieved: order_id={order_id}, status={order_status}")
                return result
            
            else:
                logger.error(f"Failed to get payment status: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': 'Failed to retrieve payment status',
                    'details': response.text
                }
        
        except Exception as e:
            logger.exception(f"Error checking payment status for order_id: {order_id}")
            return {
                'success': False,
                'error': 'Failed to check payment status',
                'details': str(e)
            }
    
    def calculate_subscription_end_date(self, start_date, duration_months: int):
        """Calculate subscription end date based on duration"""
        if duration_months == 3:
            return start_date + timedelta(days=90)
        elif duration_months == 6:
            return start_date + timedelta(days=180)
        elif duration_months == 12:
            return start_date + timedelta(days=365)
        else:
            # Default to months calculation
            return start_date + timedelta(days=30 * duration_months)
    
    def parse_webhook_data(self, webhook_data: dict) -> dict:
        """
        Parse webhook data from HDFC gateway
        Webhook structure: {"event_name": "ORDER_CHARGED", "content": {"order": {...}}}
        
        Args:
            webhook_data: POST data received on webhook URL
        
        Returns:
            dict: Parsed payment result
        """
        try:
            event_name = webhook_data.get('event_name', '')
            order_data = webhook_data.get('content', {}).get('order', {})
            
            if not order_data:
                return {
                    'error': 'Invalid webhook data structure',
                    'details': 'Missing order data in webhook payload'
                }
            
            # Parse status - HDFC sends: CHARGED, AUTHORIZATION_FAILED, etc.
            order_status = order_data.get('status', '').upper()
            
            result = {
                'event_name': event_name,
                'order_id': order_data.get('order_id'),
                'status': order_status,
                'amount': order_data.get('amount'),
                'payment_method_type': order_data.get('payment_method_type'),
                'refunded': order_data.get('refunded', False),
                'amount_refunded': order_data.get('amount_refunded', 0),
                'trn_id': order_data.get('trn_id'),
                'bank_error_message': order_data.get('bank_error_message'),
                'customer_id': order_data.get('customer_id'),
                'customer_email': order_data.get('customer_email'),
                'customer_phone': order_data.get('customer_phone'),
                
                # UDF fields
                'duration_months': order_data.get('udf1'),  # Duration
                'model_type': order_data.get('udf2'),  # TEACHER/LEARNER
                'subscription_id': order_data.get('udf3'),  # Subscription ID
                'payment_type': order_data.get('udf4'),  # SUBSCRIPTION
                'teacher_name': order_data.get('udf5'),  # Optional teacher name
                
                # Transaction details
                'transaction_id': order_data.get('txn_detail', {}).get('trn_id'),
                
                'is_success': order_status == 'CHARGED',
            }
            
            return result
        
        except Exception as e:
            logger.exception("Error parsing HDFC webhook data")
            return {
                'error': 'Failed to parse webhook data',
                'details': str(e)
            }
