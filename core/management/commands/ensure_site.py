from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Ensure the django.contrib.sites Site record exists (required by allauth)'

    def handle(self, *args, **options):
        # Verify the table actually exists before trying to query it
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_site');"
            )
            table_exists = cursor.fetchone()[0]

        if not table_exists:
            self.stderr.write('django_site table does not exist — run migrate first.')
            return

        from django.contrib.sites.models import Site

        domain = getattr(settings, 'SITE_DOMAIN', 'cvcraft-7pv3.onrender.com')
        name = getattr(settings, 'SITE_NAME', 'CVCraft')
        site_id = getattr(settings, 'SITE_ID', 1)

        site, created = Site.objects.get_or_create(
            id=site_id,
            defaults={'domain': domain, 'name': name},
        )
        if not created and site.domain in ('example.com', 'localhost'):
            site.domain = domain
            site.name = name
            site.save(update_fields=['domain', 'name'])
            self.stdout.write(self.style.SUCCESS(f'Updated site → {domain}'))
        elif created:
            self.stdout.write(self.style.SUCCESS(f'Created site → {domain}'))
        else:
            self.stdout.write(f'Site OK: {site.domain}')
