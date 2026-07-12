from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, JSON, func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class EmailContact(Base):
    __tablename__ = "email_contacts"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey(
        "job_listings.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(320), nullable=False, index=True)
    last_contacted_at = Column(DateTime, nullable=True)
    contact_count = Column(Integer, nullable=False, default=0)

    listing = relationship("JobListing", back_populates="contacts")
    email_logs = relationship(
        "EmailLog", back_populates="contact", cascade="all, delete-orphan")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    # Category used to auto-select the right letter per job title
    # e.g. "backend_developer", "tech_teacher", "general", etc.
    category = Column(String(64), nullable=True, index=True)
    subject = Column(String(256), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, nullable=True)
    # JSON list of variable names used in the template
    variables = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    email_logs = relationship("EmailLog", back_populates="template")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey(
        "email_contacts.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey(
        "email_templates.id", ondelete="SET NULL"), nullable=True)
    # sent | failed | pending
    status = Column(String(16), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, server_default=func.now())

    contact = relationship("EmailContact", back_populates="email_logs")
    template = relationship("EmailTemplate", back_populates="email_logs")


class ScrapeRunLog(Base):
    __tablename__ = "scrape_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    sources_run = Column(Integer, nullable=False, default=0)
    listings_found = Column(Integer, nullable=False, default=0)
    emails_found = Column(Integer, nullable=False, default=0)
    # JSON list of error strings
    errors = Column(JSON, nullable=False, default=list)
