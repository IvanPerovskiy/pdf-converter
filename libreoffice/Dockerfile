FROM python:3.8

RUN apt-get update && apt-get install -y gettext libgettextpo-dev
RUN apt-get install -y build-essential libssl-dev libffi-dev python-dev
RUN apt-get install -y libreoffice
ENV PYTHONUNBUFFERED 1

# PIP
RUN pip install --upgrade pip && pip install fastapi && pip install uvicorn

# DJANGO
ADD main.py /proxy/main.py

ENV PORT 6000

CMD ["python", "/proxy/main.py"]
