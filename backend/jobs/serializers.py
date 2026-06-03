from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Job, Application

User = get_user_model()

class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for the Job model.
    Handles general job listing data including company information.
    Dynamically generates salary_range if min and max salaries are provided.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)
    salary_range = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'slug', 'description', 'requirements', 
            'location', 'job_type', 'location_type', 'salary_min', 'salary_max', 
            'currency', 'salary_range', 'company_name', 'company_logo', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'is_active', 'created_at', 'salary_range']

    def get_salary_range(self, obj):
        """Returns a formatted salary range string (e.g., '$50000 - $80000 USD')."""
        if obj.salary_min and obj.salary_max:
            return f"{obj.currency} {obj.salary_min} - {obj.salary_max}"
        elif obj.salary_min:
            return f"From {obj.currency} {obj.salary_min}"
        elif obj.salary_max:
            return f"Up to {obj.currency} {obj.salary_max}"
        return "Negotiable"


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer to handle job applications mapping and validation data format.
    Includes automated AI vetting metrics and background generated PDF offer letter links.
    """
    candidate_email = serializers.EmailField(source='candidate.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'candidate_email', 
            'cover_letter', 'resume', 'status', 
            'ai_score', 'ai_judgment', 'offer_letter', # Added enterprise AI & PDF tracking fields
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'ai_score', 'ai_judgment', 'offer_letter', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication credentials were not provided.")

        user = request.user

        # Validation 1: Restrict applications to Candidates only
        if user.role != 'CANDIDATE':
            raise serializers.ValidationError("Only users with the CANDIDATE role can apply for jobs.")

        # Validation 2: Prevent duplicate applications
        job = attrs.get('job')
        if Application.objects.filter(job=job, candidate=user).exists():
            raise serializers.ValidationError("You have already applied for this job.")

        return attrs


class EmployerApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.get_full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'candidate_name', 'candidate_email',
            'cover_letter', 'resume', 'status',
            'ai_score', 'ai_judgment',
            'created_at'
        ]
        read_only_fields = [
            'id', 'job', 'job_title', 'candidate_name', 'candidate_email',
            'cover_letter', 'resume', 'ai_score', 'ai_judgment', 'created_at'
        ]