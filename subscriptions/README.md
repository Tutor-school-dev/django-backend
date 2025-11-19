# TutorSchool Subscription System

## Overview
Complete subscription management system for TutorSchool tutors using HDFC Payment Gateway integration.

## Subscription Plans

### 1. Basic Plan (₹100/month)
- **ID**: 1
- **Monthly Price**: ₹100
- **3 Months**: ₹300
- **6 Months**: ₹600
- **12 Months**: ₹1,200
- **Features**:
  - 10 tuition applications
  - Pedagogy training
  - Profile listing

### 2. Standard Plan (₹599/month)
- **ID**: 2
- **Monthly Price**: ₹599
- **3 Months**: ₹1,797
- **6 Months**: ₹3,594
- **12 Months**: ₹7,188
- **Features**:
  - 25 tuition applications
  - Verified badge
  - Priority listing
  - Mock interviews
  - Fast-track support
  - Workshops
  - Pedagogy training
  - Profile listing

### 3. Pro Plan (₹999/month)
- **ID**: 3
- **Monthly Price**: ₹999
- **3 Months**: ₹2,997
- **6 Months**: ₹5,994
- **12 Months**: ₹11,988
- **Features**:
  - Unlimited tuition applications
  - Verified badge
  - Priority listing
  - Mock interviews
  - Fast-track support
  - Workshops
  - Health insurance
  - Pedagogy training
  - Profile listing

## API Endpoints

### 1. List Subscription Plans
```
GET /api/subscriptions/
```
**Authentication**: None (Public)

**Response**:
```json
{
  "success": true,
  "plans": [
    {
      "id": 1,
      "name": "Basic",
      "monthly_price": "100.00",
      "annual_price": "1200.00",
      "three_month_price": 300.0,
      "six_month_price": 600.0,
      "twelve_month_price": 1200.0,
      "tuition_applications": 10,
      "benefits": [
        "10 tuition applications",
        "Pedagogy training",
        "Profile listing"
      ],
      "description": "Perfect for new tutors getting started"
    }
  ],
  "count": 3
}
```

### 2. Start Payment
```
POST /api/subscriptions/start-payment/
```
**Authentication**: Required (JWT Token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "sub_id": 1,
  "duration": 3
}
```

**Validation**:
- `sub_id`: Must be 1, 2, or 3
- `duration`: Must be 3, 6, or 12 (months)

**Response**:
```json
{
  "success": true,
  "payment_url": "https://smartgatewayuat.hdfcbank.com/pay/...",
  "order_id": "TS_12345678_1_20240115120000",
  "amount": 300.0,
  "subscription": "Basic",
  "duration_months": 3,
  "message": "Payment session created. Redirect user to payment_url"
}
```

**Frontend Flow**:
1. Call this endpoint with sub_id and duration
2. Receive payment_url in response
3. Redirect user to payment_url for HDFC payment gateway
4. User completes payment
5. HDFC redirects back to configured return URL
6. Check payment status using order_id

### 3. Check Payment Status
```
GET /api/subscriptions/payment-status/{order_id}/
```
**Authentication**: Required (JWT Token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (Pending)**:
```json
{
  "success": true,
  "order_id": "TS_12345678_1_20240115120000",
  "status": "PENDING",
  "amount": "300.00",
  "subscription": "Basic",
  "duration_months": 3,
  "message": "Payment is pending"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "order_id": "TS_12345678_1_20240115120000",
  "status": "CHARGED",
  "amount": "300.00",
  "subscription": "Basic",
  "duration_months": 3,
  "payment_date": "2024-01-15T12:30:00Z",
  "tracking_id": "HDFC123456",
  "bank_ref_no": "REF789",
  "message": "Payment successful"
}
```

**Payment Status Values**:
- `PENDING`: Payment initiated but not completed
- `CHARGED`: Payment successful
- `AUTHENTICATION_FAILED`: Payment failed
- `CANCELLED`: Payment cancelled by user
- `REFUNDED`: Payment refunded

### 4. Get User Subscriptions
```
GET /api/subscriptions/user-subscriptions/
```
**Authentication**: Required (JWT Token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "active_subscriptions": [
    {
      "id": "uuid-here",
      "subscription_name": "Basic",
      "subscription_details": {
        "id": 1,
        "name": "Basic",
        "monthly_price": "100.00",
        "benefits": ["10 tuition applications", "..."]
      },
      "duration_months": 3,
      "amount_paid": "300.00",
      "start_date": "2024-01-15T12:30:00Z",
      "end_date": "2024-04-15T12:30:00Z",
      "status": "ACTIVE",
      "applications_used": 3,
      "remaining_applications": 7,
      "is_currently_active": true,
      "days_remaining": 75,
      "payment_order_id": "TS_12345678_1_20240115120000"
    }
  ],
  "past_subscriptions": [],
  "total_count": 1
}
```

## Database Models

### Subscription
- **id**: IntegerField (1, 2, 3)
- **name**: CharField (Basic, Standard, Pro)
- **monthly_price**: DecimalField
- **annual_price**: DecimalField
- **tuition_applications**: IntegerField (-1 for unlimited)
- **Feature flags**: BooleanField (verified_badge, priority_listing, etc.)

### Payment
- **id**: UUIDField (Primary Key)
- **order_id**: CharField (Unique, indexed)
- **teacher**: ForeignKey(Teacher)
- **subscription**: ForeignKey(Subscription)
- **amount**: DecimalField
- **duration_months**: IntegerField
- **status**: CharField (PENDING, CHARGED, etc.)
- **HDFC fields**: tracking_id, bank_ref_no, etc.

### UserSubscription
- **id**: UUIDField (Primary Key)
- **teacher**: ForeignKey(Teacher)
- **subscription**: ForeignKey(Subscription)
- **payment**: OneToOneField(Payment)
- **start_date**: DateTimeField
- **end_date**: DateTimeField
- **status**: CharField (ACTIVE, EXPIRED, CANCELLED)
- **applications_used**: IntegerField

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py makemigrations subscriptions
python manage.py migrate
```

### 2. Populate Initial Subscription Plans
```bash
python manage.py populate_subscriptions
```

### 3. Environment Variables
Ensure these are set in `.env`:
```
HDFC_API_KEY=your_api_key
HDFC_PAYMENT_URL=https://smartgatewayuat.hdfcbank.com
HDFC_MERCHANT_ID=your_merchant_id
HDFC_CLIENT_ID=your_client_id
HDFC_RETURN_URL=https://api.tutorschool.com/api/subscriptions/payment-callback/
HDFC_CLIENT_RETURN_URL=https://tutorschool.com/payment/success
```

## Payment Flow

### Step-by-Step Process

1. **User selects plan and duration**
   - Frontend shows subscription plans
   - User picks plan (1/2/3) and duration (3/6/12)

2. **Initialize payment**
   - Frontend calls `POST /api/subscriptions/start-payment/`
   - Backend creates Payment record with status=PENDING
   - Backend calls HDFC API to create payment session
   - Backend returns payment_url

3. **User completes payment**
   - Frontend redirects to payment_url
   - User enters card/UPI details on HDFC page
   - HDFC processes payment

4. **Payment callback**
   - HDFC redirects to HDFC_RETURN_URL
   - Backend receives payment status
   - Backend updates Payment status

5. **Check payment status**
   - Frontend polls `GET /api/subscriptions/payment-status/{order_id}/`
   - Backend checks HDFC API for latest status
   - If CHARGED: Backend creates UserSubscription record
   - Backend deactivates previous subscriptions

6. **Subscription activation**
   - UserSubscription created with start_date and end_date
   - Teacher can now use subscription benefits

## HDFC Payment Gateway Integration

### Service Class: HDFCPaymentService

**Methods**:
- `generate_order_id()`: Creates unique order ID
- `create_payment_session()`: Initiates payment with HDFC
- `verify_payment_status()`: Checks payment status
- `calculate_subscription_end_date()`: Calculates subscription validity
- `parse_callback_response()`: Parses HDFC callback data

### Order ID Format
```
TS_{teacher_id[:8]}_{sub_id}_{timestamp}
Example: TS_12345678_1_20240115120000
```

### Payment Session Data
```python
{
    'merchant_id': settings.HDFC_MERCHANT_ID,
    'order_id': order_id,
    'amount': str(amount),
    'currency': 'INR',
    'redirect_url': settings.HDFC_RETURN_URL,
    'billing_name': teacher_name,
    'billing_email': teacher_email,
    'billing_tel': teacher_phone,
    'merchant_param1': teacher_id,  # Custom data
    'merchant_param2': subscription_id,
    'merchant_param3': duration_months,
}
```

## Testing

### Test Payment Flow
```bash
# 1. Get all plans
curl http://localhost:8000/api/subscriptions/

# 2. Start payment (with JWT token)
curl -X POST http://localhost:8000/api/subscriptions/start-payment/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sub_id": 1, "duration": 3}'

# 3. Check payment status
curl http://localhost:8000/api/subscriptions/payment-status/ORDER_ID/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Get user subscriptions
curl http://localhost:8000/api/subscriptions/user-subscriptions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Business Logic

### Subscription Duration Calculation
- **3 months**: +90 days from start_date
- **6 months**: +180 days from start_date
- **12 months**: +365 days from start_date

### Application Limits
- Basic: 10 applications
- Standard: 25 applications
- Pro: Unlimited (-1 in database, checked via `can_apply()` method)

### Multiple Subscriptions
- Only one ACTIVE subscription per teacher at a time
- When new subscription is activated, previous ones are marked EXPIRED
- Past subscriptions remain in history

### Status Transitions
```
PENDING -> CHARGED (success) -> ACTIVE subscription created
PENDING -> AUTHENTICATION_FAILED (failed)
PENDING -> CANCELLED (user cancelled)
ACTIVE -> EXPIRED (time-based or new subscription)
ACTIVE -> CANCELLED (manual cancellation)
```

## Admin Interface

All models registered in Django admin:
- `/admin/subscriptions/subscription/` - Manage plans
- `/admin/subscriptions/payment/` - View payment transactions
- `/admin/subscriptions/usersubscription/` - View user subscriptions

## Error Handling

### Common Errors
1. **Invalid subscription ID**: 400 - "Invalid subscription ID. Must be 1, 2, or 3."
2. **Invalid duration**: 400 - "Invalid duration. Must be 3, 6, or 12 months."
3. **Payment not found**: 404 - "Payment not found"
4. **Gateway timeout**: 500 - "Payment gateway timeout. Please try again."
5. **Authentication failed**: 401 - "Invalid or missing token"

### Logging
All operations are logged using Python's logging module:
- Payment session creation
- Payment status checks
- Subscription activation
- Errors and exceptions

## Security

### Authentication
- All payment-related endpoints require JWT authentication
- Only list subscriptions endpoint is public
- Teacher can only access their own payments/subscriptions

### Payment Security
- HDFC API key in environment variables
- SSL/HTTPS for all payment communications
- Order IDs are unique and timestamped
- No sensitive payment data stored in database

## Future Enhancements

1. **Payment Callback Endpoint**: Create endpoint to handle HDFC callbacks directly
2. **Webhook Support**: Implement webhooks for payment status updates
3. **Refund API**: Add functionality for refund processing
4. **Subscription Renewal**: Auto-renewal before expiry
5. **Promo Codes**: Discount code support
6. **Free Trials**: Initial trial period for new tutors
7. **Usage Analytics**: Track feature usage per subscription
8. **Email Notifications**: Payment success/failure emails
9. **Invoice Generation**: PDF invoices for payments

## Support

For issues or questions:
- Check logs in Django admin
- Review HDFC gateway documentation
- Contact HDFC support for gateway issues
- Check environment variables configuration
