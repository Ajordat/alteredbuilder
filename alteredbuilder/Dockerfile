FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY . .

CMD exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 0 config.wsgi:application