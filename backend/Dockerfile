FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY backend/ /app/backend/
COPY ai_core/ /app/ai_core/

# Add /app to PYTHONPATH so "from backend.engine.*" and "from ai_core.*" imports work
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "-m", "backend.app"]
