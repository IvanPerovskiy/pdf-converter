from django.contrib import admin

from pdf.models import *


class DocumentAdmin(admin.ModelAdmin):
    model = Document
    list_display = (
        'id', 'format', 'document_type', 'status', 'name', 'num_pages', 'size', 'created', 'downloaded'
    )


class OperationAdmin(admin.ModelAdmin):
    model = Operation
    list_display = (
        'operation_type', 'status', 'created'
    )


class OperationDocumentAdmin(admin.ModelAdmin):
    model = OperationDocument
    list_display = (
        'document_id', 'operation_id'
    )


admin.site.register(Document, DocumentAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(OperationDocument, OperationDocumentAdmin)
