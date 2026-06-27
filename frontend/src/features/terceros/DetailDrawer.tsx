/**
 * Panel lateral de ficha 360° reutilizable (réplica de `drawer-proveedor` /
 * `drawer-cliente`, sección 7.5/7.6). Parametrizado por contenido: cabecera con
 * avatar/estado, tarjetas de estadística y secciones de filas info.
 *
 * Es agnóstico del tipo de tercero: clientes y proveedores lo rellenan con sus
 * propios datos (composición sobre herencia), cumpliendo el patrón de "drawer
 * reutilizable" del DoD de Fase 3.
 */

import type { ReactNode } from 'react';

export interface DrawerStat {
  label: string;
  value: string;
  tone?: 'gold' | 'green' | 'red';
}

export interface DrawerRow {
  label: string;
  value: ReactNode;
}

export interface DrawerSection {
  title: string;
  rows: DrawerRow[];
}

interface DetailDrawerProps {
  open: boolean;
  onClose: () => void;
  initials: string;
  title: string;
  subtitle: string;
  badge: { label: string; className: string };
  stats: DrawerStat[];
  sections: DrawerSection[];
  footer?: ReactNode;
}

export function DetailDrawer({
  open,
  onClose,
  initials,
  title,
  subtitle,
  badge,
  stats,
  sections,
  footer,
}: DetailDrawerProps) {
  if (!open) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={title}>
        <div className="drawer-header">
          <div className="drawer-avatar">{initials}</div>
          <div className="drawer-headings">
            <h3>{title}</h3>
            <p>{subtitle}</p>
            <span className={`badge ${badge.className}`}>{badge.label}</span>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="drawer-body">
          {stats.length > 0 ? (
            <div className="drawer-stats">
              {stats.map((stat) => (
                <div key={stat.label} className="drawer-stat">
                  <span className={`drawer-stat-value ${stat.tone ?? ''}`}>{stat.value}</span>
                  <span className="drawer-stat-label">{stat.label}</span>
                </div>
              ))}
            </div>
          ) : null}

          {sections.map((section) => (
            <div key={section.title} className="drawer-section">
              <h4 className="drawer-section-title">{section.title}</h4>
              {section.rows.map((row) => (
                <div key={row.label} className="drawer-info-row">
                  <span className="drawer-info-label">{row.label}</span>
                  <span className="drawer-info-value">{row.value || '—'}</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        {footer ? <div className="drawer-footer">{footer}</div> : null}
      </aside>
    </div>
  );
}
