FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache gettext

WORKDIR /code

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 0 config.wsgi:application