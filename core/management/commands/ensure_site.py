from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Ensure the django.contrib.sites Site record exists (required by allauth)'

    def handle(self, *args, **options):
        from django.contrib.sites.models import Site

        domain = getattr(settings, 'SITE_DOMAIN', 'cvcraft-7pv3.onrender.com')
        name = getattr(settings, 'SITE_NAME', 'CVCraft')
        site_id = getattr(settings, 'SITE_ID', 1)

        site, created = Site.objects.get_or_create(
            id=site_id,
            defaults={'domain': domain, 'name': name},
        )
        if not created and (site.domain == 'example.com' or site.name == 'example.com'):
            site.domain = domain
            site.name = name
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated site: {domain}'))
        elif created:
            self.stdout.write(self.style.SUCCESS(f'Created site: {domain}'))
        else:
            self.stdout.write(f'Site OK: {site.domain}')
