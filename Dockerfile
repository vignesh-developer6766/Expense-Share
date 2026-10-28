FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including tesseract-ocr for receipt processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train ML model during build if not present
RUN python scripts/train_models.py

EXPOSE 5000

ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "python scripts/init_db.py && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 run:app"]
