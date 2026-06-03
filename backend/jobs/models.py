from django.db import models
from django.utils.text import slugify
from companies.models import Company
from django.contrib.auth import get_user_model
import os
from django.core.exceptions import ValidationError

User = get_user_model()

class Job(models.Model):
    """
    Represents a Job listing posted by a Company.
    Linked to both Company (Tenant) and the User (Recruiter/Employer) who created it.
    """
    JOB_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
    ]

    JOB_LOCATION_CHOICES = [
        ('REMOTE', 'Remote'),
        ('ONSITE', 'Onsite'),
        ('HYBRID', 'Hybrid'),
    ]

    # Core Relationships (Multi-tenant)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posted_jobs')

    # Job Details
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    requirements = models.TextField(help_text="List of requirements, experience, skills needed.")    
    # Metadata
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='FULL_TIME')
    location_type = models.CharField(max_length=20, choices=JOB_LOCATION_CHOICES, default='ONSITE')
    location = models.CharField(max_length=255, help_text="City, Country or Office address")
    
    # Salary Range
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')

    # Status & Timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def save(self, *args, **kwargs):
        """Auto-generate slug based on title and company name before saving."""
        if not self.slug:
            base_slug = slugify(self.title)
            company_slug = slugify(self.company.name)
            self.slug = f"{base_slug}-{company_slug}"
        super().save(*args, **kwargs)

def validate_pdf_file(value):
    """
    Validator to ensure the uploaded file is strictly a PDF and under 2MB.
    """
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    
    # Check file extension
    if not ext.lower() in valid_extensions:
        raise ValidationError("Unsupported file extension. Only PDF files are allowed.")
        
    # Check file size (2MB = 2 * 1024 * 1024 bytes)
    limit = 2 * 1024 * 1024
    if value.size > limit:
        raise ValidationError("File size too large. Resume must be under 2MB.")        

class Application(models.Model):
    """
    Represents a Job Application submitted by a Candidate for a specific Job.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWING', 'Reviewing'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interview'),
        ('REJECTED', 'Rejected'),
    ]

    # Relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')

    # Application Data
    cover_letter = models.TextField(blank=True, null=True)

    # AI Screening Analytics Fields
    ai_score = models.IntegerField(null=True, blank=True, help_text="Matching score out of 100 calculated by Gemini LLM.")
    ai_judgment = models.TextField(blank=True, null=True, help_text="2-line professional evaluation summary from Gemini.")
    
    # Added null=True, blank=True to avoid database migration blocks
    resume = models.FileField(
        upload_to='resumes/', 
        validators=[validate_pdf_file],
        null=True,
        blank=True,
        help_text="Upload your resume in PDF format (Max 2MB)."
    )    
    
    # Status & Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Automated PDF Offer Letter Field
    offer_letter = models.FileField(upload_to='offer_letters/', blank=True, null=True, help_text="Automatically generated PDF offer letter for selected candidates.")

    class Meta:
        ordering = ['-created_at']
        # CRITICAL SECURITY: A candidate can only apply ONCE to a specific job!
        unique_together = ('job', 'candidate')

    def __str__(self):
        return f"{self.candidate.email} applied for {self.job.title}"
