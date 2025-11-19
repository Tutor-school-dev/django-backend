from django.core.management.base import BaseCommand
from subscriptions.models import Subscription
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate initial subscription plans'
    
    def handle(self, *args, **options):
        """Create initial subscription plans"""
        
        plans = [
            {
                'id': 1,
                'name': 'Basic',
                'monthly_price': Decimal('100.00'),
                'annual_price': Decimal('1200.00'),  # 100 * 12
                'tuition_applications': 10,
                'verified_badge': False,
                'priority_listing': False,
                'mock_interviews': False,
                'fast_track_support': False,
                'workshops': False,
                'health_insurance': False,
                'pedagogy_training': True,
                'profile_listing': True,
                'description': 'Perfect for new tutors getting started',
            },
            {
                'id': 2,
                'name': 'Standard',
                'monthly_price': Decimal('599.00'),
                'annual_price': Decimal('7188.00'),  # 599 * 12
                'tuition_applications': 25,
                'verified_badge': True,
                'priority_listing': True,
                'mock_interviews': True,
                'fast_track_support': True,
                'workshops': True,
                'health_insurance': False,
                'pedagogy_training': True,
                'profile_listing': True,
                'description': 'Best for growing your tutoring business',
            },
            {
                'id': 3,
                'name': 'Pro',
                'monthly_price': Decimal('999.00'),
                'annual_price': Decimal('11988.00'),  # 999 * 12
                'tuition_applications': -1,  # Unlimited
                'verified_badge': True,
                'priority_listing': True,
                'mock_interviews': True,
                'fast_track_support': True,
                'workshops': True,
                'health_insurance': True,
                'pedagogy_training': True,
                'profile_listing': True,
                'description': 'Complete package for professional tutors',
            }
        ]
        
        for plan_data in plans:
            subscription, created = Subscription.objects.update_or_create(
                id=plan_data['id'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created subscription plan: {subscription.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated subscription plan: {subscription.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n✓ Successfully populated subscription plans'))
