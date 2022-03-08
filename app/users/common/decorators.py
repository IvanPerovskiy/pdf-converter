"""
Created on 24.08.2021

:author: Ivan Perovsky
Декораторы
"""
from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from users.models import UserRole


def roles_required(roles):
    """
    Позволяет вызывать метод пользователсям только с
    определенными ролями
    :param tuple roles: роли пользователей
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, request, **kwargs):
            role = request.user.user.role
            if role is None or role not in roles:
                return Response(status=status.HTTP_403_FORBIDDEN)
            return f(self, request, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    return roles_required(
        (UserRole.ADMIN,)
    )(f)


def auth_required(f):
    return roles_required(
        (UserRole.LOGIN_USER, )
    )(f)



