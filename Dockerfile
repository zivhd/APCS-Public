# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
# Copy the rest of the application code
COPY . /app/

# Set environment variables
ENV MAPBOX_ACCESS_TOKEN=""
ENV GOOGLE_MAPS_TOKEN=""
ENV SECRET_KEY=""
ENV MAIL_SERVER=""
ENV MAIL_PORT=465
ENV MAIL_USE_SSL=True
ENV MAIL_USERNAME="autopriority.classification.sys@gmail.com"
ENV MAIL_PASSWORD=""
ENV MAIL_DEFAULT_SENDER="autopriority.classification.sys@gmail.com"
ENV RECAPTCHA_SITE_KEY=""
ENV RECAPTCHA_SECRET_KEY=""

# Expose the Flask application port
EXPOSE 5000

# Run Gunicorn with 3 workers for handling requests
CMD ["gunicorn", "--workers=3", "--timeout=1000", "--bind=0.0.0.0:8080", "app:app"]
