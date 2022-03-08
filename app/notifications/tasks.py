from django.conf import settings
from django.template.loader import render_to_string
from django.core.management.utils import get_random_string

from core.celery import app

from notifications import smsp
from notifications.api import email_service
from notifications.models import ActivationCode, CodeType


@app.task(max_retries=None, autoretry_for=(Exception,), retry_backoff=True)
def send_sms(phone, message):
    smsp.send_message(phone, message)


@app.task(max_retries=None, autoretry_for=(Exception,), retry_backoff=True)
def get_status(sms_pk):
    pass


@app.task(max_retries=None, autoretry_for=(Exception,), retry_backoff=True)
def clear_codes(activation_code_id):
    try:
        ActivationCode.objects.filter(pk=activation_code_id).delete()
    except:
        pass


@app.task(max_retries=None, autoretry_for=(Exception,), retry_backoff=True)
def confirm_email(email, user_id):
    code = get_random_string()
    activation_code = ActivationCode.objects.create(
        code=code,
        code_type=0,
        user_id=user_id
    )
    context = {
        'subject': 'Подтвержение адреса',
        'email': email,
        'domain': settings.DOMAIN,
        'code': code,
        'user_id': user_id
    }
    body = render_to_string('mail/welcome.html', context)
    email_service.send_simple_mail(
        body=body,
        context=context
    )
    clear_codes.apply_async(
        kwargs={'activation_code_id': activation_code.id}, countdown=15*60
    )


@app.task(max_retries=None, autoretry_for=(Exception,), retry_backoff=True)
def refresh_password(email, user_id):
    code = get_random_string()
    activation_code = ActivationCode.objects.create(
        code=code,
        code_type=CodeType.EMAIL,
        user_id=user_id
    )

    context = {
        'subject': 'Подтвержение адреса',
        'email': email,
        'domain': settings.DOMAIN,
        'code': code,
        'user_id': user_id
    }
    body = render_to_string('mail/restore_password.html', context)

    email_service.send_simple_mail(
        body=body,
        context=context
    )
