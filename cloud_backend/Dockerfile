FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a proper Python package structure
COPY . .

# Create an empty __init__.py file to make directories into packages
RUN mkdir -p /app/app/routers /app/app/services /app/app/models
RUN touch /app/__init__.py
RUN touch /app/app/__init__.py
RUN touch /app/app/routers/__init__.py
RUN touch /app/app/services/__init__.py
RUN touch /app/app/models/__init__.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create directory for logs and cache
RUN mkdir -p /tmp/cad_analysis_cache

# Expose the port the app runs on
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application with proper error handling
CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "120", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-"]
