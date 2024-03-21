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
