# Contributing to CVCraft

Thank you for considering contributing! This is an open-source project and all contributions are welcome — from bug fixes to new templates to improved AI prompts.

---

## Getting Started

### 1. Fork & Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/<your-username>/cvcraft.git
cd cvcraft
```

### 2. Set Up Local Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then edit .env with your values
python manage.py migrate
python manage.py runserver
```

> You do **not** need a Gemini API key to run the app — all AI features gracefully fall back to a local regex parser.

### 3. Create a Branch

```bash
git checkout -b feat/my-feature
# or
git checkout -b fix/bug-description
```

---

## Project Layout (Quick Reference)

| Path | What lives here |
|---|---|
| `jobs/services/scraper.py` | Job board scrapers — add new sources here |
| `jobs/services/ats.py` | ATS scoring and stack intelligence |
| `resumes/views.py` | Resume builder logic, AI integration |
| `templates/resume_templates/` | Printable CV templates — add new ones here |
| `templates/core/landing.html` | Marketing landing page |
| `static/js/builder.js` | Alpine.js resume editor component |

---

## How to Add a New Job Source

1. Open `jobs/services/scraper.py`
2. Add a new entry to the `SOURCES` list:

```python
{
    "name": "MyJobBoard",
    "url": "https://api.myjobboard.com/jobs?format=json",
    "scraper_type": "json_api",      # or "bs4" for HTML scraping
    "selectors": {
        "_root": "jobs",             # top-level key if wrapped
        "title": "job_title",
        "company": "company",
        "location": "location",
        "url": "apply_url",
        "description": "description",
    },
},
```

3. Run `python manage.py scrape_jobs --dry-run` to verify it works without saving to DB
4. Open a PR with the source name, URL, and a brief description

---

## How to Add a New Resume Template

1. Copy an existing template from `templates/resume_templates/` (e.g. `clean.html`)
2. Rename it and customise the HTML/CSS
3. Register it in `resumes/views.py` in the `TEMPLATES` dict:

```python
TEMPLATES = {
    ...
    'mytemplate': 'resume_templates/mytemplate.html',
}
```

4. Add a preview screenshot to `static/images/templates/mytemplate.png` (800×566 recommended)
5. Register in `resumes/models.py`'s `TEMPLATE_CHOICES`
6. Open a PR with a screenshot in the description

---

## Code Style

- **Python**: Follow PEP 8. No type annotations required but appreciated.
- **Django**: Prefer class-based views only for complex cases; function views are fine.
- **Templates**: Keep logic minimal — use template tags/filters over in-template Python.
- **JavaScript**: Vanilla JS or Alpine.js only. No build step, no npm.
- **Comments**: Only write one when the *why* is non-obvious. Skip "what" comments.
- **Tests**: If you fix a bug, a regression test is appreciated. Use Django's `TestCase`.

---

## Pull Request Checklist

- [ ] Branch is up to date with `master`
- [ ] App runs locally without errors (`python manage.py runserver`)
- [ ] Migrations included for any model changes (`python manage.py makemigrations`)
- [ ] No secrets or `.env` files committed
- [ ] PR description explains *what* changed and *why*
- [ ] Screenshots attached for any UI changes

---

## Reporting Bugs

Open a GitHub Issue with:
- Steps to reproduce
- Expected behaviour
- Actual behaviour
- Django/Python version and any relevant error from the console

---

## Questions?

Open a GitHub Discussion or reach out via the portfolio site at [quaddev.onrender.com](https://quaddev.onrender.com).
