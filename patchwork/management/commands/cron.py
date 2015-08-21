from django.core.management.base import BaseCommand, CommandError
from patchwork.utils import send_notifications, do_expiry

class Command(BaseCommand):
    help = ('Run periodic patchwork functions: send notifications and ' 
            'expire unused users')

    def handle(self, *args, **kwargs):
        errors = send_notifications()
        for (recipient, error) in errors:
            self.stderr.write("Failed sending to %s: %s" %
                                (recipient.email, error))

        do_expiry()
