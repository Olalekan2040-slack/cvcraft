import asyncio
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.email_service import send_manual_school_email
from app.utils.auth import get_current_user

router = APIRouter(prefix="/schools", tags=["school-outreach"])


class SchoolContact(BaseModel):
    email: str
    school_name: str
    location: str = "Nigeria"


class SchoolApplyRequest(BaseModel):
    contacts: List[SchoolContact]


@router.post("/apply")
async def apply_to_schools(
    req: SchoolApplyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Send Tech / AI Instructor cover letter to a list of manually provided school emails.
    Each email is checked against the 30-day cooldown before sending.
    """
    results = []
    for item in req.contacts:
        result = await send_manual_school_email(
            db=db,
            email=item.email,
            school_name=item.school_name,
            location=item.location,
        )
        results.append(result)
        if result["status"] == "sent":
            await asyncio.sleep(settings.EMAIL_SEND_DELAY_SECONDS)

    sent = sum(1 for r in results if r["status"] == "sent")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] == "failed")

    return {
        "total": len(results),
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }
