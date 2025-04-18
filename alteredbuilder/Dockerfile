FROM python:3.12-slim

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install the gettext to translate to different locales
RUN apt update && apt install -y gettext

# Set the working directory
WORKDIR /code

# Install pip requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir 
# && find /usr/local/lib/python3.12/ \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' \+

# Copy the source code into the container
COPY . .

# Start gunicorn
CMD exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 6 --timeout 0 config.wsgi:application
