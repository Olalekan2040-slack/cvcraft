import asyncio
import logging
import os
import ssl
from datetime import datetime, timedelta, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Optional

import aiosmtplib
from sqlalchemy.orm import Session

from app.config import settings
from app.models.email import EmailContact, EmailLog, EmailTemplate

logger = logging.getLogger(__name__)

MAX_SMTP_RETRIES = 3

# Ordered priority map: category name → list of keywords to match in job title
# More specific categories are listed first.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    # Listed most-specific first so early matches win
    "tech_ai_instructor": [
        "tech instructor", "ai instructor", "tech / ai instructor",
        "technology instructor", "ict instructor", "computer science teacher",
        "it teacher", "coding instructor", "stem teacher", "python instructor",
        "programming teacher", "technology teacher", "software engineering instructor",
        "web development instructor", "digital skills instructor",
        "ai teacher", "machine learning instructor",
    ],
    "tech_teacher": [
        "ict teacher", "computer science teacher", "tech teacher",
        "coding instructor", "stem teacher", "programming teacher",
        "it teacher", "technology teacher", "it instructor",
        "secondary school teacher", "cs teacher",
        "software engineering instructor", "programming tutor", "python instructor",
        "web development instructor", "technical trainer", "ict instructor",
        "developer advocate", "technical mentor", "coding bootcamp facilitator",
        "technology education specialist", "edtech", "educational technology",
        "lms developer", "digital learning platform", "academic technology lead",
        "head of training", "training program manager",
    ],
    "data_analyst": [
        "data analyst", "data scientist", "data engineer",
        "machine learning", "ml engineer", "ai engineer",
        "business analyst", "analytics", "nlp engineer",
        "business intelligence", "bi developer", "reporting analyst",
        "ai application developer", "analytics engineer",
    ],
    "odoo_developer": ["odoo", "erp developer", "odoo customization"],
    "full_stack_developer": [
        "full stack", "fullstack", "full-stack", "react developer",
        "mern", "pern", "mean stack", "javascript developer",
        "frontend and backend", "web developer", "web application developer",
        "web engineer", "web systems developer", "software applications developer",
    ],
    "backend_developer": [
        "backend", "python developer", "fastapi", "django developer",
        "flask developer", "api developer", "rest api", "server-side",
        "backend engineer", "drf developer", "django rest framework",
    ],
    "software_engineer": [
        "software engineer", "software developer", "application developer",
        "senior developer", "lead developer", "systems developer",
        "technical lead", "engineering team lead", "tech hub manager",
        "technical operations manager", "software development lead",
        "it manager", "technology coordinator", "it coordinator",
        "innovation lab manager", "technology program director",
        "branch technology manager", "engineering supervisor",
        "technical project manager", "program manager",
        # interns/trainees fall back to software_engineer cover letter
        "intern", "trainee", "graduate trainee", "associate engineer",
        "junior technical consultant", "technology associate",
    ],
    "python_developer": [
        "python", "automation engineer", "scripting", "devops", "cloud engineer",
        "aws cloud", "deployment engineer", "infrastructure engineer",
        "site reliability", "sre", "platform engineer",
        "linux systems", "docker engineer", "cloud support",
        "qa automation", "selenium automation", "web scraping engineer",
        "rpa developer", "process automation", "technical automation",
    ],
}


def detect_category(job_title: str) -> str:
    """Return the best matching template category for a given job title."""
    title_lower = job_title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return category
    return "general"


def _render(template_str: str, variables: dict) -> str:
    """Render {{var}} placeholders safely (missing vars are left as-is)."""
    normalized = template_str.replace("{{", "${").replace("}}", "}")
    return Template(normalized).safe_substitute(variables)


def _build_mime(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str],
) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    # Alternative body (text + HTML)
    body_part = MIMEMultipart("alternative")
    if text_body:
        body_part.attach(MIMEText(text_body, "plain", "utf-8"))
    body_part.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(body_part)

    # Attach CV / Resume PDF
    cv_path = settings.CV_PATH
    if cv_path and os.path.isfile(cv_path):
        with open(cv_path, "rb") as f:
            attachment = MIMEBase("application", "pdf")
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(cv_path)}"',
        )
        msg.attach(attachment)
        logger.debug("CV attached: %s", cv_path)
    else:
        logger.warning(
            "CV not found at '%s' — sending without attachment", cv_path)

    return msg


async def _send_via_smtp(msg: MIMEMultipart) -> None:
    """Send a pre-built MIME message via aiosmtplib with exponential-backoff retry.

    Port 465  → implicit TLS  (use_tls=True  + explicit ssl context)
    Port 587  → STARTTLS      (start_tls=True)
    Port 465 is preferred: port 587 is often blocked by ISPs on residential lines.
    """
    # Gmail app passwords are shown with spaces; SMTP AUTH needs them stripped.
    smtp_password = settings.SMTP_PASSWORD.replace(" ", "")
    port = settings.SMTP_PORT
    use_tls = port == 465
    start_tls = port == 587
    # Explicit SSL context required for aiosmtplib implicit-TLS mode on port 465
    tls_ctx = ssl.create_default_context() if use_tls else None

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_SMTP_RETRIES + 1):
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=port,
                username=settings.SMTP_USERNAME,
                password=smtp_password,
                use_tls=use_tls,
                start_tls=start_tls,
                tls_context=tls_ctx,
            )
            return
        except Exception as exc:
            last_error = exc
            logger.warning("SMTP attempt %d/%d failed (port %d): %s",
                           attempt, MAX_SMTP_RETRIES, port, exc)
            if attempt < MAX_SMTP_RETRIES:
                await asyncio.sleep(2 ** attempt)
    raise last_error  # type: ignore[misc]


def _within_cooldown(contact: EmailContact, cooldown_days: int) -> bool:
    if not contact.last_contacted_at:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
    last = contact.last_contacted_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last >= cutoff


def _select_template(db: Session, category: str) -> Optional[EmailTemplate]:
    """
    Find the active template for the detected category.
    Falls back to 'general' category, then any active template.
    """
    for lookup in (category, "general", None):
        q = db.query(EmailTemplate).filter(EmailTemplate.is_active.is_(True))
        if lookup is not None:
            template = q.filter(EmailTemplate.category == lookup).first()
        else:
            template = q.first()
        if template:
            return template
    return None


async def dispatch_outreach(db: Session) -> int:
    """
    Dispatch personalised outreach emails for all new contacts.
    Automatically picks the correct cover letter template per job category.
    Attaches the applicant's CV to every email.
    Returns the number of emails successfully sent.

    Deduplication rules (both must pass):
      1. Per-contact cooldown — contact.last_contacted_at within EMAIL_COOLDOWN_DAYS
      2. Global email dedup — if ANY contact with the same email address was
         contacted within the cooldown window, skip (prevents same recruiter
         receiving multiple emails from different job listing rows).
    """
    cooldown_days = settings.EMAIL_COOLDOWN_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)

    # Build set of email addresses already contacted within the cooldown window
    recently_emailed: set = set()
    for c in db.query(EmailContact).all():
        if c.last_contacted_at:
            last = c.last_contacted_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if last >= cutoff:
                recently_emailed.add(c.email.lower())

    contacts = db.query(EmailContact).all()
    sent_count = 0
    emailed_this_cycle: set = set()  # extra guard within current run

    for contact in contacts:
        email_key = contact.email.lower()
        if email_key in recently_emailed:
            continue
        if email_key in emailed_this_cycle:
            continue

        listing = contact.listing
        job_title = listing.title if listing else ""
        category = detect_category(job_title)
        template = _select_template(db, category)

        if not template:
            logger.warning(
                "No usable template for category '%s' — skipping %s", category, contact.email
            )
            continue

        variables = {
            "job_title": job_title,
            "company": listing.company or "the company",
            "location": listing.location or "Nigeria",
            "applicant_name": settings.SMTP_FROM_NAME,
            "applicant_email": settings.SMTP_FROM_EMAIL,
            "applicant_skills": settings.APPLICANT_SKILLS,
            "applicant_github": settings.APPLICANT_GITHUB,
            "applicant_website": settings.APPLICANT_WEBSITE,
        }

        subject = _render(template.subject, variables)
        html_body = _render(template.html_body, variables)
        text_body = _render(template.text_body,
                            variables) if template.text_body else None

        msg = _build_mime(contact.email, subject, html_body, text_body)

        log = EmailLog(contact_id=contact.id, template_id=template.id)
        db.add(log)

        try:
            await _send_via_smtp(msg)
            log.status = "sent"
            contact.last_contacted_at = datetime.now(timezone.utc)
            contact.contact_count += 1
            recently_emailed.add(email_key)
            emailed_this_cycle.add(email_key)
            sent_count += 1
            logger.info(
                "Sent [%s] cover letter to %s for '%s' at %s",
                category, contact.email, job_title, listing.company or "?",
            )
        except Exception as exc:
            log.status = "failed"
            log.error_message = str(exc)
            logger.error("Failed to send to %s: %s", contact.email, exc)

        db.commit()
        await asyncio.sleep(settings.EMAIL_SEND_DELAY_SECONDS)

    return sent_count


async def send_manual_school_email(
    db: Session,
    email: str,
    school_name: str,
    location: str = "Nigeria",
) -> dict:
    """
    Send a Tech / AI Instructor cover letter to a manually provided school email.
    Creates a synthetic job listing + contact so the send is tracked in the DB.
    Returns: {email, status: 'sent'|'skipped'|'failed', reason?}
    """
    from app.models.job import JobListing, JobSource  # avoid circular at module level

    email_key = email.lower().strip()

    # ── Cooldown check ──────────────────────────────────────────────────────
    cooldown_days = settings.EMAIL_COOLDOWN_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
    existing_contact = db.query(EmailContact).filter(
        EmailContact.email == email_key).first()
    if existing_contact and existing_contact.last_contacted_at:
        last = existing_contact.last_contacted_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last >= cutoff:
            return {"email": email_key, "status": "skipped", "reason": "within cooldown"}

    # ── Template ────────────────────────────────────────────────────────────
    template = _select_template(db, "tech_ai_instructor")
    if not template:
        return {"email": email_key, "status": "failed", "reason": "no tech_ai_instructor template found"}

    # ── Synthetic job listing (tracks contact in the normal pipeline) ───────
    synthetic_url = f"school-manual://{email_key}"
    listing = db.query(JobListing).filter(
        JobListing.url == synthetic_url).first()
    if not listing:
        source = (
            db.query(JobSource).filter(JobSource.id == 25).first()
            or db.query(JobSource).first()
        )
        if not source:
            return {"email": email_key, "status": "failed", "reason": "no job source configured"}
        listing = JobListing(
            source_id=source.id,
            title="Tech / AI Instructor",
            company=school_name,
            location=location,
            url=synthetic_url,
            description=f"Manual school outreach to {school_name} ({location}).",
            raw_emails=[email_key],
        )
        db.add(listing)
        db.flush()

    # ── Contact record ──────────────────────────────────────────────────────
    contact = existing_contact
    if not contact:
        contact = EmailContact(listing_id=listing.id, email=email_key)
        db.add(contact)
        db.flush()

    # ── Render & send ───────────────────────────────────────────────────────
    variables = {
        "job_title": "Tech / AI Instructor",
        "company": school_name,
        "location": location,
        "applicant_name": settings.SMTP_FROM_NAME,
        "applicant_email": settings.SMTP_FROM_EMAIL,
        "applicant_skills": settings.APPLICANT_SKILLS,
        "applicant_github": settings.APPLICANT_GITHUB,
        "applicant_website": settings.APPLICANT_WEBSITE,
    }
    subject = _render(template.subject, variables)
    html_body = _render(template.html_body, variables)
    text_body = _render(template.text_body,
                        variables) if template.text_body else None

    msg = _build_mime(email_key, subject, html_body, text_body)
    log = EmailLog(contact_id=contact.id, template_id=template.id)
    db.add(log)

    try:
        await _send_via_smtp(msg)
        log.status = "sent"
        contact.last_contacted_at = datetime.now(timezone.utc)
        contact.contact_count += 1
        db.commit()
        logger.info("Manual school outreach sent → %s (%s, %s)",
                    email_key, school_name, location)
        return {"email": email_key, "status": "sent"}
    except BaseException as exc:  # catches CancelledError too (Python 3.8+)
        log.status = "failed"
        log.error_message = str(exc)
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.error("Manual school outreach FAILED → %s: %s", email_key, exc)
        return {"email": email_key, "status": "failed", "reason": str(exc) or type(exc).__name__}
