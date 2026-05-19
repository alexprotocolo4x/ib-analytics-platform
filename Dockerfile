# Use official Python 3.11 image with pandas pre-installed
FROM python:3.11-slim

WORKDIR /app

# Install dependencies in a single layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app ./app
COPY static ./static
COPY app.py .

# Set environment variables
ENV PORT=8100
ENV PYTHONUNBUFFERED=1

# Expose port (Render uses PORT env var)
EXPOSE $PORT

# Run the application
CMD python3 app.py
