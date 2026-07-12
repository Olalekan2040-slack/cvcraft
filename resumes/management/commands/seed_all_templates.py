"""
Creates one resume per template using Sharafdeen Quadri's data.
Run: python manage.py seed_all_templates
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from resumes.models import Resume, TEMPLATE_CHOICES
from .seed_sharafdeen import RESUME_DATA

ACCENT_COLORS = {
    'classic':   '#1a365d',
    'modern':    '#2d6a4f',
    'executive': '#7b2d00',
    'creative':  '#6b21a8',
    'student':   '#1e40af',
    'technical': '#C9A84C',
    'elegant':   '#be185d',
    'bold':      '#dc2626',
    'clean':     '#0f766e',
    'timeline':  '#7c3aed',
}


class Command(BaseCommand):
    help = "Seed Sharafdeen's resume into every template so each can be previewed"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="sharafdeen",
            defaults={
                "email": "olalekanquadri58@gmail.com",
                "first_name": "Sharafdeen",
                "last_name": "Quadri",
            },
        )
        if created:
            user.set_password("cvcraft2024!")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created user: sharafdeen"))
        else:
            self.stdout.write("User: sharafdeen (already exists)")

        self.stdout.write("")
        for slug, name in TEMPLATE_CHOICES:
            resume, _ = Resume.objects.update_or_create(
                user=user,
                title=f"Sharafdeen — {name}",
                defaults={
                    "template_slug": slug,
                    "data": RESUME_DATA,
                    "is_public": True,
                    "accent_color": ACCENT_COLORS.get(slug, "#C9A84C"),
                    "font_family": "Inter",
                },
            )
            url = f"http://localhost:8000/r/{resume.public_token}/"
            self.stdout.write(f"  [{slug:10s}]  {url}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done. All 10 templates seeded."))
        self.stdout.write("Login -> username: sharafdeen  |  password: cvcraft2024!")
