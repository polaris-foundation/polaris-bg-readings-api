FROM python:3.9

LABEL org.opencontainers.image.source=https://github.com/polaris-foundation/polaris-users-api

ARG GEMFURY_DOWNLOAD_KEY
ENV FLASK_APP gdm_bg_readings_api/autoapp.py

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN apt-get update \
    && apt-get install -y wait-for-it curl nano \
    && useradd -m app \
    && chown -R app:app /app \
    && pip install --upgrade pip poetry \
    && poetry config http-basic.sensynehealth ${GEMFURY_DOWNLOAD_KEY:?Missing build argument} '' \
    && poetry config virtualenvs.create false \
    && poetry install -v --no-dev

COPY --chown=app . ./

USER app

EXPOSE 5000

CMD ["python", "-m", "gdm_bg_readings_api"]
