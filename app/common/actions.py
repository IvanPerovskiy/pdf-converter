from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from users.models import *


def start_server():
    """
    Функция разворачивания проекта после применения миграций
    :return:
    """
    with transaction.atomic():
        get_user_model().objects.create_superuser(
            username=django_settings.SUPERUSER_NAME,
            password=django_settings.SUPERUSER_PASSWORD
        )
