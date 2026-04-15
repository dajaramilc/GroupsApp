"""
GroupsApp – Punto de entrada de la aplicación FastAPI.

Registra todos los routers de módulos, configura CORS, y sirve archivos estáticos.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import engine, Base

# Importar todos los modelos para que se registren con Base.metadata
import app.models  # noqa: F401

# Routers de cada módulo
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.groups.router import router as groups_router
from app.modules.channels.router import router as channels_router
from app.modules.messages.router import router as messages_router
from app.modules.files.router import router as files_router
from app.modules.presence.router import router as presence_router

# Configurar logging para rastrear eventos y errores
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Directorio de archivos estáticos del frontend
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crear tablas de base de datos al iniciar (conveniencia para desarrollo; usar Alembic en producción)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas de base de datos verificadas/creadas exitosamente")
    except Exception as error_db:
        logger.error(f"Error al crear tablas de base de datos: {error_db}")
        # Reintentar una vez después de un momento
        try:
            import asyncio
            await asyncio.sleep(2)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tablas creadas exitosamente en el segundo intento")
        except Exception as error_reintento:
            logger.error(f"Segundo intento de creación de tablas también falló: {error_reintento}")
            raise
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Plataforma de mensajería enfocada en grupos y canales",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — permite al frontend (CloudFront/S3) acceder a la API ──
# Parsear orígenes permitidos desde la variable de entorno CORS_ORIGINS
origenes_permitidos = [
    origen.strip()
    for origen in settings.CORS_ORIGINS.split(",")
    if origen.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos if origenes_permitidos != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrar routers de cada módulo ────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(groups_router)
app.include_router(channels_router)
app.include_router(messages_router)
app.include_router(files_router)
app.include_router(presence_router)

# ── Archivos estáticos y frontend ───────────────────────
# Montar solo si el directorio static existe (en producción el frontend va en S3/CloudFront)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de salud — usado por Lightsail para verificar que el contenedor está vivo."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/", include_in_schema=False)
async def root():
    """Servir el frontend SPA (solo cuando se ejecuta localmente con archivos estáticos)."""
    archivo_index = STATIC_DIR / "index.html"
    if archivo_index.exists():
        return FileResponse(archivo_index)
    # En producción, el frontend se sirve desde CloudFront/S3
    return {"message": f"{settings.APP_NAME} API", "docs": "/docs"}
