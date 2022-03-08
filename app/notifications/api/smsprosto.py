import requests
import logging

from time import sleep

from django.conf import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger_handler = logging.FileHandler("../logs/sms.log")

logger_handler.setLevel(logging.INFO)
logger_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(lineno)d"))
logger.addHandler(logger_handler)


class SMSProsto:
    def __init__(self):
        self.url = settings.SMSPROSTO_URL
        self.api_key = settings.SMSPROSTO_KEY

    def make_request(self, resource, params=None, method='GET', retry=3):
        """
        Выполняет запрос к сервису
        """
        if not params:
            params = {}

        main_params = {
            'method': resource,
            'format': 'json',
            'key': self.api_key,
        }
        main_params.update(**params)
        for i in range(retry):
            try:
                if method == 'GET':
                    response = requests.get(self.url, params=main_params)
                else:
                    response = requests.post(self.url, json=main_params)
                break
            except Exception as e:
                if i < 2:
                    sleep(2)
                    continue
                raise e

        return response

    def send_message(self, phone, text):
        response = self.make_request(
            resource='push_msg',
            params={'text': text, 'phone': str(phone)}
        )
        if response.status_code != 200:
            logger.info(f"Ошибка при отправлении СМС на номер {phone} - {response}")
        else:
            try:
                response = response.json()
                error_code = int(response['response']['msg']['err_code'])
                error_text = response['response']['msg']['text']
                message_id = response['response']['data']['id']
            except Exception as e:
                logger.info(f"Ошибка при разборе ответа: {response}")
                raise e

            if error_code != 0:
                logger.info(f"Ошибка при передаче СМС на номер {phone} - {error_code}, {error_text}, {message_id}")
            else:
                logger.info(f"Сообщение передано на номер {phone}, message_id: {message_id}")

        return message_id

    def get_status(self, message_id):
        response = self.make_request(
            resource='get_msg_report',
            params={'id': message_id}
        )
        if response.status_code != 200:
            logger.info(f"Ошибка получения статуса, message_id: {message_id} ")
            return None, None
        else:
            try:
                response = response.json()
                state_code = int(response['response']['data']['state'])
                state_text = response['response']['data']['state_text']
            except Exception as e:
                logger.info(f"Ошибка при разборе ответа: {response}")
                raise e
        return state_code, state_text
