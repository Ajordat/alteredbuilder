FROM python:3.12-alpine

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install the gettext to translate to different locales
RUN apk add --no-cache gettext

# Set the working directory
WORKDIR /code

# Install pip requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir

# Copy the source code into the container
COPY . .

# Start gunicorn
CMD exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 0 config.wsgi:application