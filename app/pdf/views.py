from os import path
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from pdf.models import *
from pdf.serializers import *
from pdf.actions import get_downloaded_documents
from common.responses import *
from common.decorators import log_request

from users.models import UserRole, UserTariff
from users.common.decorators import auth_required

manual_parameters = [
    {
        'name': 'id',
        'type': openapi.TYPE_STRING,
        'description': 'Идентификатор документа (UUID)'
    },
    {
        'name': 'owner_id',
        'type': openapi.TYPE_STRING,
        'description': 'Идентификатор пользователя (UUID)'
    },
    {
        'name': 'format',
        'type': openapi.TYPE_INTEGER,
        'description': 'Формат документа, PDF = 1 DOCX = 2 DOC = 3 XLSX = 4 XLS = 5 JPEG = 6 PNG = 7'},
    {
        'name': 'document_type',
        'type': openapi.TYPE_INTEGER,
        'description': 'Тип документа: загруженный - 0, созданный - 1'
    },
    {
        'name': 'status',
        'type': openapi.TYPE_INTEGER,
        'description': 'Статус документа: в процессе - 0, доступный для скачивания - 1, архив - 2'
    },
    {
        'name': 'name',
        'type': openapi.TYPE_STRING,
        'description': 'Название файла'
    }
]


def get_manual_parameters():
    params = []
    for param in manual_parameters:
        params.append(openapi.Parameter(
            param['name'],
            openapi.IN_QUERY,
            description=param['description'],
            type=param['type']
        ))
    return params


class PDFViewSet(viewsets.GenericViewSet):
    queryset = Document.objects.filter(status__in=(DocumentStatus.NEW, DocumentStatus.ACTIVE))
    serializer_class = DocumentSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id', 'owner_id', 'format', 'document_type', 'status', 'name']
    ordering_fields = ['created', 'format', 'name', 'owner_id']
    ordering = ['-created']

    document_response = openapi.Response(SUCCESS_RESPONSE, DocumentLinkSerializer)
    previews_response = openapi.Response(SUCCESS_RESPONSE, PreviewsSerializer)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return
        if self.request.user.user.role == UserRole.ADMIN:
            return self.queryset.all()
        return self.queryset.filter(owner_id=self.request.user.user.id).all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action == 'split':
            return DocumentSplitSerializer
        elif self.action == 'merge':
            return DocumentMergeSerializer
        elif self.action == 'modify':
            return DocumentModifySerializer
        elif self.action == 'convert':
            return DocumentConvertSerializer
        if not int(self.request.query_params.get('body', 0)) == 1:
            return DocumentLinkSerializer
        return self.serializer_class

    def get_response_serializer_class(self):
        return DocumentLinkSerializer

    def get_response_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_response_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_manual_parameters())
    @log_request
    def list(self, request, *args, **kwargs):
        """
        Список всех документов пользователя. Админу доступны все документы.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @log_request
    def retrieve(self, request, *args, **kwargs):
        """
        Карточка документа
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @log_request
    def destroy(self, request, *args, **kwargs):
        """
        Переносит документы в архив, физически не удаляет
        """
        instance = self.get_object()
        instance.status = DocumentStatus.ARCHIVE
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={
        201: document_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @log_request
    def create(self, request, *args, **kwargs):
        """
        Загрузка документа. Содержимое файла должно передаваться в base64
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        load_data = serializer.save(owner=request.user.user)
        return Response(
            load_data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(responses={
        201: document_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @action(
        methods=['post'],
        detail=True,
        url_path='split'
    )
    @log_request
    def split(self, request, *args, **kwargs):
        """
        Разделение документа. \n
        Разбиение по номерам страниц или по интервалу. Возвращает новый документ
        """
        source = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        load_data = serializer.save(owner=request.user.user, source=source)
        return Response(load_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        201: document_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @action(
        methods=['post'],
        detail=False,
        url_path='merge'
    )
    @log_request
    def merge(self, request, *args, **kwargs):
        """
        Объединение документов. \n
        Объединение нескольких файлов по порядку.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        load_data = serializer.save(owner=request.user.user)
        return Response(load_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        201: document_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @action(
        methods=['post'],
        detail=True,
        url_path='convert'
    )
    @log_request
    def convert(self, request, *args, **kwargs):
        """
        Конвертация документов. \n
        Конвертация документов в pdf. Возвращает новый документ
        """
        source = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_document = serializer.save(owner=request.user.user, source=source)
        return Response(self.get_response_serializer(new_document).data, status=status.HTTP_201_CREATED)

    @auth_required
    @action(
        methods=['get'],
        detail=True,
        url_path='download'
    )
    @log_request
    def download(self, request, *args, **kwargs):
        """
        Скачать документ.\n
        Метод накладывает ограничение для бесплатных пользователей. \n
        Нельзя скачать более одного документа за день.
        """
        instance = self.get_object()
        owner = self.request.user.user
        if owner.tariff == UserTariff.FREE:
            documents = get_downloaded_documents(owner.id)
            if len(documents) > 1 or (len(documents) == 1 and documents.first().id != instance.id):
                raise ValidationError('Превышен лимит скачиваний')

        serializer = self.get_serializer(instance)

        instance.downloaded = datetime.now()
        instance.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: previews_response,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @action(
        methods=['get'],
        detail=True,
        url_path='previews'
    )
    @log_request
    def get_previews(self, request, *args, **kwargs):
        """
        Получить превью всех страниц документа
        """
        instance = self.get_object()
        previews = []
        if instance.format != DocumentFormat.PDF:
            data = {
                'link': instance.get_previews_link(1),
                'status': 0
            }
            if path.exists(instance.get_previews_path(1)):
                data['status'] = 1
            previews.append(data)
        else:
            if not instance.num_pages:
                maker = PDFMaker(request.user.user)
                instance.num_pages = maker.get_num_pages(instance.file_path)
                instance.save()
                instance.refresh_from_db()

            for number in range(instance.num_pages):
                data = {
                    'link': instance.get_previews_link(number+1),
                    'status': 0
                }
                if path.exists(instance.get_previews_path(number+1)):
                    data['status'] = 1
                previews.append(data)

        return Response(data={'previews': previews}, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        201: document_response,
        400: BAD_REQUEST,
        401: NOT_AUTHORIZED
    })
    @auth_required
    @action(
        methods=['post'],
        detail=False,
        url_path='modify'
    )
    @log_request
    def modify(self, request, *args, **kwargs):
        """
        Объединение и разделение документов. \n
        Объединение страниц разных файлов в один.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        load_data = serializer.save(owner=request.user.user)
        return Response(load_data, status=status.HTTP_201_CREATED)