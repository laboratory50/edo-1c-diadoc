import os
import zipfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

MAX_SIZE = 64 * 1024


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
VALID_ZIP = os.path.join(DATA_DIR, '1111.zip')


class UploadViewTests(SimpleTestCase):

    def _upload(self, file_data, filename='test.zip'):
        return self.client.post('/', {'file': SimpleUploadedFile(filename, file_data)})

    def test_valid_zip_removes_infpol(self):
        with open(VALID_ZIP, 'rb') as f:
            zip_data = f.read()

        response = self._upload(zip_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertIn('attachment', response['Content-Disposition'])

        body = response.content.decode('windows-1251')
        self.assertNotIn('ИнфПолФХЖ1', body)
        self.assertNotIn('ИнфПолФХЖ2', body)
        self.assertIn("encoding='windows-1251'", body)

    def test_non_zip_upload_rejected(self):
        response = self._upload(b'not a zip file', filename='document.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_file_too_large_rejected(self):
        oversized = b'\x00' * (MAX_SIZE + 1)
        response = self._upload(oversized)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('file', form.errors)
        self.assertIn('64', str(form.errors['file']))

    def test_zip_without_on_file(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('meta.xml', '<root/>')
            zf.writestr('card.xml', '<root/>')
        response = self._upload(buf.getvalue())
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertIn('ON_', response.context['error'])

    def test_download_filename(self):
        with open(VALID_ZIP, 'rb') as f:
            zip_data = f.read()

        response = self._upload(zip_data)
        disposition = response['Content-Disposition']
        self.assertIn("filename*=UTF-8''", disposition)
        self.assertIn('53_26.xml', disposition)
        self.assertIn('.xml', disposition)
