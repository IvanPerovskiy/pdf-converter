from django.conf import settings

from notifications.api.unione import UnioneConnector

email_service = UnioneConnector(
    settings.EMAIL_API_KEY,
    settings.EMAIL_HOST,
    settings.EMAIL_TEMPLATE_ENGINE,
    settings.SERVER_EMAIL,
    settings.SERVER_EMAIL_NAME,
    settings.EMAIL_REPLY_TO,
    settings.EMAIL_TEMPLATES
)