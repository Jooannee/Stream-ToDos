from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from todos.models import TodoItem

class Command(BaseCommand):
    help = "Delete items archived for longer than 7 days. Runs through Ofelia every night at 2 AM."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        
        deleted_count, _ = TodoItem.objects.filter(
            status="archived",
            archived_at__lte=cutoff
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} archived items.")
        )