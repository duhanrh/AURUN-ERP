/** Endpoints de Reportes (Fase 7): catálogo, vista previa y descarga (CSV/Excel/PDF). */

import { request } from '../auth/api';
import { useAuthStore } from '../auth/authStore';
import { API_BASE_URL, API_PREFIX } from '../../lib/config';
import type { ReportTable, ReportType } from './reportes.types';

export type ExportFormat = 'csv' | 'xlsx' | 'pdf';

export const listReports = () => request<ReportType[]>('/reports');
export const previewReport = (key: string) => request<ReportTable>(`/reports/${key}`);

/** Descarga el reporte en el formato indicado, autenticado, vía un enlace temporal. */
export async function downloadReport(key: string, format: ExportFormat = 'csv'): Promise<void> {
  const { accessToken, tenantId } = useAuthStore.getState();
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (tenantId) headers['X-Tenant-ID'] = tenantId;

  const response = await fetch(
    `${API_BASE_URL}${API_PREFIX}/reports/${key}/export?format=${format}`,
    { headers },
  );
  if (!response.ok) throw new Error('No se pudo exportar el reporte.');

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  const disposition = response.headers.get('content-disposition') ?? '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  link.download = match ? match[1] : `${key}.${format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
