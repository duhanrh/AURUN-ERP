/**
 * Mapa de navegación de AURUM ERP.
 *
 * Reproduce el sidebar y los títulos de la maqueta `erp_mineria_preciosos.html`
 * (objeto `pages` + estructura `.nav-section`). Es la fuente de verdad para el
 * enrutador (React Router) y para el componente AppSidebar.
 *
 * En fases siguientes, `items` se filtrará por módulos activos del tenant
 * (sección 7.17) y permisos del usuario (sección 10.2).
 */

export interface NavItem {
  /** Identificador estable del módulo. */
  id: string;
  /** Ruta del enrutador. */
  path: string;
  /** Etiqueta visible en el sidebar. */
  label: string;
  /** Glifo/ícono (igual a la maqueta; se reemplazará por iconos reales después). */
  icon: string;
  /** Título mostrado en la topbar. */
  title: string;
  /** Subtítulo mostrado en la topbar. */
  subtitle: string;
  /** Badge numérico opcional (p. ej. pendientes). */
  badge?: number;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    label: 'Principal',
    items: [
      { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: '◈', title: 'Dashboard General', subtitle: 'Resumen operativo en tiempo real' },
      { id: 'inventario', path: '/inventario', label: 'Inventario', icon: '⬡', title: 'Gestión de Inventario', subtitle: 'Lotes, stocks y valorización' },
      { id: 'compras', path: '/compras', label: 'Compras', icon: '↓', title: 'Módulo de Compras', subtitle: 'Órdenes de compra y proveedores', badge: 3 },
      { id: 'ventas', path: '/ventas', label: 'Ventas', icon: '↑', title: 'Módulo de Ventas', subtitle: 'Órdenes de venta y clientes' },
    ],
  },
  {
    label: 'Operaciones',
    items: [
      { id: 'transformacion', path: '/transformacion', label: 'Transformación', icon: '⚙', title: 'Transformación de Materiales', subtitle: 'Procesos de refinación y conversión' },
      { id: 'proveedores', path: '/proveedores', label: 'Proveedores', icon: '⬟', title: 'Gestión de Proveedores', subtitle: 'Directorio y evaluación de proveedores' },
      { id: 'clientes', path: '/clientes', label: 'Clientes', icon: '◎', title: 'Gestión de Clientes', subtitle: 'Directorio y cartera de clientes' },
      { id: 'calidad', path: '/calidad', label: 'Calidad / Lab', icon: '◉', title: 'Control de Calidad / Laboratorio', subtitle: 'Análisis, certificaciones y muestras' },
    ],
  },
  {
    label: 'Finanzas',
    items: [
      { id: 'finanzas', path: '/finanzas', label: 'Contabilidad', icon: '$', title: 'Contabilidad y Finanzas', subtitle: 'Libro mayor, balance general y cartera' },
      { id: 'reportes', path: '/reportes', label: 'Reportes', icon: '≡', title: 'Reportes y Análisis', subtitle: 'Generación de informes y exportaciones' },
    ],
  },
  {
    label: 'Sistema',
    items: [
      { id: 'configuracion', path: '/configuracion', label: 'Configuración', icon: '✦', title: 'Configuración del Sistema', subtitle: 'Apariencia, módulos, parámetros y usuarios' },
      { id: 'auditoria', path: '/auditoria', label: 'Auditoría', icon: '◷', title: 'Registro de Auditoría', subtitle: 'Trazabilidad inmutable de operaciones críticas' },
    ],
  },
];

/** Lista plana de todos los items de navegación (para el enrutador). */
export const NAV_ITEMS: NavItem[] = NAV_SECTIONS.flatMap((section) => section.items);
