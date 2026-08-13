FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY liceu-core-schemas /app/liceu-core-schemas
RUN pip install --no-cache-dir /app/liceu-core-schemas

COPY cv-backend-core /app/cv-backend-core

WORKDIR /app/cv-backend-core
ENV PYTHONPATH=/app/cv-backend-core

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
