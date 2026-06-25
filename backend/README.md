# AURUM ERP — Backend (FastAPI)

Backend multi-tenant en Python 3.12+ / FastAPI, siguiendo Clean Architecture por módulo
de negocio. Ver el documento maestro `../IMPLEMENTACION_AURUM_ERP.md` y el ADR de stack
`../docs/adr/0001-stack-tecnologico.md`.

## Requisitos

- Python 3.12+ (probado en 3.14)
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes/entorno)
- PostgreSQL 15+ (local probado en 17.5)

## Puesta en marcha (local)

```bash
cd backend
uv sync --extra dev            # crea .venv e instala dependencias
cp .env.example .env           # ajustar AURUM_DATABASE_URL si hace falta
uv run uvicorn aurum.main:app --reload   # API en http://localhost:8000
```

- Documentación interactiva: http://localhost:8000/docs
- Salud: http://localhost:8000/health

## Comandos de desarrollo

```bash
uv run pytest                  # pruebas
uv run pytest --cov            # pruebas con cobertura
uv run ruff check .            # lint
uv run ruff format .           # formato
uv run mypy src                # tipado estático
```

## Estructura

```
src/aurum/
  main.py                # app factory FastAPI
  api.py                 # router raíz /api/v1
  shared/                # config, health, infra transversal (DB, RLS, middleware)
  modules/<modulo>/      # domain / application / infrastructure / presentation
tests/                   # refleja src/, con conftest.py
migrations/              # Alembic (se añade en Fase 1)
```
