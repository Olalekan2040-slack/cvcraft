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

# Auto-seed jobs on first deploy: kick off per-user scrapes for every user
# who has a resume but no job targets yet. Falls back to a global scrape
# when no users with resumes exist (brand-new deploy with no accounts).
try:
    from jobs.models import JobListing, JobScrapeLog, UserJobTarget
    from resumes.models import Resume
    if not JobScrapeLog.objects.filter(status='running').exists():
        from jobs.views import start_scrape_thread
        users_with_resumes = (
            Resume.objects.select_related('user')
            .values_list('user', flat=True)
            .distinct()
        )
        seeded = 0
        for uid in users_with_resumes:
            if not UserJobTarget.objects.filter(user_id=uid).exists():
                from django.contrib.auth.models import User as _User
                try:
                    u = _User.objects.get(pk=uid)
                    if not JobScrapeLog.objects.filter(status='running', user=u).exists():
                        start_scrape_thread(user=u)
                        seeded += 1
                except Exception:
                    pass
        if seeded == 0 and not JobListing.objects.exists():
            # Truly fresh deploy — global seed
            start_scrape_thread()
except Exception as _seed_err:
    import traceback
    traceback.print_exc()

# ── Self-ping: keep Render free tier alive ────────────────────────────────────
# Render spins down the service after 15 minutes of no requests.
# We ping our own /ping/ endpoint every 10 minutes so the app stays warm
# even when no browser tab is open. Uses RENDER_EXTERNAL_URL which Render
# sets automatically for web services.
def _self_ping_loop(base_url: str) -> None:
    import time
    import urllib.request
    import logging
    _log = logging.getLogger('cvcraft.keepalive')
    time.sleep(90)          # give gunicorn time to fully start
    while True:
        try:
            urllib.request.urlopen(f"{base_url}/ping/", timeout=10)
            _log.debug("keep-alive ping OK")
        except Exception as _e:
            _log.warning("keep-alive ping failed: %s", _e)
        time.sleep(600)     # ping every 10 minutes

_render_url = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/')
if _render_url:
    import threading
    _t = threading.Thread(target=_self_ping_loop, args=(_render_url,), daemon=True)
    _t.start()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
