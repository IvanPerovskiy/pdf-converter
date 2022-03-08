from django.core.management.base import BaseCommand
import shutil
from multiprocessing import Pool
import requests


def action(i):
    """
    Пока не используется
    """
    with open("/app/pdf/tests/data/input/api.docx", 'rb') as f:
        r = requests.post("http://0.0.0.0:6000/docx2pdf", files={
            'upload_file': f
        }, stream=True)

        if r.status_code == 200:
            with open('/app/pdf/tests/data/output/out{}.pdf'.format(i + 1), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            print(r.status_code, r.content)


s = requests.Session()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        pool = Pool(6)
        pool.map(action, range(10))
