from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    scraper_type = Column(String(32), nullable=False,
                          default="bs4")  # bs4 | json_api
    # JSON list of keyword strings e.g. ["Python Developer", "FastAPI"]
    keywords = Column(JSON, nullable=False, default=list)
    # CSS selector config for bs4 scraper — stored as JSON dict
    selectors = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    listings = relationship(
        "JobListing", back_populates="source", cascade="all, delete-orphan")


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey(
        "job_sources.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=False)
    company = Column(String(256), nullable=True)
    location = Column(String(256), nullable=True)
    url = Column(String(512), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    # Raw emails extracted from the listing — JSON list of strings
    raw_emails = Column(JSON, nullable=False, default=list)
    scraped_at = Column(DateTime, server_default=func.now())

    source = relationship("JobSource", back_populates="listings")
    contacts = relationship(
        "EmailContact", back_populates="listing", cascade="all, delete-orphan")
