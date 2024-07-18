# Altered TCG Builder

[![Django CICD](https://github.com/Ajordat/alteredbuilder/actions/workflows/django_cicd.yml/badge.svg)](https://github.com/Ajordat/alteredbuilder/actions/workflows/django_cicd.yml)
[![Update card pool](https://github.com/Ajordat/alteredbuilder/actions/workflows/update_card_pool.yml/badge.svg)](https://github.com/Ajordat/alteredbuilder/actions/workflows/update_card_pool.yml)

Application to build, analyze and share Altered TCG decks.

## Initial setup

Initialize the database container. Once the database is ready to accept connections, terminate the container (Ctrl+C).
```bash
docker compose run db
```

Apply `auth`'s migrations.
```bash
docker compose run web python manage.py migrate auth
```

Create the super user. Give it the username `admin` and use whatever for the other fields. Ignore the warnings of missing migrations.
```bash
docker compose run web python manage.py createsuperuser
```

Apply the remaining migrations:
```bash
docker compose run web python manage.py migrate
```

Retrieve the cards from Altered's API:
```bash
docker compose run web python manage.py update_card_pool
```

## Build

```bash
docker compose build
```

## Run

```bash
docker compose up
```

## Database

### Connect
```bash
psql -d <database> -U <user>
```

### Create a Django migration

```bash
docker compose run web python manage.py makemigrations
docker compose run web python manage.py migrate
```

### Revert a Django migration

If it's a reversible (automated) migration, simply migrate to a previous version:
```bash
docker compose run web python manage.py migrate <migration_number>
```

If it was manual, delete the record of the migration from the database and manually reverse the changes made by the migration:
```bash
DELETE FROM django_migrations WHERE name=<migration_name>
```

### Import and export

```bash
docker exec <container-name> pg_dump <db-name> -U <db-user> --no-owner > dbexport.sql
gsutil cp dbexport.sql <cloud-storage-bucket-uri>
gcloud sql import sql <cloud-sql-instance-name> <cloud-storage-bucket-uri> --database=<db-name>
```


## Testing

### Run unittests
```bash
# Discover and run all tests
docker compose run web python manage.py test

# Discover and run all tests within an app
docker compose run web python manage.py test <app>

# Run all tests within a specific file of an app's tests directory
docker compose run web python manage.py test <app>.tests.<test_file>

# Run all tests within a specific class of a file of an app's tests directory
docker compose run web python manage.py test <app>.tests.<test_file>.<class_name>

# Run the specified test
docker compose run web python manage.py test <app>.tests.<test_file>.<class_name>.<test_method_name>
```

### Run unittests and view coverage
```bash
# Discover and run all tests and generate a test coverage report
docker compose run web coverage run manage.py test
# View coverage report
docker compose run web coverage report -m
```

## Environmental variables

### At GCP

As environment variables:
```
SETTINGS_NAME=<secret_manager_secret_name>	
USE_GCS_STATICS=True 	
SERVICE_PUBLIC_URL=<public_url>
```

Within the secret:
```
DATABASE_URL=postgres://<database_user>:<escaped_database_password>@//cloudsql/<cloud_sql_connection_name>/<database_name>
GCS_BUCKET_STATICS=<gcs_bucket_for_static_files>
SECRET_KEY=<django_secret_key>
SENDGRID_API_KEY=<sendgrid_api_key>
SENDGRID_FROM_EMAIL=<email_address_used_to_send_emails>
```

Within the Cloud Build trigger:
```
_ARTIFACT_REGISTRY_REPOSITORY=<artifact_registry_repository>
_CLOUD_RUN_SA=<sa_running_cloud_run_service>
_CLOUD_SQL_CONNECTION_NAME=<database_connection_name>
_REGION=<cloud_run_service_region>
_SECRET_SETTINGS_NAME=<secret_manager_secret_name>
_SERVICE_NAME=<cloud_run_service_name>
```

### At local environment

```
DEBUG=<debug_value>

POSTGRES_DB=<database_name>
POSTGRES_USER=<database_user>
POSTGRES_PASSWORD=<database_users_password>

DATABASE_URL=psql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
SECRET_KEY=<django_secret_key>

USE_GCS_STATICS=False
GCS_BUCKET_STATICS=<gcs_bucket_with_static_files>

SENDGRID_API_KEY=<sendgrid_api_key>
SENDGRID_FROM_EMAIL=<email_address_used_to_send_emails>
```

## Translations

Generate the `.po` files, which have to be delivered to the translators:

```bash
# Generate the translations for Django (Python + templates)
docker compose run web python manage.py makemessages --all
# Generate the translations of JS
docker compose run web python manage.py makemessages --all -d djangojs
```

Once the texts are translated, the `.po` files need to be compiled:

```bash
docker compose run web python manage.py compilemessages
```
