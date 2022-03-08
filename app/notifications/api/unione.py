import json
import base64

from time import sleep

import requests

from django.conf import settings


class UnioneConnector:
    def __init__(self, api_key, domain, template_engine,
                 from_email, from_name, reply_to, templates):
        self.api_key = api_key
        self.domain = domain
        self.template_engine = template_engine
        self.from_email = from_email
        self.from_name = from_name
        self.reply_to = reply_to
        self.templates = templates

    def make_request(self, resource, params=None, method='POST'):
        """
        Выполняет запрос к сервису
        :param str resource: название запрашиваемого ресурса
        :param json data: параметры запроса
        :param str method: метод запроса

        :return: response-объект, содержащий ответ сервиса
        :rtype: requests.Response
        """
        url = '{}/{}'.format(self.domain, resource)

        if not params:
            params = {}

        params['api_key'] = self.api_key

        if settings.EMAIL_NOTIFICATIONS:
            if method == 'GET':
                response = requests.get(url, json=params)
            else:
                response = requests.post(url, json=params)

        return response

    def send_mail(self, params, retry=3):
        """
        Метод отправки сообщения

        :param params: параметры
        :return: ответ сервиса
        """
        resource = 'ru/transactional/api/v1/email/send.json'

        for i in range(retry):
            try:
                response = self.make_request(resource, params)
                break
            except Exception as e:
                if i < 2:
                    sleep(2)
                    continue
                raise e

        return response

    def generate_footer(self, context):
        # TODO Для авторизванных пользователей добавить формирование подписи
        return ''

    def send_mail_with_attachments(self, body, file_name, path=settings.MEDIA_ROOT, emails=None, context=None):
        """
        Метод отправки сообщений администратору через обратную связь

        :param body: текст письма
        :param email: адрес получателя
        :param retry: количество попыток при неуспешной отправке
        :param context: параметры письма
        :return: ответ сервиса
        """
        footer = ''
        if context:
            footer = self.generate_footer(context)

        if not emails:
            emails = settings.ADMIN_EMAILS

        recepients = [{'email': email} for email in emails]
        message = {
            "body": {"html": body + footer},
            "subject": context.get('subject'),
            "from_email": settings.FEEDBACK_EMAIL,
            "reply_to": context.get('email'),
            "from_name": context.pop('name'),
            "recipients": recepients,
            "attachments": [
                {
                    "type": "text/csv",
                    "name": file_name,
                    "content": b64e(open(path+file_name).read())
                }
            ],
        }
        params = {
            "message": message
        }

        response = self.send_mail(params)

        return response

    def send_to_admin(self, body, context=None):
        """
        Метод отправки сообщений администратору через обратную связь

        :param body: текст письма
        :param retry: количество попыток при неуспешной отправке
        :param context: параметры письма
        :return: ответ сервиса
        """
        emails = settings.FEEDBACK_EMAILS
        if not context:
            context = {}

        footer = self.generate_footer(context)
        recepients = [{'email': email} for email in emails]
        message = {
            "body": {"html": body + footer},
            "subject": "BSTR Обратная связь",
            "from_email": settings.FEEDBACK_EMAIL,
            "reply_to": context.get('email'),
            "from_name": context.get('name'),
            "recipients": recepients,
        }
        params = {
            "message": message
        }

        response = self.send_mail(params)
        return response

    def send_simple_mail(self, body, context, footer=''):
        if footer:
            footer = self.generate_footer(context)
        recepients = [{'email': context['email']}]
        message = {
            "body": {"html": body + footer},
            "subject": context.get('subject'),
            "from_email": settings.FEEDBACK_EMAIL,
            "from_name": settings.SERVER_EMAIL_NAME,
            "recipients": recepients,
        }
        params = {
            "message": message
        }

        response = self.send_mail(params)
        return response
