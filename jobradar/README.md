# JobRadar

**Automated Job Scraping & Email Outreach Platform — Nigeria Edition**  
*N-TECH Info Systems Ltd · Sharafdeen Quadri*

---

## Overview

JobRadar is a FastAPI-powered backend that automatically:

1. Scrapes Nigerian job listing platforms on a configurable cron schedule
2. Extracts recruiter/HR email addresses from listings
3. Sends personalised outreach emails via SMTP
4. Maintains a full audit trail of every scrape run and email dispatch

Pre-configured Nigerian sources include **Jobberman**, **MyJobMag**, **HotNigerianJobs**, **NgCareers**, **Indeed Nigeria**, and **Teaching Nigeria** (for secondary-school tech teaching roles).

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd jobradar
cp .env.example .env
# Edit .env with your PostgreSQL URL and SMTP credentials
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

This will:
- Start a PostgreSQL 16 container
- Run `alembic upgrade head` to apply all migrations
- Start the FastAPI app on `http://localhost:8000`

### 3. Seed Nigerian job sources

```bash
# Inside the running app container:
docker-compose exec app python seed_nigerian_sources.py
```

### 4. Explore the API

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Running Locally (without Docker)

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Seed sources
python seed_nigerian_sources.py

# Start server
uvicorn app.main:app --reload
```

---

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register an operator account |
| POST | `/auth/token` | Obtain JWT token |
| GET | `/jobs` | List scraped job listings |
| POST | `/sources` | Add a job source |
| GET | `/sources` | List all job sources |
| PUT | `/sources/{id}` | Update a source |
| DELETE | `/sources/{id}` | Remove a source |
| POST | `/scrape/run` | Trigger an immediate scrape |
| GET | `/scrape/logs` | View scrape run history |
| POST | `/templates` | Create email template |
| GET | `/emails/logs` | View email dispatch logs |
| GET | `/health` | Service health check |

---

## Nigerian Job Platforms (Pre-Configured)

| Platform | Notes |
|----------|-------|
| Jobberman | Largest Nigerian job board |
| MyJobMag | Multi-sector listings |
| HotNigerianJobs | Entry & mid-level roles |
| NgCareers | Tech-heavy listings |
| Indeed Nigeria | Global board, NG-filtered |
| Teaching Nigeria | School vacancies — ICT / Computer Science / STEM teacher roles |

---

## Secondary School Tech Teaching

JobRadar includes a dedicated keyword set for **ICT / Computer Science / STEM teacher** vacancies in Nigerian secondary schools. Keywords include: `computer science teacher`, `ICT teacher`, `coding instructor`, `technology teacher`, `STEM teacher`, `programming teacher`.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SECRET_KEY` | JWT signing key | — |
| `SCRAPE_INTERVAL_HOURS` | How often to auto-scrape | `6` |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | SMTP username/email | — |
| `SMTP_PASSWORD` | SMTP app password | — |
| `EMAIL_SEND_DELAY_SECONDS` | Delay between sends | `5` |
| `EMAIL_COOLDOWN_DAYS` | Re-contact cooldown | `30` |
| `SENTRY_DSN` | Optional Sentry DSN | `` |

---

## Tech Stack

- **FastAPI** — REST API framework  
- **APScheduler** — cron scheduling  
- **SQLAlchemy + Alembic** — ORM and migrations  
- **httpx + BeautifulSoup4** — async scraping  
- **aiosmtplib** — async email dispatch  
- **python-jose + passlib** — JWT auth  
- **slowapi** — rate limiting  
- **PostgreSQL** — primary database  
- **Docker + Compose** — containerisation  

---

*© 2026 N-TECH Info Systems Ltd. Internal — Confidential.*
