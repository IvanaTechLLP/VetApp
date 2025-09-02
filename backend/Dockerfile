# Use official Python image
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements file (no "backend/" prefix needed)
COPY requirements_new.txt . 

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --prefix=/install -r requirements_new.txt

# Copy application code
COPY . .

# Stage 2: final image
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
