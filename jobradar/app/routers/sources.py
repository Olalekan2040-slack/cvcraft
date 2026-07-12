from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import JobListing, JobSource
from app.models.user import User
from app.schemas import JobSourceCreate, JobSourceRead, JobSourceUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=JobSourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: JobSourceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(JobSource).filter(JobSource.url == payload.url).first():
        raise HTTPException(
            status_code=400, detail="A source with this URL already exists")
    source = JobSource(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/", response_model=List[JobSourceRead])
def list_sources(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(JobSource)
    if active_only:
        query = query.filter(JobSource.is_active.is_(True))
    return query.all()


@router.get("/{source_id}", response_model=JobSourceRead)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    source = db.get(JobSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.put("/{source_id}", response_model=JobSourceRead)
def update_source(
    source_id: int,
    payload: JobSourceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    source = db.get(JobSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    source = db.get(JobSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
