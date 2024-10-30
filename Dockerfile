# Use the official Python 3.8 slim image as the base image
FROM --platform=linux/amd64 python:3.8-slim

# Set the working directory within the container
WORKDIR /api-flask

# Copy the necessary files and directories into the container
COPY . .

VOLUME /instance

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Flask application
EXPOSE 5000

# Start Gunicorn and point it to the create_app() function
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]