"""
Management command to populate sample tutor and learner data
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from tutor.models import Teacher
from learner.models import Learner
from config.constants import CLASS_LEVEL_CHOICES
import random
from decimal import Decimal
from datetime import timedelta

# Location data
LOCATION_DATA = {
    "karnataka": {
        "bengaluru": [
            "koramangala", "indiranagar", "whitefield", "jayanagar",
            "btm-layout", "electronic-city", "marathahalli", "hsr-layout"
        ]
    },
    "delhi": {
        "new-delhi": [
            "dwarka", "rohini", "lajpat-nagar", "saket",
            "vasant-kunj", "pitampura", "janakpuri", "greater-kailash"
        ]
    },
    "maharashtra": {
        "mumbai": [
            "andheri", "bandra", "powai", "thane",
            "borivali", "malad", "kandivali", "juhu"
        ],
        "pune": [
            "baner", "wakad", "kothrud", "aundh",
            "hadapsar", "viman-nagar", "shivaji-nagar", "hinjewadi"
        ]
    },
    "telangana": {
        "hyderabad": [
            "gachibowli", "madhapur", "kukatpally", "secunderabad",
            "begumpet", "kondapur", "miyapur", "jubilee-hills"
        ]
    },
    "tamil-nadu": {
        "chennai": [
            "anna-nagar", "t-nagar", "velachery", "adyar",
            "tambaram", "chrompet", "omr", "porur"
        ]
    },
    "rajasthan": {
        "jaipur": [
            "malviya-nagar", "c-scheme", "vaishali-nagar", "mansarovar",
            "tonk-road", "ajmer-road", "jagatpura", "sodala"
        ]
    },
    "uttar-pradesh": {
        "lucknow": [
            "gomti-nagar", "indira-nagar", "aliganj", "mahanagar",
            "rajajipuram", "hazratganj", "chowk", "alambagh"
        ]
    },
    "madhya-pradesh": {
        "indore": [
            "vijay-nagar", "rajendra-nagar", "sapna-sangeeta", "palasia",
            "bhawarkuan", "new-palasia", "geeta-bhawan", "rau"
        ]
    },
    "west-bengal": {
        "kolkata": [
            "salt-lake", "park-street", "ballygunge", "howrah",
            "jadavpur", "new-town", "gariahat", "behala"
        ]
    }
}

# Sample data
TUTOR_FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohit", "Kavya",
    "Arun", "Divya", "Karthik", "Meera", "Suresh", "Lakshmi", "Ramesh", "Pooja",
    "Manoj", "Swati", "Nikhil", "Anjali", "Sanjay", "Nisha", "Arjun", "Ritu"
]

TUTOR_LAST_NAMES = [
    "Kumar", "Sharma", "Patel", "Singh", "Reddy", "Nair", "Gupta", "Iyer",
    "Verma", "Rao", "Desai", "Joshi", "Menon", "Agarwal", "Kapoor", "Malhotra"
]

LEARNER_FIRST_NAMES = [
    "Aarav", "Aditi", "Arnav", "Ananya", "Aditya", "Isha", "Rohan", "Diya",
    "Aryan", "Sara", "Vihaan", "Myra", "Ayaan", "Kiara", "Shaurya", "Aanya",
    "Reyansh", "Navya", "Krishna", "Saanvi", "Rudra", "Pari", "Kabir", "Amaira"
]

PARENT_FIRST_NAMES = [
    "Rahul", "Sunita", "Ajay", "Kavita", "Sandeep", "Anjali", "Prakash", "Rekha",
    "Sunil", "Geeta", "Ashok", "Preeti", "Deepak", "Neeta", "Vinod", "Seema"
]

SUBJECTS = [
    ["Mathematics", "Physics", "Chemistry"],
    ["English", "Hindi", "Social Studies"],
    ["Biology", "Chemistry", "Physics"],
    ["Mathematics", "Computer Science", "Physics"],
    ["Accountancy", "Business Studies", "Economics"],
    ["History", "Geography", "Political Science"],
    ["Mathematics", "Statistics", "Economics"],
    ["Physics", "Mathematics", "Computer Science"]
]

BOARDS = ["CBSE", "ICSE", "State Board", "IB", "IGCSE"]

UNIVERSITIES = [
    "IIT Delhi", "IIT Bombay", "IIT Madras", "Delhi University", "Mumbai University",
    "Bangalore University", "Anna University", "Pune University", "Hyderabad University",
    "Jadavpur University", "BHU Varanasi", "AMU Aligarh"
]

DEGREES = [
    "B.Tech in Computer Science", "B.Tech in Electronics", "B.Sc in Mathematics",
    "B.Sc in Physics", "M.Sc in Chemistry", "M.Tech in AI/ML", "MBA",
    "M.A in English", "B.Com", "M.Com", "BBA", "B.A in Economics"
]

CURRENT_STATUS = [
    "Working Professional", "College Student", "PhD Scholar", "Freelancer",
    "Full-time Tutor", "Part-time Tutor", "Recent Graduate"
]

REFERRALS = [
    "Google Search", "Friend Referral", "Social Media", "Advertisement",
    "Previous Student", "Website", "Word of Mouth"
]

# Center point coordinates (Jaipur area)
CENTER_LAT = 26.9802570
CENTER_LNG = 75.7697920


class Command(BaseCommand):
    help = 'Populate sample tutor and learner data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tutors',
            type=int,
            default=20,
            help='Number of tutors to create (default: 20)'
        )
        parser.add_argument(
            '--learners',
            type=int,
            default=20,
            help='Number of learners to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )
        parser.add_argument(
            '--same-city',
            action='store_true',
            help='Create tutors in the same city teaching same subjects'
        )

    def handle(self, *args, **options):
        num_tutors = options['tutors']
        num_learners = options['learners']
        clear_data = options['clear']
        same_city = options['same_city']

        if clear_data:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Teacher.objects.all().delete()
            Learner.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))

        # Create tutors
        self.stdout.write(self.style.SUCCESS(f'Creating {num_tutors} tutors...'))
        if same_city:
            tutors_created = self.create_tutors_same_city(num_tutors)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {tutors_created} tutors in same city with same subjects'))
        else:
            tutors_created = self.create_tutors(num_tutors)
            self.stdout.write(self.style.SUCCESS(f'✓ Created {tutors_created} tutors'))

        # Create learners
        self.stdout.write(self.style.SUCCESS(f'Creating {num_learners} learners...'))
        learners_created = self.create_learners(num_learners)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {learners_created} learners'))

        self.stdout.write(self.style.SUCCESS(
            f'\nTotal created: {tutors_created} tutors, {learners_created} learners'
        ))

    def get_random_location(self):
        """Get random state, city, and area"""
        state = random.choice(list(LOCATION_DATA.keys()))
        city = random.choice(list(LOCATION_DATA[state].keys()))
        area = random.choice(LOCATION_DATA[state][city])
        return state, city, area

    def get_coordinates_with_offset(self):
        """Generate coordinates with random offset from center point"""
        # Random offset within ~100km radius
        lat_offset = random.uniform(-0.9, 0.9)  # ~100km
        lng_offset = random.uniform(-0.9, 0.9)  # ~100km
        
        lat = CENTER_LAT + lat_offset
        lng = CENTER_LNG + lng_offset
        
        return lat, lng

    def get_random_pincode(self):
        """Generate random Indian pincode"""
        return f"{random.randint(100000, 899999)}"

    def create_tutors(self, count):
        """Create sample tutor records"""
        created = 0
        
        # Get all class level choices
        class_levels = [choice[0] for choice in CLASS_LEVEL_CHOICES]
        
        for i in range(count):
            try:
                first_name = random.choice(TUTOR_FIRST_NAMES)
                last_name = random.choice(TUTOR_LAST_NAMES)
                name = f"{first_name} {last_name}"
                
                # Generate unique email and phone
                email = f"{first_name.lower()}.{last_name.lower()}{i}@tutorschool.in"
                phone = f"+91{random.randint(7000000000, 9999999999)}"
                
                # Get location
                state, city, area = self.get_random_location()
                lat, lng = self.get_coordinates_with_offset()
                pincode = self.get_random_pincode()
                
                # Create point for PostGIS
                location = Point(lng, lat, srid=4326)
                
                # Random subjects (as JSON string)
                subjects = random.choice(SUBJECTS)
                subjects_str = str(subjects)
                
                # Random class level
                class_level = random.choice(class_levels)
                
                # Create tutor
                teacher = Teacher.objects.create(
                    name=name,
                    email=email,
                    primary_contact=phone,
                    secondary_contact=f"+91{random.randint(7000000000, 9999999999)}" if random.random() > 0.5 else None,
                    password='',  # Will be set through OTP/Google auth
                    
                    # Location
                    state=state.replace('-', ' ').title(),
                    city=city.replace('-', ' ').title(),
                    area=area.replace('-', ' ').title(),
                    pincode=pincode,
                    location=location,
                    latitude=str(lat),
                    longitude=str(lng),
                    
                    # Profile
                    introduction=f"Experienced tutor with {random.randint(2, 15)} years of teaching experience.",
                    teaching_desc=f"Specializing in {', '.join(subjects[:2])}. Passionate about making learning enjoyable.",
                    lesson_price=Decimal(random.choice([300, 400, 500, 600, 700, 800, 1000, 1200, 1500])),
                    teaching_mode=random.choice(['ONLINE', 'OFFLINE', 'BOTH']),
                    
                    # Academic
                    class_level=class_level,
                    current_status=random.choice(CURRENT_STATUS),
                    degree=random.choice(DEGREES),
                    university=random.choice(UNIVERSITIES),
                    subjects=subjects_str,
                    referral=random.choice(REFERRALS),
                    
                    # Onboarding
                    basic_done=True,
                    location_done=True,
                    later_onboarding_done=random.choice([True, False]),
                    
                    # Subscription (some with active subscription)
                    subscription_validity=timezone.now() + timedelta(days=random.randint(0, 90)) if random.random() > 0.3 else None
                )
                
                created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating tutor {i}: {str(e)}'))
                continue
        
        return created

    def create_tutors_same_city(self, count):
        """Create sample tutor records in the same city teaching same subjects"""
        created = 0
        
        # Get all class level choices
        class_levels = [choice[0] for choice in CLASS_LEVEL_CHOICES]
        
        # Pick one city/state/area combination for all tutors
        state = random.choice(list(LOCATION_DATA.keys()))
        city = random.choice(list(LOCATION_DATA[state].keys()))
        areas = LOCATION_DATA[state][city]
        
        # Pick one set of subjects for all tutors
        common_subjects = random.choice(SUBJECTS)
        subjects_str = str(common_subjects)
        
        # Pick one class level that all tutors will teach
        common_class_level = random.choice(class_levels)
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCreating tutors in: {state.replace("-", " ").title()}, '
            f'{city.replace("-", " ").title()}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Teaching subjects: {", ".join(common_subjects)}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Class level: {common_class_level}\n'
        ))
        
        for i in range(count):
            try:
                first_name = random.choice(TUTOR_FIRST_NAMES)
                last_name = random.choice(TUTOR_LAST_NAMES)
                name = f"{first_name} {last_name}"
                
                # Generate unique email and phone
                email = f"{first_name.lower()}.{last_name.lower()}{i}@tutorschool.in"
                phone = f"+91{random.randint(7000000000, 9999999999)}"
                
                # Use same city but different areas
                area = random.choice(areas)
                lat, lng = self.get_coordinates_with_offset()
                pincode = self.get_random_pincode()
                
                # Create point for PostGIS
                location = Point(lng, lat, srid=4326)
                
                # Create tutor with common subjects and class level
                teacher = Teacher.objects.create(
                    name=name,
                    email=email,
                    primary_contact=phone,
                    secondary_contact=f"+91{random.randint(7000000000, 9999999999)}" if random.random() > 0.5 else None,
                    password='',  # Will be set through OTP/Google auth
                    
                    # Location - same city for all
                    state=state.replace('-', ' ').title(),
                    city=city.replace('-', ' ').title(),
                    area=area.replace('-', ' ').title(),
                    pincode=pincode,
                    location=location,
                    latitude=str(lat),
                    longitude=str(lng),
                    
                    # Profile - vary these fields
                    introduction=f"Experienced tutor with {random.randint(2, 15)} years of teaching experience.",
                    teaching_desc=f"Specializing in {', '.join(common_subjects[:2])}. Passionate about making learning enjoyable.",
                    lesson_price=Decimal(random.choice([300, 400, 500, 600, 700, 800, 1000, 1200, 1500])),
                    teaching_mode=random.choice(['ONLINE', 'OFFLINE', 'BOTH']),
                    
                    # Academic - same subjects and class level for all
                    class_level=common_class_level,
                    current_status=random.choice(CURRENT_STATUS),
                    degree=random.choice(DEGREES),
                    university=random.choice(UNIVERSITIES),
                    subjects=subjects_str,
                    referral=random.choice(REFERRALS),
                    
                    # Onboarding
                    basic_done=True,
                    location_done=True,
                    later_onboarding_done=random.choice([True, False]),
                    
                    # Subscription (some with active subscription)
                    subscription_validity=timezone.now() + timedelta(days=random.randint(0, 90)) if random.random() > 0.3 else None
                )
                
                created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating tutor {i}: {str(e)}'))
                continue
        
        return created

    def create_learners(self, count):
        """Create sample learner records"""
        created = 0
        
        # Get all class level choices
        class_levels = [choice[0] for choice in CLASS_LEVEL_CHOICES]
        # Filter for school and senior secondary levels for learners
        school_levels = [cl for cl in class_levels if 'Primary' in cl or 'Secondary' in cl or 'UG' in cl]
        
        for i in range(count):
            try:
                student_name = random.choice(LEARNER_FIRST_NAMES)
                parent_first = random.choice(PARENT_FIRST_NAMES)
                parent_last = random.choice(TUTOR_LAST_NAMES)
                
                # Generate unique email and phone
                email = f"{student_name.lower()}.learner{i}@tutorschool.in"
                parent_email = f"{parent_first.lower()}.{parent_last.lower()}{i}@gmail.com"
                phone = f"+91{random.randint(7000000000, 9999999999)}"
                
                # Get location
                state, city, area = self.get_random_location()
                lat, lng = self.get_coordinates_with_offset()
                pincode = self.get_random_pincode()
                
                # Create point for PostGIS
                location = Point(lng, lat, srid=4326)
                
                # Random subjects (as JSON string)
                subjects = random.choice(SUBJECTS)
                subjects_str = str(subjects)
                
                # Random educationLevel
                educationLevel = random.choice(school_levels)
                
                # Create learner
                learner = Learner.objects.create(
                    name=student_name,
                    email=email,
                    primary_contact=phone,
                    secondary_contact=f"+91{random.randint(7000000000, 9999999999)}" if random.random() > 0.5 else None,
                    password='',  # Will be set through OTP/Google auth
                    
                    # Location
                    state=state.replace('-', ' ').title(),
                    area=area.replace('-', ' ').title(),
                    pincode=pincode,
                    location=location,
                    latitude=str(lat),
                    longitude=str(lng),
                    
                    # Learner specific
                    educationLevel=educationLevel,
                    board=random.choice(BOARDS),
                    guardian_name=f"{parent_first} {parent_last}",
                    guardian_email=parent_email,
                    subjects=subjects_str,
                    budget=Decimal(random.choice([500, 600, 800, 1000, 1200, 1500, 2000])),
                    preferred_mode=random.choice(['Online', 'Offline', 'Both'])
                )
                
                created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating learner {i}: {str(e)}'))
                continue
        
        return created
