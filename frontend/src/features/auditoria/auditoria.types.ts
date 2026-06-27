/** Tipos de Auditoría (Fase 8), espejo del API `/audit`. */

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  changes: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditFilters {
  date_from?: string;
  date_to?: string;
  entity_type?: string;
  action?: string;
}

export const ACTION_LABEL: Record<string, string> = {
  'user.create': 'Alta de usuario',
  'config.branding.update': 'Cambio de marca',
  'config.branding.reset': 'Reset de marca',
  'config.parameters.update': 'Cambio de parámetros',
  'config.module.toggle': 'Módulo activado/desactivado',
  'purchase_order.approve': 'Aprobación de OC',
  'accounting.manual_entry': 'Asiento manual',
  'auth.login_failed': 'Acceso fallido',
};
