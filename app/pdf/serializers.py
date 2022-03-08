import os
import base64

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from pdf.models import *
from pdf.maker import PDFMaker
from common.utils import get_logger

logger = get_logger('../logs/pdf_requests.log')


class ApiPDFError(ValidationError):
    def __init(self, detail=None, code=None):
        super().__init__(detail, code)
        logger.info(detail)


class BinaryField(serializers.Field):

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            decode_data = base64.b64decode(data)
        except:
            raise ApiPDFError('Невозможно декодировать тело документа')
        return decode_data


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'name', 'body', 'status', 'document_type', 'link',
                  'created', 'updated', 'num_pages', 'size', 'preview_link')


class PreviewSerializer(serializers.Serializer):
    link = serializers.CharField()
    status = serializers.ChoiceField(choices=[0,1])


class PreviewsSerializer(serializers.Serializer):
    previews = PreviewSerializer()


class DocumentLinkSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()
    num_pages = serializers.SerializerMethodField()
    link_status = serializers.SerializerMethodField()
    preview_status = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ('id', 'name', 'status', 'document_type', 'link', 'link_status',
                  'created', 'updated', 'num_pages', 'size', 'preview_link', 'preview_status')

    def get_size(self, instance):
        try:
            if not instance.size:
                instance.size = os.path.getsize(instance.file_path)
                instance.save()
                instance.refresh_from_db()
        except:
            pass
        return instance.size

    def get_num_pages(self, instance):
        if not instance.num_pages:
            if instance.format == DocumentFormat.PDF:
                try:
                    maker = PDFMaker(instance.owner)
                    instance.num_pages = maker.get_num_pages(instance.file_path)
                    instance.save()
                    instance.refresh_from_db()
                except:
                    pass
        return instance.num_pages

    def get_link_status(self, instance):
        if not instance.link_stage:
            if os.path.exists(instance.file_path):
                instance.link_stage = 1
                instance.save()
                instance.refresh_from_db()
        return instance.link_stage

    def get_preview_status(self, instance):
        if not instance.preview_stage:
            if os.path.exists(instance.get_previews_path(page_number=1)):
                instance.preview_stage = 1
                instance.save()
                instance.refresh_from_db()
        return instance.preview_stage


class DocumentCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    body = BinaryField()

    def create(self, validated_data):
        from pdf.actions import create_document
        name = validated_data['name']
        owner = validated_data['owner']
        document_id = uuid.uuid4()
        document = create_document(
            document_id,
            owner.id,
            name,
            content=validated_data['body'])
        maker = PDFMaker(validated_data['owner'])
        return maker.load_new_document(document)


class DocumentSplitSerializer(serializers.Serializer):
    pages = serializers.ListField(required=False)
    range_pages = serializers.ListField(required=False)

    def validate(self, data):
        super().validate(data)
        if not data.get('range_pages') and not data.get('pages'):
            raise ApiPDFError('Один из параметров - range или pages  должен быть передан')
        if not data.get('range_pages') and not data.get('pages'):
            raise ApiPDFError('range и pages не могут быть переданы одновременно')
        if data.get('range_pages') and len(data['range_pages']) != 2:
            raise ApiPDFError('В диапазон должны передаваться два числа')

        return data

    def create(self, validated_data):
        source = validated_data['source']
        if source.format != DocumentFormat.PDF:
            raise ApiPDFError(f"Разбиение доступно только для pdf файлов")
        maker = PDFMaker(validated_data['owner'])
        if pages := validated_data.get('pages'):
            return maker.split_pdf_pages(source, pages)
        elif range_pages := validated_data.get('range_pages'):
            return maker.split_pdf_range(source, range_pages)


class SourceSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class SourceModifySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    page_number = serializers.IntegerField()


class DocumentMergeSerializer(serializers.Serializer):
    sources = SourceSerializer(many=True)

    def validate(self, data):
        super().validate(data)
        for source in data['sources']:
            document = Document.objects.filter(id=source['id']).first()
            if not document:
                raise ApiPDFError(f"Документ {source['id']} не найден")
            if document.format != DocumentFormat.PDF:
                raise ApiPDFError(f"Объединение доступно только для pdf файлов")
        return data

    def create(self, validated_data):
        sources = validated_data['sources']
        maker = PDFMaker(validated_data['owner'])
        return maker.merge_pdf(sources)


class DocumentModifySerializer(serializers.Serializer):
    sources = SourceModifySerializer(many=True)

    def validate(self, data):
        super().validate(data)
        for source_id in {item['id'] for item in data['sources']}:
            document = Document.objects.filter(id=source_id).first()
            if not document:
                raise ApiPDFError(f"Документ {source_id} не найден")
            if document.format != DocumentFormat.PDF:
                raise ApiPDFError(f"Редактирование доступно только для pdf файлов")
        return data

    def create(self, validated_data):
        sources = validated_data['sources']
        maker = PDFMaker(validated_data['owner'])
        return maker.modify_pdf(sources)


class DocumentConvertSerializer(serializers.Serializer):
    document_format = serializers.CharField(default='pdf')

    def create(self, validated_data):
        source = validated_data['source']
        if source.format not in DocumentFormat.ACCESS_CONVERT_FORMATS.values():
            raise ApiPDFError('Конвертация файла с данным форматом недоступна')
        maker = PDFMaker(validated_data['owner'])
        if validated_data['document_format'] == 'pdf':
            return maker.convert_to_pdf(source)
