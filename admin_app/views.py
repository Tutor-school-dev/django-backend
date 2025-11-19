from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from admin_app.models import JobApplication, JobListing
from admin_app.serializers import JobListingSerializer
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from auth_app.authentication import JWTAuthentication

# Create your views here.
class JobListingsView(APIView):
    def get(self, request):
        # Get filter parameters from query params
        mode_of_teaching = request.query_params.get('mode_of_teaching', None)  # None means all modes
        subjects = request.query_params.getlist('subjects', [])  # Empty list means all subjects
        radius_km = float(request.query_params.get('radius', 50))  # Default 50 km
        learner_latitude = request.query_params.get('latitude', None)
        learner_longitude = request.query_params.get('longitude', None)
        
        # Start with all job listings
        job_listings = JobListing.objects.all()
        
        # Filter by mode of teaching if provided
        if mode_of_teaching:
            job_listings = job_listings.filter(mode_of_teaching=mode_of_teaching)
        
        # Filter by subjects if provided
        if subjects:
            job_listings = job_listings.filter(subjects__overlap=subjects)
        
        # Filter by location radius if coordinates provided
        if learner_latitude and learner_longitude:
            
            learner_point = Point(float(learner_longitude), float(learner_latitude), srid=4326)
            job_listings = job_listings.filter(
            location__distance_lte=(learner_point, D(km=radius_km))
            )
        
        serializer = JobListingSerializer(job_listings, many=True)
        return Response(serializer.data)
    

class JobApplicationView(APIView):
    authentication_classes = []  # Add appropriate authentication classes
    permission_classes = []      # Add appropriate permission classes   

    def post(self, request):

        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=401
            )
        user, token = auth_result
        if not hasattr(user, 'user_type') or user.user_type != 'tutor':
            return Response(
                {'error': 'This endpoint is only accessible to tutors'},
                status=403
            )
        
        # Handle job application submission
        job_listing_id = request.data.get('job_listing_id')
        tutor_id = user.id
        
        # Create a new JobApplication
        job_listing = JobListing.objects.get(id=job_listing_id)
        job_application = JobApplication.objects.create(
            job_listing=job_listing,
            tutor_id=tutor_id
        )
        
        return Response({'message': 'Job application submitted successfully', 'application_id': job_application.id})