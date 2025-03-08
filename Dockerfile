FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching purposes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p uploads results

# Expose the port the app runs on
EXPOSE 5001

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Command to run the application with Gunicorn (production server)
# Workers: 3 is a good starting point (2*num_cores + 1)
# Timeout: 180 seconds for processing large images
CMD gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 3 --timeout 180 wsgi:app 