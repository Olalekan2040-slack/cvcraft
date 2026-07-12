from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import JobListing, JobSource
from app.models.email import EmailLog, EmailContact, ScrapeRunLog, EmailTemplate
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_jobs = db.query(JobListing).count()
    total_sent = db.query(EmailLog).filter(EmailLog.status == "sent").count()
    total_failed = db.query(EmailLog).filter(
        EmailLog.status == "failed").count()
    active_sources = db.query(JobSource).filter(
        JobSource.is_active.is_(True)).count()
    total_contacts = db.query(EmailContact).count()
    last_run = db.query(ScrapeRunLog).order_by(
        ScrapeRunLog.started_at.desc()).first()
    return {
        "total_jobs": total_jobs,
        "total_emails_sent": total_sent,
        "total_emails_failed": total_failed,
        "active_sources": active_sources,
        "total_contacts": total_contacts,
        "last_scrape_at": last_run.started_at.isoformat() if last_run else None,
    }


@router.get("/applications/report")
def applications_report(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    logs = (
        db.query(EmailLog)
        .order_by(EmailLog.sent_at.desc())
        .limit(500)
        .all()
    )
    result = []
    for log in logs:
        contact = log.contact
        listing = contact.listing if contact else None
        template = log.template
        result.append({
            "id": log.id,
            "status": log.status,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "recipient_email": contact.email if contact else None,
            "job_title": listing.title if listing else None,
            "company": listing.company if listing else None,
            "location": listing.location if listing else None,
            "job_url": listing.url if listing else None,
            "template_name": template.name if template else None,
            "template_category": template.category if template else None,
            "error_message": log.error_message,
        })
    return result
