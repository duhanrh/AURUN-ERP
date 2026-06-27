/** Endpoint de Auditoría (Fase 8). */

import { request } from '../auth/api';
import type { AuditFilters, AuditLog } from './auditoria.types';

export function listAudit(filters: AuditFilters): Promise<AuditLog[]> {
  const params = new URLSearchParams();
  if (filters.date_from) params.set('date_from', filters.date_from);
  if (filters.date_to) params.set('date_to', filters.date_to);
  if (filters.entity_type) params.set('entity_type', filters.entity_type);
  if (filters.action) params.set('action', filters.action);
  const qs = params.toString();
  return request<AuditLog[]>(`/audit${qs ? `?${qs}` : ''}`);
}
