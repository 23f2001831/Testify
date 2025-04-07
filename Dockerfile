# Base image with Python
FROM python:3.10-slim

# Install Tesseract and system libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Run the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
