"""
Нагрузочный тест на распределенную конвертацию файлов.
При конвертации балансировщик должен распределять нагрузку на три контейнера libreoffice.
Для увеличении мощности достаточно добавить еще контейнеров
"""

import requests
from time import sleep

from datetime import datetime


def convert_premium(folder, source):
    params = {
        'folder': folder,
        'source': source
    }
    return requests.post("http://127.0.0.1:6000/convert", json=params)


def stress_test():
    for i in range(100):
        print(datetime.now())
        convert_premium("/media/stress", "/media/stress/stress.docx")
        sleep(0.1)


if __name__ == "__main__":
    stress_test()
