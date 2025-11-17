FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by Google Vision API (image handling)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (excluding items in .dockerignore)
COPY . /app

# Environment variables
ENV PORT=8080
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# GOOGLE_APPLICATION_CREDENTIALS will be injected by cloud provider secret system
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/vision-key.json

# Run the server
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

