/**
 * Transformación de Materiales (sección 7.4): KPIs reales + tabla de OT y panel
 * con el componente `Pipeline` reutilizable para la orden seleccionada, con
 * acciones avanzar/completar/cancelar (el backend bloquea si el lote está en
 * cuarentena por una muestra rechazada).
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { listLots, listMaterials } from './api';
import { grams } from './format';
import { Pipeline } from './Pipeline';
import {
  advanceTransformation,
  cancelTransformation,
  completeTransformation,
  createTransformation,
  listTransformations,
  transformationKpis,
} from './procesos.api';
import {
  PROCESS_LABEL,
  STAGE_LABEL,
  STAGE_ORDER,
  TS_STATUS_BADGE,
  TS_STATUS_LABEL,
  type CreateTransformationInput,
} from './procesos.types';
import { TransformationFormModal } from './TransformationFormModal';

const PIPELINE_STAGES = STAGE_ORDER.map((key) => ({ key, label: STAGE_LABEL[key] }));

export function TransformationPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('transformation:access'));
  const canManage = useAuthStore((s) => s.hasPermission('transformation:manage'));
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const kpis = useQuery({ queryKey: ['transformation', 'kpis'], queryFn: transformationKpis, enabled: canRead });
  const orders = useQuery({ queryKey: ['transformation', 'orders'], queryFn: listTransformations, enabled: canRead });
  const lots = useQuery({ queryKey: ['inventory', 'lots'], queryFn: listLots, enabled: canManage });
  const materials = useQuery({ queryKey: ['materials'], queryFn: listMaterials, enabled: canManage });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['transformation'] });
    await queryClient.invalidateQueries({ queryKey: ['inventory'] });
  };

  const createMutation = useMutation({
    mutationFn: (input: CreateTransformationInput) => createTransformation(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const advanceMutation = useMutation({ mutationFn: advanceTransformation, onSuccess: invalidate });
  const completeMutation = useMutation({ mutationFn: completeTransformation, onSuccess: invalidate });
  const cancelMutation = useMutation({ mutationFn: cancelTransformation, onSuccess: invalidate });

  if (!canRead) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>transformation:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;
  const selected = orders.data?.find((o) => o.id === selectedId) ?? null;
  const actionsBusy =
    advanceMutation.isPending || completeMutation.isPending || cancelMutation.isPending;

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Órdenes activas" value={k?.in_progress ?? '—'} variant="gold" />
        <KpiCard label="Total OT" value={k?.total_orders ?? '—'} variant="" />
        <KpiCard label="Completadas" value={k?.completed ?? '—'} variant="green" />
        <KpiCard label="Bloqueadas" value={k?.blocked ?? '—'} variant="blue" />
      </div>

      {selected ? (
        <div className="pipeline-panel">
          <div className="pipeline-panel-head">
            <span>
              {selected.order_code} — {selected.input_material_name} → {selected.output_material_name}
              {selected.blocked ? <span className="badge badge-red"> Bloqueada</span> : null}
            </span>
            {canManage && selected.status === 'in_progress' ? (
              <div className="row-actions">
                <button
                  className="btn btn-sm btn-ghost"
                  disabled={actionsBusy || selected.stage === 'certified'}
                  onClick={() => advanceMutation.mutate(selected.id)}
                >
                  Avanzar etapa
                </button>
                <button
                  className="btn btn-sm btn-primary"
                  disabled={actionsBusy}
                  onClick={() => completeMutation.mutate(selected.id)}
                >
                  Completar
                </button>
                <button
                  className="btn btn-sm btn-ghost"
                  disabled={actionsBusy}
                  onClick={() => cancelMutation.mutate(selected.id)}
                >
                  Cancelar
                </button>
              </div>
            ) : null}
          </div>
          <Pipeline
            stages={PIPELINE_STAGES}
            currentStage={selected.stage}
            completed={selected.status === 'completed'}
            blocked={selected.blocked}
          />
        </div>
      ) : null}

      <div className="section-head">
        <div>
          <h2 className="section-title">Órdenes de transformación</h2>
          <p className="section-subtitle">
            {orders.data ? `${orders.data.length} orden(es) · clic para ver el pipeline` : 'Cargando…'}
          </p>
        </div>
        {canManage ? (
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            + Nueva OT
          </button>
        ) : null}
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>OT #</th>
              <th>Entrada</th>
              <th>Proceso</th>
              <th>Salida</th>
              <th>Cantidad</th>
              <th>Rend. est.</th>
              <th>Etapa</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {orders.data?.map((o) => (
              <tr
                key={o.id}
                className={`row-clickable ${o.id === selectedId ? 'row-selected' : ''}`}
                onClick={() => setSelectedId(o.id)}
              >
                <td className="primary">{o.order_code}</td>
                <td>{o.input_material_name}</td>
                <td>{PROCESS_LABEL[o.process]}</td>
                <td>{o.output_material_name}</td>
                <td>{grams(o.input_quantity_g)}</td>
                <td className="gold">{(Number(o.yield_fraction) * 100).toFixed(0)}%</td>
                <td>
                  <span className="badge badge-gold">{STAGE_LABEL[o.stage]}</span>
                </td>
                <td>
                  <span className={`badge ${TS_STATUS_BADGE[o.status]}`}>
                    {o.blocked ? 'Bloqueada' : TS_STATUS_LABEL[o.status]}
                  </span>
                </td>
              </tr>
            ))}
            {orders.data?.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-row">
                  Aún no hay órdenes de transformación.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <TransformationFormModal
          lots={lots.data ?? []}
          materials={materials.data ?? []}
          submitting={createMutation.isPending}
          onSubmit={async (input) => {
            await createMutation.mutateAsync(input);
          }}
          onClose={() => setModalOpen(false)}
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
