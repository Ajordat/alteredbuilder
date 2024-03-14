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

## Database migrations


```bash
docker compose run web python manage.py makemigrations
docker compose run web python manage.py migrate
```

## Testing

```bash
# Discover and run all tests
docker compose run web python manage.py test

# Discover and run all tests within an app
docker compose run web python manage.py test <app>
```