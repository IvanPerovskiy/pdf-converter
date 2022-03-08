FROM python:3.8

RUN apt-get update && apt-get install -y gettext libgettextpo-dev
RUN apt-get install -y build-essential libssl-dev libffi-dev python-dev
RUN apt-get install -y libreoffice
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

WORKDIR /app

# PIP
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install -r /requirements.txt

# DJANGO
ADD . /app/
