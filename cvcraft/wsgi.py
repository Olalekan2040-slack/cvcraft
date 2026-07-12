import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvcraft.settings')

django.setup()

# Run any pending migrations on every startup — self-healing regardless of host config.
from django.core.management import call_command
try:
    call_command('migrate', '--noinput', verbosity=1)
except Exception as _mig_err:
    import traceback
    traceback.print_exc()

# Auto-seed jobs on first deploy: if the DB is fresh (no jobs yet), kick off
# a background scrape so Job Radar works out-of-the-box without any manual steps.
try:
    from jobs.models import JobListing, JobScrapeLog
    if not JobListing.objects.exists() and not JobScrapeLog.objects.filter(status='running').exists():
        from jobs.views import start_scrape_thread
        start_scrape_thread()
except Exception as _seed_err:
    import traceback
    traceback.print_exc()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
