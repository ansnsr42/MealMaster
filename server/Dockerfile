FROM python:3.12.3-slim-bookworm

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && \
    apt upgrade -y && \
    apt install -y build-essential nano procps

RUN pip install --upgrade pip

COPY . /usr/src/app/

RUN pip install -r requirements.txt

