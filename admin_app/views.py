from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from admin_app.models import JobListing
from admin_app.serializers import JobListingSerializer

# Create your views here.
class JobListingsView(APIView):
    def get(self, request):
        job_listings = JobListing.objects.all()
        serializer = JobListingSerializer(job_listings, many=True)
        return Response(serializer.data)