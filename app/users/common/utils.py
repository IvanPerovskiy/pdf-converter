"""
Created on 24.08.2021

:author: Ivan Perovsky
Вспомогательные функции
"""

import jwt
import hashlib

from datetime import timedelta, date
from django.utils import timezone

from django.conf import settings


def get_hash_password(password):
    h = hashlib.sha256()
    h.update(password.encode('utf-8'))
    return h.hexdigest()


def generate_jwt_tokens(user_id):
    """
    Функция генерирует access_token и refresh_token для заданного user_id

    Входные данные:
        user_id - идентификатор пользователя

    Выходные данные:
        access_token - JWT-токен для регулярных запросов, с меньшим временем действия (ACCESS_TOKEN_TIME в settings.py)
        refresh_token - JWT-токен для обновления access_token, с длительным временем действия (REFRESH_TOKEN_TIME
                        в settings.py)
    """
    # Формируем время окончания access_token
    access_token_time = timezone.localtime() + timedelta(minutes=settings.ACCESS_TOKEN_TIME)
    access_token_time = access_token_time.isoformat(' ', "seconds")
    # Формируем время окончания refresh_token
    refresh_token_time = timezone.localtime() + timedelta(minutes=settings.REFRESH_TOKEN_TIME)
    refresh_token_time = refresh_token_time.isoformat(' ', "seconds")

    # формируем JWT-токен access_token (JWT_HASH и SECRET_KEY в settings.py)
    access_token = jwt.encode({
        "user_id": str(user_id),
        "refresh_time": access_token_time},
        settings.SECRET_KEY,
        algorithm=settings.JWT_HASH)

    # формируем JWT-токен refresh_token (JWT_HASH и SECRET_KEY в settings.py)
    refresh_token = jwt.encode({
        "user_id": str(user_id),
        "refresh_time": refresh_token_time},
        settings.SECRET_KEY,
        algorithm=settings.JWT_HASH)

    return access_token, refresh_token


def get_tariff_finished(tariff):
    """
    Возвращает дату окончания подписки зависимости от типа тарифа
    """
    from users.models import UserTariff
    if tariff == UserTariff.FREE:
        return None

    elif tariff == UserTariff.MONTH:
        day = date.today()
        next_month = 1 if day.month == 12 else day.month + 1
        return day.replace(month=next_month, day=day.day)

    elif tariff == UserTariff.THREE_MONTH:
        day = date.today()
        next_month = day.month - 9 if day.month > 9 else day.month + 3
        return day.replace(month=next_month, day=day.day)

    elif tariff == UserTariff.YEAR:
        day = date.today()
        return day.replace(year=day.year+1, day=1)

