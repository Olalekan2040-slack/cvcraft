import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvcraft.settings')

django.setup()

# Run any pending migrations on every startup — this makes the app
# self-healing regardless of how Render (or any host) invokes gunicorn.
from django.core.management import call_command
try:
    call_command('migrate', '--noinput', verbosity=1)
except Exception as _mig_err:
    import traceback
    traceback.print_exc()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
