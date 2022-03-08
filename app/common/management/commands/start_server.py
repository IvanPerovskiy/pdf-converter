from django.core.management.base import BaseCommand

from common.actions import start_server


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        start_server()
