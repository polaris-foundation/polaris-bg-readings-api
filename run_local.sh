#!/bin/bash
SERVER_PORT=${1-5000}
export SERVER_PORT=${SERVER_PORT}
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=gdm-bg-readings-api
export DATABASE_PASSWORD=gdm-bg-readings-api
export DATABASE_NAME=gdm-bg-readings-api
export FLASK_APP=gdm_bg_readings_api/autoapp.py
export ENVIRONMENT=DEVELOPMENT
export ALLOW_DROP_DATA=true
export IGNORE_JWT_VALIDATION=True
export HS_KEY=secret
export PROXY_URL=http://localhost
export RABBITMQ_DISABLED=true
export SERVER_TIMEZONE=Europe/London
export AUTH0_AUDIENCE=https://dhos-dev.draysonhealth.com/
export REDIS_INSTALLED=False
export LOG_LEVEL=${LOG_LEVEL:-DEBUG}
export LOG_FORMAT=${LOG_FORMAT:-COLOUR}
export DHOS_TRUSTOMER_API_HOST=http://dhos-trustomer
export CUSTOMER_CODE=dev
export POLARIS_API_KEY=secret

if [ -z "$*" ]
then
  flask db upgrade
  python3 -m gdm_bg_readings_api
else
  python3 -m flask $*
fi
