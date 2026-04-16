# 🚀 GroupsApp — Plataforma de Mensajería en Tiempo Real

> **Entrega 1 — Arquitectura Monolítica**
>
> Aplicación de mensajería modular enfocada en **grupos y canales**, construida con FastAPI, SQLAlchemy 2.x y PostgreSQL. Diseñada como monolito modular para facilitar su futura evolución a microservicios.

---

## 👥 Integrantes del Equipo

| # | Nombre Completo |
|---|-----------------|
| 1 | **Diego Jaramillo Calderón** |
| 2 | **Adyuer Ojeda** |
| 3 | **Juan David Mendiola Ríos** |

---

## 📄 Documentación del Proyecto

📂 **Documentación completa (Google Drive):**

🔗 [Enlace a la documentación en Drive](facebook.com)

---

## 🎥 Video de Demostración

▶️ **Video demostrativo del funcionamiento (YouTube):**

🔗 [Enlace al video en YouTube]( )

---

## 📋 Tabla de Contenidos

- [👥 Integrantes del Equipo](#-integrantes-del-equipo)
- [📄 Documentación del Proyecto](#-documentación-del-proyecto)
- [🎥 Video de Demostración](#-video-de-demostración)
- [🌟 Funcionalidades Principales](#-funcionalidades-principales)
- [🛠 Stack Tecnológico](#-stack-tecnológico)
- [🏗 Arquitectura del Sistema](#-arquitectura-del-sistema)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [📡 Métodos y Endpoints de la API](#-métodos-y-endpoints-de-la-api)
- [⚙️ Variables de Entorno](#️-variables-de-entorno)
- [🏁 Guía de Despliegue Paso a Paso](#-guía-de-despliegue-paso-a-paso)
- [🧪 Pruebas de los Endpoints](#-pruebas-de-los-endpoints)
- [🗃 Migraciones de Base de Datos](#-migraciones-de-base-de-datos)
- [🧠 Decisiones de Arquitectura](#-decisiones-de-arquitectura)
- [🔮 Evolución Futura](#-evolución-futura)

---

## 🌟 Funcionalidades Principales

| Funcionalidad | Descripción |
|---------------|-------------|
| **Mensajería en Tiempo Real** | Actualizaciones de estado de mensajes con acuses de recibo (✅ Entregado / ✅ Leído) |
| **Soporte Multimedia** | Subida y previsualización de archivos adjuntos (imágenes, documentos) y **mensajes de audio** integrados en el navegador |
| **Herramientas de Administración** | Los creadores de grupo tienen control total: eliminar grupo, eliminar canales y expulsar miembros |
| **Workspaces Inteligentes** | El canal **"general"** se crea automáticamente al formar un nuevo grupo |
| **Interfaz Interactiva** | Chat fluido con auto-scroll, funcionalidad de **Swipe-to-Reply**, y pestañas de sidebar con polling en segundo plano |
| **Navegación Intuitiva** | Interacciones simples para entrar/salir de chats (`← Salir`) y cerrar grupos (`✕ Cerrar Grupo`) |
| **Mensajes Directos** | Sistema de mensajería privada entre usuarios que comparten al menos un grupo |
| **Sistema de Presencia** | Indicador de estado en línea/offline basado en heartbeat periódico |
| **Búsqueda de Usuarios** | Búsqueda de usuarios por nombre para agregar a grupos |

---

## 🛠 Stack Tecnológico

### Backend

| Tecnología | Versión | Uso en el Proyecto |
|------------|---------|---------------------|
| **Python** | 3.11 | Lenguaje principal del backend |
| **FastAPI** | 0.115.0 | Framework web ASGI para la API REST |
| **Uvicorn** | 0.30.6 | Servidor ASGI de producción (con workers) |
| **SQLAlchemy** | 2.0.35 | ORM asíncrono para acceso a base de datos |
| **asyncpg** | 0.29.0 | Driver asíncrono nativo para PostgreSQL |
| **Alembic** | 1.13.3 | Herramienta de migraciones de esquema de base de datos |
| **Pydantic** | 2.9.2 | Validación de datos y serialización de schemas |
| **pydantic-settings** | 2.5.2 | Carga de configuración desde variables de entorno / `.env` |
| **python-jose** | 3.3.0 | Generación y verificación de tokens JWT |
| **passlib + bcrypt** | 1.7.4 / 4.0.1 | Hashing seguro de contraseñas |
| **python-multipart** | 0.0.12 | Parsing de formularios multipart para upload de archivos |
| **aiofiles** | 24.1.0 | Lectura/escritura asíncrona de archivos en disco |
| **boto3** | 1.35.0 | SDK de AWS para integración con S3 (almacenamiento de archivos) |

### Frontend

| Tecnología | Uso en el Proyecto |
|------------|---------------------|
| **HTML5** | Estructura semántica de la interfaz (SPA) |
| **CSS3** | Estilos visuales, diseño responsivo y animaciones |
| **JavaScript (Vanilla)** | Lógica de la interfaz, polling, interacciones y llamadas a la API |

### Base de Datos

| Tecnología | Versión | Uso en el Proyecto |
|------------|---------|---------------------|
| **PostgreSQL** | 15-alpine | Base de datos relacional principal |
| **Supabase** | (Managed) | Hosting administrado de PostgreSQL con connection pooling |

### Infraestructura y DevOps

| Tecnología | Uso en el Proyecto |
|------------|---------------------|
| **Docker** | Contenerización de la aplicación y base de datos |
| **Docker Compose** | Orquestación de servicios (app + db) para desarrollo local |
| **GitHub Actions** | Pipeline CI/CD para despliegue automático |
| **AWS Lightsail** | Hosting del backend como Container Service |
| **AWS S3** | Almacenamiento de archivos subidos y hosting del frontend estático |
| **AWS CloudFront** | CDN para servir el frontend con baja latencia |

### Patrones y Metodologías

| Patrón | Aplicación |
|--------|------------|
| **Monolito Modular** | Dominios separados en módulos con límites claros |
| **Repository Pattern** | Separación de acceso a datos en capa de repositorio |
| **Service Layer** | Lógica de negocio encapsulada en servicios |
| **Abstract Factory** | Selección dinámica de backend de almacenamiento (Local / S3) |
| **Dependency Injection** | Inyección de sesión de BD y usuario actual vía FastAPI Depends |
| **JWT Bearer Auth** | Autenticación stateless basada en tokens |
| **Fallback / Resilience** | Mecanismos de respaldo automático (S3 → Local) |

---

## 🏗 Arquitectura del Sistema

GroupsApp sigue un patrón de **monolito modular** — una única unidad desplegable con límites de dominio claros que pueden separarse en microservicios a futuro.

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (SPA)                             │
│              HTML5 + CSS3 + JavaScript Vanilla                │
├──────────────────────────────────────────────────────────────┤
│                      API REST (HTTP)                         │
├──────────────────────────────────────────────────────────────┤
│                     FastAPI Gateway                           │
│                  (CORS + Middleware)                          │
├───────┬────────┬────────┬──────────┬───────┬───────┬────────┤
│ Auth  │ Users  │ Groups │ Channels │ Msgs  │ Files │  Pres  │
│Router │Router  │Router  │ Router   │Router │Router │ Router │
├───────┴────────┴────────┴──────────┴───────┴───────┴────────┤
│               Service Layer (Lógica de Negocio)              │
├──────────────────────────────────────────────────────────────┤
│              Repository Layer (Acceso a Datos)               │
├──────────────────────────────────────────────────────────────┤
│           SQLAlchemy ORM (Asíncrono) → PostgreSQL            │
├──────────────────────────────────────────────────────────────┤
│       Storage Backend (Abstract Factory: Local / S3)         │
└──────────────────────────────────────────────────────────────┘
```

### Capas del Sistema

| Capa | Responsabilidad | Archivos |
|------|-----------------|----------|
| **Router** | Define endpoints HTTP, parsea parámetros, devuelve respuestas | `router.py` |
| **Service** | Contiene lógica de negocio, validaciones y reglas | `service.py` |
| **Repository** | Ejecuta consultas a la base de datos con SQLAlchemy | `repository.py` |
| **Schemas** | Define modelos Pydantic de request/response | `schemas.py` |
| **Models** | Define modelos ORM (tablas de la base de datos) | `app/models/*.py` |
| **Core** | Configuración, seguridad, dependencias y excepciones | `app/core/*.py` |

---

## 📁 Estructura del Proyecto

```
groupsapp/
├── app/
│   ├── __init__.py
│   ├── main.py                         # Punto de entrada FastAPI (lifespan, CORS, routers)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                   # Configuración centralizada (pydantic-settings)
│   │   ├── database.py                 # Motor async SQLAlchemy + session factory
│   │   ├── security.py                 # JWT (creación/verificación) + hashing bcrypt
│   │   ├── dependencies.py             # Dependencia de autenticación (get_current_user)
│   │   └── exceptions.py               # Excepciones HTTP personalizadas
│   ├── models/
│   │   ├── __init__.py                 # Re-exporta todos los modelos ORM
│   │   ├── user.py                     # Modelo User (username, email, hashed_password)
│   │   ├── group.py                    # Modelo Group + GroupMember (roles admin/member)
│   │   ├── channel.py                  # Modelo Channel (pertenece a un grupo)
│   │   ├── direct_conversation.py      # Modelo DirectConversation (par canónico user1<user2)
│   │   ├── message.py                  # Modelo Message (canal o DM, con reply_to)
│   │   ├── attachment.py               # Modelo Attachment (archivos adjuntos a mensajes)
│   │   ├── message_status.py           # Modelo MessageStatus (delivered/read por usuario)
│   │   └── presence.py                 # Modelo Presence (último heartbeat del usuario)
│   └── modules/
│       ├── __init__.py
│       ├── auth/                       # Módulo de autenticación (registro + login + JWT)
│       │   ├── router.py               # 3 endpoints: register, login, me
│       │   ├── service.py              # Lógica: validar duplicados, hash password, crear token
│       │   └── schemas.py              # RegisterRequest, LoginRequest, TokenResponse
│       ├── users/                      # Módulo de usuarios (perfiles + búsqueda)
│       │   ├── router.py               # 2 endpoints: search, get_profile
│       │   ├── service.py              # Lógica: búsqueda por username/display_name
│       │   ├── repository.py           # Consultas: búsqueda ILIKE, get_by_id
│       │   └── schemas.py              # UserProfileResponse, UserSearchResponse
│       ├── groups/                     # Módulo de grupos (CRUD + membresía)
│       │   ├── router.py               # 7 endpoints: create, list, get, add/remove member, delete
│       │   ├── service.py              # Lógica: crear con canal "general", validar admin
│       │   ├── repository.py           # Consultas: grupos del usuario, miembros, admin check
│       │   └── schemas.py              # GroupCreateRequest, GroupResponse, AddMemberRequest
│       ├── channels/                   # Módulo de canales (dentro de grupos)
│       │   ├── router.py               # 4 endpoints: create, list, get, delete
│       │   ├── service.py              # Lógica: validar membresía al grupo, solo admin crea/borra
│       │   ├── repository.py           # Consultas: canales del grupo, get_by_id
│       │   └── schemas.py              # ChannelCreateRequest, ChannelResponse
│       ├── messages/                   # Módulo de mensajes (canal + DM + audio + estado)
│       │   ├── router.py               # 9 endpoints: send/list canal, send/list DM, audio x2, read, status, conversations
│       │   ├── service.py              # Lógica: envío, historial, marcar como leído, conversaciones recientes
│       │   ├── repository.py           # Consultas: mensajes con paginación, estados, conversaciones
│       │   └── schemas.py              # SendMessageRequest, MessageResponse, ConversationListResponse
│       ├── files/                      # Módulo de archivos (upload/download + storage backend)
│       │   ├── router.py               # 4 endpoints: upload, list, bulk, download
│       │   ├── service.py              # Lógica: validar tamaño, guardar metadata + archivo
│       │   ├── repository.py           # Consultas: attachments por mensaje
│       │   ├── storage.py              # Abstract StorageBackend + Local + S3 (con fallback)
│       │   └── schemas.py              # AttachmentResponse
│       └── presence/                   # Módulo de presencia (online/offline)
│           ├── router.py               # 2 endpoints: heartbeat, get_presence
│           ├── service.py              # Lógica: upsert heartbeat, calcular is_online
│           ├── repository.py           # Consultas: presencia del usuario
│           └── schemas.py              # PresenceResponse
├── static/
│   ├── index.html                      # Frontend SPA principal
│   ├── style.css                       # Estilos CSS del frontend
│   └── app.js                          # Lógica JavaScript del frontend
├── alembic/                            # Migraciones de base de datos (Alembic)
├── uploads/                            # Almacenamiento local de archivos subidos
├── alembic.ini                         # Configuración de Alembic
├── requirements.txt                    # Dependencias Python del proyecto
├── Dockerfile                          # Imagen Docker de producción (Python 3.11-slim)
├── docker-compose.yml                  # Orquestación local (app + PostgreSQL)
├── .env.example                        # Plantilla de variables de entorno
├── .github/workflows/deploy.yml        # Pipeline CI/CD (GitHub Actions → AWS)
├── test_channel.py                     # Script de prueba para canales
├── test_chat.py                        # Script de prueba para chat/mensajes
└── test_delete.py                      # Script de prueba para eliminaciones (admin)
```

---

## 📡 Métodos y Endpoints de la API

Todos los endpoints (excepto `/auth/register`, `/auth/login` y `/health`) requieren un **token JWT Bearer** en el header `Authorization`.

### 🔐 Autenticación (`/auth`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/auth/register` | Registrar un nuevo usuario | `username`, `email`, `password`, `display_name` | `UserResponse` (201) |
| `POST` | `/auth/login` | Iniciar sesión y obtener token JWT | `username`, `password` | `TokenResponse` con `access_token` |
| `GET` | `/auth/me` | Obtener perfil del usuario autenticado | — (JWT requerido) | `UserResponse` |

### 👤 Usuarios (`/users`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `GET` | `/users/search?q=` | Buscar usuarios por nombre | `q` (query string, min 1 carácter) | `UserSearchResponse` |
| `GET` | `/users/{user_id}` | Obtener perfil de un usuario | `user_id` (UUID) | `UserProfileResponse` |

### 👥 Grupos (`/groups`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/groups` | Crear un nuevo grupo | `name`, `description` | `GroupResponse` (201) |
| `GET` | `/groups` | Listar mis grupos | — | `GroupListResponse` |
| `GET` | `/groups/{group_id}` | Obtener detalles de un grupo | `group_id` (UUID) | `GroupResponse` |
| `POST` | `/groups/{group_id}/members` | Agregar miembro al grupo (solo admin) | `group_id`, `user_id` | `GroupMemberResponse` (201) |
| `GET` | `/groups/{group_id}/members` | Listar miembros del grupo | `group_id` (UUID) | `GroupMemberListResponse` |
| `DELETE` | `/groups/{group_id}` | Eliminar grupo (solo admin/creador) | `group_id` (UUID) | 204 No Content |
| `DELETE` | `/groups/{group_id}/members/{user_id}` | Expulsar miembro del grupo (solo admin) | `group_id`, `user_id` | 204 No Content |

### 📢 Canales (`/channels`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/groups/{group_id}/channels` | Crear canal en un grupo (solo admin) | `group_id`, `name`, `description` | `ChannelResponse` (201) |
| `GET` | `/groups/{group_id}/channels` | Listar canales de un grupo | `group_id` (UUID) | `ChannelListResponse` |
| `GET` | `/channels/{channel_id}` | Obtener detalles de un canal | `channel_id` (UUID) | `ChannelResponse` |
| `DELETE` | `/channels/{channel_id}` | Eliminar canal (solo admin) | `channel_id` (UUID) | 204 No Content |

### 💬 Mensajes (`/messages`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/channels/{channel_id}/messages` | Enviar mensaje en un canal | `channel_id`, `content`, `reply_to_id` (opcional) | `MessageResponse` (201) |
| `GET` | `/channels/{channel_id}/messages` | Listar historial de mensajes del canal | `channel_id`, `skip`, `limit` (paginación) | `MessageListResponse` |
| `POST` | `/users/{user_id}/messages` | Enviar mensaje directo a un usuario | `user_id`, `content`, `reply_to_id` (opcional) | `MessageResponse` (201) |
| `GET` | `/users/{user_id}/messages` | Listar historial de mensajes directos | `user_id`, `skip`, `limit` (paginación) | `MessageListResponse` |
| `POST` | `/channels/{channel_id}/messages/audio` | Enviar audio en un canal | `channel_id`, `file` (multipart) | `MessageResponse` (201) |
| `POST` | `/users/{user_id}/messages/audio` | Enviar audio como mensaje directo | `user_id`, `file` (multipart) | `MessageResponse` (201) |
| `POST` | `/messages/{message_id}/read` | Marcar mensaje como leído | `message_id` (UUID) | `MessageStatusResponse` |
| `GET` | `/messages/{message_id}/status` | Obtener estados de lectura de un mensaje | `message_id` (UUID) | `MessageStatusListResponse` |
| `GET` | `/conversations` | Listar conversaciones recientes del usuario | — | `ConversationListResponse` |

### 📎 Archivos (`/files`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/messages/{message_id}/attachments` | Subir archivo adjunto a un mensaje | `message_id`, `file` (multipart) | `AttachmentResponse` (201) |
| `GET` | `/messages/{message_id}/attachments` | Listar adjuntos de un mensaje | `message_id` (UUID) | `List[AttachmentResponse]` |
| `POST` | `/attachments/bulk` | Obtener adjuntos de múltiples mensajes | `message_ids` (lista de UUIDs) | `Dict[str, List[AttachmentResponse]]` |
| `GET` | `/attachments/{attachment_id}` | Descargar un archivo adjunto | `attachment_id`, `token` (query param opcional) | Archivo binario (inline) |

### 🟢 Presencia (`/presence`)

| Método | Endpoint | Descripción | Parámetros de Entrada | Respuesta |
|--------|----------|-------------|----------------------|-----------|
| `POST` | `/presence/heartbeat` | Actualizar estado en línea (ping periódico) | — (JWT requerido) | `PresenceResponse` |
| `GET` | `/users/{user_id}/presence` | Consultar estado de presencia de un usuario | `user_id` (UUID) | `PresenceResponse` |

### 🏥 Salud

| Método | Endpoint | Descripción | Respuesta |
|--------|----------|-------------|-----------|
| `GET` | `/health` | Verificar que la aplicación está activa | `{"status": "ok", "app": "GroupsApp"}` |

> **Total: 29 endpoints** distribuidos en 7 módulos funcionales.

---

## ⚙️ Variables de Entorno

Copiar `.env.example` a `.env` y configurar según el ambiente:

| Variable | Valor por Defecto | Descripción |
|----------|-------------------|-------------|
| `APP_NAME` | `GroupsApp` | Nombre de la aplicación |
| `DEBUG` | `false` | Modo debug (echo SQL de SQLAlchemy) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Cadena de conexión async a PostgreSQL |
| `JWT_SECRET_KEY` | `change-me-in-production` | Secreto para firmar tokens JWT |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Tiempo de vida del token (24 horas) |
| `UPLOAD_DIR` | `./uploads` | Directorio local de archivos subidos |
| `MAX_UPLOAD_SIZE_MB` | `10` | Tamaño máximo de archivo (MB) |
| `STORAGE_BACKEND` | `local` | Backend de almacenamiento (`local` o `s3`) |
| `S3_BUCKET_UPLOADS` | — | Nombre del bucket S3 para archivos |
| `S3_REGION` | `us-east-1` | Región de AWS para S3 |
| `AWS_ACCESS_KEY_ID` | — | Clave de acceso de AWS |
| `AWS_SECRET_ACCESS_KEY` | — | Clave secreta de AWS |
| `CORS_ORIGINS` | `*` | Orígenes permitidos (separados por coma) |
| `PRESENCE_TIMEOUT_SECONDS` | `120` | Segundos sin heartbeat para marcar offline |

---

## 🏁 Guía de Despliegue Paso a Paso

### Prerrequisitos

Antes de comenzar, asegurarse de tener instalados:

| Herramienta | Versión Mínima | Para qué se necesita |
|-------------|----------------|---------------------|
| **Git** | 2.x | Clonar el repositorio |
| **Docker** | 20.x | Contenerizar la aplicación |
| **Docker Compose** | 2.x | Orquestar los servicios |
| **Python** | 3.11 (opcional) | Solo si se ejecuta sin Docker |

### Paso 1: Clonar el Repositorio

```bash
# Clonar el proyecto desde GitHub
git clone https://github.com/dajaramilc/GroupsApp.git

# Entrar al directorio del proyecto
cd GroupsApp
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar la plantilla de variables de entorno
cp .env.example .env
```

Abrir el archivo `.env` con un editor de texto y configurar los valores:

```env
# Base de datos local (Docker Compose se encarga de crearla)
DATABASE_URL=postgresql+asyncpg://groupsapp:groupsapp@db:5432/groupsapp

# IMPORTANTE: Generar un secreto seguro para producción
# Se puede generar con: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=tu-secreto-seguro-aqui

# Dejar el resto de valores por defecto para desarrollo local
STORAGE_BACKEND=local
CORS_ORIGINS=*
```

### Paso 3: Construir y Levantar los Servicios con Docker Compose

```bash
# Construir las imágenes Docker y levantar los servicios en segundo plano
docker compose up --build -d
```

Este comando levanta **2 servicios**:

| Servicio | Descripción | Puerto |
|----------|-------------|--------|
| `db` | PostgreSQL 15-alpine con healthcheck | `5432` |
| `app` | Aplicación FastAPI con Uvicorn | `8000` |

### Paso 4: Verificar que los Servicios están Corriendo

```bash
# Ver el estado de los contenedores
docker compose ps
```

Deberían aparecer ambos servicios con estado `Up` o `running`.

### Paso 5: Verificar la Salud de la Aplicación

```bash
# Verificar que la API está respondiendo
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{"status": "ok", "app": "GroupsApp"}
```

### Paso 6: Acceder a la Aplicación

| Recurso | URL |
|---------|-----|
| **Frontend (SPA)** | http://localhost:8000/ |
| **Documentación Swagger (API)** | http://localhost:8000/docs |
| **Documentación ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |

### Paso 7: Crear el Primer Usuario y Probar

1. Abrir **http://localhost:8000/docs** (Swagger UI)
2. Ejecutar `POST /auth/register` con los datos del usuario
3. Ejecutar `POST /auth/login` → copiar el `access_token`
4. Clic en el botón **"Authorize"** (esquina superior derecha) → pegar `Bearer <token>`
5. ¡Probar todos los endpoints!

### Detener los Servicios

```bash
# Detener los servicios (mantiene los datos)
docker compose down

# Detener y BORRAR los datos de la base de datos
docker compose down -v
```

### (Alternativa) Despliegue Sin Docker

Si se prefiere ejecutar sin Docker, se necesita una instancia de PostgreSQL corriendo:

```bash
# 1. Crear un entorno virtual de Python
python -m venv venv

# 2. Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar la variable DATABASE_URL en .env apuntando a tu PostgreSQL local
# DATABASE_URL=postgresql+asyncpg://usuario:password@localhost:5432/groupsapp

# 5. Ejecutar la aplicación
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### (Producción) Despliegue en AWS

El proyecto incluye un pipeline CI/CD en `.github/workflows/deploy.yml` que automatiza:

1. **Backend → AWS Lightsail**: Construye imagen Docker, la sube al Container Service
2. **Frontend → S3 + CloudFront**: Sincroniza archivos estáticos con S3 e invalida caché

Para configurar producción, se deben definir los siguientes **GitHub Secrets**:

| Secret | Descripción |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | Clave de acceso de AWS |
| `AWS_SECRET_ACCESS_KEY` | Clave secreta de AWS |
| `AWS_REGION` | Región de AWS (ej. `us-east-1`) |
| `LIGHTSAIL_SERVICE_NAME` | Nombre del Container Service en Lightsail |
| `DATABASE_URL` | URL de conexión a PostgreSQL de producción |
| `JWT_SECRET_KEY` | Secreto JWT de producción |
| `S3_BUCKET_UPLOADS` | Bucket S3 para archivos subidos |
| `S3_FRONTEND_BUCKET` | Bucket S3 para el frontend estático |
| `CLOUDFRONT_DOMAIN` | Dominio de la distribución CloudFront |
| `CLOUDFRONT_DISTRIBUTION_ID` | ID de la distribución CloudFront |

---

## 🧪 Pruebas de los Endpoints

### Método 1: Swagger UI (Recomendado)

1. Abrir http://localhost:8000/docs
2. Registrar un usuario vía `POST /auth/register`
3. Login vía `POST /auth/login` → copiar el `access_token`
4. Clic en **"Authorize"** (esquina superior derecha) → pegar `Bearer <token>`
5. Probar todos los endpoints interactivamente

### Método 2: curl desde terminal

```bash
# ── Registrar un usuario ──
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123","display_name":"Alice"}'

# ── Iniciar sesión ──
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}'
# → {"access_token":"eyJ...","token_type":"bearer"}

# ── Usar el token para llamadas autenticadas ──
TOKEN="eyJ..."

# ── Crear un grupo ──
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mi Grupo","description":"Grupo de prueba"}'

# ── Enviar heartbeat de presencia ──
curl -X POST http://localhost:8000/presence/heartbeat \
  -H "Authorization: Bearer $TOKEN"
```

### Método 3: Scripts de prueba incluidos

```bash
# Ejecutar scripts de prueba (requieren httpx instalado)
python test_channel.py    # Prueba de canales y mensajes
python test_chat.py       # Prueba de chat y mensajes directos
python test_delete.py     # Prueba de eliminaciones (permisos admin)
```

---

## 🗃 Migraciones de Base de Datos

Las tablas se crean automáticamente al iniciar la aplicación (conveniente para desarrollo). Para **producción**, usar **Alembic**:

```bash
# Generar una nueva migración después de cambios en los modelos
docker compose exec app alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones pendientes
docker compose exec app alembic upgrade head

# Revertir la última migración
docker compose exec app alembic downgrade -1

# Ver historial de migraciones
docker compose exec app alembic history
```

---

## 🧠 Decisiones de Arquitectura

| Decisión | Justificación |
|----------|---------------|
| **UUIDs como primary keys** | Preparados para distribución; sin conflictos de IDs secuenciales entre servicios |
| **Monolito modular** | Límites de dominio definidos ahora; separación futura sin reescritura |
| **Repository + Service layers** | Separación de acceso a BD de la lógica de negocio para testing y refactoring |
| **Abstract StorageBackend** | Almacenamiento intercambiable (Local → S3) implementando una sola interfaz |
| **DirectConversation model** | Par canónico (user1 < user2) previene conversaciones DM duplicadas |
| **DMs solo entre pares de grupo** | Regla de negocio: los usuarios deben compartir un grupo para Chat privado |
| **Membresía implícita a canales** | Todos los miembros del grupo acceden a todos los canales (simplicidad v1) |
| **REST-only (sin WebSocket)** | Más rápido de implementar; la arquitectura soporta agregar WS después |
| **Presencia basada en heartbeat** | Simple, stateless; el cliente envía ping cada N segundos |
| **Auto-creación de tablas al iniciar** | Conveniencia para desarrollo; Alembic disponible para producción |
| **Fallback S3 → Local** | Resiliencia: si S3 falla, los archivos se guardan localmente |

---

## 🔮 Evolución Futura

### → Migración a Microservicios (Entrega 2)

Cada carpeta en `app/modules/` mapea directamente a un microservicio potencial:

1. Extraer el módulo a su propio repositorio/servicio
2. Reemplazar llamadas inter-módulo con HTTP/gRPC
3. Agregar API Gateway (AWS ALB / Kong / Traefik)
4. Cada servicio obtiene su propio esquema o base de datos

### → Servicios AWS Planificados

| Componente | Servicio AWS |
|------------|--------------|
| Aplicación | ECS Fargate / EKS |
| Base de Datos | RDS PostgreSQL |
| Almacenamiento | S3 (swap `LocalStorageBackend` → `S3StorageBackend`) |
| Autenticación | Cognito o mantener JWT |
| Load Balancer | ALB |
| Real-time | API Gateway WebSocket / AppSync |
| Colas | SQS / SNS para eventos asíncronos |
| Caché | ElastiCache (Redis) |
| CDN | CloudFront |

### → Funcionalidades Futuras

- Edición y eliminación de mensajes
- Reacciones con emoji
- Indicadores de "escribiendo..."
- Notificaciones push (SNS / FCM)
- Búsqueda de mensajes (OpenSearch)
- Roles de usuario por canal
- Llamadas de voz/video (WebRTC)

---

<p align="center">
  <strong>GroupsApp</strong> — Proyecto de Arquitectura de Software<br>
  Entrega 1 · Arquitectura Monolítica<br>
  2026
</p>
