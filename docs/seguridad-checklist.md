# Checklist de seguridad — AURUM ERP (Fase 8)

Revisión del checklist de la sección 10 del documento maestro tras el endurecimiento
de la Fase 8. Estado a 2026-06-27.

| # | Control | Estado | Implementación |
|---|---------|--------|----------------|
| 1 | Aislamiento multi-tenant | ✅ | RLS en **todas** las tablas de negocio (`tenant_id` + políticas `USING`/`WITH CHECK` sobre `app.current_tenant_id`); el tenant se fija por transacción desde el claim firmado del JWT. Probado cruzando tenants en cada módulo. |
| 2 | Autenticación | ✅ | JWT RS256 (access ~15 min) + refresh con rotación y detección de reutilización (revoca la cadena). Contraseñas con `passlib[argon2]`. |
| 3 | Fuerza bruta en login | ✅ | Bloqueo temporal tras 5 fallos por `(tenant, email)` en ventana de 5 min (`login_guard`); responde 429. Cada fallo y bloqueo se audita. |
| 4 | Autorización (RBAC) | ✅ | Permisos efectivos = rol ± excepciones, **verificados en el servidor** (`require_permission`), no solo en la UI (403 verificado). |
| 5 | Auditoría inmutable | ✅ | `audit_logs` append-only a nivel de BD: políticas RLS solo para `SELECT`/`INSERT`; `UPDATE`/`DELETE` denegados incluso para el rol de aplicación (probado). |
| 6 | API pública | ✅ | API Keys con scopes explícitos de solo lectura; nunca el JWT de sesión. Solo se guarda el hash SHA-256 del secreto. Rate limiting por clave (429). Respuestas bajo el mismo RLS. |
| 7 | Cabeceras de seguridad | ✅ | `SecurityHeadersMiddleware`: `X-Content-Type-Options`, `X-Frame-Options=DENY`, `Referrer-Policy=no-referrer`, `Cross-Origin-Opener-Policy`, `Permissions-Policy`. |
| 8 | Manejo de errores | ✅ | Respuestas de error estandarizadas con `request_id`; 100 % de los 5xx loggeados con contexto; sin filtración de stack traces al cliente. |
| 9 | Validación de entrada | ✅ | Pydantic v2 en todos los endpoints; colores de marca validados por patrón hex (evita inyección vía branding). |
| 10 | Secretos | ✅ (dev) | Claves JWT por `*_path` obligatorias en prod; en dev efímeras. Token de plataforma y superusuario solo para bootstrap local. |
| 11 | Transporte (TLS) | ⏳ | Responsabilidad del despliegue (gateway/reverse proxy); fuera del alcance de la app. |
| 12 | Rate limiting distribuido | ⏳ | En memoria por instancia; respaldar en Redis para multi-instancia (sección 10.9). |

## Pendientes documentados (no bloqueantes)

- **TLS / HSTS**: se termina en la capa de borde (no en la app).
- **Rate limiting con Redis**: la forma de la decisión (permitido/429) ya está; falta el backend compartido para multi-instancia.
- **Pentest / pruebas de carga formales**: ejecutar como paso de pre-producción.
- **Rotación de API Keys**: hoy se revoca y se crea una nueva; la rotación asistida es una mejora futura.

## Resumen

Todos los controles de aplicación de la sección 10 están implementados y cubiertos
por pruebas automatizadas. Los pendientes (TLS, Redis, pentest formal) son de
infraestructura/despliegue y están documentados explícitamente.
