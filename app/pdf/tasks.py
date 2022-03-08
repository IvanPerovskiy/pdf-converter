import re
import os
import base64
import requests
import subprocess
import contextlib

from celery import shared_task
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PIL import Image
from django.conf import settings

from pdf.models import Document, DocumentFormat


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output


def convert(folder, source, format='pdf', timeout=None):
    args = ['libreoffice', '--headless', '--convert-to',
            format, '--outdir', folder, source]

    process = subprocess.run(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=timeout)

    filename = re.search('-> (.*?) using filter', process.stdout.decode())

    if filename is None:
        print(process.stdout.decode())
        raise LibreOfficeError(process.stdout.decode())
    else:
        return filename.group(1)


def convert_premium(folder, source, format='pdf'):
    params = {
        'folder': folder,
        'source': source,
        'format': format
    }
    try:
        response = requests.post("http://balancer/convert", json=params).json()
        return response['output_path']
    except:
        print('Fail')
        return convert(folder, source, format)


@shared_task
def converted_file(document_id, operation_id, user_path, file_path):
    from pdf.actions import success_converted_document

    output_path = convert_premium(user_path, file_path)

    rename_path = output_path.split('/')
    rename_path[-1] = '.'.join([str(document_id), 'pdf'])
    rename_path = '/'.join(rename_path)
    os.rename(output_path, rename_path)
    output_pdf = PdfFileReader(rename_path)
    num_pages = output_pdf.getNumPages()
    size = os.path.getsize(rename_path)
    with open(rename_path, "rb") as content:
        document = success_converted_document(
            document_id, operation_id, base64.b64encode(content.read()), num_pages, size
        )
    return document


@shared_task
def create_previews(document_id):
    document = Document.objects.filter(pk=document_id).first()
    folder = ''.join([document.owner.user_path, 'previews/', str(document.id)])
    os.makedirs(folder, exist_ok=True)
    if document.format != DocumentFormat.PDF:
        source = document.file_path
        image_path = convert_premium(folder=folder, source=source, format='png')
        os.rename(image_path, '/'.join([folder, '1.png']))
    else:
        input_pdf = PdfFileReader(document.file_path)
        num_pages = input_pdf.getNumPages()
        for number in range(num_pages):
            output = PdfFileWriter()
            output.addPage(input_pdf.getPage(number))
            pdf_preview_path = '/'.join([folder, str(number+1) + '.pdf'])
            with open(pdf_preview_path, "wb") as output_stream:
                output.write(output_stream)

            image_path = convert_premium(folder=folder, source=pdf_preview_path, format='png')
            img = Image.open(image_path)
            new_image = img.resize((settings.PREVIEW_WIDTH, settings.PREVIEW_HEIGHT))
            new_image.save(image_path)
            os.remove(pdf_preview_path)


@shared_task
def load_document(owner_id, document_id):
    from pdf.actions import get_file_path

    document = Document.objects.get(pk=document_id)
    name = document.name
    file_format = name.split('.')[-1]
    output_path = get_file_path(owner_id, document_id, format=file_format)
    with open(output_path, 'wb') as result_file:
        result_file.write(document.body)

    document.size = os.path.getsize(output_path)
    if file_format == 'pdf':
        document.num_pages = PdfFileReader(output_path).getNumPages()
    document.save()

    create_previews.delay(document_id)


@shared_task
def modify_document(owner_id, modify_id, source_dict, name):
    from pdf.actions import create_modify_document, get_file_path

    output = PdfFileWriter()
    for source in source_dict:
        document = Document.objects.get(pk=source['id'])
        input_pdf = PdfFileReader(document.file_path)
        output.addPage(input_pdf.getPage(source['page_number'] - 1))

    output_path = get_file_path(owner_id, modify_id)
    with open(output_path, "wb") as output_stream:
        output.write(output_stream)
    num_pages = PdfFileReader(output_path).getNumPages()
    size = os.path.getsize(output_path)
    with open(output_path, "rb") as content:
        create_modify_document(
            sources={item['id'] for item in source_dict},
            pk=modify_id,
            owner_id=owner_id,
            name=name,
            content=base64.b64encode(content.read()),
            num_pages=num_pages,
            size=size
        )


@shared_task
def merge_document(owner_id, merge_id, source_dict, name):
    from pdf.actions import create_merge_document, get_file_path

    pdf_files_list = []
    for source in source_dict:
        pdf_files_list.append(get_file_path(owner_id, source['id']))

    with contextlib.ExitStack() as stack:
        pdf_merger = PdfFileMerger()
        files = [stack.enter_context(open(pdf, 'rb')) for pdf in pdf_files_list]
        for f in files:
            pdf_merger.append(f)
        output_path = get_file_path(owner_id, merge_id)
        with open(output_path, 'wb') as pdf_file_merged:
            pdf_merger.write(pdf_file_merged)
    num_pages = PdfFileReader(output_path).getNumPages()
    size = os.path.getsize(output_path)
    source_ids = [source['id'] for source in source_dict]
    with open(output_path, "rb") as content:
        create_merge_document(
            sources=source_ids,
            pk=merge_id,
            owner_id=owner_id,
            name=name,
            content=base64.b64encode(content.read()),
            num_pages=num_pages,
            size=size
        )


@shared_task
def split_document(owner_id, split_id, source_id, name, pages):
    from pdf.actions import create_split_document, get_file_path
    output_path = get_file_path(owner_id, split_id)
    input_pdf = PdfFileReader(get_file_path(owner_id, source_id))
    output = PdfFileWriter()
    for number in pages:
        # Так как номера страниц в PyPDF начинаются с 0, отнимаем единицу
        output.addPage(input_pdf.getPage(number - 1))
    with open(output_path, "wb") as output_stream:
        output.write(output_stream)
    num_pages = PdfFileReader(output_path).getNumPages()
    size = os.path.getsize(output_path)
    with open(output_path, "rb") as content:
        create_split_document(
            source_pk=source_id,
            pk=split_id,
            owner_id=owner_id,
            name=name,
            content=base64.b64encode(content.read()),
            num_pages=num_pages,
            size=size
        )
