# ── Dockerfile de producción para GroupsApp ──────────────
# Imagen base ligera con Python 3.11
FROM python:3.11-slim

# Evita archivos .pyc innecesarios en producción
ENV PYTHONDONTWRITEBYTECODE=1
# Evita buffering de stdout/stderr para ver logs en tiempo real
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema para asyncpg y healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (capa cacheada si requirements.txt no cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio temporal de uploads (fallback si S3 no está disponible)
RUN mkdir -p /app/uploads

# Healthcheck para que Lightsail verifique que el contenedor está vivo
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Producción: sin --reload, con 2 workers para aprovechar el CPU
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
