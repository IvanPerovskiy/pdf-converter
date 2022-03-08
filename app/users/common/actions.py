import uuid
import os


from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

from django.core.management.utils import get_random_secret_key, get_random_string

from users.models import User, UserRole, Device, Profile
from users.common.utils import get_hash_password


def create_auth_user(username=None):
    if not username:
        username = uuid.uuid4()
    auth_user = get_user_model().objects.create_user(
        username,
        is_active=True
    )
    return auth_user


def create_user(
        user_dict,
        password=None,
        device_dict=None,
        profile_dict=None,
        current_user=None
):
    """
    Создает клиента и его пользователя
    """
    with transaction.atomic():
        if not current_user:
            auth_user = create_auth_user(
                uuid.uuid4()
            )
            current_user = User.objects.create(
                id=auth_user.username,
                auth_user=auth_user,
                salt=get_random_secret_key(),
                **user_dict
            )
        else:
            User.objects.filter(id=current_user.id).update(**user_dict)
            current_user.refresh_from_db()
        if device_dict:
            Device.objects.create(user=current_user, **device_dict)
        if profile_dict:
            if current_user.profile:
                current_user.profile.update(**profile_dict)
            else:
                profile = Profile.objects.create(**profile_dict)
                current_user.profile = profile
                current_user.save()
        current_user.set_password(password)
        path = ''.join([settings.MEDIA_ROOT, str(current_user.id)])
        if not os.path.exists(path):
            os.mkdir(path)
    return current_user


def create_unauthorized_user():
    user_dict = {
        'role': UserRole.UNAUTHORIZED_USER
    }
    return create_user(user_dict, password='0')


def create_device_user(device_number, push_token, current_user=None):
    user_dict = {
        'role': UserRole.LOGIN_USER
    }
    device_dict = {
        'number': device_number,
        'push_token': push_token
    }
    return create_user(user_dict, password='-1', device_dict=device_dict, current_user=current_user)


def create_phone_user(phone, current_user=None):
    user_dict = {
        'role': UserRole.LOGIN_USER,
        'phone': phone
    }
    return create_user(user_dict, password='-2', current_user=current_user)


def create_login_user(login, email, password, current_user=None):
    user_dict = {
        'role': UserRole.LOGIN_USER,
        'login': login,
        'email': email
    }
    return create_user(user_dict, password=password, current_user=current_user)


def refresh_password(user):
    new_password = get_random_string()
    password = get_hash_password(new_password)
    user.set_password(user.hash_password(password))
    return new_password
