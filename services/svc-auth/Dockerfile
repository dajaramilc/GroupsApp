FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies (from project root requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared application code
COPY app/ ./app/

# Override main.py with this service's entry point
COPY services/svc-auth/main.py ./app/main.py

RUN mkdir -p /app/uploads

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
