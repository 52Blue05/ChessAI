FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY backend/ /app/backend/
COPY ai-core/ /app/ai-core/

EXPOSE 8080

CMD ["python", "backend/app.py"]
