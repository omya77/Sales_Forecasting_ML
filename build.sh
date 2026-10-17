#!/usr/bin/env bash
# exit on error
set -o errexit

echo "==> Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running Django collectstatic..."
python sales_web/manage.py collectstatic --no-input

echo "==> Applying database migrations..."
python sales_web/manage.py migrate

echo "==> Initializing dataset and admin user..."
python sales_web/manage.py seed_data

echo "==> Build completed successfully!"
