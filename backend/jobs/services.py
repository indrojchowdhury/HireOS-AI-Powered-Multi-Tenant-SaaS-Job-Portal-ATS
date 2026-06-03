import os
import json
import logging
import re
from collections import Counter
from google import genai
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger('apps')


ATS_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "our", "that", "the", "this", "to", "we",
    "with", "you", "your", "will", "job", "role", "candidate", "experience",
    "skills", "responsibilities", "requirements", "required", "preferred",
}


def _tokenize_for_ats(text):
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", (text or "").lower())
        if token not in ATS_STOP_WORDS and len(token) > 2
    ]


def _fallback_resume_screening(pdf_text, job_title, job_description=""):
    """
    Local ATS fallback used when Gemini is unavailable.
    It keeps the dashboard useful instead of saving a null score for service outages.
    """
    resume_tokens = set(_tokenize_for_ats(pdf_text))
    job_tokens = _tokenize_for_ats(f"{job_title} {job_description}")

    if not resume_tokens or not job_tokens:
        return 0, "Resume could not be confidently matched against the job details."

    weighted_job_terms = Counter(job_tokens)
    total_weight = sum(weighted_job_terms.values())
    matched_weight = sum(
        weight for term, weight in weighted_job_terms.items() if term in resume_tokens
    )
    coverage = matched_weight / total_weight if total_weight else 0

    score = max(1, min(100, round(coverage * 100)))
    matched_terms = [
        term for term, _ in weighted_job_terms.most_common(8) if term in resume_tokens
    ]

    if score >= 70:
        verdict = "Strong resume match based on overlapping job skills and requirements."
    elif score >= 40:
        verdict = "Moderate resume match; review the candidate for role-specific depth."
    else:
        verdict = "Limited keyword match; manual review is recommended before advancing."

    if matched_terms:
        verdict = f"{verdict} Matched terms: {', '.join(matched_terms[:5])}."

    return score, verdict


def screen_resume_with_gemini(pdf_text, job_title, job_description=""):
    """
    Calls Gemini AI to screen a candidate's resume against the job requirements.
    Returns a tuple of (score: int, judgment: str).
    Falls back to a local ATS score on any Gemini/API failure.
    """
    fallback_response = _fallback_resume_screening(pdf_text, job_title, job_description)

    api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        logger.error("Gemini API Key is missing. Set GEMINI_API_KEY in environment or settings.")
        return fallback_response

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert enterprise ATS AI.
Analyze the following candidate resume text against the requirements for the job title: "{job_title}".
Job Description: {job_description if job_description else "Not provided"}.

Respond ONLY with a valid raw JSON object containing exactly two keys:
1. "score": an integer between 0 and 100 representing candidate fit.
2. "judgment": a maximum 2-line professional evaluation summary.

Do NOT include markdown, code blocks, backticks, or any extra text. Raw JSON only.

Resume Text:
{pdf_text}
        """

        response = client.models.generate_content(
            model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
            contents=prompt
        )
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps the response in ```json ... ```
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        # If Gemini includes extra text, extract the first JSON object from the response.
        if not raw.startswith("{"):
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1 and end > start:
                raw = raw[start:end+1]

        data = json.loads(raw)
        score = max(0, min(100, int(data.get("score", 0))))
        judgment = str(data.get("judgment", "")).strip()
        return score, judgment

    except Exception as e:
        logger.error(f"Gemini AI Screening error: {str(e)}")
        return fallback_response


def generate_offer_letter_pdf(application):
    """
    Generates a professional branded PDF offer letter and saves it to media/offer_letters/.
    Returns the relative file path to be stored in the Application.offer_letter field.
    """
    filename    = f"Offer_Letter_{application.id}_{application.candidate.id}.pdf"
    folder_path = os.path.join(settings.MEDIA_ROOT, 'offer_letters')
    os.makedirs(folder_path, exist_ok=True)
    file_path   = os.path.join(folder_path, filename)

    doc = SimpleDocTemplate(
        file_path, pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    story  = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=20
    )
    body_style = ParagraphStyle(
        'LetterBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=12
    )
    subject_style = ParagraphStyle(
        'Subject',
        parent=body_style,
        fontSize=12,
        fontName='Helvetica-Bold'
    )

    company_name   = application.job.company.name if application.job.company else 'HireOS Partner Company'
    job_title      = application.job.title
    candidate_name = application.candidate.get_full_name() or application.candidate.email

    story.append(Paragraph(f"<b>{company_name}</b>", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"Date: {timezone.now().date().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"To,<br/><b>{candidate_name}</b>", body_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        f"<b>Subject: Offer of Employment — {job_title}</b>",
        subject_style
    ))
    story.append(Spacer(1, 15))

    letter_body = f"""
Dear {candidate_name},<br/><br/>
Following your recent screening and evaluation rounds through our HireOS AI Recruitment Platform,
we are absolutely thrilled to offer you the full-time position of <b>{job_title}</b> at {company_name}.<br/><br/>
We were deeply impressed by your credentials, technical expertise, and matching qualifications
analyzed during our automated vetting cycle. We believe your skills will be a tremendous asset
to our organization.<br/><br/>
Your formal compensation structure, onboarding timeline, and detailed corporate policies will be
shared upon your digital acceptance of this letter inside your HireOS Candidate Dashboard.<br/><br/>
Congratulations on your selection! We look forward to welcoming you to our team.
    """
    story.append(Paragraph(letter_body, body_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<b>Human Resources Department</b><br/>{company_name}",
        body_style
    ))

    doc.build(story)
    return f"offer_letters/{filename}"
