import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Idempotently create the default superuser if it doesn't already exist."

    def handle(self, *args, **options):
        is_production = os.environ.get("DJANGO_ENV", "local") == "production"

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", None if is_production else "unknown")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", None if is_production else "immoveable@26")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD must be set "
                "when DJANGO_ENV=production."
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists, skipping.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}".'))
