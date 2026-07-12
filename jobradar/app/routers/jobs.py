from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import JobListing
from app.models.user import User
from app.schemas import JobListingRead
from app.utils.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobListingRead])
def list_jobs(
    source_id: Optional[int] = Query(None),
    title: Optional[str] = Query(
        None, description="Case-insensitive partial match"),
    location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(JobListing)
    if source_id is not None:
        query = query.filter(JobListing.source_id == source_id)
    if title:
        query = query.filter(JobListing.title.ilike(f"%{title}%"))
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    return query.order_by(JobListing.scraped_at.desc()).offset(skip).limit(limit).all()


@router.get("/{job_id}", response_model=JobListingRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")
    return job
