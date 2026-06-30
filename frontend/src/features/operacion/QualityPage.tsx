/**
 * Control de Calidad / Laboratorio (sección 7.5): KPIs reales + tabla de muestras
 * (pureza declarada vs medida + diferencia). Una muestra "Rechazado" pone el lote
 * en cuarentena (lo hace el backend). Alta gated por `quality:manage`.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { listLots } from './api';
import { purityPct } from './format';
import {
  createSample,
  deleteSample,
  listSamples,
  qualityKpis,
  restoreSample,
  updateSample,
} from './procesos.api';
import {
  METHOD_LABEL,
  RESULT_BADGE,
  RESULT_LABEL,
  type CreateSampleInput,
  type QualitySample,
  type UpdateSampleInput,
} from './procesos.types';
import { SampleEditModal } from './SampleEditModal';
import { SampleFormModal } from './SampleFormModal';

export function QualityPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('quality:access'));
  const canManage = useAuthStore((s) => s.hasPermission('quality:manage'));
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<QualitySample | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);

  const kpis = useQuery({ queryKey: ['quality', 'kpis'], queryFn: qualityKpis, enabled: canRead });
  const samples = useQuery({
    queryKey: ['quality', 'samples', { showDeleted }],
    queryFn: () => listSamples(showDeleted),
    enabled: canRead,
  });
  const lots = useQuery({ queryKey: ['inventory', 'lots'], queryFn: () => listLots(), enabled: canManage });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['quality'] });
    await queryClient.invalidateQueries({ queryKey: ['inventory'] });
  };
  const createMutation = useMutation({
    mutationFn: (input: CreateSampleInput) => createSample(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const deleteMutation = useMutation({ mutationFn: deleteSample, onSuccess: invalidate });
  const restoreMutation = useMutation({ mutationFn: restoreSample, onSuccess: invalidate });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateSampleInput }) => updateSample(id, input),
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
    },
  });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>quality:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Muestras" value={k?.total_samples ?? '—'} variant="gold" />
        <KpiCard label="Aprobadas" value={k?.approved ?? '—'} variant="green" />
        <KpiCard label="Rechazadas" value={k?.rejected ?? '—'} variant="" />
        <KpiCard label="Pendientes" value={k?.pending ?? '—'} variant="blue" />
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">Muestras de laboratorio</h2>
          <p className="section-subtitle">
            {samples.data ? `${samples.data.length} muestra(s)` : 'Cargando…'}
          </p>
        </div>
        <div className="row-actions">
          <label className="toggle-deleted">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
            />
            Mostrar eliminadas
          </label>
          {canManage ? (
            <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
              + Registrar Muestra
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Muestra #</th>
              <th>Lote</th>
              <th>Material</th>
              <th>Método</th>
              <th>Declarada</th>
              <th>Medida</th>
              <th>Diferencia</th>
              <th>Analista</th>
              <th>Resultado</th>
              {canManage ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {samples.data?.map((s) => {
              const diff = Number(s.difference);
              return (
                <tr key={s.id} className={s.is_deleted ? 'row-deleted' : ''}>
                  <td className="primary">{s.sample_code}</td>
                  <td>{s.lot_code}</td>
                  <td>{s.material_name}</td>
                  <td>{METHOD_LABEL[s.method]}</td>
                  <td>{purityPct(s.declared_purity)}</td>
                  <td>{purityPct(s.measured_purity)}</td>
                  <td className={diff < 0 ? 'neg' : 'gold'}>
                    {diff >= 0 ? '+' : ''}
                    {purityPct(s.difference)}
                  </td>
                  <td>{s.analyst ?? '—'}</td>
                  <td>
                    {s.is_deleted ? (
                      <span className="badge badge-red">Eliminada</span>
                    ) : (
                      <span className={`badge ${RESULT_BADGE[s.result]}`}>{RESULT_LABEL[s.result]}</span>
                    )}
                  </td>
                  {canManage ? (
                    <td>
                      <div className="row-actions">
                        {s.is_deleted ? (
                          <button
                            className="btn btn-sm btn-ghost"
                            disabled={restoreMutation.isPending}
                            onClick={() => restoreMutation.mutate(s.id)}
                          >
                            Restaurar
                          </button>
                        ) : (
                          <>
                            <button className="btn btn-sm btn-ghost" onClick={() => setEditing(s)}>
                              Editar
                            </button>
                            <button
                              className="btn btn-sm btn-ghost"
                              disabled={deleteMutation.isPending}
                              onClick={() => deleteMutation.mutate(s.id)}
                            >
                              Eliminar
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  ) : null}
                </tr>
              );
            })}
            {samples.data?.length === 0 ? (
              <tr>
                <td colSpan={canManage ? 10 : 9} className="empty-row">
                  Aún no hay muestras registradas.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <SampleFormModal
          lots={lots.data ?? []}
          submitting={createMutation.isPending}
          onSubmit={async (input) => {
            await createMutation.mutateAsync(input);
          }}
          onClose={() => setModalOpen(false)}
        />
      ) : null}

      {editing ? (
        <SampleEditModal
          sample={editing}
          submitting={updateMutation.isPending}
          onSubmit={async (input) => {
            await updateMutation.mutateAsync({ id: editing.id, input });
          }}
          onClose={() => setEditing(null)}
        />
      ) : null}
    </div>
  );
}

function KpiCard({ label, value, variant }: { label: string; value: string | number; variant: string }) {
  return (
    <div className={`kpi-card ${variant}`}>
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{label}</span>
    </div>
  );
}
