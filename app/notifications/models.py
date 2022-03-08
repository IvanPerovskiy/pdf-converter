from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

from users.models import User


class CodeType:
    EMAIL = 0
    PHONE = 1

    choices = (
        (EMAIL, 'Email'),
        (PHONE, 'Телефон'),
    )


class Notification(models.Model):
    phone = models.CharField(max_length=25)
    text = models.TextField()
    status = models.PositiveSmallIntegerField()
    date_add = models.DateTimeField(auto_now_add=True)
    log = models.TextField(default=None, null=True, blank=True)
    external_id = models.CharField(null=True, blank=True, max_length=100)


class ActivationCode(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True,
        related_name='activation_codes')
    code = models.CharField(max_length=200)
    code_type = models.IntegerField(choices=CodeType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)
        db_table = "activation_codes"
        verbose_name = "Код активации"
        verbose_name_plural = "Коды активации"

    def __str__(self):
        return self.code

    def expired(self):
        if self.code_type == 0:
            lifetime = settings.EMAIL_REGISTRATION_CODE_LIFETIME
        elif self.code_type == 1:
            lifetime = settings.PHONE_REGISTRATION_CODE_LIFETIME
        return timezone.now() > self.timestamp + timedelta(seconds=lifetime)
