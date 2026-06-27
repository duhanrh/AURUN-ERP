/**
 * Auditoría (sección 7.18): registro inmutable de operaciones críticas, con filtros
 * por fecha, entidad y acción. Solo lectura (el log es append-only en el backend).
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { listAudit } from './auditoria.api';
import { ACTION_LABEL, type AuditFilters } from './auditoria.types';

export function AuditoriaPage() {
  const canRead = useAuthStore((s) => s.hasPermission('audit:access'));
  const [filters, setFilters] = useState<AuditFilters>({});

  const logs = useQuery({
    queryKey: ['audit', filters],
    queryFn: () => listAudit(filters),
    enabled: canRead,
  });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>audit:access</code>.</p>
      </div>
    );
  }

  const set = (patch: Partial<AuditFilters>) => setFilters((f) => ({ ...f, ...patch }));

  return (
    <div className="module-page">
      <div className="audit-filters">
        <label className="field">
          <span>Desde</span>
          <input
            type="date"
            value={filters.date_from ?? ''}
            onChange={(e) => set({ date_from: e.target.value || undefined })}
          />
        </label>
        <label className="field">
          <span>Hasta</span>
          <input
            type="date"
            value={filters.date_to ?? ''}
            onChange={(e) => set({ date_to: e.target.value || undefined })}
          />
        </label>
        <label className="field">
          <span>Acción</span>
          <select value={filters.action ?? ''} onChange={(e) => set({ action: e.target.value || undefined })}>
            <option value="">Todas</option>
            {Object.entries(ACTION_LABEL).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Acción</th>
              <th>Entidad</th>
              <th>Usuario</th>
              <th>IP</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {logs.data?.map((log) => (
              <tr key={log.id}>
                <td className="ledger-date">{new Date(log.created_at).toLocaleString('es-CO')}</td>
                <td className="primary">{ACTION_LABEL[log.action] ?? log.action}</td>
                <td>{log.entity_type}</td>
                <td className="audit-mono">{log.user_id ? log.user_id.slice(0, 8) : '—'}</td>
                <td className="audit-mono">{log.ip_address ?? '—'}</td>
                <td className="audit-changes">
                  {log.changes ? JSON.stringify(log.changes) : '—'}
                </td>
              </tr>
            ))}
            {logs.data?.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-row">Sin eventos para los filtros seleccionados.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
