from datetime import date

from django.db import transaction

from pdf.models import *
from pdf.tasks import create_previews


def create_document(pk, owner_id, name, content, num_pages=None, size=None):
    with transaction.atomic():
        file_format = name.split('.')[-1]
        document = Document.objects.create(
            id=pk,
            owner_id=owner_id,
            document_type=DocumentType.LOAD,
            name=name,
            format=DocumentFormat.inverted_dict[file_format],
            body=content,
            num_pages=num_pages,
            size=size
        )
        return document


def create_split_document(source_pk, pk, owner_id,  name, content, num_pages, size):
    with transaction.atomic():
        document = Document.objects.create(
            id=pk,
            owner_id=owner_id,
            document_type=DocumentType.MAKE,
            name=name,
            body=content,
            num_pages=num_pages,
            size=size
        )
        operation = Operation.objects.create(
            owner_id=owner_id,
            operation_type=OperationType.SPLIT,
            status=OperationStatus.SUCCESS
        )
        OperationDocument.objects.create(
            document_id=source_pk,
            operation_id=operation.id,
        )
        OperationDocument.objects.create(
            document_id=pk,
            operation_id=operation.id,
            is_source=False
        )
        create_previews.delay(document.id)
        return document


def create_merge_document(sources, pk, owner_id, name, content, num_pages, size):
    with transaction.atomic():
        document = Document.objects.create(
            id=pk,
            owner_id=owner_id,
            document_type=DocumentType.MAKE,
            name=name,
            body=content,
            num_pages=num_pages,
            size=size
        )
        operation = Operation.objects.create(
            owner_id=owner_id,
            operation_type=OperationType.MERGE,
            status=OperationStatus.SUCCESS
        )
        for source_pk in sources:
            OperationDocument.objects.create(
                document_id=source_pk,
                operation_id=operation.id,
            )
        OperationDocument.objects.create(
            document_id=pk,
            operation_id=operation.id,
            is_source=False
        )
        create_previews.delay(document.id)

        return document


def create_modify_document(sources, pk, owner_id, name, content, num_pages, size):
    with transaction.atomic():
        document = Document.objects.create(
            id=pk,
            owner_id=owner_id,
            document_type=DocumentType.MAKE,
            name=name,
            body=content,
            num_pages=num_pages,
            size=size
        )
        operation = Operation.objects.create(
            owner_id=owner_id,
            operation_type=OperationType.MERGE,
            status=OperationStatus.SUCCESS
        )
        for source_pk in sources:
            OperationDocument.objects.create(
                document_id=source_pk,
                operation_id=operation.id,
            )
        OperationDocument.objects.create(
            document_id=pk,
            operation_id=operation.id,
            is_source=False
        )
        create_previews.delay(document.id)

        return document


def create_converted_document(source_pk, owner, name):
    with transaction.atomic():
        document = Document.objects.create(
            owner=owner,
            document_type=DocumentType.MAKE,
            name=name,
            status=DocumentStatus.NEW
        )
        operation = Operation.objects.create(
            owner=owner,
            operation_type=OperationType.CONVERT,
            status=OperationStatus.PENDING
        )
        OperationDocument.objects.create(
            document_id=source_pk,
            operation_id=operation.id,
        )
        OperationDocument.objects.create(
            document_id=document.id,
            operation_id=operation.id,
            is_source=False
        )
        return document, operation


def success_converted_document(document_id, operation_id, content, num_pages, size):
    document = Document.objects.get(id=document_id)
    operation = Operation.objects.get(id=operation_id)
    with transaction.atomic():
        document.status = DocumentStatus.ACTIVE
        document.body = content
        document.num_pages = num_pages
        document.size = size
        document.save()

        operation.status = OperationStatus.SUCCESS
        operation.save()
        create_previews.delay(document.id)

        return document


def get_downloaded_documents(owner_id):
    return Document.objects.filter(
        owner_id=owner_id,
        downloaded__day=date.today().day
    ).all()


def get_file_link(owner_id, document_id, format='pdf'):
    return ''.join([
        settings.MEDIA_URL,
        str(owner_id),
        '/',
        str(document_id),
        '.',
        format
    ])


def get_file_path(owner_id, document_id, format='pdf'):
    return ''.join([
        settings.MEDIA_ROOT,
        str(owner_id),
        '/',
        str(document_id),
        '.',
        format
    ])


def get_preview_link(owner_id, document_id, format='png'):
    return ''.join([
        settings.MEDIA_URL,
        str(owner_id),
        '/',
        'previews',
        '/',
        str(document_id),
        '/1.',
        format
    ])
