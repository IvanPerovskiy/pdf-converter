from django.conf import settings
from django.template.loader import render_to_string
from django.core.management.utils import get_random_string


from notifications import smsp
from notifications.models import ActivationCode


def send_phone_code(user, phone):
    code = get_random_string(length=4, allowed_chars='0123456789')
    ActivationCode.objects.create(
        code=code,
        code_type=1,
        user=user
    )
    context = {
        'code': code
    }
    message = render_to_string('sms/confirm.txt', context)
    smsp.send_message(phone, message)
