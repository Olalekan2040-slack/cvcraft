"""
Synchronous job scraper for CVCraft JobRadar.
Adapted from jobradar/app/services/scraper.py.

Uses JSON API + BS4 sources only (no Playwright dependency).
Covers 7 reliable international + Nigerian job boards.
"""
import logging
import random
import time
import re
from typing import List, Dict, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

MAX_RETRIES = 3

# ── Source definitions ────────────────────────────────────────────────────────
SOURCES: List[Dict[str, Any]] = [
    # JSON API — fast, reliable, no bot protection
    {
        "name": "Remotive",
        "url": "https://remotive.com/api/remote-jobs?category=software-dev&limit=200",
        "scraper_type": "json_api",
        "selectors": {
            "_root": "jobs",
            "title": "title",
            "company": "company_name",
            "location": "candidate_required_location",
            "url": "url",
            "description": "description",
        },
    },
    {
        "name": "WorkingNomads",
        "url": "https://www.workingnomads.com/api/exposed_jobs/?category=development",
        "scraper_type": "json_api",
        "selectors": {
            "title": "title",
            "company": "company_name",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },
    {
        "name": "Himalayas",
        "url": "https://himalayas.app/jobs/api?limit=200",
        "scraper_type": "json_api",
        "selectors": {
            "_root": "jobs",
            "title": "title",
            "company": "companyName",
            "location": "locationRestrictions",   # list value — handled below
            "url": "applicationLink",
            "description": "description",
        },
    },
    {
        "name": "Remote OK",
        "url": "https://remoteok.com/api",
        "scraper_type": "json_api",
        "selectors": {
            "title": "position",
            "company": "company",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },
    {
        "name": "Arbeitnow",
        "url": "https://arbeitnow.com/api/job-board-api",
        "scraper_type": "json_api",
        "selectors": {
            "_root": "data",
            "title": "title",
            "company": "company_name",
            "location": "location",
            "url": "url",
            "description": "description",
        },
    },
    {
        "name": "Jobicy",
        "url": "https://jobicy.com/api/v2/remote-jobs?count=50&tag=developer",
        "scraper_type": "json_api",
        "selectors": {
            "_root": "jobs",
            "title": "jobTitle",
            "company": "companyName",
            "location": "jobGeo",
            "url": "url",
            "description": "jobDescription",
        },
    },
    # BS4 — static HTML
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com/remote-jobs",
        "scraper_type": "bs4",
        "selectors": {
            "listing_container": "li.new-listing-container",
            "title": "span.new-listing__header__title__text",
            "company": "p.new-listing__company-name",
            "location": "p.new-listing__company-headquarters",
            "url": "a.listing-link--unlocked",
            "description": "span.new-listing__header__title__text",
        },
    },
]


def _headers() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "application/json, text/html, */*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }


def _fetch(url: str, timeout: int = 25) -> httpx.Response:
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, headers=_headers())
                if resp.status_code in (429, 503) and attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt * 3)
                    continue
                resp.raise_for_status()
                return resp
        except httpx.HTTPStatusError:
            raise
        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url}")


def _keyword_match(text: str, keywords: List[str]) -> List[str]:
    tl = text.lower()
    return [k for k in keywords if k.lower() in tl]


def _strip_html(html: str) -> str:
    return re.sub(r'<[^>]+>', ' ', html)


def _scrape_json_api(source: dict, keywords: List[str]) -> List[dict]:
    sel = source['selectors']
    try:
        resp = _fetch(source['url'])
        data = resp.json()
    except Exception as exc:
        logger.warning(f"[{source['name']}] failed: {exc}")
        return []

    if isinstance(data, dict):
        root = sel.get('_root')
        if root:
            data = data.get(root, [])
        else:
            for key in ('jobs', 'data', 'results', 'job_postings', 'listings'):
                if key in data:
                    data = data[key]
                    break

    if not isinstance(data, list):
        return []

    listings = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get(sel.get('title', 'title'), '') or '').strip()
        company = str(item.get(sel.get('company', 'company'), '') or '').strip()
        location = item.get(sel.get('location', 'location'), '') or ''
        if isinstance(location, list):
            location = ', '.join(str(x) for x in location if x)
        else:
            location = str(location).strip()
        url = str(item.get(sel.get('url', 'url'), '') or '').strip()
        description = _strip_html(str(item.get(sel.get('description', 'description'), '') or ''))

        if not title or not url or not url.startswith('http'):
            continue

        matched = _keyword_match(f"{title} {description}", keywords)
        if not matched:
            continue

        listings.append({
            'source_name': source['name'],
            'title': title[:500],
            'company': company[:300],
            'location': location[:300],
            'url': url[:2000],
            'description': description[:8000],
            'keywords_matched': matched[:10],
        })
    return listings


def _scrape_bs4(source: dict, keywords: List[str]) -> List[dict]:
    sel = source['selectors']
    try:
        resp = _fetch(source['url'])
    except Exception as exc:
        logger.warning(f"[{source['name']}] failed: {exc}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    containers = soup.select(sel.get('listing_container', 'li'))

    listings = []
    seen = set()
    for container in containers:
        title_el = container.select_one(sel['title'])
        url_el = container.select_one(sel['url'])
        company_el = container.select_one(sel.get('company', '')) if sel.get('company') else None
        location_el = container.select_one(sel.get('location', '')) if sel.get('location') else None
        desc_el = container.select_one(sel.get('description', '')) if sel.get('description') else None

        title = title_el.get_text(strip=True) if title_el else ''
        raw_url = url_el.get('href', '') if url_el else ''
        if raw_url and not raw_url.startswith('http'):
            raw_url = urljoin(source['url'], raw_url)
        company = company_el.get_text(strip=True) if company_el else ''
        location = location_el.get_text(strip=True) if location_el else ''
        description = desc_el.get_text(strip=True) if desc_el else title

        if not title or not raw_url or raw_url in seen:
            continue

        matched = _keyword_match(f"{title} {description}", keywords)
        if not matched:
            continue

        seen.add(raw_url)
        listings.append({
            'source_name': source['name'],
            'title': title[:500],
            'company': company[:300],
            'location': location[:300],
            'url': raw_url[:2000],
            'description': description[:8000],
            'keywords_matched': matched[:10],
        })
    return listings


def scrape_all(keywords: List[str]) -> List[dict]:
    """
    Scrape all configured sources with given keywords.
    Returns raw listing dicts (not yet persisted).
    """
    all_listings: List[dict] = []
    for source in SOURCES:
        try:
            if source['scraper_type'] == 'json_api':
                results = _scrape_json_api(source, keywords)
            elif source['scraper_type'] == 'bs4':
                results = _scrape_bs4(source, keywords)
            else:
                continue
            logger.info(f"[{source['name']}] {len(results)} matched")
            all_listings.extend(results)
            time.sleep(random.uniform(0.8, 2.0))
        except Exception as exc:
            logger.error(f"[{source['name']}] unexpected error: {exc}")
    return all_listings
