FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy project code (backend imports shared modules from repository)
COPY . /app

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT}"]
