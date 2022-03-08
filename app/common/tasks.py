from datetime import date
from celery import shared_task

from users.models import UserTariff, User
from notifications.tasks import send_sms


@shared_task
def task_every_day():
    """
    Запускается каждые 00:00 по московскому времени
    Действия:
    """
    current_date = date.today()
    for user in User.objects.filter(
        tariff__in=(UserTariff.MONTH, UserTariff.THREE_MONTH, UserTariff.YEAR)
    ).all():
        if user.tariff_finished == current_date:
            user.set_tariff(UserTariff.FREE)
            if user.phone:
                send_sms.delay(
                    phone=user.phone, message='PDF converter. Your subscription is over'
                )


@shared_task
def task_every_month():
    """
    Запускается каждые 00:00 в первый день месяца по московскому времени
    """
    pass


@shared_task
def task_every_year():
    """
    Запускается каждые 00:00 1 января по московскому времени
    Действия:
    """
    pass

