"""
scraper.py
==========
Tri-mode job scraper with full anti-ban hardening.

scraper_type values:
  "bs4"        — httpx + BeautifulSoup  (fast; for static/HTML sites)
  "json_api"   — httpx + JSON parse     (Remote OK and similar open APIs)
  "playwright" — headless Chromium + playwright-stealth
                 (JS/React/Vue-rendered sites, bot-protected sources)

Anti-ban measures
-----------------
  • playwright-stealth (hides navigator.webdriver, fixes Canvas/WebGL fingerprints,
    patches plugins list, mocks chrome runtime, etc.)
  • Rotating realistic Chrome/Firefox/Safari User-Agent strings
  • Random viewport (1280px – 1920px wide)
  • Locale / timezone spoofing (en-US / America/New_York)
  • Blocking images, media, and font resources (faster + smaller fingerprint)
  • Human-like scroll (slow incremental) to trigger lazy-loaded cards
  • Random human delay (1.5–4 s) before content grab
  • Per-domain asyncio.Semaphore — max 1 concurrent request per domain
  • Exponential backoff on HTTP 4xx / network errors (bs4 mode)
  • Per-source retry: Playwright sources retried up to 2 times before giving up
  • Multi-keyword URL pagination for search-based sources (Indeed, LinkedIn,
    Jobberman) — iterates top keyword groups to maximise job coverage
  • URL-level deduplication across all pages scraped per source
"""
import logging
import random
import asyncio
import json as _json
import urllib.parse
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlencode, urlparse

import httpx
from bs4 import BeautifulSoup

from app.utils.email_extractor import extract_emails

logger = logging.getLogger(__name__)

# ── Per-domain concurrency cap — max 1 concurrent request per domain ─────────
_DOMAIN_SEMAPHORES: Dict[str, asyncio.Semaphore] = {}


def _domain_sem(url: str) -> asyncio.Semaphore:
    domain = urlparse(url).netloc
    if domain not in _DOMAIN_SEMAPHORES:
        _DOMAIN_SEMAPHORES[domain] = asyncio.Semaphore(1)
    return _DOMAIN_SEMAPHORES[domain]


# ── Master keyword list covering every target role ───────────────────────────
_ALL_KEYWORDS: List[str] = [
    # Backend / Python
    "backend engineer", "backend developer", "python developer",
    "software engineer", "software engineer backend",
    # Full-Stack
    "full-stack developer", "full-stack engineer",
    "full stack developer", "full stack engineer",
    # Frameworks
    "django developer", "fastapi developer", "api developer",
    # AI / ML / Data
    "ai application developer", "machine learning engineer",
    "data analyst",
    # EdTech
    "educational technology", "edtech developer",
    # Teaching / Training
    "software engineering instructor", "python instructor",
    "full-stack development trainer",
    # Lead / Management
    "technical lead", "tech hub manager", "technology program manager",
]

# ── Condensed search terms for URL-based keyword pagination ──────────────────
# Used by Indeed, LinkedIn, Jobberman search URLs. Keep small to avoid
# hammering the same site — broad terms yield the most relevant results.
_SEARCH_TERMS = [
    "backend engineer python",
    "python developer",
    "software engineer",
    "full stack developer",
    "django developer",
    "fastapi developer",
    "data analyst python",
    "machine learning engineer",
    "software engineering instructor",
    "technical lead",
]

# ── Rotating realistic User-Agents ───────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
    {"width": 1536, "height": 864},
]

MAX_RETRIES = 3
BASE_BACKOFF = 2.0   # seconds (HTTP mode)
PW_RETRIES = 2     # extra retries for Playwright sources


# ── Job listing platform definitions ─────────────────────────────────────────
#
# Each source dict keys:
#   name         — display name
#   url          — base/start URL
#   scraper_type — "bs4" | "json_api" | "playwright"
#   keywords     — filter results by title/description
#   selectors    — CSS/field map. For playwright/bs4: listing_container, title,
#                  company, location, url, description.
#                  For playwright sources, include "_wait_for" key with the CSS
#                  selector to wait for before grabbing page content.
#                  For json_api sources, include "_root" to name the array key
#                  inside a dict-wrapper response (e.g. "jobs").
#
NIGERIAN_SOURCES: List[Dict[str, Any]] = [

    # ── LOCAL NIGERIAN BOARDS ─────────────────────────────────────────────

    # 1. MyJobMag — upgraded to Playwright (site now JS-rendered)
    {
        "name": "MyJobMag",
        "url": "https://www.myjobmag.com/jobs?category=it-telecom",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "div[class*='job'], li[class*='job'], article",
            "listing_container": "li.job-list-li, div[class*='job-item'], article[class*='job']",
            "title": "li.mag-b h2 a, h2 a, h3 a, a[class*='title']",
            "company": "li.job-logo a img, span[class*='company'], a[class*='company']",
            "location": "li.job-item ul li, span[class*='location']",
            "url": "li.mag-b h2 a, h2 a, h3 a",
            "description": "li.job-desc, p[class*='desc'], div[class*='snippet']",
        },
    },

    # 3. HotNigerianJobs — upgraded to Playwright (site now blocks scrapers)
    {
        "name": "HotNigerianJobs",
        "url": "https://www.hotnigerianjobs.com",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "div.jobheader, div[class*='job'], article",
            "listing_container": "div.jobheader, div[class*='job-item'], article[class*='job']",
            "title": "h1 a, h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], p[class*='company']",
            "location": "span[class*='location'], p[class*='location']",
            "url": "h1 a, h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='snippet']",
        },
    },

    # 4. Remotive — public JSON API (replaces dead joblist.ng)
    #    Response shape: {"jobs": [{title, company_name, candidate_required_location,
    #    url, description, ...}]}
    {
        "name": "Remotive",
        "url": "https://remotive.com/api/remote-jobs?category=software-dev&limit=200",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_root": "jobs",
            "title": "title",
            "company": "company_name",
            "location": "candidate_required_location",
            "url": "url",
            "description": "description",
        },
    },

    # 5. Indeed Nigeria — Playwright + stealth; confirmed 16 cards per search
    #    Container: .result  |  Title: h2.jobTitle a span  |  URL: a[data-jk]
    #    Company: span[data-testid='company-name']  |  Location: div[data-testid='text-location']
    {
        "name": "Indeed Nigeria",
        "url": "https://ng.indeed.com/jobs?q=software+developer&l=Nigeria",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "[data-jk]",
            "listing_container": ".result",
            "title": "h2.jobTitle a span, h2.jobTitle span",
            "company": "span[data-testid='company-name']",
            "location": "div[data-testid='text-location']",
            "url": "a[data-jk]",
            "description": "div.job-snippet, div[class*='snippet']",
        },
    },

    # 6. Working Nomads — public JSON API (replaces dead teachingnigeria.com)
    #    Response shape: [{title, company_name, location, url, description, ...}]
    {
        "name": "WorkingNomads",
        "url": "https://www.workingnomads.com/api/exposed_jobs/?category=development",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "title": "title",
            "company": "company_name",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },

    # 7. Himalayas — public JSON API (replaces dead nigerianjobseeker.com)
    #    Response shape: {"jobs": [{title, companyName, applicationLink,
    #    locationRestrictions (list), description, ...}]}
    {
        "name": "Himalayas",
        "url": "https://himalayas.app/jobs/api?limit=200",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_root": "jobs",
            "title": "title",
            "company": "companyName",
            # value is a list — handled in _parse_json_api
            "location": "locationRestrictions",
            "url": "applicationLink",
            "description": "description",
        },
    },

    # ── REMOTE / GLOBAL BOARDS ────────────────────────────────────────────

    # 8. We Work Remotely — CONFIRMED STATIC HTML; 236 listings per page
    #    Container: li.new-listing-container  |  URL: a.listing-link--unlocked (relative)
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com/remote-jobs",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "li.new-listing-container",
            "title": "span.new-listing__header__title__text",
            "company": "p.new-listing__company-name",
            "location": "p.new-listing__company-headquarters",
            "url": "a.listing-link--unlocked",
            "description": "span.new-listing__header__title__text",
        },
    },

    # 9. Remote OK — public JSON API; array of objects (first element is legal notice)
    {
        "name": "Remote OK",
        "url": "https://remoteok.com/api",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "title": "position",
            "company": "company",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },

    # 10. Arbeitnow — public JSON API; 100 remote+tech jobs per page
    #    Response shape: {"data": [{title, company_name, description, url, location, remote, tags}]}
    {
        "name": "Arbeitnow",
        "url": "https://arbeitnow.com/api/job-board-api",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_root": "data",
            "title": "title",
            "company": "company_name",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },

    # 11. Jobicy — public JSON API; remote jobs filtered by dev tag
    #    Response shape: {"jobs": [{jobTitle, companyName, jobGeo, url, jobDescription}]}
    {
        "name": "Jobicy",
        "url": "https://jobicy.com/api/v2/remote-jobs?count=50&tag=developer",
        "scraper_type": "json_api",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_root": "jobs",
            "title": "jobTitle",
            "company": "companyName",
            "location": "jobGeo",
            "url": "url",
            "description": "jobDescription",
        },
    },

    # 12. DynamiteJobs — React/Tailwind SPA; Playwright; dev-category URL
    #    Container: div[class*='space-y-1'][class*='gray'] (20 per page)
    #    Title+URL: a[href*='/remote-job/']  |  Company: non-job company link
    {
        "name": "DynamiteJobs",
        "url": "https://dynamitejobs.com/category/remote-development-jobs",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "a[href*='/remote-job/']",
            "listing_container": "div[class*='space-y-1'][class*='gray']",
            "title": "a[href*='/remote-job/']",
            "company": "a[href*='/company/']:not([href*='/remote-job/'])",
            "location": "span",
            "url": "a[href*='/remote-job/']",
            "description": "a[href*='/remote-job/']",
        },
    },

    # ── NIGERIAN BOARDS (EXPANDED) ─────────────────────────────────────────

    # 13. Jobberman — Nigeria's largest job board; React/SPA (Playwright)
    #     Container: div[class*='job-listing'] or article[class*='job']
    #     Title: h3 a, h2 a  |  Company: span[class*='company']  |  URL: a[href*='/job/']
    {
        "name": "Jobberman",
        "url": "https://www.jobberman.com/jobs?q=software+developer&l=Nigeria",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "article, div[class*='job'], div[class*='listing']",
            "listing_container": "article[class*='job'], div[class*='job-listing'], div[class*='job-summary']",
            "title": "h3 a, h2 a, a[class*='title']",
            "company": "span[class*='company'], p[class*='company'], a[class*='company']",
            "location": "span[class*='location'], p[class*='location']",
            "url": "h3 a, h2 a, a[class*='title']",
            "description": "p[class*='description'], span[class*='snippet'], div[class*='summary']",
        },
    },

    # 14. NgCareers — static HTML; category /it/ for tech jobs
    {
        "name": "NgCareers",
        "url": "https://www.ngcareers.com/jobs?q=software+developer",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div.job, article.job, li.job, div[class*='job-item']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='company']",
            "location": "span[class*='location'], span[class*='city']",
            "url": "h2 a, h3 a, a[class*='title']",
            "description": "div[class*='description'], p[class*='summary']",
        },
    },

    # 15. LinkedIn Jobs — JS-heavy SPA; Playwright; Nigeria filter
    #     Public search page (no login required for listings)
    {
        "name": "LinkedIn Jobs",
        "url": "https://www.linkedin.com/jobs/search/?keywords=software+developer&location=Nigeria&f_TPR=r2592000",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "ul.jobs-search__results-list, div.jobs-search-results-list",
            "listing_container": "li.jobs-search-results__list-item, div.base-card",
            "title": "h3.base-search-card__title, span.job-search-card__title, a.base-card__full-link",
            "company": "h4.base-search-card__subtitle, a[class*='company']",
            "location": "span.job-search-card__location, span[class*='location']",
            "url": "a.base-card__full-link, h3 a",
            "description": "p.job-search-card__snippet, div[class*='description']",
        },
    },

    # 16. JobGurus Nigeria — bs4; use homepage/jobs listing
    {
        "name": "JobGurus Nigeria",
        "url": "https://www.jobgurus.com.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div.job, article, div[class*='job-list'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='employer']",
            "location": "span[class*='location'], span[class*='city']",
            "url": "h2 a, h3 a",
            "description": "p, div[class*='desc'], div[class*='snippet']",
        },
    },

    # 17. JobsGivers — static/PHP site; general listings
    {
        "name": "JobsGivers",
        "url": "https://www.jobsgivers.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='excerpt'], div[class*='content']",
        },
    },

    # 18. Jobzilla Nigeria — static HTML; tech category
    {
        "name": "Jobzilla",
        "url": "https://www.jobzilla.ng/jobs?category=it-telecom",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 19. Delon Jobs — Nigerian board; tech/remote roles
    {
        "name": "Delon Jobs",
        "url": "https://jobs.delon.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article, li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p, div[class*='desc']",
        },
    },

    # 20. Fuzu Nigeria — AI-matched platform; React SPA (Playwright)
    {
        "name": "Fuzu Nigeria",
        "url": "https://www.fuzu.com/nigeria/job-listings?industry=Information+Technology",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "div[class*='job'], article[class*='job']",
            "listing_container": "div[class*='job-item'], div[class*='job-card'], article[class*='job']",
            "title": "h3 a, h2 a, a[class*='title'], span[class*='title']",
            "company": "span[class*='company'], p[class*='company']",
            "location": "span[class*='location'], p[class*='location']",
            "url": "h3 a, h2 a, a[class*='title']",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 21. Careers24 Nigeria — education & corporate listings; bs4
    {
        "name": "Careers24 Nigeria",
        "url": "https://www.careers24.com.ng/jobs",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article, li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='snippet']",
        },
    },

    # 22. Nairaland Jobs — community forum; new posts daily; bs4
    #     Each post is a <tr> row; title link text is "Job Title At Company"
    {
        "name": "Nairaland Jobs",
        "url": "https://www.nairaland.com/jobs",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "td[class*='bold'], tr[id*='top']",
            "title": "a[class*='']",
            "company": "",
            "location": "",
            "url": "a[class*='']",
            "description": "a[class*='']",
        },
    },

    # 23. Jiji.ng Jobs — marketplace + job listings; Playwright (React)
    {
        "name": "Jiji.ng Jobs",
        "url": "https://www.jiji.ng/jobs",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "div[class*='listing'], article[class*='ad']",
            "listing_container": "article[class*='listing'], div[class*='listing-item'], li[class*='listing']",
            "title": "h3 a, h2 a, a[class*='title']",
            "company": "span[class*='company'], p[class*='author']",
            "location": "span[class*='location']",
            "url": "h3 a, h2 a, a[href*='/jobs/']",
            "description": "p[class*='desc'], span[class*='snippet']",
        },
    },

    # 24. Jobstoday Nigeria — daily alerts; bs4
    {
        "name": "Jobstoday Nigeria",
        "url": "https://www.jobstoday.com.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 25. NigeriaJob — recruitment listings; bs4
    {
        "name": "NigeriaJob",
        "url": "https://www.nigeriajob.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article, li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p, div[class*='desc']",
        },
    },

    # 26. CareerJET Nigeria — job aggregator scraping 100+ sources
    {
        "name": "CareerJET Nigeria",
        "url": "https://www.careerjet.com.ng/jobs?s=software+developer&l=Nigeria",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "article.job, li.job",
            "title": "h2 a",
            "company": "span[class*='company'], p.company",
            "location": "ul.location li",
            "url": "h2 a",
            "description": "div.desc, p.desc",
        },
    },

    # 27. Glassdoor — comprehensive platform; Playwright (JS-heavy + login-wall)
    {
        "name": "Glassdoor",
        "url": "https://www.glassdoor.com/Job/nigeria-software-developer-jobs-SRCH_IL.0,7_IN178_KO8,26.htm",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "li[data-test='jobListing'], div[class*='JobCard']",
            "listing_container": "li[data-test='jobListing'], div[class*='JobCard'], div[class*='jobCard']",
            "title": "a[class*='JobCard_jobTitle'], span[class*='title']",
            "company": "span[class*='EmployerProfile'], span[class*='employer']",
            "location": "div[class*='JobCard_location'], span[class*='location']",
            "url": "a[class*='JobCard_jobTitle'], a[class*='JobCard']",
            "description": "div[class*='JobCard_jobDescriptionSnippet']",
        },
    },

    # 28. Snaphunt — AI-matched; growing Nigeria focus; Playwright (React)
    {
        "name": "Snaphunt",
        "url": "https://snaphunt.com/jobs?locations=Nigeria",
        "scraper_type": "playwright",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "_wait_for": "div[class*='job'], article[class*='job']",
            "listing_container": "div[class*='job-card'], article[class*='job'], div[class*='result-card']",
            "title": "h3 a, h2 a, span[class*='title']",
            "company": "span[class*='company'], p[class*='company']",
            "location": "span[class*='location'], p[class*='location']",
            "url": "h3 a, h2 a, a[href*='/job/']",
            "description": "p[class*='desc'], div[class*='snippet']",
        },
    },

    # 29. Edudelight — education/teaching-focused job board; bs4
    {
        "name": "Edudelight",
        "url": "https://edudelight.ng/jobs",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='school'], span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 30. NELEX — gov. employment databank; bs4
    {
        "name": "NELEX",
        "url": "https://nelex.gov.ng/jobs",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], tr, li[class*='job']",
            "title": "h2 a, h3 a, td a, a[class*='title']",
            "company": "span[class*='company'], td:nth-child(2)",
            "location": "span[class*='location'], td:nth-child(3)",
            "url": "h2 a, h3 a, td a",
            "description": "p, td[class*='desc']",
        },
    },

    # 31. Federal Civil Service Commission — public sector vacancies; bs4
    {
        "name": "Federal Civil Service Commission",
        "url": "https://recruitment.fedcivilservice.gov.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], div[class*='vacancy'], article, tr",
            "title": "h2 a, h3 a, td a, a[class*='title']",
            "company": "",
            "location": "span[class*='location'], td[class*='location']",
            "url": "h2 a, h3 a, td a, a",
            "description": "p, td[class*='desc']",
        },
    },

    # 32. LEEP Jobs — Federal Ministry of Labour portal; bs4
    {
        "name": "LEEP Jobs",
        "url": "https://jobs.leep.gov.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article, li[class*='job'], tr",
            "title": "h2 a, h3 a, td a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a, td a",
            "description": "p, div[class*='desc']",
        },
    },

    # 33. NDE — National Directorate of Employment; bs4 (skip SSL verify)
    {
        "name": "NDE",
        "url": "https://nde.gov.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article, li, tr",
            "title": "h2 a, h3 a, td a, a",
            "company": "",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a, td a, a",
            "description": "p, div[class*='content']",
        },
    },

    # 34. NaijaHotJobs — community-driven listings; bs4
    {
        "name": "NaijaHotJobs",
        "url": "https://www.naijahotjobs.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 35. HotJobsNg — local daily job alerts; bs4 (alt domain)
    {
        "name": "HotJobsNg",
        "url": "https://hotjobsng.com.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 36. JobListNigeria — general listings; bs4
    {
        "name": "JobListNigeria",
        "url": "https://www.joblistnigeria.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='excerpt']",
        },
    },

    # 37. CareerNaija — career-oriented listings; bs4
    {
        "name": "CareerNaija",
        "url": "https://www.careernaija.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company'], a[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='excerpt'], div[class*='content']",
        },
    },

    # 38. O'hunwa — emerging Nigerian platform; bs4
    {
        "name": "Ohunwa",
        "url": "https://ohunwa.ng",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },

    # 39. Peepuu — remote & international jobs for Nigerians; bs4
    {
        "name": "Peepuu",
        "url": "https://www.peepuu.com",
        "scraper_type": "bs4",
        "keywords": _ALL_KEYWORDS,
        "selectors": {
            "listing_container": "div[class*='job'], article[class*='job'], li[class*='job']",
            "title": "h2 a, h3 a, a[class*='title']",
            "company": "span[class*='company']",
            "location": "span[class*='location']",
            "url": "h2 a, h3 a",
            "description": "p[class*='desc'], div[class*='summary']",
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# BS4 / HTTP fetcher
# ═══════════════════════════════════════════════════════════════════════════════

async def _fetch_with_retry(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch a URL with up to MAX_RETRIES attempts and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {
                "User-Agent": random.choice(_USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                # Do NOT set Accept-Encoding manually — let httpx handle
                # compression negotiation and auto-decompression.
                "Cache-Control": "no-cache",
            }
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=20.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP %s on %s (attempt %d/%d)",
                           exc.response.status_code, url, attempt, MAX_RETRIES)
            if exc.response.status_code in (403, 429):
                # Respect rate-limit: back off longer
                await asyncio.sleep(BASE_BACKOFF ** attempt * 2)
                continue
        except httpx.RequestError as exc:
            logger.warning("Request error on %s: %s (attempt %d/%d)",
                           url, exc, attempt, MAX_RETRIES)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(BASE_BACKOFF ** attempt)
    return None


def _parse_html(html: str, selectors: Dict[str, str], source_url: str) -> List[Dict[str, Any]]:
    """Parse static HTML with CSS selectors. Handles comma-separated multi-selectors."""
    soup = BeautifulSoup(html, "lxml")
    results = []

    container_sel = selectors.get("listing_container", "div")
    containers = soup.select(container_sel)
    if not containers:
        # Wide fallback — try common job card patterns
        containers = soup.select(
            "article, li.job, div[class*='job'], div[class*='Job']")

    for container in containers:
        def _text(sel: str) -> str:
            if not sel:
                return ""
            for s in [x.strip() for x in sel.split(",")]:
                el = container.select_one(s)
                if el:
                    # Special case: img — use alt attribute as text (e.g. MyJobMag company logos)
                    if el.name == "img":
                        return el.get("alt", "").strip()
                    return el.get_text(strip=True)
            return ""

        def _href(sel: str) -> str:
            if not sel:
                return ""
            for s in [x.strip() for x in sel.split(",")]:
                el = container.select_one(s)
                if el:
                    href = el.get("href", "") or ""
                    if href and not href.startswith("http"):
                        href = urljoin(source_url, href)
                    return href
            return ""

        title = _text(selectors.get("title", ""))
        company = _text(selectors.get("company", ""))
        location = _text(selectors.get("location", ""))
        url = _href(selectors.get("url", ""))
        description = _text(selectors.get("description", ""))

        if not title or not url:
            continue

        combined = " ".join([title, company, description,
                            container.get_text(separator=" ")])
        emails = extract_emails(combined)

        results.append({
            "title": title,
            "company": company or None,
            "location": location or None,
            "url": url,
            "description": description or None,
            "raw_emails": emails,
        })

    return results


def _parse_json_api(raw: str, field_map: Dict[str, str], source_url: str) -> List[Dict[str, Any]]:
    """
    Parse a JSON API response into listing dicts.

    Supports three response shapes:
      • Plain array  — e.g. RemoteOK (first element is a legal-notice dict with no title)
      • Dict-wrapped — e.g. Remotive {"jobs": [...]}, Himalayas {"jobs": [...]}
        The root array key is read from field_map["_root"] (default: auto-detect).
      • Direct list  — e.g. WorkingNomads [{...}, ...]

    field_map keys: _root (optional), title, company, location, url, description.
    List-valued fields (e.g. Himalayas locationRestrictions) are joined with ", ".
    """
    try:
        data = _json.loads(raw)
    except Exception as exc:
        logger.warning("JSON parse error: %s", exc)
        return []

    # Unwrap dict response → find the jobs array
    if isinstance(data, dict):
        root_key = field_map.get("_root", "")
        if root_key and root_key in data:
            data = data[root_key]
        else:
            # Auto-detect common root keys
            for key in ("jobs", "data", "results", "job_postings", "listings"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                logger.warning("JSON API: could not find jobs array in response keys: %s", list(
                    data.keys())[:10])
                return []

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue

        def _get(field_key: str, default_keys: str = "") -> str:
            """Get field value; handle list by joining. Tries field_map key then default_keys."""
            key = field_map.get(field_key, default_keys)
            val = item.get(key, "") if key else ""
            if val is None:
                val = ""
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val if v) or ""
            return str(val).strip()

        title = _get("title", "position")
        if not title:
            continue  # skip legal-notice / header elements

        company = _get("company", "company")
        location = _get("location", "location") or "Remote"
        url = _get("url", "url")
        description = _get("description", "description")

        if not url:
            continue

        combined = f"{title} {company} {description}"
        emails = extract_emails(combined)
        results.append({
            "title": title,
            "company": company or None,
            "location": location,
            "url": url,
            "description": description or None,
            "raw_emails": emails,
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Playwright scraper — headless Chromium with stealth
# ═══════════════════════════════════════════════════════════════════════════════

async def _playwright_fetch(url: str, wait_for: Optional[str] = None) -> Optional[str]:
    """
    Fetch a JS-rendered page using Playwright with full stealth configuration.

    Anti-detection measures:
      - playwright-stealth hides navigator.webdriver, fixes Canvas/WebGL fingerprints
      - Random viewport size
      - Rotating realistic User-Agent via Playwright's extra_http_headers
      - Disables images & fonts (faster, less fingerprint surface)
      - Random human-like delay before grab
      - Per-domain semaphore prevents concurrent requests to the same host
    """
    from playwright.async_api import async_playwright, TimeoutError as PwTimeout
    try:
        from playwright_stealth import Stealth
        _stealth = Stealth()
    except Exception:
        _stealth = None

    sem = _domain_sem(url)
    async with sem:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--ignore-certificate-errors",
                ],
            )
            viewport = random.choice(_VIEWPORTS)
            context = await browser.new_context(
                viewport=viewport,
                user_agent=random.choice(_USER_AGENTS),
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            # Block images, fonts, and media — faster and reduces fingerprint surface
            await context.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ("image", "media", "font")
                else route.continue_(),
            )
            page = await context.new_page()

            # Apply stealth patches to the page
            if _stealth:
                await _stealth.apply_stealth_async(page)

            html = None
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

                # Wait for network to go idle (JS-rendered content finishes loading).
                # This ensures XHR/fetch-driven job cards are present before we grab HTML.
                try:
                    await page.wait_for_load_state("networkidle", timeout=20_000)
                except PwTimeout:
                    logger.debug(
                        "networkidle timeout on %s — continuing anyway", url)

                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=10_000)
                    except PwTimeout:
                        logger.warning(
                            "wait_for selector '%s' timed out on %s — grabbing page anyway", wait_for, url)

                # Human-like pause: 1.5–4 seconds
                await asyncio.sleep(random.uniform(1.5, 4.0))

                # Scroll down slowly to trigger lazy-loaded content
                await page.evaluate(
                    """() => {
                        return new Promise(resolve => {
                            let total = 0;
                            const timer = setInterval(() => {
                                window.scrollBy(0, 300);
                                total += 300;
                                if (total >= document.body.scrollHeight) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 150);
                        });
                    }"""
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
                html = await page.content()

            except PwTimeout:
                logger.error("Playwright timeout loading %s", url)
            except Exception as exc:
                logger.error("Playwright error on %s: %s", url, exc)
            finally:
                await browser.close()

        return html


# ═══════════════════════════════════════════════════════════════════════════════
# Google Jobs — JSON-LD extraction via search page
# ═══════════════════════════════════════════════════════════════════════════════

_GOOGLE_JOBS_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# Broad search terms used for Google Jobs queries (covers Nigeria + remote roles)
_GOOGLE_SEARCH_TERMS = [
    "software engineer jobs nigeria",
    "python developer jobs nigeria",
    "backend developer jobs nigeria",
    "full stack developer jobs nigeria",
    "remote software engineer jobs nigeria",
    "data analyst jobs nigeria",
    "web developer jobs nigeria",
    "devops engineer jobs nigeria",
]


async def _scrape_google_jobs() -> List[Dict[str, Any]]:
    """
    Fetch Google Jobs results by scraping the JSON-LD structured data
    embedded in Google Search job-filter pages.

    Google embeds JobPosting schema markup on the SERP when the ibp=htl;jobs
    parameter is present. This lets us extract structured data without a paid API.

    Gracefully returns an empty list if Google blocks the request.
    """
    all_listings: List[Dict[str, Any]] = []
    seen_urls: set = set()

    async with httpx.AsyncClient(
        headers={**_GOOGLE_JOBS_HEADERS,
                 "User-Agent": random.choice(_USER_AGENTS)},
        follow_redirects=True,
        timeout=20.0,
    ) as client:
        for search_term in _GOOGLE_SEARCH_TERMS:
            params = urllib.parse.urlencode(
                {"q": search_term, "ibp": "htl;jobs", "hl": "en", "gl": "ng"})
            url = f"https://www.google.com/search?{params}"
            try:
                resp = await client.get(url)
                if resp.status_code in (429, 403):
                    logger.warning(
                        "Google Jobs blocked (%d) for query '%s' — skipping", resp.status_code, search_term)
                    await asyncio.sleep(random.uniform(5.0, 10.0))
                    continue
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Extract all JSON-LD scripts and look for JobPosting objects
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = _json.loads(script.string or "[]")
                    except Exception:
                        continue

                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        if item.get("@type") != "JobPosting":
                            continue

                        title = str(item.get("title", "")).strip()
                        if not title:
                            continue

                        org = item.get("hiringOrganization", {})
                        company = str(org.get("name", "")).strip(
                        ) if isinstance(org, dict) else ""

                        loc_data = item.get("jobLocation", [])
                        if isinstance(loc_data, dict):
                            loc_data = [loc_data]
                        location = "Nigeria"
                        for loc in (loc_data or []):
                            addr = loc.get("address", {}) if isinstance(
                                loc, dict) else {}
                            parts = [addr.get("addressLocality", ""), addr.get(
                                "addressCountry", "")]
                            location = ", ".join(
                                p for p in parts if p) or "Nigeria"
                            break

                        job_url = str(item.get("url", "")
                                      or item.get("sameAs", "")).strip()
                        if not job_url or job_url in seen_urls:
                            continue

                        description = str(
                            item.get("description", "")).strip()[:600]
                        emails = extract_emails(description)
                        seen_urls.add(job_url)
                        all_listings.append({
                            "title": title,
                            "company": company or None,
                            "location": location,
                            "url": job_url,
                            "description": description or None,
                            "raw_emails": emails,
                        })

            except Exception as exc:
                logger.warning(
                    "Google Jobs fetch error for '%s': %s", search_term, exc)
                continue

            # polite delay between queries
            await asyncio.sleep(random.uniform(3.0, 6.0))

    logger.info("Google Jobs → %d listings scraped", len(all_listings))
    return all_listings


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

async def scrape_source(source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scrape a single source config dict.
    Dispatches to the correct backend based on scraper_type:
      - bs4       → httpx + BeautifulSoup
      - json_api  → httpx + JSON parse
      - playwright→ headless Chromium + stealth
    Returns list of listing dicts (title, company, location, url, description, raw_emails).
    """
    url = source_config["url"]
    scraper_type = source_config.get("scraper_type", "bs4")
    raw_selectors = dict(source_config.get("selectors") or {})

    # Extract private (_-prefixed) control keys stored inside selectors dict
    # so they don't get passed as CSS selectors to the parsers.
    wait_for = source_config.get(
        "wait_for") or raw_selectors.pop("_wait_for", None)
    # Strip all other private keys before passing to parsers
    selectors = {k: v for k, v in raw_selectors.items()
                 if not k.startswith("_")}

    keywords: List[str] = [k.lower()
                           for k in source_config.get("keywords", [])]

    html: Optional[str] = None

    if scraper_type == "google_jobs":
        listings = await _scrape_google_jobs()

    elif scraper_type == "json_api":
        async with httpx.AsyncClient() as client:
            html = await _fetch_with_retry(client, url)
        if html is None:
            logger.error("JSON API fetch failed: %s", url)
            return []
        # pass raw (with _root etc)
        listings = _parse_json_api(html, raw_selectors, url)

    elif scraper_type == "playwright":
        html = await _playwright_fetch(url, wait_for=wait_for)
        if html is None:
            logger.error("Playwright fetch failed: %s", url)
            return []
        listings = _parse_html(html, selectors, url)

    else:  # bs4 (default)
        async with httpx.AsyncClient() as client:
            html = await _fetch_with_retry(client, url)
        if html is None:
            logger.error("BS4 fetch failed: %s", url)
            return []
        listings = _parse_html(html, selectors, url)

    # Filter by keywords — match against title + description
    if keywords:
        filtered = []
        for listing in listings:
            text = (listing["title"] + " " +
                    (listing["description"] or "")).lower()
            if any(kw in text for kw in keywords):
                filtered.append(listing)
        logger.info(
            "Source '%s' → %d raw listings, %d after keyword filter",
            source_config.get("name", url), len(listings), len(filtered),
        )
        return filtered

    logger.info("Source '%s' → %d listings",
                source_config.get("name", url), len(listings))
    return listings
