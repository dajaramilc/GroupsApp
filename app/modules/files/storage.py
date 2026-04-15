"""
Backends de almacenamiento de archivos — Local y S3.
El backend activo se selecciona con la variable de entorno STORAGE_BACKEND.
Diseñado con fallback automático: si S3 falla, se intenta almacenamiento local.
"""
import os
import uuid
import logging
from abc import ABC, abstractmethod

import aiofiles

from app.core.config import settings

# Logger para rastrear operaciones de almacenamiento y errores
logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Interfaz abstracta para almacenamiento de archivos — implementar para S3, GCS, etc."""

    @abstractmethod
    async def save(self, file_data: bytes, filename: str) -> str:
        """Guarda el archivo y retorna la ruta/key de almacenamiento."""
        ...

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Lee y retorna los bytes del archivo."""
        ...

    @abstractmethod
    def get_full_path(self, storage_path: str) -> str:
        """Retorna la ruta completa del sistema de archivos o URL."""
        ...


class LocalStorageBackend(StorageBackend):
    """Guarda archivos en disco local bajo settings.UPLOAD_DIR."""

    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        logger.info(f"LocalStorageBackend inicializado en: {settings.UPLOAD_DIR}")

    async def save(self, file_data: bytes, filename: str) -> str:
        """Guarda archivo en disco con nombre único para evitar colisiones."""
        extension_archivo = os.path.splitext(filename)[1]
        nombre_unico = f"{uuid.uuid4().hex}{extension_archivo}"
        ruta_completa = os.path.join(settings.UPLOAD_DIR, nombre_unico)

        async with aiofiles.open(ruta_completa, "wb") as archivo:
            await archivo.write(file_data)

        return nombre_unico

    async def read(self, storage_path: str) -> bytes:
        """Lee archivo desde disco local."""
        ruta_completa = self.get_full_path(storage_path)
        async with aiofiles.open(ruta_completa, "rb") as archivo:
            return await archivo.read()

    def get_full_path(self, storage_path: str) -> str:
        """Retorna la ruta absoluta del archivo en disco."""
        return os.path.join(settings.UPLOAD_DIR, storage_path)


class S3StorageBackend(StorageBackend):
    """
    Guarda archivos en AWS S3.
    Incluye fallback automático a almacenamiento local si S3 falla.
    """

    def __init__(self):
        """Inicializa el cliente S3 con las credenciales configuradas."""
        try:
            import boto3
            self._cliente_s3 = boto3.client(
                "s3",
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            self._nombre_bucket = settings.S3_BUCKET_UPLOADS
            logger.info(f"S3StorageBackend inicializado con bucket: {self._nombre_bucket}")
        except ImportError as error_importacion:
            logger.error(f"boto3 no está instalado: {error_importacion}. Ejecuta: pip install boto3")
            raise
        except Exception as error_inicializacion:
            logger.error(f"Error inicializando cliente S3: {error_inicializacion}")
            raise

    async def save(self, file_data: bytes, filename: str) -> str:
        """
        Sube archivo a S3 y retorna la key.
        Si S3 falla, intenta guardar localmente como fallback.
        """
        extension_archivo = os.path.splitext(filename)[1]
        clave_unica = f"uploads/{uuid.uuid4().hex}{extension_archivo}"

        try:
            self._cliente_s3.put_object(
                Bucket=self._nombre_bucket,
                Key=clave_unica,
                Body=file_data,
            )
            logger.info(f"Archivo subido exitosamente a S3: {clave_unica}")
            return clave_unica

        except Exception as error_subida:
            # Mecanismo de resiliencia: si S3 falla, guardar localmente
            logger.warning(f"S3 falló al subir archivo, usando fallback local: {error_subida}")
            try:
                backend_local = LocalStorageBackend()
                ruta_local = await backend_local.save(file_data, filename)
                logger.info(f"Archivo guardado localmente como fallback: {ruta_local}")
                return ruta_local
            except Exception as error_fallback:
                logger.error(f"Fallback local también falló: {error_fallback}")
                raise error_subida

    async def read(self, storage_path: str) -> bytes:
        """
        Descarga archivo desde S3.
        Si falla, intenta leerlo desde almacenamiento local (para archivos migrados parcialmente).
        """
        try:
            respuesta = self._cliente_s3.get_object(
                Bucket=self._nombre_bucket, Key=storage_path
            )
            contenido = respuesta["Body"].read()
            return contenido

        except Exception as error_descarga:
            # Mecanismo de resiliencia: intentar lectura local como fallback
            logger.warning(f"S3 falló al leer, intentando almacenamiento local: {error_descarga}")
            try:
                backend_local = LocalStorageBackend()
                contenido_local = await backend_local.read(storage_path)
                logger.info(f"Archivo leído exitosamente desde fallback local: {storage_path}")
                return contenido_local
            except Exception as error_lectura_local:
                logger.error(f"Lectura local también falló: {error_lectura_local}")
                raise error_descarga

    def get_full_path(self, storage_path: str) -> str:
        """Retorna la URL pública del archivo en S3."""
        return f"https://{self._nombre_bucket}.s3.{settings.S3_REGION}.amazonaws.com/{storage_path}"


def _crear_storage_backend() -> StorageBackend:
    """
    Fábrica que selecciona el backend de almacenamiento según la configuración.
    Si STORAGE_BACKEND='s3' y la inicialización falla, usa Local como fallback.
    """
    tipo_backend = settings.STORAGE_BACKEND.lower()

    if tipo_backend == "s3":
        try:
            return S3StorageBackend()
        except Exception as error_creacion_s3:
            # Resiliencia: si S3 no se puede inicializar, seguir con almacenamiento local
            logger.warning(
                f"No se pudo crear S3StorageBackend, usando LocalStorageBackend como fallback: {error_creacion_s3}"
            )
            return LocalStorageBackend()

    # Por defecto: almacenamiento local
    return LocalStorageBackend()


# Singleton — se selecciona automáticamente según la variable STORAGE_BACKEND
storage_backend = _crear_storage_backend()
