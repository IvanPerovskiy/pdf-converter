import uuid

from django.db import models
from django.conf import settings
from django.utils import safestring

from common.utils import b64e


class DocumentFormat:
    PDF = 1
    DOCX = 2
    DOC = 3
    XLSX = 4
    XLS = 5
    JPEG = 6
    PNG = 7
    JPG = 8

    choices = (
        (PDF, 'pdf'),
        (DOCX, 'docx'),
        (DOC, 'doc'),
        (XLSX, 'xlsx'),
        (XLS, 'xls'),
        (JPEG, 'jpeg'),
        (PNG, 'png'),
        (JPG, 'jpg')
    )
    inverted_dict = {v: k for k, v in choices}

    ACCESS_CONVERT_FORMATS = {
        'doc': DOC,
        'docx': DOCX,
        'xls': XLS,
        'xlsx': XLSX,
        'jpg': JPG,
        'jpeg': JPEG,
        'png': PNG
    }


class DocumentType:
    LOAD = 0
    MAKE = 1

    choices = (
        (LOAD, 'Загруженный'),
        (MAKE, 'Сгенерированный'),
    )


class DocumentStatus:
    NEW = 0
    ACTIVE = 1
    ARCHIVE = 2

    choices = (
        (NEW, 'Новый'),
        (ACTIVE, 'Активный'),
        (ARCHIVE, 'Архив')
    )


class OperationType:
    CONVERT = 1
    SPLIT = 2
    MERGE = 3

    choices = (
        (CONVERT, 'Конвертировать'),
        (SPLIT, 'Разделить'),
        (MERGE, 'Объединить')
    )


class OperationStatus:
    NEW = 0
    PENDING = 1
    SUCCESS = 2
    ERROR = 3

    choices = (
        (NEW, 'Новая'),
        (PENDING, 'В процессе'),
        (SUCCESS, 'Успешно'),
        (ERROR, 'Ошибка'),
    )


class DocumentStage:
    LOADING = 0
    SUCCESS = 1
    DELETED = 2

    choices = (
        (LOADING, 'Загружается'),
        (SUCCESS, 'Загружен'),
        (DELETED, 'Удален'),
    )


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('users.User', related_name='documents', on_delete=models.PROTECT)

    format = models.SmallIntegerField(choices=DocumentFormat.choices, default=DocumentFormat.PDF)
    document_type = models.SmallIntegerField(choices=DocumentType.choices, default=DocumentType.LOAD)
    status = models.SmallIntegerField(choices=DocumentStatus.choices, default=DocumentStatus.ACTIVE)

    name = models.CharField(max_length=200)
    body = models.BinaryField()
    num_pages = models.IntegerField(null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    downloaded = models.DateTimeField(null=True, blank=True)

    link_stage = models.SmallIntegerField(choices=DocumentStage.choices, default=0)
    preview_stage = models.SmallIntegerField(choices=DocumentStage.choices, default=0)

    @property
    def operations(self):
        operation_ids = OperationDocument.objects.filter(document_id=self.id).values_list('operation_id', flat=True)
        return Operation.objects.filter(id__in=operation_ids).all()

    @property
    def file_path(self):
        return ''.join([
            settings.MEDIA_ROOT,
            str(self.owner_id),
            '/',
            str(self.id),
            '.',
            dict(DocumentFormat.choices)[self.format]
        ])

    @property
    def link(self):
        return ''.join([
            settings.MEDIA_URL,
            str(self.owner_id),
            '/',
            str(self.id),
            '.',
            dict(DocumentFormat.choices)[self.format]
        ])

    @property
    def preview_link(self):
        return ''.join([
            settings.MEDIA_URL,
            str(self.owner_id),
            '/',
            'previews',
            '/',
            str(self.id),
            '/1.',
            dict(DocumentFormat.choices)[DocumentFormat.PNG]
        ])

    def get_previews_link(self, page_number):
        return ''.join([
            settings.MEDIA_URL,
            str(self.owner_id),
            '/',
            'previews',
            '/',
            str(self.id),
            '/',
            str(page_number),
            '.',
            dict(DocumentFormat.choices)[DocumentFormat.PNG]
        ])

    def get_previews_path(self, page_number):
        return ''.join([
            settings.MEDIA_ROOT,
            str(self.owner_id),
            '/',
            'previews',
            '/',
            str(self.id),
            '/',
            str(page_number),
            '.',
            dict(DocumentFormat.choices)[DocumentFormat.PNG]
        ])


class Operation(models.Model):
    owner = models.ForeignKey('users.User', related_name='operations', on_delete=models.PROTECT)
    operation_type = models.SmallIntegerField(choices=OperationType.choices)
    status = models.SmallIntegerField(choices=OperationStatus.choices, default=OperationStatus.NEW)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def documents(self):
        document_ids = OperationDocument.objects.filter(operation_id=self.id).values_list('document_id', flat=True)
        return Document.objects.filter(id__in=document_ids).all()

    def set_status(self, status):
        self.status = status
        self.save()


class OperationDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='operation_ids')
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, related_name='document_ids')
    is_source = models.BooleanField(default=True, verbose_name="Это исходный документ?")
    created = models.DateTimeField(auto_now_add=True)
