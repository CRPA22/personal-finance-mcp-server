# Personal Finance MCP Server

Servidor MCP para gestionar finanzas personales: cuentas, transacciones, análisis y proyecciones.

## Requisitos previos

- **Docker** y **Docker Compose** (opción recomendada)
- O: **Python 3.11+**, **uv** y **PostgreSQL 14+**

---

## Cómo probarlo

### Opción 1: Todo con Docker (recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/personal-finance-mcp-server.git
cd personal-finance-mcp-server

# 2. Levantar PostgreSQL + app (migraciones automáticas)
docker compose -f infra/docker/docker-compose.yml up -d --build

# 3. Probar el servidor
docker compose -f infra/docker/docker-compose.yml run --rm -it app
```

El servidor arranca y queda esperando en stdin. Usa **Ctrl+C** para cerrarlo.

### Opción 2: Sin Docker (Python local)

```bash
# 1. Clonar
git clone https://github.com/TU_USUARIO/personal-finance-mcp-server.git
cd personal-finance-mcp-server

# 2. Instalar dependencias (requiere uv: pip install uv)
uv sync --all-extras

# 3. Levantar solo PostgreSQL con Docker
docker compose -f infra/docker/docker-compose.yml up -d postgres

# 4. Configurar variables de entorno
cp .env.example .env

# 5. Migraciones
uv run alembic upgrade head

# 6. Iniciar servidor
uv run python -m app.mcp.server
```

---

## Probar con un cliente MCP

### MCP Inspector (navegador)

```bash
# Con Docker
npx @modelcontextprotocol/inspector docker compose -f infra/docker/docker-compose.yml run --rm -it app

# Sin Docker (app local)
npx @modelcontextprotocol/inspector uv run python -m app.mcp.server
```

### Cursor o Claude Desktop

Configura el servidor MCP con **ruta absoluta** al `docker-compose.yml`:

```json
{
  "mcpServers": {
    "personal-finance": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "C:\\ruta\\completa\\a\\tu\\proyecto\\infra\\docker\\docker-compose.yml",
        "run", "--rm", "app"
      ]
    }
  }
}
```

Sustituye `C:\ruta\completa\a\tu\proyecto` por la ruta real de la carpeta del proyecto.

Ver [docs/RUN_AND_TEST.md](docs/RUN_AND_TEST.md) para más opciones.

---

## Herramientas disponibles

| Tool | Descripción |
|------|-------------|
| `health_check` | Comprueba conexión con la base de datos |
| `get_token` | Obtiene JWT para pruebas |
| `create_account` | Crea cuenta (checking, savings, investment) |
| `delete_account` | Elimina cuenta y sus transacciones |
| `add_transaction` | Añade transacción (income/expense) |
| `delete_transaction` | Elimina transacción y revierte el balance |
| `get_financial_status` | Balance total, flujo mensual, ratio de ahorro |
| `analyze_month` | Análisis de un mes concreto |
| `forecast_balance` | Proyección de balance a N meses |
| `detect_anomalies` | Detecta transacciones anómalas (Z-score) |

---

## Prueba rápida

1. **health_check** → Verificar que todo está bien
2. **create_account** → `name="Mi cuenta"`, `account_type="checking"`
3. **add_transaction** → Usar el `account_id` devuelto: `amount=50`, `transaction_type="expense"`, `category="comida"`, `transaction_date="2025-02-20"`
4. **get_financial_status** → Ver el estado agregado

---

## Comandos de desarrollo

```bash
uv run pytest                    # Ejecutar tests
uv run alembic upgrade head      # Aplicar migraciones
uv run alembic revision --autogenerate -m "desc"  # Nueva migración
```
