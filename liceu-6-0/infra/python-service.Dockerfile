FROM python:3.12-slim

ARG REQUIREMENTS_PATH

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ${REQUIREMENTS_PATH} /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt