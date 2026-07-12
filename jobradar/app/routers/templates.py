from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import EmailTemplate
from app.models.user import User
from app.schemas import EmailTemplateCreate, EmailTemplateRead, EmailTemplateUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/", response_model=EmailTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: EmailTemplateCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # If this template should be active, deactivate all others first
    if payload.is_active:
        db.query(EmailTemplate).update({"is_active": False})

    template = EmailTemplate(**payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/", response_model=List[EmailTemplateRead])
def list_templates(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(EmailTemplate).order_by(EmailTemplate.id.desc()).all()


@router.get("/{template_id}", response_model=EmailTemplateRead)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    template = db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=EmailTemplateRead)
def update_template(
    template_id: int,
    payload: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    template = db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Activating this template → deactivate all others
    if update_data.get("is_active"):
        db.query(EmailTemplate).filter(EmailTemplate.id !=
                                       template_id).update({"is_active": False})

    # Bump version on content changes
    content_fields = {"subject", "html_body", "text_body"}
    if content_fields & set(update_data.keys()):
        template.version += 1

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    template = db.get(EmailTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
