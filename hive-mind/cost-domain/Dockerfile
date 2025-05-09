FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port for external access
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"] 