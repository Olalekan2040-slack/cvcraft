
PRODUCT REQUIREMENTS DOCUMENT
JobRadar
Automated Job Scraping & Email Outreach Platform

Version: 1.0
Status: Draft
Author: Sharafdeen Quadri	Date: 02 April 2026
Stack: FastAPI · Python · SMTP · PostgreSQL
Organisation: N-TECH Info Systems Ltd


  1. Product Overview

1.1 Problem Statement
Job seekers and recruiters currently spend hours manually scouring multiple job boards, copying contact emails, and sending individual outreach messages. This process is repetitive, error-prone, and difficult to scale. There is no unified tool that automatically discovers relevant job listings, extracts recruiter contact information, and delivers personalised email notifications — all on a configurable schedule.

1.2 Product Vision
JobRadar is a FastAPI-powered backend service that periodically scrapes configurable job boards for targeted job listings, extracts any email contacts embedded in those listings, and automatically dispatches personalised outreach emails via SMTP — with full logging, scheduling, and a REST API management interface.

1.3 Goals & Success Metrics

Goal	Measurable Metric
Automate job discovery	Scrapes at least 3 job sources on a configurable cron schedule
Extract contact emails reliably	≥ 85% extraction accuracy on listings that contain emails
Deliver outreach emails	SMTP delivery success rate ≥ 95% per scheduled run
Prevent duplicate outreach	Zero duplicate emails sent to the same contact per 30-day window
Provide management API	Full CRUD endpoints for job sources, keywords, and email templates
Maintain audit trail	All scrape runs and email dispatches logged with timestamps and status

  1.4 Target Market — Nigeria Focus
JobRadar v1 is specifically scoped to the Nigerian job market. The following platforms will be pre-configured as default job sources:

| Platform | URL | Type | Notes |
|---|---|---|---|
| Jobberman | jobberman.com | HTML (BS4) | Largest Nigerian job board |
| MyJobMag | myjobmag.com | HTML (BS4) | Multi-sector Nigerian listings |
| HotNigerianJobs | hotnigerianJobs.com | HTML (BS4) | Entry & mid-level roles |
| NgCareers | ngcareers.com | HTML (BS4) | Tech-heavy listings |
| Indeed Nigeria | ng.indeed.com | HTML (BS4) | Global board with NG filter |
| Careers24 Nigeria | careers24.com/jobs/nigeria | HTML (BS4) | SA-origin, strong NG presence |
| GraduateNigeria | graduatenigeria.com | HTML (BS4) | Entry-level & graduate roles |
| NGO Jobs Africa | devnetjobsafrica.org | HTML (BS4) | NGO/development sector |

1.5 Secondary School Tech Teaching — Use Case Extension
Sharafdeen is also open to opportunities teaching technology courses (Computer Science, ICT, Coding/Programming, Robotics) in Nigerian secondary schools (JSS/SSS). JobRadar will include a dedicated keyword set and source list for this use case:

Keyword group: `"computer science teacher"`, `"ICT teacher"`, `"coding instructor"`, `"technology teacher"`, `"STEM teacher"`, `"programming teacher"`, `"secondary school teacher"`.

Additional sources for teaching roles:
| Platform | URL | Notes |
|---|---|---|
| TeachingNigeria | teachingnigeria.com | Education-specific job board |
| SchoolsNet Nigeria | schoolsnet.com.ng | School vacancies across Nigeria |
| eduBridge Nigeria | edubridgenigeria.com | EdTech & classroom roles |

  2. Stakeholders & Users

2.1 Primary Users
•	Developer / Operator — configures job sources, keywords, schedule, and email templates via the API.
•	Job Seeker (indirect) — benefits from automated outreach campaigns sent on their behalf.
•	Recruiter / HR Contact (recipient) — receives the outreach emails extracted from job listings.

2.2 Out of Scope
•	A consumer-facing frontend UI (API only for v1).
•	LinkedIn scraping (ToS restrictions — use their official API or job feed instead).
•	SMS or WhatsApp notification channels (future enhancement).

  3. Functional Requirements

3.1 Job Scraping Engine
3.1.1 Source Configuration
•	Operators can add, update, or delete job sources via API (target URL, scraper type, active flag).
•	Supported scraper types in v1: HTML/CSS selectors (BeautifulSoup), JSON API endpoints.
•	Each source has configurable keyword filters (e.g. 'Python Developer', 'FastAPI', 'Remote').

3.1.2 Scraping Logic
•	On each scheduled run, the engine iterates active sources and fetches listings matching configured keywords.
•	Extracted fields per listing: job title, company name, location, posting URL, description snippet, raw contact email(s).
•	Email extraction uses regex patterns across title, description, and any embedded mailto: links.
•	Listings are stored in the database; duplicates (same URL) are skipped.
•	Failed scrapes are retried up to 3 times with exponential backoff before marking as failed.

3.2 Scheduler
•	Built using APScheduler (AsyncIOScheduler) integrated into the FastAPI lifespan context.
•	Default schedule: every 6 hours (configurable via environment variable SCRAPE_INTERVAL_HOURS).
•	Operators can also trigger an immediate scrape run via a POST /scrape/run endpoint.
•	A scrape run log is created for every execution, recording: start time, end time, sources attempted, listings found, emails extracted, errors.

3.3 Email Outreach Engine
3.3.1 Email Template System
•	Operators create and manage email templates via API (subject, HTML body, plain text fallback).
•	Templates support variable interpolation: {{job_title}}, {{company}}, {{location}}, {{applicant_name}}, {{applicant_skills}}.
•	Templates are versioned; the active template is used per run.

3.3.2 Sending Logic
•	After each scrape run, newly discovered emails (not yet contacted in the last 30 days) are queued for sending.
•	Emails are dispatched via Python's smtplib using configurable SMTP credentials (supports Gmail, Outlook, custom SMTP).
•	Sending is rate-limited to avoid spam detection (configurable delay between sends, default: 5 seconds).
•	All outbound emails are logged with: recipient, template used, job listing linked, status (sent/failed), timestamp.

3.3.3 Deduplication
•	Before sending, the system checks if the same email was contacted in the last 30 days for the same or related job keyword.
•	A cooldown_days setting is configurable per campaign (default: 30 days).

3.4 REST API Endpoints

Method	Endpoint	Description
GET	/jobs	List all scraped jobs with filters
GET	/jobs/{id}	Get a single job listing detail
POST	/sources	Add a new job source
GET	/sources	List all configured job sources
PUT	/sources/{id}	Update a job source
DELETE	/sources/{id}	Remove a job source
POST	/scrape/run	Trigger an immediate scrape run
GET	/scrape/logs	List scrape run history
POST	/templates	Create an email template
GET	/templates	List all email templates
PUT	/templates/{id}	Update an email template
GET	/emails/logs	List all outbound email logs
GET	/emails/logs/{id}	Get details of a specific email send
POST	/auth/token	Obtain a JWT access token
GET	/health	Service health check

  4. Non-Functional Requirements

4.1 Performance
•	API response time: < 300ms for all read endpoints (p95).
•	Scrape run for up to 5 sources: completes within 10 minutes.
•	Concurrent email dispatch: handled via asyncio tasks, not blocking the API.

4.2 Security
•	All API endpoints (except /health) protected by JWT Bearer authentication.
•	SMTP credentials stored in environment variables only — never committed to source control.
•	Rate limiting on POST endpoints using slowapi (100 req/min per IP).
•	Input sanitisation and Pydantic validation on all request bodies.

4.3 Reliability & Resilience
•	Graceful handling of scrape failures — one failing source does not abort the full run.
•	SMTP connection failures are retried up to 3 times before logging as failed.
•	Database transactions used for all writes to ensure consistency.

4.4 Observability
•	Structured JSON logging with log levels (INFO, WARNING, ERROR) using Python's logging module.
•	Each scrape run and email dispatch is persisted to the database for audit and replay.
•	Optional integration with Sentry for error tracking (configured via SENTRY_DSN env var).

4.5 Deployability
•	Fully containerised with Docker and Docker Compose (app + PostgreSQL + optional Redis).
•	Environment configured entirely via .env file — no hard-coded values.
•	Compatible with deployment on Railway, Render, AWS EC2 (Sharafdeen's existing preference).

  5. System Architecture

JobRadar follows a clean layered architecture pattern consistent with production FastAPI projects:

┌─────────────────────────────────────────────────┐
│              FastAPI Application Layer           │
│  Routers · Pydantic Schemas · JWT Auth           │
├─────────────────────────────────────────────────┤
│              Service Layer                       │
│  ScraperService · EmailService · JobService      │
├──────────────────┬──────────────────────────────┤
│  APScheduler     │  SMTP (smtplib/aiosmtplib)   │
│  (cron trigger)  │  BeautifulSoup / httpx       │
├──────────────────┴──────────────────────────────┤
│              Data Layer                          │
│  SQLAlchemy ORM · Alembic Migrations             │
├─────────────────────────────────────────────────┤
│  PostgreSQL Database                             │
└─────────────────────────────────────────────────┘

5.1 Tech Stack

Backend
•	FastAPI — REST API framework
•	APScheduler — cron job scheduling
•	SQLAlchemy + Alembic — ORM & migrations
•	httpx — async HTTP client for scraping
•	BeautifulSoup4 — HTML parsing
•	aiosmtplib — async SMTP email sending
•	python-jose — JWT authentication
•	slowapi — rate limiting	Infrastructure
•	PostgreSQL — primary database
•	Docker + Docker Compose
•	Pydantic v2 — data validation
•	python-dotenv — env config
•	Alembic — DB migration management
•	Sentry SDK (optional) — error tracking
•	Render / AWS EC2 — deployment target

  6. Data Models

6.1 Core Database Tables

Table	Key Fields	Purpose
job_sources	id, name, url, scraper_type, keywords, is_active	Stores configured job board sources and their keyword filters
job_listings	id, source_id, title, company, location, url, description, raw_emails, scraped_at	Stores every unique job listing discovered
email_contacts	id, listing_id, email, last_contacted_at, contact_count	Tracks all discovered email contacts and outreach history
email_templates	id, name, subject, html_body, text_body, variables, is_active, version	Stores reusable email templates with variable placeholders
email_logs	id, contact_id, template_id, status, error_message, sent_at	Audit log of every email dispatch attempt
scrape_run_logs	id, started_at, ended_at, sources_run, listings_found, emails_found, errors	Audit log of each scheduled or manual scrape run
users	id, username, hashed_password, is_active, created_at	Operator accounts for API authentication

  7. Feature Priority & Phasing

Feature	Priority	MVP	Phase 2
Job source CRUD API	Critical	✅ Yes	—
Keyword-based scraping (BS4)	Critical	✅ Yes	—
Email extraction via regex	Critical	✅ Yes	—
APScheduler cron integration	Critical	✅ Yes	—
SMTP email dispatch	Critical	✅ Yes	—
Deduplication (30-day window)	Critical	✅ Yes	—
Email template CRUD	High	✅ Yes	—
JWT authentication	High	✅ Yes	—
Scrape & email audit logs	High	✅ Yes	—
Rate limiting (slowapi)	Medium	✅ Yes	—
Docker / Compose setup	Medium	✅ Yes	—
Playwright/Selenium scraping	Medium	—	✅ Yes
Admin dashboard (HTML/React)	Low	—	✅ Yes
Email open/click tracking	Low	—	✅ Yes
Multi-user campaigns	Low	—	✅ Yes
Webhook notifications	Low	—	✅ Yes

  8. Recommended Project Structure

jobradar/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── job.py
│   │   ├── email.py
│   │   └── user.py
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # FastAPI routers
│   │   ├── jobs.py
│   │   ├── sources.py
│   │   ├── templates.py
│   │   ├── emails.py
│   │   └── auth.py
│   ├── services/            # Business logic
│   │   ├── scraper.py
│   │   ├── email_service.py
│   │   └── scheduler.py
│   └── utils/
│       ├── email_extractor.py
│       └── auth.py
├── alembic/                 # DB migrations
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

  9. Risks & Mitigations

Risk	Likelihood	Mitigation
Job board blocks scraper IP	High	Use rotating user-agents, respect robots.txt, add delays between requests
Emails extracted are invalid or role-based	Medium	Validate format with regex; filter known no-reply patterns
SMTP provider flags messages as spam	Medium	Use SPF/DKIM configured domain, warm up sending volume gradually
Target site HTML structure changes	High	Abstract selectors into source config; add change-detection alerts
Rate-limit abuse by API consumers	Low	JWT auth + slowapi rate limiting on all write endpoints
GDPR / legal concerns on cold outreach	Medium	Include unsubscribe link in every email; honour opt-out requests

  10. Suggested Build Timeline (Solo Developer)

Week	Milestone	Deliverables
Week 1	Project Bootstrap	FastAPI skeleton, DB models, Alembic migrations, Docker Compose, JWT auth, health endpoint
Week 2	Scraping Engine	job_sources CRUD, httpx + BS4 scraper, email regex extractor, job_listings persistence
Week 3	Scheduler + Email	APScheduler integration, SMTP email service, template system, deduplication logic
Week 4	Logging + Polish	Scrape & email audit logs, rate limiting, .env config, error handling, README documentation
Week 5	Testing + Deploy	Unit & integration tests (pytest), Docker image build, deployment to Render/AWS EC2

  11. Acceptance Criteria (MVP)

The MVP is considered complete when all of the following are verified:

1.	A scheduled scrape run executes automatically every N hours without manual intervention.
2.	At least 2 job sources are scraped; listings are persisted to the database without duplicates.
3.	Email addresses embedded in job listings are extracted and stored in email_contacts.
4.	A personalised email is dispatched via SMTP to each new contact using the active template.
5.	The same email address is not contacted twice within the configured cooldown window.
6.	All scrape runs and email dispatches are logged with status, timestamps, and error details.
7.	All write API endpoints return 401 without a valid JWT token.
8.	The application starts cleanly via docker-compose up with only a .env file required.

  Document Control

Document Owner: Sharafdeen Quadri
Organisation: N-TECH Info Systems Ltd
Version: 1.0 — Initial Release	Created: 02 April 2026
Review Cycle: Per sprint / on major scope change
Classification: Internal — Confidential

This document supersedes all prior verbal discussions regarding the JobRadar project scope. Any changes to requirements after sign-off must go through a formal change request and will update the version number.
