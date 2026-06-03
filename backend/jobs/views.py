from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Count
from django.http import FileResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer, EmployerApplicationSerializer
from .tasks import (
    process_ai_resume_screening,
    process_automated_offer_letter,
    send_application_notifications,
    send_asynchronous_status_email,
    generate_job_applications_csv,
)
from .services import generate_offer_letter_pdf
from datetime import datetime, timedelta, timezone
import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class StandardResultsSetPagination(PageNumberPagination):
    """Global pagination: 10 records per page."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(is_active=True).select_related('company').order_by('-created_at')
    serializer_class = JobSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['job_type', 'location_type', 'location', 'company__slug']
    search_fields = ['title', 'description', 'company__name']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'EMPLOYER' or not user.company:
            raise PermissionDenied("Only employers with an associated company can post jobs.")
        serializer.save(company=user.company, created_by=user)


class JobRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        job = self.get_object()
        if self.request.user.role != 'EMPLOYER' or job.company != self.request.user.company:
            raise PermissionDenied("You do not have permission to modify this job.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != 'EMPLOYER' or instance.company != self.request.user.company:
            raise PermissionDenied("You do not have permission to delete this job.")
        instance.is_active = False
        instance.save()


class ApplicationCreateView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        application = serializer.save(candidate=self.request.user)

        # Use background processing when available, but fall back to immediate screening
        # during local development so ATS score appears even if Celery is not running.
        if settings.DEBUG:
            process_ai_resume_screening(application.id)
        else:
            process_ai_resume_screening.delay(application.id)

        send_application_notifications.delay(application.id)


# ─── NEW: Candidate নিজের applications দেখবে ───────────────────────────────
class CandidateApplicationListView(generics.ListAPIView):
    """
    Candidate নিজের সব applications দেখতে পারবে।
    AI score এবং status সহ।
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != 'CANDIDATE':
            raise PermissionDenied("Only candidates can view their own applications.")
        return (
            Application.objects
            .filter(candidate=user)
            .select_related('job', 'job__company')
            .order_by('-created_at')
        )
# ────────────────────────────────────────────────────────────────────────────


class EmployerApplicationListView(generics.ListAPIView):
    """
    Employer তার company-র সব applications দেখবে।
    """
    serializer_class = EmployerApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role != 'EMPLOYER' or not user.company:
            raise PermissionDenied("Only employers can view job applications.")
        return (
            Application.objects
            .filter(job__company=user.company)
            .select_related('job', 'candidate')
            .order_by('-created_at')
        )


class EmployerApplicationUpdateView(generics.UpdateAPIView):
    """
    Employer application status update করবে।
    throttle_classes সরানো হয়েছে — এটাই status update fail করাচ্ছিল।
    """
    serializer_class = EmployerApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    # ✅ FIX: UserRateThrottle সরানো হয়েছে

    def get_queryset(self):
        user = self.request.user
        if user.role != 'EMPLOYER' or not user.company:
            raise PermissionDenied("Only employers can modify job applications.")
        return Application.objects.filter(job__company=user.company)

    def perform_update(self, serializer):
        application = serializer.save()

        if application.status and application.status.upper() == 'SHORTLISTED':
            process_automated_offer_letter.delay(application.id)
            offer_letter_rel_path = (
                f"offer_letters/Offer_Letter_{application.id}_{application.candidate.id}.pdf"
            )
            send_asynchronous_status_email.delay(
                candidate_email=application.candidate.email,
                candidate_name=f"{application.candidate.first_name} {application.candidate.last_name}",
                job_title=application.job.title,
                new_status=application.status,
                company_name=application.job.company.name,
                offer_letter_path=offer_letter_rel_path
            )
        else:
            send_asynchronous_status_email.delay(
                candidate_email=application.candidate.email,
                candidate_name=f"{application.candidate.first_name} {application.candidate.last_name}",
                job_title=application.job.title,
                new_status=application.status,
                company_name=application.job.company.name
            )


class ScheduleInterviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'EMPLOYER':
            raise PermissionDenied("Only employers can schedule interviews.")

        candidate_email  = request.data.get('candidate_email')
        interview_date   = request.data.get('date')
        interview_time   = request.data.get('time')
        title            = request.data.get('title', 'Interview')
        duration_minutes = int(request.data.get('duration_minutes', 30))

        if not candidate_email or not interview_date or not interview_time:
            raise ParseError("candidate_email, date, and time are required.")

        try:
            start_datetime = datetime.strptime(
                f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            raise ParseError("Date must be YYYY-MM-DD and time must be HH:MM.")

        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/calendar.events'],
        )
        if getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_SUBJECT', None):
            credentials = credentials.with_subject(settings.GOOGLE_SERVICE_ACCOUNT_SUBJECT)

        service = build('calendar', 'v3', credentials=credentials)

        event_body = {
            'summary': title,
            'description': f'Interview scheduled by {request.user.email}',
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'UTC'},
            'end':   {'dateTime': end_datetime.isoformat(),   'timeZone': 'UTC'},
            'attendees': [{'email': candidate_email}],
            'conferenceData': {
                'createRequest': {
                    'requestId': f'interview-{uuid.uuid4()}',
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                }
            },
            'reminders': {'useDefault': True},
        }

        try:
            created_event = service.events().insert(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                body=event_body,
                conferenceDataVersion=1,
            ).execute()
        except HttpError as exc:
            return Response(
                {"detail": f"Google Calendar error: {exc.content.decode() if hasattr(exc, 'content') else str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                'event_id':   created_event.get('id'),
                'event_link': created_event.get('htmlLink'),
                'meet_link':  created_event.get('hangoutLink'),
            },
            status=status.HTTP_201_CREATED,
        )


class EmployerDashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.role != 'EMPLOYER' or not user.company:
            return Response(
                {"detail": "Access denied. Only employers linked to a company can view analytics."},
                status=status.HTTP_403_FORBIDDEN
            )

        company = user.company
        total_jobs         = Job.objects.filter(company=company).count()
        total_applications = Application.objects.filter(job__company=company).count()

        status_breakdown = (
            Application.objects.filter(job__company=company)
            .values('status')
            .annotate(count=Count('id'))
        )
        stats_dict = {item['status']: item['count'] for item in status_breakdown}

        for status_choice, _ in Application.STATUS_CHOICES:
            stats_dict.setdefault(status_choice, 0)

        return Response({
            "company_name": company.name,
            "company_slug": company.slug,
            "metrics": {
                "total_jobs":         total_jobs,
                "total_applications": total_applications,
            },
            "application_status_counts": stats_dict
        }, status=status.HTTP_200_OK)


class SecureResumeDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id, *args, **kwargs):
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            raise Http404("Application not found.")

        user = request.user
        is_candidate_owner = (user.role == 'CANDIDATE' and application.candidate == user)
        is_job_employer    = (user.role == 'EMPLOYER'   and user.company == application.job.company)

        if not (is_candidate_owner or is_job_employer):
            return Response(
                {"detail": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not application.resume or not application.resume.storage.exists(application.resume.name):
            return Response(
                {"detail": "Resume file not found on the server."},
                status=status.HTTP_404_NOT_FOUND
            )

        file_handle = application.resume.open()
        response = FileResponse(file_handle, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{application.resume.name.split("/")[-1]}"'
        )
        return response


class GenerateOfferLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id, *args, **kwargs):
        try:
            application = Application.objects.select_related(
                'job', 'job__company', 'candidate'
            ).get(id=application_id)
        except Application.DoesNotExist:
            raise Http404("Application not found.")

        user = request.user
        if user.role != 'EMPLOYER' or user.company != application.job.company:
            return Response(
                {"detail": "Access denied."},
                status=status.HTTP_403_FORBIDDEN
            )

        if application.status != 'SHORTLISTED':
            return Response(
                {"detail": "Offer letters can only be generated for shortlisted candidates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer_letter_path = generate_offer_letter_pdf(application)
        application.offer_letter.name = offer_letter_path
        application.save(update_fields=['offer_letter'])

        file_handle = application.offer_letter.open('rb')
        filename    = offer_letter_path.split('/')[-1]
        response    = FileResponse(file_handle, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportCandidatesCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        user = request.user
        if user.role != 'EMPLOYER':
            return Response(
                {"detail": "Access denied. Only employers can export candidate data."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            job = Job.objects.get(id=job_id, company=user.company)
        except Job.DoesNotExist:
            return Response(
                {"detail": "Job not found or you do not have permission to export it."},
                status=status.HTTP_404_NOT_FOUND
            )

        generate_job_applications_csv.delay(job.id, user.email)

        return Response(
            {"detail": "CSV export queued successfully. You will receive it via email shortly."},
            status=status.HTTP_202_ACCEPTED
        )
