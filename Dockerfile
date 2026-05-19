FROM python:3.11-slim

WORKDIR /app

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
