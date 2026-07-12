import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.email import ScrapeRunLog
from app.models.job import JobListing, JobSource
from app.models.email import EmailContact
from app.services.scraper import scrape_source
from app.services.email_service import dispatch_outreach
from app.services.school_scraper import scrape_nigerian_schools

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_scrape_cycle() -> None:
    """
    Core scrape + email dispatch cycle.
    1. Fetch all active job sources from DB.
    2. Scrape each source, persist new listings and contacts.
    3. Dispatch outreach emails to new contacts.
    """
    db: Session = SessionLocal()
    run_log = ScrapeRunLog(started_at=datetime.now(timezone.utc))
    db.add(run_log)
    db.commit()
    db.refresh(run_log)

    errors = []
    total_listings = 0
    total_emails = 0
    sources_run = 0

    try:
        active_sources = db.query(JobSource).filter(
            JobSource.is_active.is_(True)).all()
        sources_run = len(active_sources)

        for source in active_sources:
            source_cfg = {
                "name": source.name,
                "url": source.url,
                "scraper_type": source.scraper_type,
                "keywords": source.keywords or [],
                # Pass full selectors dict including _wait_for, _root etc.
                # scrape_source extracts private keys before calling parsers.
                "selectors": source.selectors or {},
            }
            try:
                if source.scraper_type == "school_scraper":
                    listings = await scrape_nigerian_schools()
                else:
                    listings = await scrape_source(source_cfg)
            except Exception as exc:
                msg = f"Source '{source.name}' failed: {exc}"
                logger.error(msg)
                errors.append(msg)
                continue

            for listing_data in listings:
                # Skip if URL already stored
                exists = db.query(JobListing).filter(
                    JobListing.url == listing_data["url"]).first()
                if exists:
                    continue

                job = JobListing(
                    source_id=source.id,
                    title=listing_data["title"],
                    company=listing_data.get("company"),
                    location=listing_data.get("location"),
                    url=listing_data["url"],
                    description=listing_data.get("description"),
                    raw_emails=listing_data.get("raw_emails", []),
                )
                db.add(job)
                db.flush()  # get job.id before adding contacts

                for email_addr in listing_data.get("raw_emails", []):
                    contact = EmailContact(listing_id=job.id, email=email_addr)
                    db.add(contact)
                    total_emails += 1

                total_listings += 1

            db.commit()

        # Trigger outreach for any new contacts
        sent = await dispatch_outreach(db)
        logger.info("Scrape cycle complete — listings: %d, emails found: %d, sent: %d",
                    total_listings, total_emails, sent)

    except Exception as exc:
        errors.append(str(exc))
        logger.exception("Unexpected error in scrape cycle")
    finally:
        run_log.ended_at = datetime.now(timezone.utc)
        run_log.sources_run = sources_run
        run_log.listings_found = total_listings
        run_log.emails_found = total_emails
        run_log.errors = errors
        db.commit()
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        run_scrape_cycle,
        trigger="interval",
        hours=settings.SCRAPE_INTERVAL_HOURS,
        id="scrape_cycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — interval: every %d hour(s)",
                settings.SCRAPE_INTERVAL_HOURS)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
