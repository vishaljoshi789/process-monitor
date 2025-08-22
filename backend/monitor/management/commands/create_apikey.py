import secrets
from django.core.management.base import BaseCommand
from monitor.models import ApiKey, Host

class Command(BaseCommand):
    help = "Create an API key (optionally bind to a hostname)."

    def add_arguments(self, parser):
        parser.add_argument("--hostname", type=str, default=None)
        parser.add_argument("--note", type=str, default="")

    def handle(self, *args, **opts):
        key = secrets.token_hex(24)
        host = None
        if opts["hostname"]:
            host, _ = Host.objects.get_or_create(hostname=opts["hostname"])
        ApiKey.objects.create(key=key, host=host, note=opts["note"])
        self.stdout.write(self.style.SUCCESS(key))