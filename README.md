# Altered TCG Builder

Application to build Altered TCG decks.

## Build

```bash
docker compose build
```

## Run

```bash
docker compose up
```

## Database

### Create a Django migration

```bash
docker compose run web python manage.py makemigrations
docker compose run web python manage.py migrate
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
```