"""
HDFC Payment Gateway Integration Service
"""
import base64
import hashlib
import hmac
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
        self.webhook_username = settings.HDFC_WEBHOOK_USERNAME
        self.webhook_password = settings.HDFC_WEBHOOK_PASSWORD

    def verify_webhook_signature(self, webhook_data: dict) -> bool:
        """
        Verify the HMAC-SHA256 signature HDFC includes in the webhook payload.
        HDFC sends: signature field = HMAC-SHA256(order_id + status_id, webhook_encryption_key)
        Returns True if signature matches or if no encryption key is configured.
        """
        encryption_key = getattr(settings, 'HDFC_WEBHOOK_ENCRYPTION_KEY', '')
        if not encryption_key:
            # Key not configured — skip verification but log a warning
            logger.warning("HDFC_WEBHOOK_ENCRYPTION_KEY not set; skipping signature verification")
            return True
        try:
            def get_val(key):
                val = webhook_data.get(key, '')
                return val[0] if isinstance(val, list) else val

            order_id = get_val('order_id')
            status_id = get_val('status_id')
            received_signature = get_val('signature')

            message = f"{order_id}{status_id}"
            expected = hmac.new(
                encryption_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            expected_b64 = base64.b64encode(expected).decode('utf-8')
            return hmac.compare_digest(expected_b64, received_signature)
        except Exception:
            logger.exception("Error verifying webhook signature")
            return False
    
    def _get_auth_header(self):
        """Generate Base64 encoded Authorization header"""
        # HDFC expects: 'Basic {BASE64_ENCODED_API_KEY}:'
        credentials = f"{self.api_key}:"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def generate_order_id(self, teacher_id: str, subscription_id: int, timestamp: str) -> str:
        """
        Generate unique order ID for payment within 30 chars.
        Format: TS_{teacher_id[:8]}_{sub_id}_{timestamp}
        Max length: 3 + 8 + 1 + 1 + 1 + 14 = 28 chars
        """
        short_teacher_id = str(teacher_id).replace('-', '')[:8]
        order_id = f"TS_{short_teacher_id}_{timestamp}"
        assert len(order_id) <= 30, f"order_id too long: {len(order_id)} chars"
        return order_id
    
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
                'return_url': self.client_return_url,  # Browser redirect URL after payment (frontend page)
                
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
        Parse webhook data from HDFC gateway.
        HDFC sends a flat form-encoded POST (QueryDict) where all values are lists:
        {
            'status': ['CHARGED'],
            'order_id': ['TS_...'],
            'signature': ['...'],
            'signature_algorithm': ['HMAC-SHA256'],
            'status_id': ['21'],
        }
        status_id reference: 21=CHARGED, 22=FAILED, 26=CANCELLED
        """
        try:
            def get_val(key):
                """Extract first element from list value or return string directly."""
                val = webhook_data.get(key, '')
                return val[0] if isinstance(val, list) else val

            order_id = get_val('order_id')
            order_status = get_val('status').upper()
            status_id = get_val('status_id')

            if not order_id:
                return {
                    'error': 'Invalid webhook data structure',
                    'details': 'Missing order_id in webhook payload'
                }

            return {
                'order_id': order_id,
                'status': order_status,
                'status_id': status_id,
                'signature': get_val('signature'),
                'signature_algorithm': get_val('signature_algorithm'),
                'is_success': order_status == 'CHARGED',
            }

        except Exception as e:
            logger.exception("Error parsing HDFC webhook data")
            return {
                'error': 'Failed to parse webhook data',
                'details': str(e)
            }
