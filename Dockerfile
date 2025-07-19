# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (default FastAPI/Uvicorn port)
EXPOSE 8000

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Serve static files (index.html, etc.) from /app
# Add FastAPI static files mount if needed in main.py

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 