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

CMD ["python", "run.py"]
