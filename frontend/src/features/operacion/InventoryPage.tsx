/**
 * Gestión de Inventario (sección 7.1): KPIs reales + tabla de lotes con
 * valorización (peso × pureza × precio). Alta de lote gated por `inventory:manage`.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import {
  createLot,
  inventoryKpis,
  listLots,
  listMaterials,
  listSuppliers,
} from './api';
import { grams, money, purityPct } from './format';
import { LotFormModal } from './LotFormModal';
import { LOT_STATUS_BADGE, LOT_STATUS_LABEL, type CreateLotInput } from './types';

export function InventoryPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('inventory:access'));
  const canManage = useAuthStore((s) => s.hasPermission('inventory:manage'));
  const [modalOpen, setModalOpen] = useState(false);

  const kpis = useQuery({ queryKey: ['inventory', 'kpis'], queryFn: inventoryKpis, enabled: canRead });
  const lots = useQuery({ queryKey: ['inventory', 'lots'], queryFn: listLots, enabled: canRead });
  const materials = useQuery({ queryKey: ['materials'], queryFn: listMaterials, enabled: canManage });
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: listSuppliers, enabled: canManage });

  const createMutation = useMutation({
    mutationFn: (input: CreateLotInput) => createLot(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setModalOpen(false);
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
        {canManage ? (
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            + Nuevo Lote
          </button>
        ) : null}
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
            </tr>
          </thead>
          <tbody>
            {lots.data?.map((lot) => (
              <tr key={lot.id}>
                <td className="primary">{lot.lot_code}</td>
                <td>{lot.material_name}</td>
                <td>{lot.form === 'raw' ? 'Crudo' : 'Refinado'}</td>
                <td>{purityPct(lot.declared_purity)}</td>
                <td>{grams(lot.available_weight_g)}</td>
                <td className="gold">{money(lot.value_usd)}</td>
                <td>
                  <span className={`badge ${LOT_STATUS_BADGE[lot.status]}`}>
                    {LOT_STATUS_LABEL[lot.status]}
                  </span>
                </td>
              </tr>
            ))}
            {lots.data?.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-row">
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
