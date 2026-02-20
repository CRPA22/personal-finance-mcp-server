# Personal Finance MCP Server — Arquitectura Detallada

> **Documento de diseño**. No implementar código hasta confirmación explícita.

---

## 1. Visión General

El **Personal Finance MCP Server** es un servidor MCP (Model Context Protocol) que expone operaciones financieras personales vía tools. La arquitectura sigue **Clean Architecture** con separación estricta entre capas:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MCP LAYER (Orquestación)                         │
│  Tools: create_account, add_transaction, get_financial_status, etc.     │
│  Responsabilidad: Validar input (Pydantic) → Llamar services → Responder │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER (Lógica de negocio)                │
│  account_service, transaction_service, analytics_service                 │
│  Responsabilidad: Reglas de negocio, orquestación de modelos, cálculos   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         REPOSITORY LAYER (Persistencia)                  │
│  SQLAlchemy 2.0, repositorios por entidad                                │
│  Responsabilidad: CRUD, queries, transacciones                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INFRAESTRUCTURA                                  │
│  PostgreSQL, Alembic, Docker                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Estructura de Directorios (Final)

```
finance-mcp/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point FastMCP
│   │
│   ├── core/                        # Configuración y utilidades core
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (Pydantic BaseSettings)
│   │   └── exceptions.py            # Excepciones de dominio
│   │
│   ├── db/                          # Capa de persistencia
│   │   ├── __init__.py
│   │   ├── session.py               # Session factory, dependency
│   │   ├── base.py                  # Base declarativa SQLAlchemy
│   │   └── repositories/            # Repositorios por entidad
│   │       ├── __init__.py
│   │       ├── account_repository.py
│   │       ├── transaction_repository.py
│   │       └── user_repository.py
│   │
│   ├── models/                      # Modelos SQLAlchemy (ORM)
│   │   ├── __init__.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── user.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                     # DTOs Pydantic
│   │   ├── __init__.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── analytics.py
│   │   └── auth.py
│   │
│   ├── services/                    # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── transaction_service.py
│   │   └── analytics_service.py     # Delegación a app/analytics
│   │
│   ├── analytics/                   # Motor analítico (independiente)
│   │   ├── __init__.py
│   │   ├── calculator.py            # Balance, ratios, distribución
│   │   ├── forecast.py              # Proyección 3 meses
│   │   └── anomaly.py               # Detección Z-score
│   │
│   ├── auth/                        # Autenticación
│   │   ├── __init__.py
│   │   ├── jwt.py                   # Crear/validar tokens
│   │   └── middleware.py            # Validación JWT en requests
│   │
│   ├── mcp/                         # Capa MCP
│   │   ├── __init__.py
│   │   ├── server.py                # Instancia FastMCP
│   │   ├── tools/                   # Definición de tools
│   │   │   ├── __init__.py
│   │   │   ├── accounts.py          # create_account
│   │   │   ├── transactions.py     # add_transaction
│   │   │   ├── status.py           # get_financial_status
│   │   │   ├── analysis.py         # analyze_month, forecast_balance
│   │   │   └── anomalies.py        # detect_anomalies
│   │   └── dependencies.py         # Inyección de session, auth
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py               # Logging estructurado
│       └── validators.py            # Validaciones auxiliares
│
├── tests/
│   ├── conftest.py                  # Fixtures (DB, client, auth)
│   ├── unit/
│   │   ├── analytics/
│   │   ├── services/
│   │   └── schemas/
│   ├── integration/
│   │   └── mcp/
│   └── e2e/                         # (opcional, fase posterior)
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── azure/
│   │   └── deploy.md
│   └── gcp/
│       └── deploy.md
│
├── migrations/                      # Alembic
│   └── versions/
│
├── pyproject.toml
├── .env.example
├── alembic.ini
├── README.md
└── docs/
    └── ARCHITECTURE.md
```

---

## 3. UV — Estructura del Proyecto

### 3.1 Comandos Iniciales

```bash
uv init finance-mcp
cd finance-mcp
```

`uv init` crea:
- `pyproject.toml` con metadata del proyecto
- Estructura básica de paquetes

### 3.2 Dependencias (pyproject.toml)

| Grupo | Dependencias |
|-------|-------------|
| **Producción** | fastmcp, sqlalchemy>=2.0, asyncpg, alembic, pydantic, pydantic-settings, python-jose, passlib, python-multipart |
| **Desarrollo** | pytest, pytest-asyncio, pytest-cov, httpx, uv |

```toml
[project]
dependencies = [
    "fastmcp>=0.2",
    "sqlalchemy>=2.0",
    "asyncpg",
    "alembic",
    "pydantic>=2",
    "pydantic-settings",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "python-multipart",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "httpx",
]
```

### 3.3 Comandos UV Clave

| Comando | Uso |
|---------|-----|
| `uv sync` | Instala dependencias según lockfile; crea `.venv` si no existe |
| `uv add <pkg>` | Añade dependencia y actualiza pyproject.toml |
| `uv add --dev <pkg>` | Dependencia de desarrollo |
| `uv run python -m app.mcp.server` | Ejecuta en entorno aislado |
| `uv run pytest` | Ejecuta tests con entorno correcto |
| `uv lock` | Regenera uv.lock |

### 3.4 Entornos Reproducibles

- **uv.lock**: Lockfile que fija versiones exactas.
- **.python-version**: Versión de Python del proyecto (ej. `3.12`).
- Sin `pip` ni `requirements.txt`: todo vía `uv`.

---

## 4. Flujo de Datos — Ejemplo: add_transaction

```
1. Cliente MCP llama tool "add_transaction" con JSON
2. FastMCP recibe → Pydantic valida TransactionCreate
3. Tool (orquestador) llama transaction_service.create(...)
4. Service:
   - Valida reglas (cuenta existe, monto coherente)
   - Llama transaction_repository.create()
   - Session.commit()
5. Service devuelve TransactionSchema
6. Tool serializa → respuesta JSON al cliente
```

**Regla de oro**: Las tools no contienen lógica; solo validan y delegan.

---

## 5. Motor Analítico (app/analytics)

Independiente de MCP y de HTTP. Recibe datos estructurados (listas de transacciones, cuentas) y devuelve métricas.

| Módulo | Responsabilidad |
|--------|-----------------|
| `calculator.py` | Balance total, por cuenta, flujo mensual, ratio ahorro, distribución por categoría, tendencia mensual |
| `forecast.py` | Proyección de balance 3 meses (regresión lineal o media móvil) |
| `anomaly.py` | Detección Z-score (umbral configurable) |

**Input**: Datos ya cargados desde DB (listas de Pydantic o dicts).  
**Output**: Objetos Pydantic tipados.  
**Testeable**: Sí, sin levantar servidor ni DB.

---

## 6. Seguridad

| Componente | Implementación |
|------------|----------------|
| JWT | `python-jose`; secret y exp vía env |
| Roles | Enum: `admin`, `user`; validación en middleware |
| Middleware | Validar `Authorization: Bearer <token>` antes de ejecutar tools |
| Secrets | `JWT_SECRET`, `DATABASE_URL` solo vía variables de entorno |
| Audit | Tabla `audit_logs` (acción, user_id, timestamp, metadata) |

---

## 7. Testing Local

### 7.1 Preparación

```bash
# 1. Entorno
uv sync

# 2. PostgreSQL local (Docker)
docker compose -f infra/docker/docker-compose.yml up -d

# 3. Variables
cp .env.example .env
# Editar .env con DATABASE_URL, JWT_SECRET, etc.

# 4. Migraciones
uv run alembic upgrade head
```

### 7.2 Ejecución

| Objetivo | Comando |
|----------|---------|
| Servidor MCP | `uv run python -m app.mcp.server` |
| Tests unitarios | `uv run pytest tests/unit -v` |
| Tests integración | `uv run pytest tests/integration -v` |
| Todos los tests | `uv run pytest -v` |
| Con cobertura | `uv run pytest --cov=app --cov-report=term-missing` |

### 7.3 Tests sin DB

- **analytics/**: Datos in-memory (listas de transacciones mock).
- **schemas/**: Validación Pydantic pura.
- **services**: Con `pytest` + mocks de repositorios o DB en memoria (SQLite).

### 7.4 Tests con DB

- `conftest.py` usa fixture con DB PostgreSQL de test (o SQLite para CI).
- Transacciones por test con rollback para aislamiento.

---

## 8. Despliegue en Nube

### 8.1 Principios

- **Config por env**: `DATABASE_URL`, `JWT_SECRET`, `LOG_LEVEL`, etc.
- **Sin estado en disco**: Todo en PostgreSQL.
- **Health check**: Endpoint `/health` (si se expone HTTP) o equivalente para el runtime.

### 8.2 Azure

| Componente | Servicio |
|------------|----------|
| Servidor | Azure Container Apps |
| Base de datos | Azure Database for PostgreSQL (Flexible Server) |
| Secrets | Azure Key Vault o variables de Container Apps |

Flujo: Build imagen → Push ACR → Deploy Container App con env y conexión a PostgreSQL.

### 8.3 GCP

| Componente | Servicio |
|------------|----------|
| Servidor | Cloud Run |
| Base de datos | Cloud SQL (PostgreSQL) |
| Secrets | Secret Manager |

Flujo: Build imagen → Push Artifact Registry → Deploy Cloud Run con conexión Cloud SQL.

### 8.4 Docker

- `Dockerfile`: Multi-stage; `uv sync --frozen`; usuario no-root.
- `docker-compose.yml`: Servicio `app` + servicio `postgres`; redes y volúmenes para persistencia.
- Comando: `docker compose up --build`.

---

## 9. Tools MCP — Especificación

| Tool | Input | Output | Service |
|------|-------|--------|---------|
| `create_account` | name, type, currency, initial_balance | AccountSchema | account_service.create |
| `add_transaction` | account_id, amount, type, category, date, description | TransactionSchema | transaction_service.create |
| `get_financial_status` | user_id (opcional, desde JWT) | FinancialStatusSchema | analytics_service.get_status |
| `analyze_month` | year, month | MonthAnalysisSchema | analytics_service.analyze_month |
| `forecast_balance` | account_id, months | ForecastSchema | analytics_service.forecast |
| `detect_anomalies` | account_id, threshold | AnomaliesSchema | analytics_service.detect_anomalies |

---

## 10. Modelo de Datos (Esquema)

### Entidades principales

- **users**: id, email, hashed_password, role, created_at
- **accounts**: id, user_id, name, type (checking/savings/investment), currency, balance, created_at
- **transactions**: id, account_id, amount, type (income/expense), category, date, description, created_at
- **audit_logs**: id, user_id, action, entity_type, entity_id, metadata, created_at

### Relaciones

- User 1:N Accounts  
- Account 1:N Transactions  
- User 1:N AuditLogs  

---

## 11. Fases de Implementación (Resumen)

| Fase | Entregable | Criterio de éxito |
|------|------------|-------------------|
| **1** | Setup base | `uv run python -m app.mcp.server` corre; conexión PostgreSQL; Alembic; server mínimo |
| **2** | CRUD | Servicios + tests; tools create_account, add_transaction |
| **3** | Motor analítico | calculator, forecast, anomaly + tests matemáticos |
| **4** | MCP completo | Todas las tools; logging; manejo de errores |
| **5** | Seguridad | JWT, middleware, audit_logs |
| **6** | Docker + Cloud | Dockerfile, compose, guías Azure/GCP |

---

## 12. Próximos Pasos

1. **Confirmar** esta arquitectura (ajustes si los hay).  
2. Iniciar **Fase 1** con `uv init` y estructura de carpetas.  
3. Avanzar fase por fase, validando cada una antes de continuar.

---

*Documento vivo. Actualizar según decisiones de implementación.*
