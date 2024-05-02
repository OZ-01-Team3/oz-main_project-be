FROM python:3.11
LABEL authors="yyysolhhh"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /backend

COPY ./pyproject.toml ./poetry.lock* ./

RUN poetry config virtualenvs.create false \
  && poetry install --without dev --no-interaction --no-ansi

COPY ./manage.py ./manage.py
COPY ./config ./config
COPY ./apps ./apps
COPY ./env-be ./env-be

RUN export $(cat env-be/.env | xargs)

ENV DB_HOST db

COPY ./entrypoint.sh ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
