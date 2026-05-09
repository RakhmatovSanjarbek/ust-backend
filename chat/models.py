from django.db import models
from accounts.models import User


class ChatMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_chat_messages'  # ✅ Yangi unique nom
    )
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_chat_responses'  # ✅ Unique nom
    )
    message = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_from_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = "Admin" if self.is_from_admin else self.user.phone
        return f"{sender}: {self.message[:30] if self.message else '📷 Rasm'}"

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat xabari"
        verbose_name_plural = "Chat xabarlari"