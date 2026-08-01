FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional auto-deploy dependencies
RUN pip install --no-cache-dir paramiko cryptography sse-starlette

# Copy backend code
COPY backend/ ./backend/
COPY web/ ./web/
COPY src/ ./src/

# Copy frontend (single-file HTML + PWA assets)
COPY frontend/index.html ./frontend/index.html
COPY frontend/sitemap.xml ./frontend/sitemap.xml
COPY frontend/download.html ./frontend/download.html
COPY frontend/manifest.json ./frontend/manifest.json
COPY frontend/sw.js ./frontend/sw.js
COPY frontend/icons/ ./frontend/icons/
COPY frontend/icon-192.png ./frontend/icon-192.png
COPY frontend/app.apk ./frontend/app.apk

# Create data directories
RUN mkdir -p /app/data /app/web/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend/main.py"]
