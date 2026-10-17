FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY scripts ./scripts

# Don't run as root inside the container
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV DATABASE_URL=sqlite:////app/data/glossary.db
EXPOSE 8000

# Load the terms from the CSV, then start the API
CMD ["sh", "-c", "python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
