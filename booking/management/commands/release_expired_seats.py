from django.core.management.base import BaseCommand
from django.utils import timezone
from booking.models import Seat


class Command(BaseCommand):
    help = 'Release seats with expired reservations'
    """
    Finds all seats with expired reservations and releases them back to available.
    Runs as a scheduled management command.
    """
    def handle(self, *args, **kwargs):
        expired = Seat.objects.filter(
            status='reserved',
            reserved_until__lt=timezone.now()
        )
        count = expired.count()
        expired.update(status='available', reserved_until=None)
        self.stdout.write(f'Released {count} expired seats')