import sys
import subprocess
import re
from django.core.management.base import BaseCommand


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output


def convert_to(folder, source, timeout=None):
    args = ['libreoffice', '--headless', '--convert-to',
            'pdf:blbl', '--outdir', folder, source]

    process = subprocess.run(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=timeout)

    print(process.stdout.decode())
    filename = re.search('-> (.*?) using filter', process.stdout.decode())

    if filename is None:
        raise LibreOfficeError(process.stdout.decode())
    else:
        return filename.group(1)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        convert_to('/app/pdf/tests/data/output/', '/app/pdf/tests/data/input/fff.jpg')
