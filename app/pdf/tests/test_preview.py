import os

from PIL import Image
from django.conf import settings

from users.tests.parent import ParentTestCase
from pdf.tasks import convert


class PDFTestCase(ParentTestCase):

    def setUp(self):
        super().setUp()
        self.load_path = '/app/pdf/tests/data/input'
        self.make_path = '/app/pdf/tests/data/output'

    def test_preview(self):
        pass
        '''print(os.getcwd())
        folder = '/app/pdf/tests/data/test_root/1dddf17c-e910-40c3-9fc5-fcf2aedd1d6e'
        source = '/app/pdf/tests/data/test_root/1dddf17c-e910-40c3-9fc5-fcf2aedd1d6e/projects1.xls'

        image_path = convert(folder=folder, source=source,format='png')
        print(image_path)
        img = Image.open(image_path)
        # получаем ширину и высоту
        width, height = img.size
        print(width, height)
        # открываем картинку в окне
        img.show()
        new_image = img.resize((settings.PREVIEW_WIDTH, settings.PREVIEW_HEIGHT))
        new_image.save(image_path)'''

