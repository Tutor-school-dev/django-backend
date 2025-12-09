import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from tutor.models import Teacher, TeacherPedagogyProfile


class Command(BaseCommand):
    help = 'Populate random pedagogy profiles for existing tutors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            help='Number of tutors to create profiles for (default: all existing tutors)',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing pedagogy profiles',
        )

    def handle(self, *args, **options):
        """Create random pedagogy profiles for existing tutors"""
        
        self.stdout.write(self.style.SUCCESS('Starting pedagogy profile population...'))
        
        # Get tutors to create profiles for
        tutors = Teacher.objects.all()
        
        if options['count']:
            tutors = tutors[:options['count']]
            
        total_tutors = tutors.count()
        self.stdout.write(f'Found {total_tutors} tutors to process')
        
        if total_tutors == 0:
            self.stdout.write(self.style.WARNING('No tutors found!'))
            return
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Trait choices for random selection
        trait_choices = ['HIGH', 'LOW']
        
        for tutor in tutors:
            try:
                # Check if profile already exists
                existing_profile = TeacherPedagogyProfile.objects.filter(teacher=tutor).first()
                
                if existing_profile and not options['overwrite']:
                    self.stdout.write(f'  Skipping {tutor.name} - profile already exists')
                    skipped_count += 1
                    continue
                
                # Generate random pedagogy traits
                random_traits = {
                    'tcs': random.choice(trait_choices),      # Confidence Support
                    'tspi': random.choice(trait_choices),     # Speed Regulation 
                    'twmls': random.choice(trait_choices),    # Working Memory Support
                    'tpo': random.choice(trait_choices),      # Precision Focus
                    'tecp': random.choice(trait_choices),     # Error Regulation
                    'tet': random.choice(trait_choices),      # Exploration Control
                    'tics': random.choice(trait_choices),     # Impulse Regulation
                    'trd': random.choice(trait_choices),      # Reasoning Depth
                    'completed_at': timezone.now(),
                }
                
                if existing_profile:
                    # Update existing profile
                    for trait, value in random_traits.items():
                        setattr(existing_profile, trait, value)
                    existing_profile.save()
                    
                    self.stdout.write(f'  Updated profile for {tutor.name}')
                    updated_count += 1
                else:
                    # Create new profile
                    TeacherPedagogyProfile.objects.create(
                        teacher=tutor,
                        **random_traits
                    )
                    
                    self.stdout.write(f'  Created profile for {tutor.name}')
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing {tutor.name}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nPedagogy Profile Population Complete!'))
        self.stdout.write(f'  Created: {created_count} profiles')
        self.stdout.write(f'  Updated: {updated_count} profiles')
        self.stdout.write(f'  Skipped: {skipped_count} profiles')
        self.stdout.write(f'  Total Processed: {created_count + updated_count + skipped_count}')
        
        # Display some example profiles
        self.display_sample_profiles()
    
    def display_sample_profiles(self):
        """Display a few sample pedagogy profiles"""
        self.stdout.write(self.style.SUCCESS('\nSample Pedagogy Profiles:'))
        
        sample_profiles = TeacherPedagogyProfile.objects.select_related('teacher')[:3]
        
        for profile in sample_profiles:
            fingerprint = profile.get_pedagogy_fingerprint()
            traits_str = ', '.join([f'{trait}:{value}' for trait, value in fingerprint.items()])
            
            self.stdout.write(f'  {profile.teacher.name}: {traits_str}')