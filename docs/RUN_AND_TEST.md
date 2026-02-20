# Personal Finance MCP Server — Levantar y probar

## Requisitos previos

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — gestor de paquetes y entornos
- **PostgreSQL 14+** (o Docker)
- **Cliente MCP** (Cursor, Claude Desktop, npx @modelcontextprotocol/inspector, etc.)

---

## 1. Levantar todo el sistema

### Opción A: Todo en Docker (recomendado)

```bash
cd "d:\Code\Python\Personal Finance MCP Server"

# Levantar PostgreSQL + App (migraciones automáticas)
docker compose -f infra/docker/docker-compose.yml up -d --build

# Probar con MCP Inspector (abre navegador)
docker compose -f infra/docker/docker-compose.yml run --rm -it app
```

Para configurar Cursor/Claude con Docker, usa **ruta absoluta** al docker-compose (Claude Desktop no usa `cwd`):

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "d:\\Code\\Python\\Personal Finance MCP Server\\infra\\docker\\docker-compose.yml",
        "run", "--rm", "app"
      ]
    }
  }
}
```

**Importante:** Sustituye la ruta por la de tu proyecto si es distinta. No uses `-it` con Claude Desktop (puede fallar).

### Opción B: Solo PostgreSQL en Docker

```bash
cd "d:\Code\Python\Personal Finance MCP Server"

# Levantar solo PostgreSQL
docker compose -f infra/docker/docker-compose.yml up -d postgres

# Instalar y ejecutar app localmente
uv sync --all-extras
copy .env.example .env
uv run alembic upgrade head
uv run python -m app.mcp.server
```

### Opción C: Sin Docker (PostgreSQL local)

```bash
# 1. Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE finance_mcp"

# 2. Configurar .env con tu DATABASE_URL
# DATABASE_URL=postgresql://usuario:password@localhost:5432/finance_mcp

# 3. Resto igual que arriba
uv sync --all-extras
copy .env.example .env
uv run alembic upgrade head
uv run python -m app.mcp.server
```

---

## 2. Configurar cliente MCP

El servidor usa **stdio** (stdin/stdout) por defecto. Configura tu cliente para ejecutar el comando del servidor.

### Cursor

En **Cursor Settings → MCP** añade:

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "app.mcp.server"
      ],
      "cwd": "d:\\Code\\Python\\Personal Finance MCP Server",
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/finance_mcp"
      }
    }
  }
}
```

O con ruta absoluta al proyecto:

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "d:\\Code\\Python\\Personal Finance MCP Server\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp.server"],
      "cwd": "d:\\Code\\Python\\Personal Finance MCP Server"
    }
  }
}
```

### Claude Desktop

En `claude_desktop_config.json` (ver [docs](https://docs.anthropic.com/claude/docs/model-context-protocol)):

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp.server"],
      "cwd": "d:\\Code\\Python\\Personal Finance MCP Server"
    }
  }
}
```

### MCP Inspector (pruebas manuales)

Con Docker:
```bash
cd "d:\Code\Python\Personal Finance MCP Server"
npx @modelcontextprotocol/inspector docker compose -f infra/docker/docker-compose.yml run --rm -it app
```

Sin Docker (app local):
```bash
npx @modelcontextprotocol/inspector uv run python -m app.mcp.server
```

---

## 3. Tools disponibles

| Tool | Descripción |
|------|-------------|
| `health_check` | Comprueba conectividad con la base de datos |
| `get_token` | Obtiene JWT (para pruebas) |
| `create_account` | Crea cuenta (checking/savings/investment) |
| `delete_account` | Elimina cuenta y sus transacciones |
| `add_transaction` | Añade transacción (income/expense) |
| `delete_transaction` | Elimina transacción y revierte balance |
| `get_financial_status` | Estado: balance, flujo, ratio ahorro |
| `analyze_month` | Análisis de un mes |
| `forecast_balance` | Proyección de balance N meses |
| `detect_anomalies` | Detección de anomalías por Z-score |

---

## 4. Flujo de prueba

1. **health_check**  
   - Verificar que el servidor y la DB responden.

2. **create_account**  
   - Parámetros: `name`, `account_type` (`checking` / `savings` / `investment`), opcionales: `currency`, `initial_balance`.  
   - Ejemplo: `name="Cuenta principal"`, `account_type="checking"`, `initial_balance=1000`.

3. **add_transaction**  
   - Usar el `account_id` devuelto.  
   - Parámetros: `account_id`, `amount`, `transaction_type` (`income`/`expense`), `category`, `transaction_date` (YYYY-MM-DD).  
   - Ejemplo: `add_transaction(account_id="...", amount=50, transaction_type="expense", category="groceries", transaction_date="2025-02-19")`.

4. **get_financial_status**  
   - Revisar balance total, flujo mensual y distribución.

---

## 5. Variables de entorno (.env)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://postgres:postgres@localhost:5432/finance_mcp` |
| `LOG_LEVEL` | DEBUG / INFO / WARNING / ERROR | `INFO` |
| `JWT_SECRET` | Secreto para firmar JWT | `change-me-in-production` |
| `JWT_EXPIRE_HOURS` | Expiración del token en horas | `24` |

---

## 6. Comandos útiles

```bash
# Tests
uv run pytest

# Migraciones
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "descripcion"

# Ejecutar servidor
uv run python -m app.mcp.server
```
