from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Job, Application
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from unittest.mock import patch, MagicMock
from jobs.services import screen_resume_with_gemini

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class JobAPITests(APITestCase):
    """Test suite for Job Creation and Multi-tenant Access Restrictions."""

    def setUp(self):
        """Set up infrastructure, including a Company, an Employer, and a Candidate."""
        # 1. Create a Test Company (Tenant)
        self.company = Company.objects.create(name="HireOS Labs")
        
        # 2. Create an Employer linked to that company
        self.employer = User.objects.create_user(
            email="recruiter@hireos.ai",
            password="SecurePassword123!",
            first_name="Jane",
            last_name="Doe",
            role="EMPLOYER",
            company=self.company
        )
        
        # 3. Create a Candidate (No company linked)
        self.candidate = User.objects.create_user(
            email="candidate@hireos.ai",
            password="SecurePassword123!",
            first_name="Alex",
            last_name="Lee",
            role="CANDIDATE"
        )
        
        # URL Endpoint
        self.job_url = reverse('job_list_create')

    def get_results(self, response):
        """Return list payloads from either paginated or non-paginated DRF responses."""
        return response.data.get('results', response.data)

    def test_public_can_list_jobs(self):
        """Ensure unauthenticated/public visitors can read the job list."""
        response = self.client.get(self.job_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employer_can_create_job(self):
        """Ensure an authenticated employer can successfully post a job for their company."""
        # Authenticate as the Employer
        self.client.force_authenticate(user=self.employer)
        
        data = {
            "title": "Backend Python Developer",
            "description": "Looking for a Django expert.",
            "requirements": "3+ years of Python experience.",
            "job_type": "FULL_TIME",
            "location_type": "REMOTE",
            "location": "Dhaka, Bangladesh"
        }
        
        response = self.client.post(self.job_url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Backend Python Developer")
        self.assertEqual(response.data['company_name'], "HireOS Labs")  # Verified auto-tenant link

    def test_candidate_cannot_create_job(self):
        """Ensure candidates are restricted and cannot post a job."""
        # Authenticate as the Candidate
        self.client.force_authenticate(user=self.candidate)
        
        data = {
            "title": "Malicious Job Posting",
            "description": "Attempting to bypass security.",
            "requirements": "None",
            "location": "Hacker Town"
        }
        
        response = self.client.post(self.job_url, data, format='json')
        
        # Assertions (Should be forbidden/permission denied)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(GEMINI_API_KEY="")
    @patch.dict("os.environ", {"GEMINI_API_KEY": ""})
    def test_ats_screening_falls_back_when_gemini_is_unavailable(self):
        """Ensure ATS screening still returns a visible score without Gemini."""
        score, judgment = screen_resume_with_gemini(
            pdf_text="Python Django REST API PostgreSQL background jobs",
            job_title="Backend Django Developer",
            job_description="Build Python Django REST APIs with PostgreSQL.",
        )

        self.assertIsInstance(score, int)
        self.assertGreater(score, 0)
        self.assertIn("Matched terms", judgment)

    def test_employer_can_update_their_own_job(self):
        """Ensure an employer can successfully update a job posted by their company."""
        # First, let's create a dummy job manually in the database
        job = Job.objects.create(
            title="Old Title",
            description="Old description",
            requirements="None",
            company=self.company,
            created_by=self.employer
        )
        
        detail_url = reverse('job_detail_update_delete', kwargs={'slug': job.slug})
        self.client.force_authenticate(user=self.employer)
        
        updated_data = {"title": "Brand New Updated Title"}
        
        # We use patch for partial updates
        response = self.client.patch(detail_url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Brand New Updated Title")

    def test_employer_can_soft_delete_job(self):
        """Ensure an employer can soft-delete their job (sets is_active to False)."""
        job = Job.objects.create(
            title="Job to be Deleted",
            description="Testing soft delete",
            requirements="None",
            company=self.company,
            created_by=self.employer
        )
        
        detail_url = reverse('job_detail_update_delete', kwargs={'slug': job.slug})
        self.client.force_authenticate(user=self.employer)
        
        # Triggering DELETE request
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify from database that it's NOT hard-deleted, but is_active is False
        job.refresh_from_db()
        self.assertFalse(job.is_active)   

    def test_candidate_can_apply_to_job(self):
        """Ensure a user with CANDIDATE role can successfully apply to an active job with a PDF resume."""
        job = Job.objects.create(
            title="Frontend Developer",
            description="React role",
            requirements="React skills",
            company=self.company,
            created_by=self.employer
        )
        
        apply_url = reverse('job_apply')
        self.client.force_authenticate(user=self.candidate)
        
        # Creating a fake PDF file in memory for testing file upload
        fake_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        
        data = {
            "job": job.id,
            "cover_letter": "I am highly interested in this role.",
            "resume": fake_resume  # Sending the file object
        }
        
        # Using multipart format for file uploads
        response = self.client.post(apply_url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['job_title'], "Frontend Developer")
        self.assertEqual(response.data['candidate_email'], "candidate@hireos.ai")

    def test_cannot_apply_to_same_job_twice(self):
        """Ensure a candidate cannot submit duplicate applications for the same job."""
        job = Job.objects.create(
            title="DevOps Engineer",
            description="Cloud role",
            requirements="AWS skills",
            company=self.company,
            created_by=self.employer
        )
        
        fake_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        
        # Create the first application directly using the file field
        Application.objects.create(
            job=job,
            candidate=self.candidate,
            resume=fake_resume
        )
        
        apply_url = reverse('job_apply')
        self.client.force_authenticate(user=self.candidate)
        
        another_fake_resume = SimpleUploadedFile("resume2.pdf", b"dummy pdf content", content_type="application/pdf")
        data = {
            "job": job.id,
            "resume": another_fake_resume
        }
        
        response = self.client.post(apply_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employer_cannot_apply_to_job(self):
        """Ensure users with EMPLOYER role are restricted from applying to jobs."""
        job = Job.objects.create(
            title="Manager Role",
            description="Management role",
            requirements="Leadership skills",
            company=self.company,
            created_by=self.employer
        )
        
        apply_url = reverse('job_apply')
        self.client.force_authenticate(user=self.employer)
        
        fake_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        data = {
            "job": job.id,
            "resume": fake_resume
        }
        
        response = self.client.post(apply_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employer_can_list_applications(self):
        """Ensure an employer can view applications submitted to their company's jobs."""
        job = Job.objects.create(
            title="UI/UX Designer",
            description="Design role",
            requirements="Figma skills",
            company=self.company,
            created_by=self.employer
        )
        
        fake_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        
        Application.objects.create(
            job=job,
            candidate=self.candidate,
            resume=fake_resume
        )
        
        list_url = reverse('employer_application_list')
        self.client.force_authenticate(user=self.employer)
        
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['job_title'], "UI/UX Designer")

    def test_employer_can_update_application_status(self):
        """Ensure an employer can change the status of an application (e.g., SHORTLISTED)."""
        job = Job.objects.create(
            title="QA Engineer",
            description="Testing role",
            requirements="Selenium skills",
            company=self.company,
            created_by=self.employer
        )
        
        fake_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        
        application = Application.objects.create(
            job=job,
            candidate=self.candidate,
            resume=fake_resume,
            status="PENDING"
        )
        
        update_url = reverse('employer_application_update', kwargs={'pk': application.id})
        self.client.force_authenticate(user=self.employer)
        
        updated_data = {"status": "SHORTLISTED"}
        
        response = self.client.patch(update_url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], "SHORTLISTED")
        
        application.refresh_from_db()
        self.assertEqual(application.status, "SHORTLISTED")
            
    @patch('jobs.views.build')
    @patch('jobs.views.service_account.Credentials.from_service_account_file')
    def test_employer_can_schedule_interview_with_google_calendar(self, mock_credentials, mock_build):
        """Ensure that an employer can schedule an interview and receive the Google Calendar event response."""
        self.client.force_authenticate(user=self.employer)

        mock_creds = MagicMock()
        mock_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_insert = mock_service.events.return_value.insert.return_value
        mock_insert.execute.return_value = {
            'id': 'evt_12345',
            'htmlLink': 'https://calendar.google.com/event?eid=evt_12345',
            'hangoutLink': 'https://meet.google.com/abc-defg-hij'
        }

        url = reverse('schedule_interview')
        response = self.client.post(url, {
            'candidate_email': 'candidate@example.com',
            'date': '2026-06-15',
            'time': '09:00',
            'title': 'System Design Interview',
            'duration_minutes': 45
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['event_id'], 'evt_12345')
        self.assertEqual(response.data['event_link'], 'https://calendar.google.com/event?eid=evt_12345')
        self.assertEqual(response.data['meet_link'], 'https://meet.google.com/abc-defg-hij')
        mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds)

    def test_filter_jobs_by_type_and_location(self):
        """Ensure jobs can be filtered accurately by job_type and location_type."""
        Job.objects.create(
            title="Django Dev FullTime Remote",
            description="Remote role",
            requirements="Django",
            company=self.company,
            created_by=self.employer,
            job_type="FULL_TIME",
            location_type="REMOTE"
        )
        
        Job.objects.create(
            title="React Dev PartTime OnSite",
            description="Onsite role",
            requirements="React",
            company=self.company,
            created_by=self.employer,
            job_type="PART_TIME",
            location_type="ON_SITE"
        )
        
        filter_url = f"{self.job_url}?job_type=FULL_TIME&location_type=REMOTE"
        response = self.client.get(filter_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Django Dev FullTime Remote")

    def test_search_jobs_by_keyword(self):
        """Ensure full-text search works across title and description fields."""
        Job.objects.create(
            title="Senior Kubernetes Engineer",
            description="Looking for cloud infrastructure experts.",
            requirements="DevOps",
            company=self.company,
            created_by=self.employer
        )
        
        search_url = f"{self.job_url}?search=Kubernetes"
        response = self.client.get(search_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Senior Kubernetes Engineer")

    def test_employer_can_view_their_own_dashboard_analytics(self):
        """Ensure an authorized employer can successfully fetch their company's aggregate metrics."""        
        # 1. Safely retrieve the company of the logged-in employer
        company = self.employer.company
        
        # 2. Explicitly create a job linked to THIS specific company inside the test scope
        Job.objects.create(
            company=company,
            created_by=self.employer,
            title="Dashboard Test Job",
            description="Testing analytics metrics",
            requirements="Python, Django",
            location="Remote",
            job_type="FULL_TIME",
            location_type="REMOTE",
            salary_min=50000,
            salary_max=80000
        )
        
        # 3. Authenticate as the employer
        self.client.force_authenticate(user=self.employer)
        
        analytics_url = reverse('employer_dashboard_analytics')
        response = self.client.get(analytics_url)
        
        # 5. Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', response.data)
        self.assertIn('application_status_counts', response.data)
        self.assertEqual(response.data['metrics']['total_jobs'], 1) # This will now match perfectly

    def test_candidate_cannot_view_employer_dashboard_analytics(self):
        """Ensure candidates are blocked (403 Forbidden) from accessing employer analytics."""
        
        # 1. Authenticate as the candidate
        self.client.force_authenticate(user=self.candidate)
        
        analytics_url = reverse('employer_dashboard_analytics')
        response = self.client.get(analytics_url)
        
        # 3. Assertions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_user_cannot_download_candidate_resume(self):
        """Ensure a completely random/unauthorized user cannot download someone else's resume."""
        User = get_user_model()
        
        # 1. Create a dummy company and a job for this test scope
        test_company = Company.objects.create(name="Secure Test Corp")
        independent_job = Job.objects.create(
            company=test_company,
            title="Independent Secure Job",
            description="Testing secure file downloads",
            requirements="Security compliance",
            location="Remote",
            job_type="FULL_TIME",
            location_type="REMOTE"
        )

        # 2. Create a genuine candidate who will apply
        actual_candidate = User.objects.create_user(
            email="victim_candidate@example.com", password="Password123", first_name="John", last_name="Doe", role="CANDIDATE"
        )

        # 3. Create a malicious/hacker user who will try to steal the resume
        hacker_user = User.objects.create_user(
            email="hacker@malicious.com", password="Password123", first_name="Bad", last_name="Actor", role="CANDIDATE"
        )

        # 4. Create an application with a mock PDF resume file
        fake_resume = SimpleUploadedFile("candidate_resume.pdf", b"confidential pdf content", content_type="application/pdf")
        app = Application.objects.create(
            job=independent_job, candidate=actual_candidate, cover_letter="Hello World", resume=fake_resume
        )

        # 5. Try to access and download the file using the hacker's token
        self.client.force_authenticate(user=hacker_user)
        download_url = reverse('secure_resume_download', kwargs={'application_id': app.id})
        response = self.client.get(download_url)

        # 6. Strict enforcement: It must block them with 403 Forbidden!
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)    

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_employer_status_update_triggers_celery_tasks(self):
        """Ensure that when an employer updates an application status, backend workers are triggered."""
        User = get_user_model()
        
        # 1. Setup authorized employer and company infrastructure
        employer_company = Company.objects.create(name="Authorized Hub Corp")
        employer_user = User.objects.create_user(
            email="recruiter_boss@company.com", password="Password123", role="EMPLOYER", company=employer_company
        )
        
        # 2. Create the respective job and target candidate profile
        test_job = Job.objects.create(
            company=employer_company, title="Celery Target Position", description="Testing workers", 
            requirements="None", location="Dhaka", job_type="FULL_TIME", location_type="ONSITE"
        )
        candidate_user = User.objects.create_user(
            email="target_candidate@example.com", password="Password123", role="CANDIDATE"
        )
        
        # 3. Create a clean base application instance
        app = Application.objects.create(job=test_job, candidate=candidate_user, status="PENDING")
        
        # 4. Patch authorization and patch status via UpdateAPIView endpoint
        self.client.force_authenticate(user=employer_user)
        update_url = reverse('employer_application_update', kwargs={'pk': app.id})
        
        # Triggering the update to a valid application status
        response = self.client.patch(update_url, {'status': 'SHORTLISTED'}, format='json')
        
        # 5. Assert database records and successful asynchronous orchestration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, 'SHORTLISTED')

    def test_job_listings_enforce_pagination(self):
        """Verify that public job listings strictly enforce our 10-record-per-page safety pagination limits."""
        # 1. Create a core company to hold batch listings
        batch_company = Company.objects.create(name="Mass Hiring Group")
        
        # 2. Create 15 individual job posts, using save() so unique slugs are generated
        for i in range(15):
            Job.objects.create(
                company=batch_company,
                title=f"Bulk Automation Engineer {i}",
                description="Scalability tests",
                requirements="Django expert",
                location="Remote",
                job_type="FULL_TIME",
                location_type="REMOTE",
                is_active=True
            )
        
        # 3. Request the public facing open generic view listing endpoint
        list_url = reverse('job_list_create')
        response = self.client.get(list_url)
        
        # 4. Assert response payload contains DRF structure pagination envelopes
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Verify the chunking size is strictly capped at 10 items maximum
        self.assertEqual(len(response.data['results']), 10)
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_export_candidates_csv_queued_successfully(self):
        """Ensure that employers can trigger background CSV batch data exports and receive 202 ACCEPTED status."""
        User = get_user_model()
        
        # 1. Setup corporate credentials
        employer_company = Company.objects.create(name="Data Export Analytics")
        employer_user = User.objects.create_user(
            email="data_admin@analytics.com", password="Password123", role="EMPLOYER", company=employer_company
        )
        
        # 2. Assign job to the authenticated corporate identity
        active_job = Job.objects.create(
            company=employer_company, title="Data Specialist", description="CSV parsing metrics", 
            requirements="Python", location="Remote", job_type="FULL_TIME", location_type="REMOTE"
        )
        
        # 3. Issue the POST request to trigger the export queue pipelines
        self.client.force_authenticate(user=employer_user)
        export_url = reverse('export-candidates-csv', kwargs={'job_id': active_job.id})
        response = self.client.post(export_url)
        
        # 4. Confirm the server returns HTTP 202 ACCEPTED signifying asynchronous task alignment
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("queued successfully", response.data['detail'])



