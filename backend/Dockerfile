# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY backend/requirements_new.txt .
RUN pip install --upgrade pip
RUN pip install --prefix=/install -r requirements_new.txt

# Copy application code
COPY backend/ .

# Stage 2: Final image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Expose port for FastAPI
EXPOSE 8000

# Environment variables (can override from docker-compose or .env)
ENV PORT=8000

# Run Uvicorn server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
