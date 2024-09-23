# Altered TCG Builder

[![](https://dcbadge.limes.pink/api/server/https://discord.gg/aSj8wR3qqu?style=flat)](https://discord.gg/https://discord.gg/aSj8wR3qqu)

[![Django CICD](https://github.com/Ajordat/alteredbuilder/actions/workflows/django_cicd.yml/badge.svg)](https://github.com/Ajordat/alteredbuilder/actions/workflows/django_cicd.yml)


Application to build, analyze and share Altered TCG decks: [altered.ajordat.com](https://altered.ajordat.com)

Our goal with this open-source release is to invite users, developers, and enthusiasts to actively participate in the growth of this project.
We believe that open collaboration will lead to more features, faster development, and a platform that serves the needs of the Altered TCG community.

Running this platform comes with ongoing hosting and maintenance costs. If you enjoy using the platform and would like to support its continued development, consider making a donation or becoming a sponsor. Your contributions help us cover expenses and ensure the platform remains free for everyone.

We welcome contributions of all types! Whether it’s fixing bugs, adding new features, or simply giving feedback, every bit of help is appreciated.
If you encounter issues, have suggestions, or want to share ideas for new features, please open an issue or join our [Discord](https://discord.gg/aSj8wR3qqu) for discussion.

A big thank you to our growing community of users who have supported this project from the beginning. Your feedback help make this platform what it is today.

## Initial setup

Initialize the database container. Once the database is ready to accept connections, terminate the container (Ctrl+C).

This is done because this container takes a bit more to initialize than the `web` one, thus that one fails while `db` is still being created. We want to give this one enough time to properly setup.
```bash
docker compose run db
```

Apply the database migrations:
```bash
docker compose run web python manage.py migrate
```

Create the super user:
```bash
docker compose run web python manage.py createsuperuser
```

Finally, create a copy of [`.env.example`](.env.example) and name it `.env`.
Fill the values in the database section (make it up) and you're ready to run the platform.

## Build

```bash
docker compose build
```

## Run

When a Python file is saved, Django will detect it and will update itself, creating a very fast iteration between modification and verification.
For static files and templates, that is not the case simply because no refresh is required. Simply request the page once again and it will be updated (for static files refresh without cache).

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
DELETE FROM django_migrations WHERE name='<migration_name>';
```

### Import and export

```bash
docker exec <container-name> pg_dump <db-name> -U <db-user> --no-owner > dbexport.sql
gsutil cp dbexport.sql <cloud-storage-bucket-uri>
gcloud sql import sql <cloud-sql-instance-name> <cloud-storage-bucket-uri> --database=<db-name>
```


## Development

### Code format and style

This code base uses `black` to enforce formatting rules of PEP8.

```bash
docker compose run web black .
```

This code base uses `flake8` to highlight broken styling rules of PEP8.

```bash
flake8 alteredbuilder --ignore=E501,W503
```

The above rules are ignored:

* [E501](https://www.flake8rules.com/rules/E501.html): Line too long. I prefer to use `black`'s preference for 88 character lines; and ignore those lines that `black` doesn't fix.
* [W503](https://www.flake8rules.com/rules/W503.html): Line break occurred before a binary operator. Currently `flake8` considers it an anti-pattern, but in future versions it will be considered the best practice. This warning is ignored as `black` already enforces this as the best practice.


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
# The above test selection also applies to `coverage`
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

# Required
POSTGRES_DB=<database_name>
POSTGRES_USER=<database_user>
POSTGRES_PASSWORD=<database_users_password>

# Required
DATABASE_URL=psql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
SECRET_KEY=<django_secret_key>

# Optional (best False)
USE_GCS_STATICS=False
GCS_BUCKET_STATICS=<gcs_bucket_with_static_files>

# Optional (best empty)
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
