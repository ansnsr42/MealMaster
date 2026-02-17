FROM python:3.12.3-alpine3.20

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
      build-base \
      linux-headers \
      procps \
    && pip install --upgrade pip


COPY . /usr/src/app/

RUN pip install -r requirements.txt

