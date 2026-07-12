from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import EmailLog, ScrapeRunLog
from app.models.user import User
from app.schemas import EmailLogRead, ScrapeRunLogRead
from app.utils.auth import get_current_user

router = APIRouter(tags=["logs"])


# ─── Scrape run logs ──────────────────────────────────────────────────────────

@router.get("/scrape/logs", response_model=List[ScrapeRunLogRead])
def list_scrape_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(ScrapeRunLog).order_by(ScrapeRunLog.started_at.desc()).limit(limit).all()


# ─── Email logs ───────────────────────────────────────────────────────────────

@router.get("/emails/logs", response_model=List[EmailLogRead])
def list_email_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(limit).all()


@router.get("/emails/logs/{log_id}", response_model=EmailLogRead)
def get_email_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    log = db.get(EmailLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    return log
