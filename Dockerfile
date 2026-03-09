# ============================================================
# Dockerfile – Enterprise Employee Management Portal
# Phase 1 base image – security hardening in later phases
# ============================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Create non-root user (security best practice – Phase 2 enforcement)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance and uploads directories
RUN mkdir -p instance app/static/uploads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 5000

CMD ["python", "run.py"]
