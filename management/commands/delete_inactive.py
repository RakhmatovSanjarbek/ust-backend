from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import User


class Command(BaseCommand):
    help = "3 oy kirmagan foydalanuvchilarni o'chiradi"

    def handle(self, *args, **kwargs):
        limit = timezone.now() - timedelta(days=90)
        # Faqat admin bo'lmagan mijozlarni o'chiramiz
        deleted_count, _ = User.objects.filter(
            last_active__lt=limit,
            is_staff=False,
            is_superuser=False
        ).delete()
        self.stdout.write(f"O'chirildi: {deleted_count} ta foydalanuvchi")