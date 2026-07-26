FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Node.js build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional auto-deploy dependencies
RUN pip install --no-cache-dir paramiko cryptography sse-starlette

# Copy backend code
COPY backend/ ./backend/
COPY web/ ./web/
COPY src/ ./src/

# Copy and build frontend
COPY frontend/ ./frontend-src/
WORKDIR /app/frontend-src
RUN npm install && npm run build

# Copy built assets to frontend serving directory
WORKDIR /app
RUN rm -rf frontend && mkdir -p frontend
RUN cp -r frontend-src/dist/* frontend/ && \
    cp -r frontend-src/public/icons frontend/icons 2>/dev/null || true

# Create data directories
RUN mkdir -p /app/data /app/web/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend/main.py"]
