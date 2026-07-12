# CVCraft — AI-Powered Resume Builder

> Build stunning, ATS-friendly resumes in minutes. Powered by Gemini AI, matched to real remote jobs.

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.x-green?logo=django)](https://djangoproject.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-Welcome-brightgreen)](CONTRIBUTING.md)

---

## What is CVCraft?

CVCraft is a free, open-source resume builder that helps job seekers:

- **Build** professional CVs using 10+ beautiful templates
- **Import** an existing CV (PDF or Word) and have it parsed automatically
- **Polish** their CV text using Gemini AI paraphrasing
- **Analyse** their resume with full AI feedback and an improvement score
- **Find Jobs** via the built-in Job Radar — a live job feed from 7 remote job boards, ranked by ATS score against the user's own CV
- **Filter** jobs by country and detect tech stack mismatches instantly

---

## Features

| Feature | Details |
|---|---|
| 10 Resume Templates | Classic, Modern, Executive, Creative, Elegant, Technical, Bold, Clean, Timeline, Student |
| AI Polish | Rewrite any text section in a professional tone (Gemini 2.0 Flash) |
| AI CV Analysis | Full resume review with score, strengths, improvements, missing sections |
| CV Import | Upload PDF or DOCX — AI or regex parser fills the builder automatically |
| Job Radar | Scrapes 7 job boards, ranks every listing by ATS score vs your CV |
| Stack Intelligence | Detects tech stack mismatches (e.g. Java job vs Python developer) |
| Location Filter | Pick target countries; remote/worldwide jobs always visible |
| ATS Score Breakdown | Per-job skills, title, tech, and experience score breakdown |
| Save & Dismiss | Bookmark jobs for later; dismiss irrelevant ones |
| Keep-Alive Ping | 30-second client ping prevents Render cold starts |
| Dark UI | TailwindCSS dark theme, gold accent, fully responsive |

---

## Tech Stack

**Backend**
- Python 3.13 / Django 6.x
- django-allauth (email authentication)
- Gemini 2.0 Flash via `google-generativeai`
- httpx + BeautifulSoup4 for job scraping
- pdfplumber + python-docx for CV parsing

**Frontend**
- TailwindCSS (CDN) + custom dark design system
- Alpine.js (reactive UI without a heavy build step)
- HTMX (partial page updates)
- Lucide icons

**Database & Hosting**
- PostgreSQL (Aiven free tier for production) / SQLite for local dev
- Render (free web service)
- WhiteNoise for static file serving

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Install

```bash
git clone https://github.com/Olalekan2040-slack/cvcraft.git
cd cvcraft
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=True

# Optional — enables AI features (free tier at ai.google.dev)
GEMINI_API_KEY=your-gemini-api-key

# Optional — defaults to SQLite for local dev
DATABASE_URL=sqlite:///db.sqlite3

# Optional — comma-separated list
ALLOWED_HOSTS=localhost,127.0.0.1
```

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key — any random string for dev |
| `DEBUG` | No | `True` for dev, `False` for production |
| `GEMINI_API_KEY` | No | Enables AI polish & analysis. App works without it (regex fallback) |
| `DATABASE_URL` | No | Postgres URL for production. Defaults to SQLite locally |
| `ALLOWED_HOSTS` | No | Comma-separated allowed hostnames |

### 3. Database & Run

```bash
python manage.py migrate
python manage.py runserver
```

Visit **http://localhost:8000** — sign up and start building.

### 4. Populate Job Radar (optional)

```bash
python manage.py scrape_jobs
```

This scrapes 7 remote job boards and populates the Job Radar feed. Takes ~60 seconds. On production (Render), this runs automatically on first deploy.

---

## Deployment (Render + Aiven)

1. Fork this repo
2. Create a free [Aiven](https://aiven.io) PostgreSQL instance — copy the connection URL
3. Create a new **Web Service** on [Render](https://render.com), connect your fork
4. Set these environment variables in Render's dashboard:

| Key | Value |
|---|---|
| `DATABASE_URL` | Your Aiven Postgres connection string |
| `GEMINI_API_KEY` | Your Google AI Studio key |
| `DEBUG` | `False` |
| `SECRET_KEY` | A strong random string |

5. Deploy — migrations and first job scrape run automatically via `wsgi.py`

---

## Project Structure

```
cvcraft/
├── accounts/               # User registration, login, profile
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── billing/                # Pricing page (app is currently free)
│   └── views.py
│
├── core/                   # Landing page, about, ping endpoint
│   ├── views.py
│   ├── urls.py
│   └── management/commands/
│
├── jobs/                   # Job Radar — scraping, ATS, feed
│   ├── models.py           # JobListing, UserJobInteraction, JobScrapeLog, JobPreference
│   ├── views.py            # feed, trigger_scrape, save_preferences, …
│   ├── urls.py
│   ├── migrations/
│   ├── services/
│   │   ├── ats.py          # ATS scoring + stack intelligence
│   │   ├── keywords.py     # Resume keyword extraction
│   │   └── scraper.py      # 7-source job scraper (httpx + BS4)
│   └── templates/jobs/
│       └── feed.html
│
├── resumes/                # Resume builder — core app
│   ├── models.py           # Resume model (JSON data field)
│   ├── views.py            # builder, preview, upload_cv, ai_generate, ai_analyze, …
│   ├── urls.py
│   └── management/commands/
│
├── templates/
│   ├── base.html           # Global layout (navbar, footer, flash messages)
│   ├── components/
│   │   ├── navbar.html
│   │   └── footer.html
│   ├── resume_templates/   # 10 printable CV templates
│   │   ├── modern.html
│   │   ├── classic.html
│   │   └── … (8 more)
│   ├── resumes/
│   │   ├── builder.html    # Main resume editor (Alpine.js)
│   │   ├── dashboard.html  # User's CV list
│   │   └── print_page.html # PDF wrapper
│   └── core/
│       └── landing.html
│
├── static/
│   ├── css/main.css
│   ├── js/
│   │   ├── builder.js      # Builder Alpine.js component
│   │   └── main.js
│   └── images/
│       └── templates/      # Template preview screenshots
│
├── cvcraft/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py             # Auto-migrate + auto-scrape on startup
│
├── requirements.txt
├── render.yaml             # Render deployment config
└── .env                    # Local secrets (not committed)
```

---

## Architecture Decisions

**Why JSON field for resume data?**
Resume structure varies wildly between templates and users. A single `data = JSONField()` on the Resume model is far simpler than a normalised schema with 8 tables — and fast enough for this use case.

**Why background threads for scraping?**
Scraping 7 job boards takes 60–90 seconds. Running it in a daemon thread from the HTTP request allows the server to respond immediately while the scrape proceeds. A `JobScrapeLog` record guards against double-triggers.

**Why no Celery?**
Celery adds significant operational complexity (broker, worker process, deployment config). For a small open-source project on a free Render tier, a threading approach is simpler and effective.

**Why django-allauth instead of custom auth?**
Email verification, password reset, and account management out of the box. The `socialaccount` module is intentionally disabled to keep things simple.

---

## API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/dashboard/` | User's saved resumes |
| GET | `/resumes/builder/<id>/` | Resume editor |
| GET | `/resumes/preview/<id>/` | Iframe-embeddable preview |
| GET | `/resumes/print/<id>/` | Print/PDF page |
| POST | `/resumes/ai/generate/` | AI text improvement (paraphrase, summary, etc.) |
| POST | `/resumes/ai/analyze/` | Full CV analysis and scoring |
| POST | `/resumes/upload/` | Import CV from PDF or DOCX |
| GET | `/jobs/` | Job Radar feed |
| POST | `/jobs/scrape/trigger/` | Start background job scrape |
| GET | `/jobs/scrape/status/` | Scrape progress + job count |
| POST | `/jobs/preferences/` | Save user location preferences |
| POST | `/jobs/<id>/save/` | Toggle save a job listing |
| POST | `/jobs/<id>/dismiss/` | Dismiss a job listing |
| GET | `/ping/` | Keep-alive endpoint |

---

## Contributing

Contributions are welcome and appreciated! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, conventions, and how to open a pull request.

**Good first issues:**
- Add more job board sources to `jobs/services/scraper.py`
- Add a new resume template in `templates/resume_templates/`
- Improve ATS scoring weights in `jobs/services/ats.py`
- Add email notifications for new job matches
- Write tests (currently minimal coverage)

---

## License

MIT — see [LICENSE](LICENSE).

---

## Credits

Built and designed by **[Quaddev](https://quaddev.onrender.com)**.

> Free to use. Free to fork. Free forever.
