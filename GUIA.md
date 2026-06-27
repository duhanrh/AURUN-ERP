# Guía rápida de desarrollo local — AURUM ERP

Cómo levantar el proyecto y probar el frontend con datos sembrados.
Entorno: Windows / PowerShell. La BD `aurum_dev` y las migraciones ya están aplicadas.

---

## Tenant de pruebas (ACME Metales)

Provisionado el 2026-06-26 para probar la Fase 3 (Terceros). **Solo para desarrollo local.**

| Dato | Valor |
|---|---|
| **Tenant ID** (login en dev → campo `X-Tenant-ID`) | `da1bb041-b7ac-43d3-a2ea-d587b59704fe` |
| **Email** | `admin@acme.example.com` |
| **Contraseña** | `Admin-12345` |
| Subdominio | `acme` |
| Rol | superusuario (acceso total) |

### Datos sembrados

- **5 proveedores** — 3 activos, 1 en evaluación (PlatGroup LATAM), 1 inactivo (Mineros del Cauca), con rating y certificaciones.
- **4 clientes** — 3 activos, 1 en evaluación (Global Metals), con segmento, contacto y línea de crédito.

---

## 1. Levantar el backend

```powershell
cd "C:\Users\Asesor\Documents\AURUN ERP\backend"
.\.venv\Scripts\python.exe -m uvicorn aurum.main:app --port 8000 --reload
```

- API: `http://localhost:8000`
- Swagger (probar endpoints a mano): `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

---

## 2. Crear un tenant + sembrar datos

> Solo si necesitas un tenant **nuevo**. El de la tabla de arriba ya existe.

Crear tenant + admin (endpoint abierto en local):

```powershell
$r = Invoke-RestMethod -Uri http://localhost:8000/api/v1/platform/tenants -Method Post -ContentType 'application/json' -Body (@{
  name            = 'ACME Metales'
  subdomain       = 'acme'            # cambia si ya existe (daría 409)
  admin_email     = 'admin@acme.example.com'
  admin_full_name = 'Admin Minero'
  admin_password  = 'Admin-12345'
} | ConvertTo-Json)
$r | ConvertTo-Json   # anota el tenant_id
```

Sembrar proveedores/clientes de ejemplo (maneja UTF-8 correctamente; re-ejecutable,
los existentes se omiten con 409):

```powershell
# Edita el TENANT dentro del script si provisionaste uno nuevo.
cd "C:\Users\Asesor\Documents\AURUN ERP\backend"
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe ..\scripts\dev\seed_terceros.py
```

> ⚠️ Sembrar con `curl` directo desde la terminal corrompe los acentos (á/ó/é) y
> el backend responde 400 ("error parsing the body"). Usa el script Python.

---

## 3. Levantar el frontend

```powershell
cd "C:\Users\Asesor\Documents\AURUN ERP\frontend"
npm run dev
```

Abre `http://localhost:5173` y entra con:

- **Tenant ID:** `da1bb041-b7ac-43d3-a2ea-d587b59704fe`
- **Email:** `admin@acme.example.com`
- **Contraseña:** `Admin-12345`

Luego ve a **Proveedores** / **Clientes**: KPIs de cabecera, tabla con badges de
estado y, al hacer clic en una fila, la ficha 360° en el panel lateral.

El frontend lee `VITE_API_URL` (por defecto `http://localhost:8000`).

---

## Notas

- **Login en dev:** pide el Tenant ID (UUID) porque aún no hay resolución por
  subdominio; se manda como cabecera `X-Tenant-ID`.
- **Saldos CxC/CxP, compras y nº de órdenes** salen como `—` en la ficha: son datos
  operativos de la **Fase 4**, aún no implementada. La Fase 3 solo persiste el maestro.
- **RBAC:** un usuario con rol `solo_lectura` ve las tablas pero **sin** botón de
  alta (y el backend devuelve 403 si se fuerza el POST).
</content>
