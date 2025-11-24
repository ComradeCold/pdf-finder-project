FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Google Vision
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import pymysql; print('PyMySQL successfully installed')"

# Copy project files
COPY . /app

# Environment variables
ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/vision-key.json

# Run the server with Gunicorn, binding to 0.0.0.0:8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--timeout", "120"]
