import os
from celery import shared_task
import pypdf
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import Application
from .services import screen_resume_with_gemini
from .services import generate_offer_letter_pdf
from django.utils import timezone
from datetime import timedelta, date

User = get_user_model()

@shared_task
def process_ai_resume_screening(application_id):
    """
    Celery background worker task that extracts text from a candidate's PDF resume,
    invokes Gemini LLM service layer, and writes matching analytics data directly back to the database.
    """
    try:
        application = Application.objects.get(id=application_id)
        
        # Guard clause in case the application has no resume file attached
        if not application.resume:
            application.ai_score = None
            application.ai_judgment = "No resume attached for ATS screening."
            application.save()
            return f"Application {application_id} has no resume attached."
            
        # Extract Text from the uploaded PDF resume file path safely
        pdf_text = ""
        with application.resume.open('rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
        
        if not pdf_text.strip():
            application.ai_score = None
            application.ai_judgment = "Empty or unreadable PDF resume content."
            application.save()
            return f"Application {application_id} processed with empty resume text content."
            
        # Trigger our specialized service layer to connect with Gemini LLM Cloud
        ai_score, ai_judgment = screen_resume_with_gemini(
            pdf_text=pdf_text,
            job_title=application.job.title,
            job_description=(
                f"{getattr(application.job, 'description', '')}\n"
                f"{getattr(application.job, 'requirements', '')}"
            )
        )
        
        # Persist the score and two-line judgment inside PostgreSQL database
        application.ai_score = ai_score
        application.ai_judgment = ai_judgment
        application.save()
        
        return f"Successfully screened application {application_id} with AI Score: {ai_score}"
        
    except Application.DoesNotExist:
        return f"Application with ID {application_id} not found."
    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to process Celery AI background worker for application {application_id}: {str(e)}")
        try:
            application.ai_score = None
            application.ai_judgment = "AI screening could not be completed due to a service error."
            application.save()
        except Exception:
            pass
        return f"Failure executing background task for application {application_id}."
    

@shared_task
def process_automated_offer_letter(application_id):
    """
    Celery background worker task that generates a professional PDF offer letter,
    stores it in the file system, and updates the application's offer_letter field inside PostgreSQL.
    """
    try:
        application = Application.objects.get(id=application_id)
        
        # Trigger the PDF Generation Service Layer
        pdf_relative_path = generate_offer_letter_pdf(application)
        
        # Update and persist the model
        application.offer_letter = pdf_relative_path
        application.save()
        
        return f"Successfully generated background PDF Offer Letter for Application ID: {application_id}"
        
    except Application.DoesNotExist:
        return f"Application with ID {application_id} not found for PDF generation."
    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to execute background PDF Generation for application {application_id}: {str(e)}")
        return f"Failure executing PDF generator task for application {application_id}."   


@shared_task
def send_application_notifications(application_id):
    """
    Celery task that sends application submission emails to the candidate and the employer(s).
    """
    try:
        application = Application.objects.select_related('job', 'job__company', 'candidate').get(id=application_id)
        candidate = application.candidate
        job = application.job
        company = job.company

        candidate_subject = f"Your application for {job.title} has been submitted"
        candidate_message = (
            f"Hi {candidate.first_name or candidate.email},\n\n"
            f"Thanks for applying to {job.title} at {company.name}. "
            "Your application has been received and is now under review. "
            "We will update you soon with the next steps.\n\n"
            "Best regards,\n"
            f"{company.name} Hiring Team"
        )

        send_mail(
            subject=candidate_subject,
            message=candidate_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hireos.com'),
            recipient_list=[candidate.email],
            fail_silently=False,
        )

        employer_emails = list(
            User.objects.filter(company=company, role=User.Role.EMPLOYER)
            .values_list('email', flat=True)
            .distinct()
        )

        if employer_emails:
            employer_subject = f"New application received for {job.title}"
            employer_message = (
                f"Hello,\n\n"
                f"A new candidate has applied for {job.title} at {company.name}.\n\n"
                f"Candidate Name: {candidate.get_full_name() or candidate.email}\n"
                f"Candidate Email: {candidate.email}\n"
                f"Application ID: {application.id}\n\n"
                "Please review the application in the employer dashboard and update the status accordingly.\n\n"
                "Best regards,\n"
                "HireOS Notification Service"
            )
            send_mail(
                subject=employer_subject,
                message=employer_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hireos.com'),
                recipient_list=employer_emails,
                fail_silently=False,
            )

        return f"Application notifications sent for application {application_id}."
    except Application.DoesNotExist:
        return f"Application with ID {application_id} not found."
    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to send application notifications for {application_id}: {str(e)}")
        return f"Failure sending application notification emails for application {application_id}."


from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@shared_task
def send_asynchronous_status_email(candidate_email, candidate_name, job_title, new_status, company_name, offer_letter_path=None):
    """
    Celery background task to send automated job application status update emails to candidates.
    If an offer letter PDF exists, it attaches the file directly from the local media storage system.
    """
    try:
        subject = f"Update on your application for {job_title} at {company_name}"
        
        # Inline basic text template construction for the recruitment status update
        context_message = f"Dear {candidate_name},\n\nYour application status for the position of {job_title} has been updated to: {new_status}.\n\n"
        
        if new_status.upper() == 'SELECTED' and offer_letter_path:
            context_message += "Congratulations! Your official corporate Offer Letter has been successfully generated and attached to this email. You can also view and accept it directly from your HireOS candidate dashboard.\n\n"
        else:
            context_message += "Please log in to your HireOS dashboard to review the full details regarding the next stages of our evaluation process.\n\n"
            
        context_message += f"Best Regards,\nHuman Resources Department\n{company_name}"

        # Initialize core Django corporate email construction setup
        email = EmailMessage(
            subject=subject,
            body=context_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[candidate_email],
        )

        # Attach the physical PDF Offer Letter file if candidate is officially selected
        if new_status.upper() == 'SELECTED' and offer_letter_path:
            absolute_pdf_path = os.path.join(settings.MEDIA_ROOT, offer_letter_path)
            if os.path.exists(absolute_pdf_path):
                email.attach_file(absolute_pdf_path)

        # Dispatch the constructed email payload to SMTP server via background thread
        email.send(fail_silently=False)
        return f"Successfully dispatched background asynchronous email notification to: {candidate_email}"

    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to send background status update email to {candidate_email}: {str(e)}")
        return f"Failure executing background email notification worker task."     
    

from datetime import date
from .models import Job

@shared_task
def check_and_expire_expired_jobs():
    """
    Celery Beat scheduled task that runs automatically to scan the database.
    It updates the status of jobs from active to inactive if they are older than 30 days.
    """
    try:
        # Calculate the cutoff date (30 days ago) using timezone-aware datetime
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Filter jobs that are active but created before the cutoff date
        expired_jobs = Job.objects.filter(is_active=True, created_at__lt=cutoff_date)
        
        # Count the targeted jobs and execute a bulk update
        count = expired_jobs.count()
        if count > 0:
            expired_jobs.update(is_active=False)
            return f"Successfully processed Cron Job. Automatically deactivated {count} old jobs on {date.today()}."
        
        return f"Cron Job executed. No expired jobs found for date: {date.today()}."
        
    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to execute automated scheduled task for job expiration: {str(e)}")
        return "Failure executing Celery Beat job expiration scheduled task workflow."

import csv
from django.utils.timezone import now

@shared_task
def generate_job_applications_csv(job_id, employer_email):
    """
    Celery background task to export all shortlisted/selected candidates for a specific job into a CSV file.
    Saves the file securely into the media directory for asynchronous high-volume data downloading.
    """
    try:
        # Fetch the job instance and its corresponding processed applications optimized with select_related
        job = Job.objects.get(id=job_id)
        applications = Application.objects.filter(job=job).select_related('candidate')

        # Define file naming and structural paths safely inside media directory
        filename = f"Candidate_Export_Job_{job_id}_{now().strftime('%Y%m%d_%H%M%S')}.csv"
        folder_path = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)

        # Write data to CSV using standard python csv library structures
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write CSV Header Block
            writer.writerow(['Application ID', 'Candidate Name', 'Candidate Email', 'AI Score', 'AI Judgment', 'Application Status', 'Applied Date'])
            
            # Populate data iteratively from relational PostgreSQL rows
            for app in applications:
                candidate_name = app.candidate.get_full_name() or app.candidate.username
                writer.writerow([
                    app.id,
                    candidate_name,
                    app.candidate.email,
                    app.ai_score,
                    app.ai_judgment,
                    app.status,
                    app.created_at.strftime('%Y-%m-%d')
                ])

        # Return relative link path for frontend storage and integration downstream
        relative_csv_path = f"exports/{filename}"
        
        # Optional Move: Trigger an automated notification or log for the recruiter
        return f"Successfully generated background CSV Export for Job ID {job_id} at path: {relative_csv_path}"

    except Job.DoesNotExist:
        return f"Job with ID {job_id} not found for async CSV processing operations."
    except Exception as e:
        from logging import getLogger
        getLogger('apps').error(f"Failed to execute background CSV batch export for Job {job_id}: {str(e)}")
        return "Failure executing background CSV exporter worker task workflow."     
