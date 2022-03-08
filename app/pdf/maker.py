import os
import uuid
import base64
import contextlib

from datetime import datetime

from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger

from pdf.actions import create_split_document, create_merge_document, \
    create_converted_document, get_file_link, get_preview_link
from pdf.models import Document, DocumentType, DocumentStage, DocumentStatus
from pdf.tasks import converted_file, modify_document, merge_document, split_document, load_document
from users.models import UserTariff


class PDFMaker:
    def __init__(self, owner):
        self.owner = owner

    def __get_split_filename(self, format='pdf'):
        return '_'.join([datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), 'split']) + '.' + format

    def __get_modify_filename(self, format='pdf'):
        return '_'.join([datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), 'modified']) + '.' + format

    def __get_merge_filename(self, format='pdf'):
        return '_'.join([datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), 'merged']) + '.' + format

    def __get_convert_filename(self, format='pdf'):
        return '_'.join([datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), 'converted']) + '.' + format

    def __get_load_data(self, result_id, name, document_type=DocumentType.MAKE):
        return {
            "id": result_id,
            "name": name,
            "status": DocumentStatus.NEW,
            "document_type": document_type,
            "link": get_file_link(self.owner.id, result_id),
            "link_status": DocumentStage.LOADING,
            "created": "",
            "updated": "",
            "num_pages": None,
            "size": None,
            "preview_link": get_preview_link(self.owner.id, result_id),
            "preview_status": DocumentStage.LOADING
        }

    def convert_from_pdf(self):
        pass

    def get_num_pages(self, path):
        output_pdf = PdfFileReader(path)
        return output_pdf.getNumPages()

    def load_new_document(self, document: Document):
        load_document.apply_async(
            kwargs={
                'owner_id': self.owner.id,
                'document_id': document.id,
            }
        )
        return self.__get_load_data(document.id, document.name, document_type=DocumentType.LOAD)

    def split_pdf_pages(self, source: Document, pages: list):
        split_id = uuid.uuid4()
        name = self.__get_split_filename()
        split_document.apply_async(
            kwargs={
                'owner_id': self.owner.id,
                'split_id': split_id,
                'source_id': source.id,
                'name': name,
                'pages': pages
            }
        )
        return self.__get_load_data(split_id, name)

    def split_pdf_range(self, source: Document, range_pages: list):
        split_id = uuid.uuid4()
        name = self.__get_split_filename()
        split_document.apply_async(
            kwargs={
                'owner_id': self.owner.id,
                'split_id': split_id,
                'source_id': source.id,
                'name': name,
                'pages': list(range(range_pages[0], range_pages[1]+1))
            }
        )
        return self.__get_load_data(split_id, name)

    def merge_pdf(self, source_dict: dict):
        merge_id = uuid.uuid4()
        name = self.__get_merge_filename()
        merge_document.apply_async(
            kwargs={
                'owner_id': self.owner.id,
                'merge_id': merge_id,
                'source_dict': source_dict,
                'name': name
            }
        )
        return self.__get_load_data(merge_id, name)

    def convert_to_pdf(self, source):
        document, operation = create_converted_document(
            source_pk=source.id,
            owner=self.owner,
            name=self.__get_convert_filename(),
        )
        converted_file.apply_async(
            kwargs={
                'document_id': document.id,
                'operation_id': operation.id,
                'user_path': self.owner.user_path,
                'file_path': source.file_path
            }
        )
        return document

    def modify_pdf(self, source_dict: dict):
        modify_id = uuid.uuid4()
        name = self.__get_modify_filename()

        modify_document.apply_async(
            kwargs={
                'owner_id': self.owner.id,
                'modify_id': modify_id,
                'source_dict': source_dict,
                'name': name
            }
        )
        return self.__get_load_data(modify_id, name)




