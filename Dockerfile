FROM python:3.12
LABEL authors="yyysolhhh"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN pip install --upgrade pip \
  && pip install poetry && pip install awscli

RUN --mount=type=secret,id=aws,target=/.aws/credentials

WORKDIR /backend

COPY ./pyproject.toml ./poetry.lock* ./

RUN poetry config virtualenvs.create false \
  && poetry install --without dev --no-interaction --no-ansi

COPY ./manage.py ./manage.py
COPY ./config ./config
COPY ./apps ./apps
COPY ./tools ./tools

COPY ./entrypoint.sh ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
