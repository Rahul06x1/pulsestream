FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY mapper ./mapper
COPY main.py ./
RUN pip install --no-cache-dir .

# Pub/Sub push delivers HTTP; gunicorn serves the Flask app on $PORT.
CMD exec gunicorn --bind ":$PORT" --workers 1 --threads 8 --timeout 30 main:app
