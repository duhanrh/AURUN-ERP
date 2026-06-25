# ADR 0001 — Stack tecnológico de AURUM ERP

- **Estado:** Aceptado
- **Fecha:** 2026-06-25
- **Decisores:** Propietario del producto / equipo de ingeniería
- **Contexto del documento maestro:** `IMPLEMENTACION_AURUM_ERP.md` (secciones 3.2, 3.3, 4.4, 5.5, 13.1, 13.4, 13.5)

## Contexto

El documento maestro proponía como *referencia* (no obligatoria, salvo PostgreSQL) un stack Node.js + NestJS + TypeScript en el backend. Tras evaluar las preferencias y capacidades del equipo, se decide adoptar un backend en **Python**. El frontend se mantiene en React (alineado con la referencia), usando Vite como herramienta de build.

Restricción dura heredada del documento: **PostgreSQL** como único motor de base de datos, con multi-tenant vía `tenant_id` + Row Level Security (RLS).

Entorno de desarrollo verificado (2026-06-25): Python 3.14.4, pip 26.1.1, Node 20.20.2, git 2.53, PostgreSQL 17.5 instalado localmente. Docker **no** instalado (se pospone; el entorno local usa el PostgreSQL nativo).

## Decisión

### Backend
- **Lenguaje:** Python 3.12+ (entorno local: 3.14).
- **Framework web:** FastAPI (ASGI, async), por su DI nativa (`Depends`), tipado vía type hints + Pydantic y OpenAPI automático.
- **Validación / esquemas:** Pydantic v2 + pydantic-settings para configuración.
- **ORM:** SQLAlchemy 2.0 en modo async.
- **Migraciones:** Alembic (DDL de RLS escrito a mano dentro de cada revisión).
- **Auth:** PyJWT (RS256) + passlib con argon2 para hashing de contraseñas.
- **Tareas asíncronas:** ARQ sobre Redis (se introduce en Fase 7; Celery como alternativa).
- **Servidor:** Uvicorn en desarrollo; Gunicorn + Uvicorn workers en producción.
- **Gestor de paquetes/entorno:** uv (lockfile `uv.lock` reproducible).
- **Pruebas:** pytest + pytest-asyncio + httpx + pytest-cov.
- **Calidad de código:** Ruff (lint + formato) + mypy (tipado estático).

### Frontend
- **React 18 + Vite + TypeScript** estricto.
- TanStack Query (estado de servidor) + Zustand (estado de UI).
- Theming dinámico vía CSS Custom Properties inyectadas desde `tenant_branding` (replica el patrón `document.documentElement.style.setProperty` de la maqueta).

### Base de datos
- PostgreSQL 15+ (local probado en 17.5). Multi-tenant: `tenant_id` + RLS.
- El `SET LOCAL app.current_tenant_id` se ejecuta al inicio de cada transacción desde un único *dependency* central de FastAPI (compatible con PgBouncer en modo `transaction`).

### Infraestructura
- Docker/`docker-compose` se pospone; el desarrollo local corre contra PostgreSQL nativo y, opcionalmente, Redis local. Se contenedizará en una etapa posterior antes de `staging`.

## Consecuencias

**Positivas**
- Equipo trabaja en el lenguaje elegido (Python) en el backend.
- FastAPI da OpenAPI/Swagger sin esfuerzo adicional (cumple sección 9.6).
- SQLAlchemy + RLS cubren el aislamiento multi-tenant en profundidad (secciones 5.2–5.5).
- Frontend permanece fiel a la referencia React de la maqueta.

**Negativas / riesgos**
- Python 3.14 es muy reciente; algunas librerías con extensiones nativas (p. ej. `pydantic-core`) podrían requerir wheels recientes. Mitigación: usar últimas versiones; si falta wheel, fijar a una versión con soporte o usar 3.12/3.13.
- Se pierde el lenguaje compartido front/back (TS en ambos). Se asume conscientemente.
- Docker pospuesto implica que la reproducibilidad del entorno (RNF-09) se cubre temporalmente con `uv.lock` + scripts; se cierra al contenedizar.

## Alternativas consideradas

- **NestJS + TypeScript** (referencia original): descartada por preferencia de lenguaje del equipo.
- **Django REST Framework:** válida, pero más opinada y menos async-first que FastAPI para este caso.
- **Poetry / pip+venv** en vez de uv: válidas; uv elegido por velocidad y lockfile.
- **Celery** en vez de ARQ: válida; ARQ elegido por ser async-native y ligero (revisable en Fase 7).
