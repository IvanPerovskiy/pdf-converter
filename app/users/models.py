import hashlib
import uuid

from datetime import datetime

from django.db import transaction
from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

from users.common.utils import get_tariff_finished


class UserStatus:
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2
    DELETED = 3

    choices = (
        (NEW, 'Новый'),
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DELETED, 'Удаленный'),
    )


class UserTariff:
    FREE = 0
    MONTH = 1
    THREE_MONTH = 2
    YEAR = 3

    choices = (
        (FREE, 'Бесплатный'),
        (MONTH, 'Премиум на месяц'),
        (THREE_MONTH, 'Премиум на три месяца'),
        (YEAR, 'Премиум на год'),
    )


class UserRole:
    UNAUTHORIZED_USER = 0
    LOGIN_USER = 1
    ADMIN = 10

    choices = (
        (ADMIN, 'Администратор'),
        (LOGIN_USER, 'Авторизованный пользователь'),
        (UNAUTHORIZED_USER, 'Анонимный пользователь'),
    )


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=True, blank=True, max_length=250)
    surname = models.CharField(null=True, blank=True, max_length=250)
    patronymic = models.CharField(null=True, blank=True, max_length=250)
    address = models.CharField(null=True, blank=True, max_length=250)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    login = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)

    email_confirmed = models.BooleanField(default=False, verbose_name="Почта подтверждена?")
    phone_confirmed = models.BooleanField(default=False, verbose_name="Телефон подтвержден?")

    status = models.IntegerField(choices=UserStatus.choices, default=UserStatus.ACTIVE)
    tariff = models.IntegerField(choices=UserTariff.choices, default=UserTariff.FREE)
    role = models.IntegerField(choices=UserRole.choices)

    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    profile = models.OneToOneField(Profile, on_delete=models.PROTECT, null=True, blank=True)
    salt = models.CharField(max_length=200)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    password_updated = models.DateTimeField(null=True, blank=True)
    tariff_updated = models.DateTimeField(null=True, blank=True)
    tariff_finished = models.DateField(null=True, blank=True)

    @property
    def user_path(self):
        return ''.join([
            settings.MEDIA_ROOT,
            str(self.id),
            '/'
        ])

    def hash_password(self, password):
        h = hashlib.sha256()
        h.update(password.encode('utf-8'))
        h.update(self.salt.encode('utf-8'))
        return h.hexdigest()

    def set_status(self, status):
        if self.status == UserStatus.DELETED:
            raise ValidationError('Нельзя поменять статус удаленного пользователя')
        elif status == UserStatus.NEW:
            raise ValidationError('Нельзя поменять статус на Новый')

        with transaction.atomic():
            self.status = status
            self.save()

    def notify(self):
        pass

    def set_tariff(self, tariff):
        self.tariff = tariff
        self.tariff_updated = datetime.utcnow()
        self.tariff_finished = get_tariff_finished(tariff)
        self.save()

    def set_password(self, password):
        self.auth_user.set_password(self.hash_password(password))
        self.auth_user.save()
        self.password_updated = datetime.utcnow()
        self.save()

    def set_email(self, email):
        self.email = email
        self.email_confirmed = True
        self.save()

    class Meta():
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')

    number = models.CharField(max_length=250, null=True, blank=True)
    push_token = models.CharField(max_length=250, null=True, blank=True)

    maker = models.CharField(max_length=200, null=True, blank=True)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    factory_number = models.CharField(max_length=100, null=True, blank=True)
    series_number = models.CharField(max_length=100, null=True, blank=True)
    operation_system = models.CharField(max_length=100, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
