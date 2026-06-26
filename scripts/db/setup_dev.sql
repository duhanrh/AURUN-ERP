-- ─────────────────────────────────────────────────────────────────────────────
-- AURUM ERP — bootstrap de base de datos de desarrollo
-- Ejecutar UNA sola vez como superusuario (postgres). Crea:
--   • el rol de aplicación `aurum_app` (NOSUPERUSER, NOBYPASSRLS → respeta RLS)
--   • la base de datos `aurum_dev`
--   • los privilegios para que `aurum_app` pueda crear y operar el esquema
--
-- Tras esto, las migraciones (Alembic) y la app corren como `aurum_app`; ya no se
-- necesita la contraseña de `postgres`. Que `aurum_app` sea NOBYPASSRLS es lo que
-- permite que las pruebas de aislamiento multi-tenant (sección 9.3) sean válidas.
--
-- Uso:  psql -U postgres -h localhost -f scripts/db/setup_dev.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- Rol de aplicación (idempotente)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aurum_app') THEN
    CREATE ROLE aurum_app WITH LOGIN PASSWORD 'aurum_app'
      NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

-- Base de datos de desarrollo, propiedad del rol de aplicación
-- (CREATE DATABASE no admite IF NOT EXISTS; si ya existe, ignorar el error).
CREATE DATABASE aurum_dev OWNER aurum_app;

-- Privilegios sobre el esquema public de aurum_dev
\connect aurum_dev
GRANT ALL ON SCHEMA public TO aurum_app;
