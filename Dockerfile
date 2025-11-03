# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy code and requirements
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Cloud Run expects
ENV PORT 8080
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

