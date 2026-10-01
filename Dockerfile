FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    HOST=0.0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Ensure storage directories exist
RUN mkdir -p storage/media storage/thumbnails storage/avatars

# Seed initial database if needed
RUN python backend/seed.py

EXPOSE 5000

CMD ["sh", "-c", "gunicorn 'backend.app:create_app()' --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120"]
