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
cp .env.example .env           # ajustar AURUM_DB_* y POSTGRES_SUPERUSER_PASSWORD
```

Bootstrap de la base de datos (una sola vez; crea el rol `aurum_app` y la BD
`aurum_dev`). Requiere la contraseña del superusuario `postgres` en el `.env`:

```bash
# Crea rol + BD usando psql como superusuario (lee POSTGRES_SUPERUSER_PASSWORD del .env)
psql -U postgres -h localhost -f ../scripts/db/setup_dev.sql
uv run alembic upgrade head    # aplica las migraciones como aurum_app
```

Arranque de la API:

```bash
uv run uvicorn aurum.main:app --reload   # API en http://localhost:8000
```

La conexión se define por componentes en el `.env` (`AURUM_DB_HOST`, `AURUM_DB_PORT`,
`AURUM_DB_USER`, `AURUM_DB_PASSWORD`, `AURUM_DB_NAME`); `config.py` construye la URL.

- Documentación interactiva: http://localhost:8000/docs
- Salud: http://localhost:8000/health

## Comandos de desarrollo

```bash
uv run pytest                  # pruebas
uv run pytest --cov            # pruebas con cobertura
uv run ruff check .            # lint
uv run ruff format .           # formato (aplica)
uv run ruff format --check .   # formato (verifica, igual que el CI)
uv run mypy src                # tipado estático
```

> El CI ejecuta `ruff check .` **y** `ruff format --check .`. Para reproducir el
> gate completo antes de hacer commit, instala los hooks (desde la raíz del repo):
>
> ```bash
> pre-commit install            # una vez
> pre-commit run --all-files    # opcional: corre el gate sobre todo el repo
> ```

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
