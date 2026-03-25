# 🚀 GroupsApp — Messaging Platform

A modular monolith messaging application focused on **groups and channels**, built with FastAPI, SQLAlchemy 2.x, and PostgreSQL. Designed for easy evolution to microservices and AWS deployment.

---

## 📋 Table of Contents

- [🌟 Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [API Overview](#-api-overview)
- [Environment Variables](#-environment-variables)
- [Database Migrations](#-database-migrations)
- [Testing the Endpoints](#-testing-the-endpoints)
- [Architecture Decisions](#-architecture-decisions)
- [Project Structure](#-project-structure)
- [Future Evolution](#-future-evolution)

---

## 🌟 Key Features

- **Real-Time Messaging**: Built-in real-time message status updates offering Delivery and Read receipts (✅ Entregado / ✅ Leído).
- **Multimedia Support**: Upload and preview file attachments like images and documents, plus fully integrated **Voice Audio Messages** right inside the browser.
- **Admin Moderation Tools**: Group creators have full administrative control to **Delete the Group**, **Delete Channels**, and **Expel Members** from their communities.
- **Smart Workspaces**: The **"general"** channel is automatically created whenever a new Group is formed.
- **Interactive UI**: Fluid chat histories with bottom auto-scrolling, intuitive **Swipe-to-Reply** / Sliding functionalities, and responsive sidebar tabs driven by real-time background polling.
- **Enhanced Navigation**: Simple, semantic interactions to quickly enter or exit chats (`← Salir`) and close groups (`✕ Cerrar Grupo` / `← Grupos`).

---

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose installed

### Steps

```bash
# 1. Clone / navigate to the project
cd gropsapps

# 2. Copy environment file
cp .env.example .env

# 3. Build and start services
docker compose up --build -d

# 4. Verify everything is running
docker compose ps

# 5. Check app health
curl http://localhost:8000/health
# → {"status":"ok","app":"GroupsApp"}

# 6. Open Swagger UI in your browser
# → http://localhost:8000/docs
```

### Stop services
```bash
docker compose down

# To also remove database data:
docker compose down -v
```

---

## 🏗 Architecture

GroupsApp follows a **modular monolith** pattern — a single deployable unit with clear domain boundaries that can be split into microservices later.

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Gateway                      │
├──────┬────────┬────────┬──────────┬───────┬─────────────┤
│ Auth │ Users  │ Groups │ Channels │ Msgs  │ Files │ Pres│
├──────┴────────┴────────┴──────────┴───────┴─────────────┤
│                  Service Layer (Business Logic)          │
├─────────────────────────────────────────────────────────┤
│                  Repository Layer (Data Access)          │
├─────────────────────────────────────────────────────────┤
│              SQLAlchemy ORM → PostgreSQL                 │
└─────────────────────────────────────────────────────────┘
```

Each module contains:
- **`schemas.py`** — Pydantic request/response models
- **`repository.py`** — Database queries
- **`service.py`** — Business logic & validation
- **`router.py`** — FastAPI endpoints

---

## 📡 API Overview

| Area | Endpoint | Method | Description |
|------|----------|--------|-------------|
| **Auth** | `/auth/register` | POST | Register new user |
| | `/auth/login` | POST | Login, get JWT |
| | `/auth/me` | GET | Current user profile |
| **Users** | `/users/search?q=` | GET | Search users |
| | `/users/{id}` | GET | User profile |
| **Groups** | `/groups` | POST | Create group |
| | `/groups` | GET | My groups |
| | `/groups/{id}` | GET | Group details |
| | `/groups/{id}/members` | POST | Add member (admin) |
| | `/groups/{id}/members` | GET | List members |
| **Channels** | `/groups/{id}/channels` | POST | Create channel (admin) |
| | `/groups/{id}/channels` | GET | List channels |
| | `/channels/{id}` | GET | Channel details |
| **Messages** | `/channels/{id}/messages` | POST | Send channel message |
| | `/channels/{id}/messages` | GET | Channel history |
| | `/users/{id}/messages` | POST | Send DM |
| | `/users/{id}/messages` | GET | DM history |
| **Files** | `/messages/{id}/attachments` | POST | Upload attachment |
| | `/attachments/{id}` | GET | Download file |
| **Status** | `/messages/{id}/read` | POST | Mark as read |
| | `/messages/{id}/status` | GET | Message statuses |
| **Presence** | `/presence/heartbeat` | POST | Update online |
| | `/users/{id}/presence` | GET | User presence |

All endpoints except `/auth/register`, `/auth/login`, and `/health` require a Bearer JWT token.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://groupsapp:groupsapp@db:5432/groupsapp` | Async DB connection string |
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret for signing JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token TTL (24h) |
| `UPLOAD_DIR` | `./uploads` | File upload directory |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max upload size |
| `PRESENCE_TIMEOUT_SECONDS` | `120` | Time before user marked offline |
| `DEBUG` | `false` | SQLAlchemy echo mode |

---

## 🗃 Database Migrations

Tables are auto-created on startup via `Base.metadata.create_all` for development convenience.

For production, use **Alembic**:

```bash
# Generate a new migration after model changes
docker compose exec app alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec app alembic upgrade head

# Rollback one step
docker compose exec app alembic downgrade -1
```

---

## 🧪 Testing the Endpoints

### Via Swagger UI (recommended)
1. Open http://localhost:8000/docs
2. Register a user via `POST /auth/register`
3. Login via `POST /auth/login` → copy the `access_token`
4. Click **"Authorize"** (top right) → paste `Bearer <token>`
5. Test all endpoints!

### Via curl

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123","display_name":"Alice"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}'
# → {"access_token":"eyJ...","token_type":"bearer"}

# Use the token
TOKEN="eyJ..."

# Create a group
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Group","description":"A test group"}'

# Send heartbeat
curl -X POST http://localhost:8000/presence/heartbeat \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧠 Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **UUID primary keys** | Distributed-ready, no sequential ID conflicts across services |
| **Modular monolith** | Domain boundaries defined now; split later without rewriting |
| **Repository + Service layers** | Separation of DB access from business logic enables testing and refactoring |
| **Abstract StorageBackend** | File storage swappable to S3 by implementing one interface |
| **DirectConversation model** | Canonical pair (user1 < user2) prevents duplicate DM conversations |
| **DMs only between group peers** | Business rule: users must share a group to message privately |
| **Implicit channel membership** | All group members access all channels; simpler for v1 |
| **REST-only (no WebSocket)** | Faster to ship; architecture supports adding WS gateway later |
| **Heartbeat-based presence** | Simple, stateless; client pings every N seconds |
| **Auto-create tables on startup** | Dev convenience; Alembic available for production |

---

## 📁 Project Structure

```
gropsapps/
├── app/
│   ├── main.py                         # FastAPI app entry point
│   ├── core/
│   │   ├── config.py                   # Settings (pydantic-settings)
│   │   ├── database.py                 # Async SQLAlchemy engine
│   │   ├── security.py                 # JWT + password hashing
│   │   ├── dependencies.py             # Auth dependency
│   │   └── exceptions.py               # HTTP exceptions
│   ├── models/
│   │   ├── __init__.py                 # Re-exports all models
│   │   ├── user.py
│   │   ├── group.py                    # Group + GroupMember
│   │   ├── channel.py
│   │   ├── direct_conversation.py
│   │   ├── message.py
│   │   ├── attachment.py
│   │   ├── message_status.py
│   │   └── presence.py
│   └── modules/
│       ├── auth/                       # Registration + login
│       ├── users/                      # User profiles + search
│       ├── groups/                     # Groups + membership
│       ├── channels/                   # Channels within groups
│       ├── messages/                   # Channel + DM messages + read status
│       ├── files/                      # File upload/download + storage backend
│       └── presence/                   # Online/offline tracking
├── alembic/                            # Database migrations
├── uploads/                            # Local file storage
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔮 Future Evolution

### → Microservices Migration
Each `app/modules/` folder maps to a potential microservice:
1. Extract module to its own repo/service
2. Replace inter-module function calls with HTTP/gRPC
3. Add API Gateway (AWS ALB / Kong / Traefik)
4. Each service gets its own DB schema or database

### → AWS Deployment
| Component | AWS Service |
|-----------|-------------|
| Application | ECS Fargate / EKS |
| Database | RDS PostgreSQL |
| File storage | S3 (swap `LocalStorageBackend` for `S3StorageBackend`) |
| Auth | Cognito or keep JWT |
| Load balancer | ALB |
| Real-time | API Gateway WebSocket / AppSync |
| Queues | SQS / SNS for async events |
| Cache | ElastiCache (Redis) |
| CDN | CloudFront |

### → Real-Time Messaging
1. Add WebSocket endpoint in `messages` module
2. Use Redis pub/sub for multi-instance message broadcast
3. Keep REST endpoints for history queries
4. Consider AWS API Gateway WebSocket for managed scaling

### → Additional Features
- Message editing/deletion
- Reactions/emoji
- Typing indicators
- Push notifications (SNS/FCM)
- Message search (OpenSearch)
- User roles per channel
- Voice/video (WebRTC)
