from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── JobSource ───────────────────────────────────────────────────────────────

class JobSourceBase(BaseModel):
    name: str
    url: str
    scraper_type: str = "bs4"
    keywords: List[str] = []
    selectors: Optional[Dict[str, Any]] = None
    is_active: bool = True


class JobSourceCreate(JobSourceBase):
    pass


class JobSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    scraper_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    selectors: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class JobSourceRead(JobSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── JobListing ──────────────────────────────────────────────────────────────

class JobListingRead(BaseModel):
    id: int
    source_id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    url: str
    description: Optional[str]
    raw_emails: List[str]
    scraped_at: datetime

    model_config = {"from_attributes": True}


# ─── EmailContact ─────────────────────────────────────────────────────────────

class EmailContactRead(BaseModel):
    id: int
    listing_id: int
    email: str
    last_contacted_at: Optional[datetime]
    contact_count: int

    model_config = {"from_attributes": True}


# ─── EmailTemplate ────────────────────────────────────────────────────────────

class EmailTemplateBase(BaseModel):
    name: str
    category: Optional[str] = None
    subject: str
    html_body: str
    text_body: Optional[str] = None
    variables: List[str] = []
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateRead(EmailTemplateBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── EmailLog ────────────────────────────────────────────────────────────────

class EmailLogRead(BaseModel):
    id: int
    contact_id: int
    template_id: Optional[int]
    status: str
    error_message: Optional[str]
    sent_at: datetime

    model_config = {"from_attributes": True}


# ─── ScrapeRunLog ─────────────────────────────────────────────────────────────

class ScrapeRunLogRead(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    sources_run: int
    listings_found: int
    emails_found: int
    errors: List[str]

    model_config = {"from_attributes": True}


# ─── Auth ─────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
