FROM --platform=linux/amd64 python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and entrypoint script
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/instance/uploads && \
    chmod 777 /app/instance && \
    chmod 777 /app/instance/uploads && \
    chmod +x entrypoint.sh

# Create a non-root user and set ownership
RUN useradd -m myuser && \
    chown -R myuser:myuser /app

# Switch to non-root user
USER myuser

# Expose port 5000
EXPOSE 5000

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]