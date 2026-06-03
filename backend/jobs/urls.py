from django.urls import path
from .views import (
    JobListCreateView,
    JobRetrieveUpdateDestroyView,
    ApplicationCreateView,
    CandidateApplicationListView,   # ✅ নতুন
    EmployerApplicationListView,
    EmployerApplicationUpdateView,
    ScheduleInterviewView,
    EmployerDashboardAnalyticsView,
    SecureResumeDownloadView,
    GenerateOfferLetterView,
    ExportCandidatesCSVView,
)

urlpatterns = [
    path('api/jobs/', JobListCreateView.as_view(), name='job_list_create'),
    path('api/jobs/apply/', ApplicationCreateView.as_view(), name='job_apply'),

    # ✅ Candidate নিজের applications দেখার জন্য আলাদা endpoint
    path('api/jobs/my-applications/', CandidateApplicationListView.as_view(), name='candidate_my_applications'),

    # Employer Application Management
    path('api/jobs/applications/', EmployerApplicationListView.as_view(), name='employer_application_list'),
    path('api/jobs/applications/<int:pk>/', EmployerApplicationUpdateView.as_view(), name='employer_application_update'),
    path('api/jobs/applications/<int:pk>/Status/', EmployerApplicationUpdateView.as_view(), name='employer_application_status_update'),
    path('api/jobs/applications/<int:application_id>/offer-letter/', GenerateOfferLetterView.as_view(), name='generate_offer_letter'),

    path('api/schedule-interview/', ScheduleInterviewView.as_view(), name='schedule_interview'),
    path('api/jobs/<slug:slug>/', JobRetrieveUpdateDestroyView.as_view(), name='job_detail_update_delete'),
    path('dashboard/analytics/', EmployerDashboardAnalyticsView.as_view(), name='employer_dashboard_analytics'),
    path('applications/<int:application_id>/download-resume/', SecureResumeDownloadView.as_view(), name='secure_resume_download'),
    path('jobs/<int:job_id>/export-candidates/', ExportCandidatesCSVView.as_view(), name='export-candidates-csv'),
]
