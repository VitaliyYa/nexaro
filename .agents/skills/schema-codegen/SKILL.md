---
name: schema-codegen
description: >-
  Standards and workflows for Single Source of Truth (SSOT) JSON Schema definitions
  and automated code generation for Pydantic models (Backend) and TypeScript interfaces (Frontend).
---

# Schema Codegen & Single Source of Truth (SSOT) Guide

This skill governs data contract definitions across IoT Edge nodes, Backend (FastAPI), and Frontend (Vue 3 SPA).

---

## 1. Directory Structure

All schemas live in the root `schemas/` directory:

```
schemas/
├── mqtt/
│   ├── climate_state.json
│   ├── lock_state.json
│   ├── lock_command.json
│   └── valve_event.json
└── api/
    ├── property.json
    └── device.json
```

---

## 2. Code Generation Workflow

Whenever a contract is modified or added in `schemas/`:

### Backend (Python / Pydantic v2)
Using `datamodel-code-generator`:
```bash
uv run datamodel-codegen \
  --input schemas/ \
  --input-file-type jsonschema \
  --output backend/src/schemas/models.py \
  --target-python-version 3.14 \
  --use-standard-collections \
  --use-schema-description
```

### Frontend (TypeScript / Vue 3)
Using `json-schema-to-typescript`:
```bash
npm --prefix frontend run generate:types
```

---

## 3. Contract Rules

1. **Explicit Nullability:** Always explicitly define `type` and whether fields are `required`.
2. **Version Compatibility:** Do not introduce breaking field name changes without a migration plan or versioned topic.
3. **Validation:** Backend API endpoints and MQTT workers must parse raw JSON through the generated Pydantic models to catch invalid payloads at runtime.
