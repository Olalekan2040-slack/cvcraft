"""
python manage.py scrape_jobs

Aggregates keywords from all users' resumes, then scrapes all configured
job sources and stores new listings in the database.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from resumes.models import Resume
from jobs.models import JobListing, JobScrapeLog
from jobs.services.scraper import scrape_all
from jobs.services.keywords import extract_keywords

logger = logging.getLogger(__name__)

_FALLBACK_KEYWORDS = [
    'software engineer', 'python developer', 'django developer',
    'full stack developer', 'backend developer', 'javascript developer',
    'react developer', 'data analyst', 'machine learning engineer',
]


class Command(BaseCommand):
    help = 'Scrape job listings from all configured sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keywords', nargs='+', type=str,
            help='Override keywords for this run',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Scrape but do not save to DB',
        )

    def handle(self, *args, **options):
        log = JobScrapeLog.objects.create(status='running')
        errors = []

        try:
            # Build keyword list from all users' resumes
            if options.get('keywords'):
                keywords = options['keywords']
                self.stdout.write(f"Using {len(keywords)} custom keywords.")
            else:
                kw_set: set = set()
                for resume in Resume.objects.all():
                    try:
                        kw_set.update(extract_keywords(resume.get_data()))
                    except Exception as exc:
                        errors.append(f"keyword extract: {exc}")
                keywords = list(kw_set) if kw_set else _FALLBACK_KEYWORDS
                self.stdout.write(
                    f"Extracted {len(keywords)} keywords from "
                    f"{Resume.objects.count()} resumes."
                )

            self.stdout.write(f"Sample: {', '.join(keywords[:8])}...")
            self.stdout.write("Scraping sources — this may take 1-2 minutes...")

            raw = scrape_all(keywords)
            self.stdout.write(f"Fetched {len(raw)} raw listings.")

            if options.get('dry_run'):
                self.stdout.write(self.style.WARNING("Dry run — not saving."))
                for item in raw[:5]:
                    self.stdout.write(f"  {item['source_name']}: {item['title']}")
                return

            new_count = 0
            skip_count = 0
            sources_seen = set()

            for item in raw:
                url = (item.get('url') or '').strip()
                if not url:
                    skip_count += 1
                    continue
                sources_seen.add(item['source_name'])
                _, created = JobListing.objects.get_or_create(
                    url=url,
                    defaults={
                        'source_name': item['source_name'],
                        'title': item['title'],
                        'company': item.get('company', ''),
                        'location': item.get('location', ''),
                        'description': item.get('description', ''),
                        'keywords_matched': item.get('keywords_matched', []),
                    },
                )
                if created:
                    new_count += 1
                else:
                    skip_count += 1

            log.ended_at = timezone.now()
            log.listings_new = new_count
            log.listings_skipped = skip_count
            log.sources_run = len(sources_seen)
            log.errors = errors
            log.status = 'done'
            log.save()

            self.stdout.write(self.style.SUCCESS(
                f"Done. New: {new_count}  |  Duplicates skipped: {skip_count}  "
                f"|  Sources: {len(sources_seen)}"
            ))

        except Exception as exc:
            log.status = 'error'
            log.errors = errors + [str(exc)]
            log.ended_at = timezone.now()
            log.save()
            raise
