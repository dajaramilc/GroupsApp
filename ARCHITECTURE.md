# 🏗 GroupsApp — Documentación de Arquitectura Distribuida

## 1. Visión General

GroupsApp es una plataforma de mensajería grupal construida como un **sistema distribuido de 7 microservicios**, un API Gateway, y middleware orientado a mensajes (MOM). El sistema está diseñado para ser escalable, resiliente y desplegable en la nube.

```
                        ┌─────────────────────┐
                        │   Clientes (Web UI)  │
                        └──────────┬──────────┘
                                   │ HTTPS
                        ┌──────────▼──────────┐
                        │   API Gateway (Nginx)│   ← Service Discovery
                        │     Puerto: 80/443   │
                        └──┬──┬──┬──┬──┬──┬──┬┘
                           │  │  │  │  │  │  │
              ┌────────────┘  │  │  │  │  │  └────────────┐
              ▼               ▼  ▼  ▼  ▼  ▼               ▼
        ┌──────────┐  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────────┐
        │svc-auth  │  │svc-  ││svc-  ││svc-  ││svc-  ││svc-      │
        │:8001     │  │users ││groups││chans ││msgs  ││presence  │
        └──────────┘  │:8002 ││:8003 ││:8004 ││:8005 ││:8007     │
                      └──────┘└──────┘│:50051│└──┬───┘└────┬─────┘
                                      │(gRPC)│   │         │
                                      └──┬───┘   │         │
                                         │ gRPC  │         │
                                         ◄───────┘         │
                                                            │
                              ┌──────────────────┐          │
                              │    RabbitMQ       │◄─────────┘
                              │ (MOM Broker)      │  consume
                              │    :5672          │  "message.sent"
                              └──────────────────┘
                                      ▲
                                      │ publish
                                      │ "message.sent"
                              ┌───────┴──────┐
                              │  svc-messages │
                              │  (productor)  │
                              └──────────────┘
```

### Microservicios

| Servicio | Puerto REST | Puerto gRPC | Responsabilidad |
|----------|-------------|-------------|-----------------|
| svc-auth | 8001 | — | Registro, login, JWT, gestión de usuarios |
| svc-users | 8002 | — | Búsqueda y perfiles de usuarios |
| svc-groups | 8003 | — | Grupos, membresías, roles |
| svc-channels | 8004 | 50051 | Canales dentro de grupos + servidor gRPC |
| svc-messages | 8005 | — | Mensajes directos/canal, estados, conversaciones |
| svc-files | 8006 | — | Upload/download de archivos adjuntos |
| svc-presence | 8007 | — | Heartbeat, estado online/offline |

---

## 2. Diseño Arquitectónico Escalable y Despliegue en Nube

### 2.1 Modelo de Despliegue

| Capa | Tecnología | Tipo de Servicio |
|------|------------|------------------|
| **Cómputo** | AWS EC2 + Kubernetes | IaaS + CaaS |
| **Base de Datos** | Supabase (PostgreSQL managed) | PaaS |
| **Message Broker** | RabbitMQ (containerized) | IaaS (self-hosted) |
| **API Gateway** | Nginx (containerized) | IaaS |
| **Almacenamiento** | Volúmenes persistentes (K8s PV) | IaaS |

### 2.2 Orquestación con Kubernetes

El directorio `k8s/` contiene los manifiestos para desplegar cada microservicio como un **Deployment + Service** independiente en Kubernetes:

```
k8s/
├── 00-namespace.yaml          # Namespace aislado
├── 01-secrets.yaml            # JWT keys, DB credentials
├── 02-configmap-nginx.yaml    # Nginx routing config
├── 10-svc-auth.yaml           # Deployment + Service
├── 11-svc-users.yaml
├── 12-svc-groups.yaml
├── 13-svc-channels.yaml       # Expone gRPC:50051
├── 14-svc-messages.yaml
├── 15-svc-files.yaml
├── 16-svc-presence.yaml
└── 20-api-gateway.yaml        # LoadBalancer/NodePort
```

### 2.3 Escalabilidad Horizontal

Los microservicios son **stateless** (sin estado local), lo que permite escalar horizontalmente con Kubernetes HPA (Horizontal Pod Autoscaler):

```yaml
# Ejemplo de escalado automático
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    name: svc-messages
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        targetAverageUtilization: 70
```

---

## 3. Diseño e Implementación de los Datos

### 3.1 Base de Datos

Se utiliza **PostgreSQL** (vía Supabase PaaS) como motor de base de datos relacional con acceso asíncrono mediante SQLAlchemy 2.x + asyncpg.

**Decisión Arquitectónica**: Se optó por un patrón de *Shared Database* con separación lógica por módulos. Cada microservicio accede únicamente a las tablas de su dominio a través de un **Repository Pattern** dedicado, garantizando el desacoplamiento lógico:

| Microservicio | Tablas que gestiona |
|---------------|---------------------|
| svc-auth | `users` |
| svc-groups | `groups`, `group_members` |
| svc-channels | `channels` |
| svc-messages | `messages`, `direct_conversations`, `message_statuses` |
| svc-files | `attachments` |
| svc-presence | `presences` |

> **Nota**: La separación física por esquemas PostgreSQL (`CREATE SCHEMA svc_auth`) está planificada para la siguiente fase de escalado, cuando el volumen de datos lo justifique.

### 3.2 Almacenamiento de Archivos

Los archivos multimedia (imágenes, audio, documentos) se almacenan en el sistema de archivos local (`./uploads/`) gestionado exclusivamente por `svc-files`. En producción, esto se reemplaza por un volumen persistente de Kubernetes o un bucket S3.

### 3.3 Logs

Cada microservicio genera logs estructurados usando el módulo `logging` de Python con formato:
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

---

## 4. Comunicaciones Remotas

### 4.1 API REST (Comunicación Síncrona Externa)

Todos los microservicios exponen endpoints REST via FastAPI. El API Gateway (Nginx) enruta las peticiones según el path:

| Patrón de URL | Microservicio destino |
|---------------|----------------------|
| `/auth/*` | svc-auth:8001 |
| `/users/search`, `/users/{id}` | svc-users:8002 |
| `/users/{id}/messages` | svc-messages:8005 |
| `/users/{id}/presence` | svc-presence:8007 |
| `/groups/*` | svc-groups:8003 |
| `/groups/{id}/channels` | svc-channels:8004 |
| `/channels/{id}/messages` | svc-messages:8005 |
| `/messages/{id}/attachments` | svc-files:8006 |
| `/attachments/{id}` | svc-files:8006 |
| `/presence/heartbeat` | svc-presence:8007 |

### 4.2 gRPC (Comunicación Síncrona Interna)

Se utiliza gRPC para comunicación interna de alta eficiencia entre microservicios. Implementación actual:

**Flujo: svc-messages → svc-channels (CheckChannelAccess)**

```protobuf
// channels.proto
service ChannelService {
  rpc CheckChannelAccess (CheckChannelAccessRequest)
      returns (CheckChannelAccessResponse);
}

message CheckChannelAccessRequest {
  string channel_id = 1;
  string user_id = 2;
}

message CheckChannelAccessResponse {
  bool allowed = 1;
  string channel_id = 2;
  string group_id = 3;
  string reason = 4;
}
```

**Diagrama de secuencia:**
```
┌──────────────┐         ┌──────────────┐
│ svc-messages │         │ svc-channels │
│  (REST:8005) │         │  (gRPC:50051)│
└──────┬───────┘         └──────┬───────┘
       │  CheckChannelAccess()  │
       │───────────────────────►│
       │                        │ Consulta membresía
       │  {allowed, group_id}   │
       │◄───────────────────────│
       │                        │
```

**Resiliencia**: Si el servicio gRPC no está disponible, svc-messages aplica un **fallback local** para garantizar disponibilidad:

```python
allowed, _group_id, reason = await check_channel_access(channel_id, user_id)
if reason == "grpc_unavailable":
    # Fallback: verificación local
    channel = await ChannelRepository.get_by_id(db, channel_id)
    member = await GroupRepository.get_member(db, channel.group_id, user_id)
```

### 4.3 MOM – Message-Oriented Middleware (Comunicación Asíncrona)

Se utiliza **RabbitMQ** con exchange tipo **Topic** para comunicación asíncrona basada en eventos entre microservicios.

**Tecnologías**: RabbitMQ 3.13 + aio-pika (cliente Python async)

**Exchange**: `groupsapp.events` (Topic Exchange)

#### Eventos definidos:

| Evento | Productor | Consumidor | Descripción |
|--------|-----------|------------|-------------|
| `message.sent` | svc-messages | svc-presence | Actualiza presencia del remitente |
| `user.registered` | svc-auth | svc-presence | Registra nuevo usuario en el sistema |

#### Arquitectura MOM:

```
┌──────────────┐    publish     ┌──────────────────┐    consume    ┌──────────────┐
│  svc-auth    │───────────────►│                  │──────────────►│              │
│ (productor)  │ "user.registered"│   RabbitMQ      │               │ svc-presence │
└──────────────┘               │                  │               │ (consumidor) │
                               │  Exchange:       │               │              │
┌──────────────┐    publish    │  groupsapp.events│    consume    │  Actualiza   │
│ svc-messages │───────────────►│  (Topic)         │──────────────►│  last_seen   │
│ (productor)  │ "message.sent"│                  │               │  automático  │
└──────────────┘               └──────────────────┘               └──────────────┘
```

#### Ejemplo de código – Productor:

```python
# En svc-messages, al enviar un DM:
await EventPublisher.publish(MessageSentEvent(
    sender_id=str(current_user.id),
    message_id=str(msg.id),
    message_type="direct",
    target_id=str(target_user_id),
    content_preview=data.content[:100],
))
```

#### Ejemplo de código – Consumidor:

```python
# En svc-presence, al recibir el evento:
async def handle_event(event_data: dict):
    if event_data["event_type"] == "message.sent":
        # Actualizar presencia automáticamente
        await PresenceRepository.upsert_online(db, UUID(sender_id))
```

#### Graceful Degradation:
Si RabbitMQ no está disponible, los servicios operan normalmente. Los eventos se descartan con un log de advertencia, sin afectar la funcionalidad core.

---

## 5. Otros Aspectos del Sistema Distribuido

### 5.1 Servicios de Coordinación y Nombres

- **Service Discovery**: En Kubernetes, cada microservicio se registra como un `Service` con DNS interno (ej: `svc-auth.groupsapp.svc.cluster.local`).
- **API Gateway**: Nginx actúa como punto único de entrada, resolviendo el enrutamiento de peticiones al microservicio correcto basado en reglas de path.
- **gRPC Discovery**: La dirección del servidor gRPC se configura via variable de entorno `SVC_CHANNELS_GRPC_ADDR` (default: `svc-channels:50051`).

### 5.2 Gestión de la Configuración

Se sigue el patrón **12-Factor App**:
- Todas las configuraciones son **variables de entorno** (`.env`).
- En Kubernetes, se gestionan via `Secrets` y `ConfigMaps`.
- La clase `Settings` (Pydantic) valida y tipifica todas las variables al inicio.

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    RABBITMQ_URL: str
    # ... etc
    model_config = {"env_file": ".env"}
```

### 5.3 Seguridad Básica

| Aspecto | Implementación |
|---------|---------------|
| **Autenticación** | JWT (JSON Web Tokens) con HS256 |
| **Hashing de contraseñas** | bcrypt (via passlib) |
| **Autorización** | Middleware `get_current_user` en cada endpoint protegido |
| **CORS** | Configurado en API Gateway |
| **Tokens** | Expiración configurable (default: 24h) |
| **gRPC** | Canal inseguro interno (dentro del cluster K8s) |

### 5.4 Pruebas

| Tipo | Herramienta | Archivo |
|------|-------------|---------|
| Integración REST | Scripts bash/Python | `test_microservices.sh` |
| E2E Chat | Script Python | `test_chat.py` |
| Canales | Script Python | `test_channel.py` |
| Health checks | curl / Python | Automatizado en scripts |

### 5.5 Escalabilidad en Usuarios

- **Servicios Stateless**: Permiten escalado horizontal sin sincronización.
- **Polling Optimizado**: El frontend usa polling inteligente (5s) con fingerprinting de mensajes para evitar re-renders innecesarios.
- **Base de Datos**: Supabase PaaS maneja connection pooling y escalado automático.
- **RabbitMQ**: Soporta millones de mensajes/segundo con clustering.

---

## 6. Patrones de Diseño Utilizados

| Patrón | Dónde se aplica |
|--------|----------------|
| **Repository Pattern** | Cada módulo tiene su `repository.py` con queries aisladas |
| **Service Layer** | `service.py` encapsula lógica de negocio |
| **API Gateway** | Nginx enruta tráfico a microservicios |
| **Event-Driven Architecture** | RabbitMQ para comunicación asíncrona |
| **Graceful Degradation** | gRPC y MOM con fallbacks ante fallos |
| **Singleton** | Clientes gRPC y MOM Publisher |
| **12-Factor App** | Configuración via variables de entorno |

---

## 7. Stack Tecnológico

| Categoría | Tecnología |
|-----------|-----------|
| **Backend** | Python 3.14, FastAPI, SQLAlchemy 2.x |
| **Base de Datos** | PostgreSQL (Supabase PaaS) |
| **Message Broker** | RabbitMQ 3.13 + aio-pika |
| **RPC** | gRPC + Protocol Buffers |
| **API Gateway** | Nginx 1.25 |
| **Contenedores** | Docker + Docker Compose |
| **Orquestación** | Kubernetes (AWS) |
| **Frontend** | HTML5 + CSS3 + Vanilla JS |
| **Autenticación** | JWT (python-jose) + bcrypt |
