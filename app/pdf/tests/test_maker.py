import base64

from users.tests.parent import ParentTestCase
from users.models import UserTariff
from pdf.models import *


class PDFTestCase(ParentTestCase):

    def setUp(self):
        super().setUp()
        self.load_path = '/app/pdf/tests/data/input'
        self.make_path = '/app/pdf/tests/data/output'

    def test_split(self):
        input_path = '/'.join([self.load_path, 'test.pdf'])
        content = base64.b64encode(open(input_path, 'rb').read())

        response = self.device_user.post('/api/documents/', {
            'name': 'new.pdf',
            'body': content
        }, format='json')
        self.assertEqual(response.status_code, 201)
        document_id = response.data['id']
        document = Document.objects.get(pk=document_id)
        input_path = '/'.join([self.load_path, 'test.pdf'])
        output_path = self.make_path
        response = self.device_user.post(f'/api/documents/{document_id}/split', {
            'pages': [1, 2, 5],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        split_document_id = response.data['id']
        split_document = Document.objects.get(pk=split_document_id)
        self.assertEqual(split_document.name.endswith('split.pdf'), True)
        self.assertEqual(split_document.format, DocumentFormat.PDF)

        response = self.device_user.post(f'/api/documents/{document_id}/split', {
            'range_pages': [1, 5],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        document_id = response.data['id']
        document = Document.objects.get(pk=document_id)
        self.assertEqual(document.name.endswith('split.pdf'), True)
        self.assertEqual(document.format, DocumentFormat.PDF)

        response = self.device_user.get(f'/api/documents/{document_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['num_pages'], 5)

    def test_base64(self):
        input_path = '/'.join([self.load_path, 'test.pdf'])
        content = base64.b64encode(open(input_path, 'rb').read())
        output_path = '/'.join([self.make_path, 'new_test.pdf'])
        with open(output_path, 'wb') as result_file:
            result_file.write(base64.b64decode(content))

    def test_create(self):
        input_path = '/'.join([self.load_path, 'test.pdf'])
        content = base64.b64encode(open(input_path, 'rb').read())

        response = self.device_user.post('/api/documents/', {
            'name': 'new.pdf',
            'body': content
        }, format='json')
        self.assertEqual(response.status_code, 201)
        document_id = response.data['id']
        document = Document.objects.get(pk=document_id)
        self.assertEqual(document.name, 'new.pdf')
        self.assertEqual(document.format, DocumentFormat.PDF)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 1)
        self.assertEqual(response.data['split_count'], 0)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 0)

        response = self.device_user.get('/api/documents/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('body' not in response.data[0].keys(), True)

        response = self.device_user.get('/api/documents/?body=1')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('body' in response.data[0].keys(), True)

        response = self.device_user.get(f'/api/documents/{document_id}?body=0')
        self.assertEqual(response.data['num_pages'], 10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('body' not in response.data.keys(), True)

        response = self.device_user.post(f'/api/documents/{document_id}/split', {
            'pages': [1, 3, 6, 10],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        new_document_id = response.data['id']
        document = Document.objects.get(pk=new_document_id)
        self.assertEqual(document.name.endswith('split.pdf'), True)
        self.assertEqual(document.format, DocumentFormat.PDF)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 1)
        self.assertEqual(response.data['split_count'], 1)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 0)

        response = self.device_user.post(f'/api/documents/merge', {
            'sources': [
                {'id': document_id},
                {'id': new_document_id}
            ],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        new_document_id = response.data['id']
        document = Document.objects.get(pk=new_document_id)
        self.assertEqual(document.name.endswith('merged.pdf'), True)
        self.assertEqual(document.format, DocumentFormat.PDF)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 1)
        self.assertEqual(response.data['split_count'], 1)
        self.assertEqual(response.data['merge_count'], 1)
        self.assertEqual(response.data['convert_count'], 0)

        response = self.device_user.get(f'/api/documents/{document_id}/download?body=0')
        self.assertEqual(response.status_code, 200)

        response = self.device_user.get(f'/api/documents/{document_id}/download?body=0')
        self.assertEqual(response.status_code, 200)

        response = self.device_user.get(f'/api/documents/{new_document_id}/download?body=0')
        self.assertEqual(response.status_code, 400)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        response = self.device_user.put(f'/api/users/update-tariff', {
            'tariff': UserTariff.MONTH
        }, format='json')
        self.assertEqual(response.status_code, 403)

        response = self.admin_user.put(f'/api/users/update-tariff', {
            'tariff': UserTariff.MONTH,
            'user_id': self.current_device_user.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.current_device_user.refresh_from_db()
        self.assertEqual(self.current_device_user.tariff, UserTariff.MONTH)
        print(response.json())

        response = self.device_user.get(f'/api/documents/{new_document_id}/download?body=0')
        self.assertEqual(response.status_code, 200)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)

    def test_converted(self):
        input_path = '/'.join([self.load_path, 'test1.docx'])
        content = base64.b64encode(open(input_path, 'rb').read())

        response = self.device_user.post('/api/documents/', {
            'name': 'new.docx',
            'body': content
        }, format='json')
        self.assertEqual(response.status_code, 201)
        document_id = response.data['id']
        document = Document.objects.get(pk=document_id)
        self.assertEqual(document.name, 'new.docx')
        self.assertEqual(document.format, DocumentFormat.DOCX)

        response = self.device_user.get('/api/documents/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('body' not in response.data[0].keys(), True)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 1)
        self.assertEqual(response.data['split_count'], 0)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 0)

        response = self.device_user.get('/api/documents/?body=1')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('body' in response.data[0].keys(), True)

        response = self.device_user.get(f'/api/documents/{document_id}?body=0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['num_pages'], None)
        self.assertEqual('body' not in response.data.keys(), True)

        response = self.admin_user.put(f'/api/users/update-tariff', {
            'tariff': UserTariff.FREE,
            'user_id': self.current_device_user.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.current_device_user.refresh_from_db()
        self.assertEqual(self.current_device_user.tariff, UserTariff.FREE)

        response = self.device_user.post(f'/api/documents/{document_id}/convert')
        self.assertEqual(response.status_code, 201)

        new_document_id = response.data['id']
        document = Document.objects.get(pk=new_document_id)
        self.assertEqual(document.format, DocumentFormat.PDF)
        self.assertEqual(document.name.endswith('converted.pdf'), True)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 1)
        self.assertEqual(response.data['split_count'], 0)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 1)

        response = self.device_user.get(f'/api/documents/{document_id}/previews')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['previews']), 1)
        response = self.device_user.get(f'/api/documents/{new_document_id}/previews')
        self.assertEqual(response.status_code, 200)

        response = self.device_user.get(f'/api/documents/{document.id}?body=0')
        self.assertEqual(response.data['num_pages'], 15)

        response = self.device_user.get('/api/documents/')
        self.assertEqual(response.status_code, 200)
        response = self.device_user.get('/api/documents/?document_type=1')
        self.assertEqual(response.status_code, 200)

        response = self.admin_user.put(f'/api/users/update-tariff', {
            'tariff': UserTariff.MONTH,
            'user_id': self.current_device_user.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.current_device_user.refresh_from_db()
        self.assertEqual(self.current_device_user.tariff, UserTariff.MONTH)

        input_path = '/'.join([self.load_path, 'test1.docx'])
        content = base64.b64encode(open(input_path, 'rb').read())

        response = self.device_user.post('/api/documents/', {
            'name': 'new_2.docx',
            'body': content
        }, format='json')
        self.assertEqual(response.status_code, 201)
        new_document_id = response.data['id']
        new_document = Document.objects.get(pk=new_document_id)
        self.assertEqual(new_document.name, 'new_2.docx')
        self.assertEqual(new_document.format, DocumentFormat.DOCX)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 2)
        self.assertEqual(response.data['split_count'], 0)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 1)

        response = self.device_user.post(f'/api/documents/{document_id}/convert')
        self.assertEqual(response.status_code, 201)

        response = self.device_user.get(f'/api/users/me')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['load_count'], 2)
        self.assertEqual(response.data['split_count'], 0)
        self.assertEqual(response.data['merge_count'], 0)
        self.assertEqual(response.data['convert_count'], 2)
