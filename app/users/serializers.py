from rest_framework import serializers

from users.models import *


class LoginDeviceSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=200, source='device_number')
    push_token = serializers.CharField(max_length=200, required=False)


class LoginPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


class ConfirmPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=15)


class CredentialsSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires = serializers.DateTimeField()
    user_id = serializers.UUIDField()


class LoginUserSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()


class RegisterUserSerializer(serializers.Serializer):
    login = serializers.CharField(required=False)
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'login', 'email', 'phone', 'tariff',
                  'email_confirmed', 'phone_confirmed', 'status',
                  'role', 'profile', 'created', 'password_updated',
                  'tariff_updated', 'tariff_finished')


class UserUpdateSerializer(serializers.Serializer):
    tariff = serializers.ChoiceField(choices=list(dict(UserTariff.choices).keys()))
    user_id = serializers.UUIDField()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RestorePasswordSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    code = serializers.CharField()
    new_password = serializers.CharField()


class ConfirmEmailSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    code = serializers.CharField()
    email = serializers.EmailField()


class EmptySerializer(serializers.Serializer):
    pass















