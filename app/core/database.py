"""
Async SQLAlchemy engine, session factory, and declarative Base.

En el modo distribuido, cada microservicio establece su propio DATABASE_URL
via os.environ ANTES de importar este módulo, garantizando aislamiento de datos.
"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Crear engine con la URL del servicio actual
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Desactivar FK enforcement en SQLite para soportar BD distribuidas
# (las FK cruzadas entre servicios no pueden existir en BD separadas)
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db():
    """FastAPI dependency – yields a DB session and closes it afterwards."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
