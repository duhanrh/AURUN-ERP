# AURUM ERP

Plataforma ERP multi-tenant SaaS especializada en minería y comercialización de metales
preciosos (oro, plata, platino, paladio), cubriendo material crudo y refinado.

## Documentación

- **`IMPLEMENTACION_AURUM_ERP.md`** — guía maestra de implementación (fuente única de verdad del proceso).
- **`erp_mineria_preciosos.html`** — maqueta de referencia visual/funcional (prototipo de alta fidelidad).
- **`docs/analisis-maqueta.md`** — análisis de la maqueta (entregable de la Fase 0).
- **`docs/adr/`** — Architecture Decision Records (decisiones de arquitectura).

## Stack

- **Backend:** Python 3.12+ · FastAPI · SQLAlchemy 2.0 async · Alembic · Pydantic v2 — ver `backend/`.
- **Frontend:** React 18 · Vite · TypeScript · TanStack Query · Zustand — ver `frontend/` (Fase 1+).
- **Base de datos:** PostgreSQL 15+ con multi-tenant `tenant_id` + Row Level Security (RLS).

Detalle y justificación en `docs/adr/0001-stack-tecnologico.md`.

## Estado

En construcción — **Fase 0 (Análisis y cimentación)**. Ver fases en la sección 6 del documento maestro.

## Arranque rápido (backend)

```bash
cd backend
uv sync --extra dev
uv run uvicorn aurum.main:app --reload
```
