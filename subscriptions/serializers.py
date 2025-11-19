from rest_framework import serializers
from .models import Subscription, Payment, UserSubscription


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    
    benefits = serializers.SerializerMethodField()
    three_month_price = serializers.SerializerMethodField()
    six_month_price = serializers.SerializerMethodField()
    twelve_month_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'name',
            'monthly_price',
            'annual_price',
            'three_month_price',
            'six_month_price',
            'twelve_month_price',
            'tuition_applications',
            'verified_badge',
            'priority_listing',
            'mock_interviews',
            'fast_track_support',
            'workshops',
            'health_insurance',
            'pedagogy_training',
            'profile_listing',
            'benefits',
            'description',
        ]
    
    def get_benefits(self, obj):
        """Get formatted list of benefits"""
        return obj.get_benefits_list()
    
    def get_three_month_price(self, obj):
        """Calculate 3-month price"""
        return obj.calculate_price(3)
    
    def get_six_month_price(self, obj):
        """Calculate 6-month price"""
        return obj.calculate_price(6)
    
    def get_twelve_month_price(self, obj):
        """Calculate 12-month price (annual)"""
        return obj.calculate_price(12)


class StartPaymentSerializer(serializers.Serializer):
    """Serializer for starting a payment"""
    
    sub_id = serializers.IntegerField(required=True)
    duration = serializers.IntegerField(required=True)
    
    def validate_sub_id(self, value):
        """Validate subscription ID"""
        if value not in [1, 2, 3]:
            raise serializers.ValidationError("Invalid subscription ID. Must be 1, 2, or 3.")
        
        # Check if subscription exists and is active
        try:
            subscription = Subscription.objects.get(id=value, is_active=True)
        except Subscription.DoesNotExist:
            raise serializers.ValidationError(f"Subscription plan with ID {value} not found or inactive.")
        
        return value
    
    def validate_duration(self, value):
        """Validate duration"""
        if value not in [3, 6, 12]:
            raise serializers.ValidationError("Invalid duration. Must be 3, 6, or 12 months.")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment details"""
    
    subscription_name = serializers.CharField(source='subscription.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_email = serializers.EmailField(source='teacher.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'subscription_name',
            'teacher_name',
            'teacher_email',
            'amount',
            'duration_months',
            'status',
            'hdfc_transaction_id',
            'hdfc_tracking_id',
            'hdfc_bank_ref_no',
            'payment_method',
            'payment_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'order_id', 'status', 'created_at', 'updated_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    
    subscription_name = serializers.CharField(source='subscription.name', read_only=True)
    subscription_details = SubscriptionSerializer(source='subscription', read_only=True)
    payment_order_id = serializers.CharField(source='payment.order_id', read_only=True)
    is_currently_active = serializers.SerializerMethodField()
    remaining_applications = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'subscription_name',
            'subscription_details',
            'duration_months',
            'amount_paid',
            'start_date',
            'end_date',
            'status',
            'applications_used',
            'remaining_applications',
            'is_currently_active',
            'days_remaining',
            'payment_order_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_currently_active(self, obj):
        """Check if subscription is currently active"""
        return obj.is_active()
    
    def get_remaining_applications(self, obj):
        """Calculate remaining applications"""
        return max(0, obj.subscription.tuition_applications - obj.applications_used)
    
    def get_days_remaining(self, obj):
        """Calculate days remaining in subscription"""
        from django.utils import timezone
        if obj.status != UserSubscription.STATUS_ACTIVE:
            return 0
        delta = obj.end_date - timezone.now()
        return max(0, delta.days)


class StartPaymentResponseSerializer(serializers.Serializer):
    """Serializer for payment initiation response"""
    
    success = serializers.BooleanField()
    payment_url = serializers.URLField(required=False)
    order_id = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response"""
    
    order_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.CharField(required=False)
    tracking_id = serializers.CharField(required=False)
    bank_ref_no = serializers.CharField(required=False)
    payment_mode = serializers.CharField(required=False)
    trans_date = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
