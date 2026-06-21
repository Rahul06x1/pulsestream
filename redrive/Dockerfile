FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY redrive ./redrive
COPY main.py ./
RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "main.py"]
