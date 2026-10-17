#!/usr/bin/env bash
set -o errexit

echo "==> Ensuring SQLite database migrations are applied..."
python sales_web/manage.py migrate --no-input

echo "==> Ensuring admin user and dataset are seeded..."
python sales_web/manage.py seed_data

echo "==> Starting Gunicorn server on 0.0.0.0:$PORT..."
exec gunicorn --chdir sales_web sales_web.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
