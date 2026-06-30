/**
 * Gestión de Inventario (sección 7.1): KPIs reales + tabla de lotes con
 * valorización (peso × pureza × precio). Alta de lote gated por `inventory:manage`.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import {
  createLot,
  deleteLot,
  inventoryKpis,
  listLots,
  listMaterials,
  listSuppliers,
  restoreLot,
  updateLot,
} from './api';
import { ApiError } from '../auth/api';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import { grams, money, purityPct } from './format';
import { LotEditModal } from './LotEditModal';
import { LotFormModal } from './LotFormModal';
import {
  LOT_STATUS_BADGE,
  LOT_STATUS_LABEL,
  type CreateLotInput,
  type Lot,
  type UpdateLotInput,
} from './types';

export function InventoryPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('inventory:access'));
  const canManage = useAuthStore((s) => s.hasPermission('inventory:manage'));
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Lot | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);

  const kpis = useQuery({ queryKey: ['inventory', 'kpis'], queryFn: inventoryKpis, enabled: canRead });
  const lots = useQuery({
    queryKey: ['inventory', 'lots', { showDeleted }],
    queryFn: () => listLots(showDeleted),
    enabled: canRead,
  });
  const materials = useQuery({ queryKey: ['materials'], queryFn: listMaterials, enabled: canManage });
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: listSuppliers, enabled: canManage });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['inventory'] });
  const createMutation = useMutation({
    mutationFn: (input: CreateLotInput) => createLot(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteLot,
    onSuccess: invalidate,
    onError: (e) => alert(e instanceof ApiError ? e.message : 'No se pudo eliminar el lote.'),
  });
  const restoreMutation = useMutation({ mutationFn: restoreLot, onSuccess: invalidate });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateLotInput }) => updateLot(id, input),
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
        <p>No tienes el permiso <code>inventory:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;
  const split = k && k.total_lots > 0 ? `${k.raw_lots} / ${k.refined_lots}` : '—';

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Valor total inventario" value={money(k?.total_value_usd)} variant="gold" />
        <KpiCard label="Total lotes" value={k?.total_lots ?? '—'} variant="" />
        <KpiCard label="Peso disponible" value={grams(k?.total_gross_weight_g)} variant="blue" />
        <KpiCard label="Crudos / Refinados" value={split} variant="green" />
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">Lotes de inventario</h2>
          <p className="section-subtitle">
            {lots.data ? `${lots.data.length} lote(s)` : 'Cargando…'}
          </p>
        </div>
        <div className="row-actions">
          <label className="toggle-deleted">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
            />
            Mostrar eliminados
          </label>
          {canManage ? (
            <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
              + Nuevo Lote
            </button>
          ) : (
            <ReadOnlyHint permission="inventory:manage" />
          )}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Lote</th>
              <th>Material</th>
              <th>Tipo</th>
              <th>Pureza</th>
              <th>Peso disp.</th>
              <th>Valor est.</th>
              <th>Estado</th>
              {canManage ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {lots.data?.map((lot) => (
              <tr key={lot.id} className={lot.is_deleted ? 'row-deleted' : ''}>
                <td className="primary">{lot.lot_code}</td>
                <td>{lot.material_name}</td>
                <td>{lot.form === 'raw' ? 'Crudo' : 'Refinado'}</td>
                <td>{purityPct(lot.declared_purity)}</td>
                <td>{grams(lot.available_weight_g)}</td>
                <td className="gold">{money(lot.value_usd)}</td>
                <td>
                  {lot.is_deleted ? (
                    <span className="badge badge-red">Eliminado</span>
                  ) : (
                    <span className={`badge ${LOT_STATUS_BADGE[lot.status]}`}>
                      {LOT_STATUS_LABEL[lot.status]}
                    </span>
                  )}
                </td>
                {canManage ? (
                  <td>
                    <div className="row-actions">
                      {lot.is_deleted ? (
                        <button
                          className="btn btn-sm btn-ghost"
                          disabled={restoreMutation.isPending}
                          onClick={() => restoreMutation.mutate(lot.id)}
                        >
                          Restaurar
                        </button>
                      ) : (
                        <>
                          <button className="btn btn-sm btn-ghost" onClick={() => setEditing(lot)}>
                            Editar
                          </button>
                          <button
                            className="btn btn-sm btn-ghost"
                            disabled={deleteMutation.isPending}
                            onClick={() => deleteMutation.mutate(lot.id)}
                          >
                            Eliminar
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
            {lots.data?.length === 0 ? (
              <tr>
                <td colSpan={canManage ? 8 : 7} className="empty-row">
                  Aún no hay lotes. Crea uno o aprueba una orden de compra.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <LotFormModal
          materials={materials.data ?? []}
          suppliers={suppliers.data ?? []}
          submitting={createMutation.isPending}
          onSubmit={async (input) => {
            await createMutation.mutateAsync(input);
          }}
          onClose={() => setModalOpen(false)}
        />
      ) : null}

      {editing ? (
        <LotEditModal
          lot={editing}
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
