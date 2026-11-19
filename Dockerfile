FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (needed for compiling python dependencies if any)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY req.txt /app/
RUN pip install --no-cache-dir -r req.txt

# Copy project files
COPY . /app/

# Create directory for collected static files
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/uploads
