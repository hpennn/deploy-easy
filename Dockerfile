FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional auto-deploy dependencies
RUN pip install --no-cache-dir paramiko cryptography sse-starlette

# Copy backend code
COPY backend/ ./backend/
COPY web/ ./web/
COPY src/ ./src/

# Copy pre-built frontend assets (no npm build needed)
# Backend looks for frontend/dist/ first, so keep that structure
COPY frontend/dist/ ./frontend/dist/

# Create data directories
RUN mkdir -p /app/data /app/web/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend/main.py"]
