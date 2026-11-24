from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, transaction

from learning.python_curriculum import install_python_curriculum


class Command(BaseCommand):
    help = 'Install the Python curriculum and preserve existing author edits'

    @transaction.atomic
    def handle(self, *args, **options):
        if install_python_curriculum(apps, DEFAULT_DB_ALIAS):
            self.stdout.write(self.style.SUCCESS('Python curriculum installed.'))
        else:
            self.stdout.write('Python curriculum is already installed.')
