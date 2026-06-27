/**
 * Reportes (sección 7.15): réplica de `page-reportes`. Grid de tarjetas de reporte
 * + vista previa dinámica con datos reales del tenant y descarga del CSV real.
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { downloadReportCsv, listReports, previewReport } from './reportes.api';
import type { ReportTable } from './reportes.types';

export function ReportesPage() {
  const canRead = useAuthStore((s) => s.hasPermission('reports:access'));
  const [selected, setSelected] = useState<string | null>(null);

  const reports = useQuery({ queryKey: ['reports'], queryFn: listReports, enabled: canRead });
  const preview = useQuery({
    queryKey: ['reports', selected],
    queryFn: () => previewReport(selected as string),
    enabled: canRead && selected !== null,
  });
  const download = useMutation({ mutationFn: (key: string) => downloadReportCsv(key) });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>reports:access</code>.</p>
      </div>
    );
  }

  return (
    <div className="module-page">
      <div className="section-head">
        <div>
          <h2 className="section-title">Generador de reportes</h2>
          <p className="section-subtitle">Datos reales del tenant. Exporta a CSV descargable.</p>
        </div>
      </div>

      <div className="report-grid">
        {reports.data?.map((r) => (
          <button
            key={r.key}
            className={`report-card${selected === r.key ? ' selected' : ''}`}
            onClick={() => setSelected(r.key)}
          >
            <span className="report-title">{r.title}</span>
            <span className="report-desc">{r.description}</span>
          </button>
        ))}
      </div>

      {selected ? (
        <ReportPreview
          table={preview.data}
          loading={preview.isLoading}
          downloading={download.isPending}
          onDownload={() => download.mutate(selected)}
        />
      ) : (
        <div className="report-empty">Selecciona un reporte para ver la vista previa.</div>
      )}
    </div>
  );
}

function ReportPreview({
  table,
  loading,
  downloading,
  onDownload,
}: {
  table: ReportTable | undefined;
  loading: boolean;
  downloading: boolean;
  onDownload: () => void;
}) {
  if (loading || !table) return <div className="report-preview">Generando reporte…</div>;
  return (
    <div className="report-preview">
      <div className="report-brand">
        <div>
          <div className="report-brand-name">{table.brand_name}</div>
          <div className="report-doc-title">{table.title}</div>
        </div>
        <div className="report-meta">
          <div>{table.document_number}</div>
          <div>{new Date(table.generated_at).toLocaleString('es-CO')}</div>
        </div>
      </div>

      <div className="section-head">
        <span className="section-subtitle">{table.rows.length} fila(s)</span>
        <button className="btn btn-sm btn-primary" disabled={downloading} onClick={onDownload}>
          {downloading ? 'Exportando…' : 'Exportar CSV'}
        </button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              {table.columns.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j} className={j === 0 ? 'primary' : ''}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
            {table.rows.length === 0 ? (
              <tr>
                <td colSpan={table.columns.length} className="empty-row">
                  Sin datos para este reporte todavía.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {table.summary.length ? (
        <div className="report-summary">
          {table.summary.map((s) => (
            <div className="report-summary-item" key={s.label}>
              <span className="report-summary-label">{s.label}</span>
              <span className="report-summary-value">{s.value}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
