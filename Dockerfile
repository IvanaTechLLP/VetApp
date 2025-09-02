# ---- Backend ----
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY ./backend ./backend
COPY requirements_new.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements_new.txt

# ---- Frontend build ----
FROM node:20 AS frontend

WORKDIR /app

COPY ./frontend/vet-app/package*.json ./
RUN npm install --legacy-peer-deps

COPY ./frontend/vet-app ./
RUN npm run build

# ---- Final image ----
FROM python:3.11-slim

WORKDIR /app

# Copy backend
COPY --from=backend /app /app

# Copy frontend build
COPY --from=frontend /app/build ./frontend/build

# Expose FastAPI port
EXPOSE 8000

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Command to run FastAPI
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
