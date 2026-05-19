FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY static ./static
COPY app.py .

# Expose port
EXPOSE 8100

# Start command
CMD ["python3", "app.py"]
