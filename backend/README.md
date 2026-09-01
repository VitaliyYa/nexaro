# SmartRent Backend

FastAPI application and background MQTT Worker for the SmartRent B2B SaaS platform.

## Features
- **Supabase Auth & RLS Integration**: User operations execute with end-user JWT and strict PostgreSQL RLS policies.
- **Mosquitto Dynamic Webhook**: Endpoints for dynamic authentication and property-scoped ACL verification via `mosquitto-go-auth`.
- **Encrypted PIN Management**: Smart lock PIN codes encrypted at rest with full audit trail in `audit_logs`.
- **MQTT Worker**: Ingests device telemetry, updates live states, and writes event logs.
- **Command Dispatcher**: Sends device commands with QoS 1 and retain=false.

## Development
```bash
# Sync dependencies
uv sync

# Run tests
uv run pytest

# Lint & Format
uv run ruff check .
uv run ruff format --check .

# Start development server
uv run uvicorn src.main:app --reload --port 8000
```
