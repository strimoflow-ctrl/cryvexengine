FROM python:3.12-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY "bideo automation/backend/requirements.txt" ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend and frontend source code
COPY "bideo automation/backend/" ./backend/
COPY "bideo automation/frontend/" ./frontend/

# Set working directory to backend
WORKDIR /app/backend

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]
