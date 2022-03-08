# pdf-converter
Сервис по конвертации и изменению pdf файлов.
Позволяет конвертировать в pdf форматы xls, xlsx, doc, docx, png, jpg
Документы PDF можно расщеплять, объединять, менять местами страницы в любом количестве.

# Инструкция сборки и запуска

  1. Заполнить файл .env.

    docker-compose up --build
  
  2. Запустить сборку.

    docker-compose up --build
    
  3. Запустить скрипт для заполнения базы
   
    docker-compose run --rm backend python manage.py start_server

  4. Админпанель Джанго должна работать.

    http://127.0.0.1/admin
     

  5. Автодокументация.

    http://127.0.0.1/api/swagger/
    http://127.0.0.1/api/redoc/

 