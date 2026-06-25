# Análisis de la maqueta `erp_mineria_preciosos.html`

> Entregable obligatorio de la **Fase 0 — Análisis y cimentación** (checklist de la sección 2.2 de `IMPLEMENTACION_AURUM_ERP.md`).
> Documenta el inventario completo extraído del prototipo de alta fidelidad, base para el desarrollo modular.

Fecha de análisis: 2026-06-25 · Archivo analizado: `erp_mineria_preciosos.html` (2680 líneas, HTML + CSS + JS vanilla, sin dependencias salvo Google Fonts).

---

## 1. Inventario de páginas (`page-*`) y su propósito de negocio

| Página (`id`) | Título topbar | Subtítulo | Propósito de negocio |
|---|---|---|---|
| `page-dashboard` | Dashboard General | Resumen operativo en tiempo real | KPIs ejecutivos, ticker spot, transacciones recientes, alertas, inventario por material, pipeline, ubicaciones |
| `page-inventario` | Gestión de Inventario | Lotes, stocks y valorización | Tabs (Todos/Crudos/Refinados/Cuarentena) + tabla de lotes con pureza/peso/ubicación/estado |
| `page-compras` | Módulo de Compras | Órdenes de compra y proveedores | Tabla de OC con flujo de aprobación (botón Aprobar/Seguir/Ver lote) |
| `page-ventas` | Módulo de Ventas | Órdenes de venta y clientes | Tabla de OV con estado de pago y badge de factura |
| `page-transformacion` | Transformación de Materiales | Procesos de refinación y conversión | Tabla de OT (entrada→proceso→salida, rendimiento, responsable, etapa) |
| `page-calidad` | Control de Calidad / Laboratorio | Análisis, certificaciones y muestras | Tabla de muestras: pureza declarada vs medida, diferencia, resultado |
| `page-proveedores` | Gestión de Proveedores | Directorio y evaluación | Tabla clicable → `drawer-proveedor` (ficha 360°) |
| `page-clientes` | Gestión de Clientes | Directorio y cartera | Tabla clicable → `drawer-cliente` (ficha 360°) |
| `page-finanzas` | Contabilidad y Finanzas | Libro mayor, balance general y cartera | Tabs: CxC/CxP · Libro Mayor (asientos) · Balance General (con verificación de cuadre) |
| `page-reportes` | Reportes y Análisis | Generación de informes y exportaciones | Grid de 6 reportes → vista previa dinámica `renderReport()` |
| `page-configuracion` | Configuración del Sistema | Apariencia, módulos, parámetros y usuarios | Tabs: Apariencia/Marca · Módulos · Parámetros · Usuarios y Roles |

**11 páginas SPA** conmutadas por `navigate(id, el)` (muestra/oculta `.page.active`, sin router real).

---

## 2. Inventario de modales (`modal-*`) y formularios

| Modal (`id`) | Título | Campos del formulario |
|---|---|---|
| `modal-transaccion` | Nueva Transacción | Tipo (compra/venta), Material, Peso (g), Precio/oz, Contraparte, Observaciones |
| `modal-lote` | Registrar Nuevo Lote | Material, Tipo (crudo/refinado), Pureza declarada, Peso bruto (g), Ubicación, Origen/Proveedor |
| `modal-compra` | Nueva Orden de Compra | Proveedor, Material, Cantidad (g), Precio pactado (USD/oz), Fecha entrega |
| `modal-venta` | Nueva Orden de Venta | Cliente, Lote a vender, Cantidad (g), Precio venta (USD/oz) |
| `modal-transformacion` | Nueva Orden de Transformación | Lote origen, Tipo de proceso, Cantidad a procesar (g), Responsable, Fecha fin estimada |
| `modal-muestra` | Registrar Muestra de Laboratorio | Lote a analizar, Método de análisis, Analista, Pureza declarada |
| `modal-asiento` | Nuevo Asiento Contable | Fecha, Cuenta débito, Cuenta crédito, Monto (USD), Descripción/Referencia |
| `modal-proveedor` | Nuevo Proveedor | Razón social, NIT/RUC, País/Región, Material principal, Contacto, Teléfono, Email, Certificaciones |
| `modal-cliente` | Nuevo Cliente | Nombre/Razón social, NIT/Documento, Ciudad, Segmento, Contacto, Teléfono, Email, ¿Línea de crédito? |
| `modal-usuario` | Nuevo Usuario | Nombre, Email corporativo, Rol, checklist de Módulos con acceso (8 checkboxes) |

**10 modales**, abiertos con `openModal(id)` / cerrados con `closeModal(id)` (toggle clase `.open`; cierre por click en overlay). Todos los "submit" son `alert()` simulados.

**2 drawers** (paneles laterales de ficha): `drawer-proveedor`, `drawer-cliente` — abiertos con `openProveedor(i)` / `openCliente(i)`, rellenados desde arrays JS (`fillDrawer`).

---

## 3. Componentes visuales reutilizables detectados

| Componente | Selector/clase | Reutilizado en |
|---|---|---|
| KPI card | `.kpi-card`, `.kpi-grid`, variantes `.gold/.green/.blue/.highlight` | Todas las páginas con cabecera de métricas |
| Panel contenedor | `.panel`, `.panel-header`, `.panel-title`, `.panel-actions` | Todas las páginas |
| Tabla de datos | `table`, `.table-scroll`, `td.primary/.gold/.green/.red` | Inventario, Compras, Ventas, Transf., Calidad, Prov., Clientes, Config |
| Badge de estado | `.badge.green/.gold/.red/.blue/.gray` | Ubicuo (estados de dominio) |
| Botón | `.btn.primary/.secondary`, `.btn-sm`, `.btn-sm.primary` | Ubicuo |
| Tab-bar | `.tab-bar`, `.tab.active` | Inventario, Finanzas, Configuración |
| Drawer de ficha | `.drawer-overlay`, `.drawer`, `.drawer-stat`, `.drawer-info-row`, `.drawer-timeline` | Proveedores, Clientes |
| Timeline | `.drawer-timeline`, `.tl-item`, `.tl-dot` | Drawers de ficha |
| Modal de formulario | `.modal-overlay`, `.modal`, `.form-group`, `.form-input/.form-select` | 10 modales |
| Pipeline de etapas | `.pipeline`, `.pipe-step.done/.active/.pending`, `.pipe-dot` | Dashboard, Transformación |
| Material card | `.material-card`, `.material-grid` | Dashboard, Reportes (como tarjeta de reporte) |
| Alert item | `.alert-item.warn/.info/.ok` | Dashboard, Configuración, Balance |
| Location card | `.location-item` | Dashboard |
| Ticker de precios | `.ticker-strip`, `.ticker-item`, `.ticker-change.up/.down` | Topbar (global) |
| Ledger entry | `.ledger-entry`, `.ledger-debit/.ledger-credit` | Finanzas → Libro Mayor |
| Balance row | `.balance-row`, `.balance-section-title`, `.balance-row.total` | Finanzas → Balance General |
| Report preview | `.report-preview`, `.report-brand`, `.report-meta` | Reportes |
| Theme preset card | `.theme-preset`, `.theme-preset-dots` | Config → Apariencia |
| Color picker | `.color-input-row`, `.color-swatch`, `.color-hex` | Config → Apariencia |
| Logo upload zone | `.logo-upload-zone` | Config → Apariencia |
| Sidebar nav | `.sidebar`, `.nav-item`, `.nav-label`, `.nav-badge` | Layout global |
| Topbar | `.topbar`, `.topbar-title`, `.icon-btn` | Layout global |

---

## 4. Paleta de colores y variables CSS (`:root`) — base del Design System

```css
--gold: #C9A84C;          --gold-light: #E8C96A;     --gold-dim: #7A6228;
--bg-deep: #0A0A0B;       --bg-panel: #13131A;       --bg-card: #1A1A24;
--bg-hover: #22222E;      --border: #2A2A38;         --border-gold: rgba(201,168,76,0.3);
--text-primary: #F0EDE8;  --text-secondary: #8A8A9A; --text-dim: #4A4A5A;
--green: #3DAA6E;         --red: #D45454;            --blue: #4A7CC7;
--emerald: #2D6B5A;       --silver: #A8B0C0;         --platinum: #D8DCE8;
```

**Tipografías:** `Inter` (300–900, texto general) y `Space Grotesk` (400/500/700, cifras y branding).
**Presets de tema** (Config → Apariencia): `gold` (Aurum, default), `emerald`, `platinum`, `copper` — definidos en `THEME_PRESETS` (líneas 2536-2541). El tema por defecto vive en `DEFAULT_BRAND` (2523-2534).

---

## 5. Mapa de navegación (sidebar → página → subtítulo)

```
Principal
  ◈ Dashboard        → page-dashboard      "Resumen operativo en tiempo real"
  ⬡ Inventario       → page-inventario     "Lotes, stocks y valorización"
  ↓ Compras (badge 3)→ page-compras        "Órdenes de compra y proveedores"
  ↑ Ventas           → page-ventas         "Órdenes de venta y clientes"
Operaciones
  ⚙ Transformación   → page-transformacion "Procesos de refinación y conversión"
  ⬟ Proveedores      → page-proveedores    "Directorio y evaluación de proveedores"
  ◎ Clientes         → page-clientes       "Directorio y cartera de clientes"
  ◉ Calidad / Lab    → page-calidad        "Análisis, certificaciones y muestras"
Finanzas
  $ Contabilidad     → page-finanzas       "Libro mayor, balance general y cartera"
  ≡ Reportes         → page-reportes       "Generación de informes y exportaciones"
Sistema
  ✦ Configuración    → page-configuracion  "Apariencia, módulos, parámetros y usuarios"
```

Footer del sidebar: usuario activo (`Admin Minero` / `Superusuario`) + botón colapsar (`toggleSidebar()`).

---

## 6. Flujos de datos simulados (arrays JS embebidos) → entidades de dominio reales

| Array / fuente en la maqueta | Líneas | Entidad de dominio destino |
|---|---|---|
| `proveedoresData[]` | 2344-2350 | `Supplier` (+ contacto, rating, certificaciones, saldo CxP) |
| `clientesData[]` | 2352-2357 | `Client` (+ segmento, crédito, saldo CxC, material preferente) |
| `modules[]` (toggles) | 2318-2329 | `TenantModuleConfig` (módulos activos por tenant) |
| `reportDefs{}` | 2411-2481 | `ReportsModule` (6 reportes con datos reales del tenant) |
| `DEFAULT_BRAND`, `THEME_PRESETS` | 2523-2541 | `TenantBranding` (tema por defecto + presets) |
| `prices{}` + `setInterval` ticker | 2662-2676 | Adaptador de precios spot (XAU/XAG/XPT/XPD) con caché |
| Filas `<tr>` hardcodeadas (lotes, OC, OV, OT, muestras, asientos) | varias | `InventoryLot`, `PurchaseOrder`, `SalesOrder`, `TransformationOrder`, `QualitySample`, `JournalEntry`/`LedgerEntry` |

---

## 7. Sistema de branding (base del multi-tenant de personalización)

- Persistencia actual: `localStorage` con clave `aurumerp_branding_v1` (`STORAGE_KEY`, línea 2543) → **en producción debe migrar a tabla `tenant_branding` + Redis cache** (secciones 5.6 / 7.17).
- Aplicación en runtime: `applyBrandToDOM(brand)` usa `document.documentElement.style.setProperty('--gold', ...)` etc. → **este es exactamente el patrón de CSS Custom Properties que el `ThemeProvider` de React debe replicar**.
- Funciones clave: `loadBranding()`, `saveBranding()`, `resetBranding()` (restaura `DEFAULT_BRAND`), `applyPreset()`, `handleLogoUpload()` (Base64 — en prod va a Object Storage), `shadeColor()` (deriva gold-light/gold-dim del color primario).
- Comportamiento por defecto: sin personalización guardada → se aplica `DEFAULT_BRAND` (tema Aurum). **Requisito explícito** (RF-08).

---

## 8. Patrones de interacción → traducción idiomática al framework

| Patrón en maqueta (vanilla JS) | Mecanismo | Traducción en producción (React) |
|---|---|---|
| `navigate(id, el)` | show/hide `.page` | React Router (`/dashboard`, `/inventario`, …) con `<NavLink>` |
| `toggleSidebar()` | toggle clase + `collapsed` global | Estado UI en store ligero (Zustand) |
| `openModal/closeModal` | toggle `.open` | Componente `<FormModal>` controlado por estado |
| `openProveedor/openCliente(i)` | rellena DOM desde array | `<DetailDrawer>` parametrizado + React Query (datos del API) |
| `switchFinTab/switchConfigTab` | show/hide `.fin-tab`/`.config-tab` | Componente `<Tabs>` con estado local |
| `renderReport(key)` | inyecta HTML | `<ReportPreview>` + datos reales del backend |
| `applyBrandToDOM` | CSS vars en `:root` | `<ThemeProvider>` que inyecta CSS Custom Properties desde `tenant_branding` |
| ticker `setInterval` | mock de precios | Adaptador real a proveedor spot + caché Redis + WebSocket/polling |

---

## 9. Catálogo de dominio inferido de la maqueta

- **Materiales:** Oro (24K/22K/18K), Plata (.999/.925), Platino, Paladio. Símbolos de mercado: XAU/XAG/XPT/XPD. Estados: Crudo / Refinado.
- **Estados de lote:** Disponible, Reservado, En proceso, Stock mínimo, En cuarentena.
- **Estados de OC:** Pendiente aprobación, En tránsito, Recibida, (Rechazada/Cancelada).
- **Estados de OV:** Completada, Pago pendiente, En preparación.
- **Etapas de transformación:** Recepción → Análisis → Fundición → Refinado → Certificado (pipeline de 5 etapas).
- **Procesos:** Refinación ácida, Fusión/Aleación, Laminado, Granulación, Purificación.
- **Métodos de lab:** Copelación (Fire Assay), XRF, Ensayo de fuego, Gravimetría. Resultados: Aprobado / Rechazado.
- **Roles:** Superusuario, Gerente, Operativo, Finanzas, Laboratorio, Solo lectura.
- **Segmentos de cliente:** Joyería/Retail, Institución Financiera, Exportador, Industria, Particular.
- **Cuentas contables vistas:** Caja/Bancos, Inventario-Materia Prima, Cuentas por Cobrar, Cuentas por Pagar, Ingresos por Venta, Costo de Transformación. Balance: Activos / Pasivos / Patrimonio (con verificación de cuadre).
- **Ubicaciones:** Minas (La Esperanza, El Progreso) y Planta (Medellín — bodega + refinería).
- **Reguladores:** DIAN / UIAF (Colombia), SUNAT (Perú), SAT (México).

---

## Checklist de la sección 2.2 — Estado

- [x] Inventario completo de páginas (`page-*`) y su propósito de negocio.
- [x] Inventario completo de modales (`modal-*`) y los formularios que contienen.
- [x] Inventario de componentes visuales reutilizables.
- [x] Extracción de la paleta de colores y variables CSS (`:root`).
- [x] Mapeo de la navegación (sidebar → página → subtítulo).
- [x] Identificación de los flujos de datos simulados (arrays JS).
- [x] Identificación del sistema de branding (localStorage + CSS custom properties).
- [x] Identificación de patrones de interacción para traducir al framework.

**Conclusión:** la maqueta está completamente analizada. Comprende 11 páginas, 10 modales, 2 drawers y ~22 componentes reutilizables sobre un Design System coherente de tema oscuro/dorado. Se procede a la cimentación técnica del repositorio (resto de la Fase 0).
