from datetime import datetime

from django.contrib.auth import authenticate
from django.http import HttpResponse
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from users.models import UserRole, User, UserTariff
from common.responses import *
from common.errors import ApiError
from common.decorators import log_request
from users.common.actions import create_device_user, create_login_user, create_unauthorized_user
from users.common.utils import get_hash_password
from users.serializers import *

from notifications.actions import send_phone_code
from notifications.tasks import confirm_email, refresh_password

from notifications.models import ActivationCode, CodeType
from common.utils import get_logger
from users.common.decorators import admin_required

logger = get_logger('../logs/user_requests.log')


class UserViewSet(viewsets.GenericViewSet):

    queryset = User.objects.select_related('profile').prefetch_related('devices')
    serializer_class = UserSerializer

    REFRESHTOKEN_COOKIE = 'REFRESHTOKEN'
    credentials_response = openapi.Response(SUCCESS_RESPONSE, CredentialsSerializer)
    user_response = openapi.Response(SUCCESS_RESPONSE, UserSerializer)

    def get_queryset(self):
        if self.request.user.user.role == UserRole.ADMIN:
            return self.queryset.all()
        return self.queryset.filter(id=self.request.user.user.id).first()

    def get_serializer_class(self):
        return self.serializer_class

    def __set_refreshtoken_cookie(self, response, refresh_token):
        response.set_cookie(
            self.REFRESHTOKEN_COOKIE,
            value=refresh_token,
            secure=True,
            httponly=True,
        )

    def __delete_refreshtoken_cookie(self, response):
        response.delete_cookie(self.REFRESHTOKEN_COOKIE)

    def __get_credentials_response(self, user, refresh_token=None):
        if refresh_token is None:
            refresh_token = RefreshToken.for_user(user.auth_user)

        serializer = CredentialsSerializer(data={
            'access_token': str(refresh_token.access_token),
            'expires': datetime.utcfromtimestamp(refresh_token['exp']),
            'user_id': user.pk
        })

        if not serializer.is_valid():
            raise RuntimeError(serializer.errors)

        response = Response(serializer.validated_data)
        self.__set_refreshtoken_cookie(response, str(refresh_token))

        return response

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST
    }, request_body=EmptySerializer)
    @action(
        detail=False,
        methods=['post'],
        permission_classes=(AllowAny,),
    )
    @log_request
    def unauthorized(self, request, **kwargs):
        """
        Создание анонимного пользователя
        """
        current_user = create_unauthorized_user()
        return self.__get_credentials_response(current_user)

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=LoginDeviceSerializer,
        permission_classes=(AllowAny,),
    )
    @log_request
    def login_device(self, request, **kwargs):
        """
        Регистрация и вход по device_id
        """
        logger.info(f"{request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = Device.objects.filter(
            number=serializer.validated_data['device_number']
        ).first()
        push_token = serializer.validated_data.get('push_token')
        if not device:
            if not self.request.user.is_anonymous:
                current_user = create_device_user(
                    device_number=serializer.validated_data['device_number'],
                    push_token=push_token,
                    current_user=self.request.user.user
                )
            else:
                current_user = create_device_user(
                    device_number=serializer.validated_data['device_number'],
                    push_token=push_token
                )
        else:
            current_user = device.user
            if push_token:
                device.push_token = push_token
                device.save()

        return self.__get_credentials_response(current_user)

    @swagger_auto_schema(responses={
        200: SEND_CODE_SUCCES,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=LoginPhoneSerializer,
    )
    @log_request
    def login_phone(self, request, **kwargs):
        """
        Регистрация и вход по телефонному номеру.\n
        Посылает смс код для подтверждения.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get('phone')
        user = User.objects.filter(phone=phone, phone_confirmed=True).first()
        if user:
            send_phone_code(user, phone)
        else:
            send_phone_code(self.request.user.user, phone)

        return Response('Код отправлен', status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=ConfirmPhoneSerializer,
    )
    def confirm_phone(self, request, **kwargs):
        """
        Подтверждение номера телефона
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get('phone', '')
        code = serializer.validated_data.get('code', '')
        user = User.objects.filter(phone=phone, phone_confirmed=True).first()
        if not user:
            user = self.request.user.user
        activation_code = ActivationCode.objects.filter(
            code=code,
            code_type=1,
            user_id=user.id
        ).first()
        if not activation_code:
            raise ApiError('WRONG_CODE')
        if activation_code.expired():
            raise ApiError('CODE_EXPIRED')
        if user == self.request.user.user:
            user.role = UserRole.LOGIN_USER
            user.phone = phone
            user.phone_confirmed = True
            user.save()
        activation_code.delete()
        return self.__get_credentials_response(user)

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=LoginUserSerializer,
        permission_classes=(AllowAny,),
    )
    @log_request
    def login_password(self, request, **kwargs):
        """
        Вход по логину и паролю
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get('password')
        login = serializer.validated_data.get('login')
        user = User.objects.filter(login=login).first()
        if not user:
            return Response('Учетные данные неверны', status=status.HTTP_401_UNAUTHORIZED)
        password = user.hash_password(
            password
        )
        auth_user = authenticate(
            request=request,
            username=user.id,
            password=password
        )
        if auth_user is None:
            return Response('Учетные данные неверны', status=status.HTTP_401_UNAUTHORIZED)

        return self.__get_credentials_response(user)

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=RegisterUserSerializer,
        permission_classes=(AllowAny,),
    )
    @log_request
    def register(self, request, **kwargs):
        """
        Регистрация пользователя с логином и паролем
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email', '')
        password = serializer.validated_data.get('password', '')
        login = serializer.validated_data.get('login', email)
        user = User.objects.filter(login=login).first()
        if user:
            raise ApiError('Пользователь с таким учетными данными уже существует')
        if not self.request.user.is_anonymous:
            user = create_login_user(login, email, password, self.request.user.user)
        else:
            user = create_login_user(login, email, password)
        confirm_email.delay(email, user.id)
        return self.__get_credentials_response(user)

    @swagger_auto_schema(responses={
        200: credentials_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['get'],
        permission_classes=(AllowAny,),
        url_path='refresh-token',
    )
    @log_request
    def refresh_token(self, request, **kwargs):
        """
        Обновление refresh токена
        """
        refresh_token = self.request.COOKIES.get(self.REFRESHTOKEN_COOKIE)

        refresh = RefreshToken(refresh_token)
        user_id = refresh.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects \
            .filter(auth_user=user_id) \
            .first()
        if user is None or user.status != UserStatus.ACTIVE:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        refresh.set_jti()
        refresh.set_exp()

        return self.__get_credentials_response(user, refresh_token=refresh)

    @swagger_auto_schema(responses={
        200: SUCCESS_RESPONSE
    })
    @action(
        detail=False,
        methods=['get'],
        permission_classes=(AllowAny,),
        url_path='revoke-token',
    )
    @log_request
    def revoke_token(self, request, **kwargs):
        """
        Очистка  refreshtoken_cookie
        """
        response = HttpResponse('', content_type='text/plain')
        self.__delete_refreshtoken_cookie(response)
        return response

    @swagger_auto_schema(responses={
        200: user_response,
        401: NOT_AUTHORIZED
    })
    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    @log_request
    def get_current_user(self, request, **kwargs):
        """
        Информация о текущем юзере
        """
        from pdf.models import DocumentType, OperationType
        current_user = self.request.user.user
        load_count = len(current_user.documents.filter(document_type=DocumentType.LOAD).all())
        split_count = len(current_user.operations.filter(operation_type=OperationType.SPLIT).all())
        merge_count = len(current_user.operations.filter(operation_type=OperationType.MERGE).all())
        convert_count = len(current_user.operations.filter(operation_type=OperationType.CONVERT).all())
        serializer = self.get_serializer(instance=current_user)
        data = {
            'load_count': load_count,
            'split_count': split_count,
            'merge_count': merge_count,
            'convert_count': convert_count,
        }
        data.update(serializer.data)
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: user_response,
        401: NOT_AUTHORIZED,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @action(
        detail=False,
        methods=['put'],
        permission_classes=(IsAuthenticated,),
        serializer_class=UserUpdateSerializer,
        url_path='update-tariff'
    )
    @admin_required
    @log_request
    def update_tariff(self, request, *args, **kwargs):
        """
        Смена тарифа пользователя.
        Доступно только администратору.
        0 - Бесплатный тариф, 1 - Премиум месяц, 2 - три месяца, 3- год
        """
        update_user = User.objects.filter(id=request.data.get('user_id')).first()
        if not update_user:
            raise ValidationError('Пользователь не найден')
        if request.data.get('tariff') not in dict(UserTariff.choices):
            raise ValidationError('Тариф не найден')
        update_user.set_tariff(request.data.get('tariff'))
        serializer = UserSerializer(instance=update_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: SUCCESS_RESPONSE,
        401: NOT_AUTHORIZED,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=EmailSerializer,
        permission_classes=(AllowAny,),
        url_path='send-password',
    )
    @log_request
    def send_password(self, request, **kwargs):
        """
        Отправляет письмо на email для восстановления
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            current_email = serializer.validated_data['email']

            current_user = User.objects.filter(
                email=current_email
            ).first()
            if not current_user:
                raise ValidationError('Пользователь c таким email не найден')

            refresh_password.delay(email=current_email, user_id=current_user.id)

            return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: user_response,
        401: NOT_AUTHORIZED,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=RestorePasswordSerializer,
        permission_classes=(AllowAny,),
        url_path='restore-password',
    )
    @log_request
    def restore_password(self, request, **kwargs):
        """
        Восстанавливает пароль по ссылке из письма
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            code = serializer.validated_data['code']
            user_id = serializer.validated_data['user_id']
            activation_code = ActivationCode.objects.filter(
                code=code,
                code_type=CodeType.EMAIL,
                user_id=user_id
            ).first()
            if not activation_code:
                raise ValidationError('Код не найден')
            else:
                activation_code.delete()

            current_user = User.objects.filter(pk=user_id).first()
            if not current_user:
                raise ValidationError('Пользователь не найден')

            new_password = serializer.validated_data['new_password']
            current_user.set_password(new_password)
            return self.__get_credentials_response(current_user)

    @swagger_auto_schema(responses={
        200: user_response,
        401: NOT_AUTHORIZED,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=ChangePasswordSerializer,
        permission_classes=(IsAuthenticated,),
        url_path='change-password',
    )
    def change_password(self, request, **kwargs):
        """
        Обновляет пароль (надо указать старый)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = request.user.user.hash_password(
            serializer.validated_data['old_password']
        )

        auth_user = authenticate(
            request=request,
            username=request.user.username,
            password=password
        )
        if auth_user is None:
            return Response(data='Wrong old password', status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            new_password = serializer.validated_data['new_password']
            user = auth_user.user

            auth_user.set_password(user.hash_password(new_password))
            auth_user.save()

            return self.__get_credentials_response(user)

    @swagger_auto_schema(responses={
        200: user_response,
        401: NOT_AUTHORIZED,
        400: BAD_REQUEST,
        403: ACCESS_FORBIDDEN
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=ConfirmEmailSerializer,
        permission_classes=(AllowAny,),
        url_path='confirm-email',
    )
    def confirm_email_adress(self, request, **kwargs):
        """
        Подтверждает email. Метод должен вызываться по ссылке
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user_id = serializer.validated_data['user_id']
            code = serializer.validated_data['code']
            activation_code = ActivationCode.objects.filter(
                code=code,
                code_type=CodeType.EMAIL,
                user_id=user_id
            )
            if not activation_code.first():
                raise ValidationError('Код не найден')
            else:
                activation_code.delete()
            current_user = User.objects.filter(pk=user_id)
            if not current_user:
                raise ValidationError('Пользователь не найден')

            current_user.set_email(serializer.validated_data['email'])
            return self.__get_credentials_response(current_user)

