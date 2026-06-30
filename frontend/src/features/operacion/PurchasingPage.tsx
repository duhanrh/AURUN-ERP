/**
 * Módulo de Compras (sección 7.2): KPIs reales + tabla de OC con flujo de
 * aprobación. Aprobar una OC genera el lote de inventario (lo hace el backend).
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import {
  approvePurchaseOrder,
  createPurchaseOrder,
  deletePurchaseOrder,
  listMaterials,
  listPurchaseOrders,
  listSuppliers,
  purchasingKpis,
  rejectPurchaseOrder,
  restorePurchaseOrder,
  updatePurchaseOrder,
} from './api';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import { grams, money, purityPct } from './format';
import { PurchaseOrderEditModal } from './PurchaseOrderEditModal';
import { PurchaseOrderFormModal } from './PurchaseOrderFormModal';
import {
  PO_STATUS_BADGE,
  PO_STATUS_LABEL,
  type CreatePurchaseOrderInput,
  type PurchaseOrder,
  type UpdatePurchaseOrderInput,
} from './types';

export function PurchasingPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('purchasing:access'));
  const canManage = useAuthStore((s) => s.hasPermission('purchasing:manage'));
  const canApprove = useAuthStore((s) => s.hasPermission('purchase_order:approve'));
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PurchaseOrder | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);

  const kpis = useQuery({ queryKey: ['purchasing', 'kpis'], queryFn: purchasingKpis, enabled: canRead });
  const orders = useQuery({
    queryKey: ['purchasing', 'orders', { showDeleted }],
    queryFn: () => listPurchaseOrders(showDeleted),
    enabled: canRead,
  });
  const materials = useQuery({ queryKey: ['materials'], queryFn: listMaterials, enabled: canManage });
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: listSuppliers, enabled: canManage });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['purchasing'] });
    await queryClient.invalidateQueries({ queryKey: ['inventory'] });
  };

  const createMutation = useMutation({
    mutationFn: (input: CreatePurchaseOrderInput) => createPurchaseOrder(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const approveMutation = useMutation({ mutationFn: approvePurchaseOrder, onSuccess: invalidate });
  const rejectMutation = useMutation({ mutationFn: rejectPurchaseOrder, onSuccess: invalidate });
  const deleteMutation = useMutation({ mutationFn: deletePurchaseOrder, onSuccess: invalidate });
  const restoreMutation = useMutation({ mutationFn: restorePurchaseOrder, onSuccess: invalidate });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdatePurchaseOrderInput }) =>
      updatePurchaseOrder(id, input),
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
        <p>No tienes el permiso <code>purchasing:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Monto en órdenes" value={money(k?.total_amount_usd)} variant="gold" />
        <KpiCard label="Total OC" value={k?.total_orders ?? '—'} variant="" />
        <KpiCard label="Pendientes aprobación" value={k?.pending_approval ?? '—'} variant="blue" />
        <KpiCard label="Aprobadas" value={k?.approved ?? '—'} variant="green" />
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">Órdenes de compra</h2>
          <p className="section-subtitle">
            {orders.data ? `${orders.data.length} orden(es)` : 'Cargando…'}
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
              + Nueva OC
            </button>
          ) : (
            <ReadOnlyHint permission="purchasing:manage" />
          )}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>OC #</th>
              <th>Proveedor</th>
              <th>Material</th>
              <th>Cantidad</th>
              <th>Pureza</th>
              <th>Precio/oz</th>
              <th>Total</th>
              <th>Estado</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {orders.data?.map((o) => (
              <tr key={o.id} className={o.is_deleted ? 'row-deleted' : ''}>
                <td className="primary">{o.order_code}</td>
                <td>{o.supplier_name}</td>
                <td>{o.material_name}</td>
                <td>{grams(o.quantity_g)}</td>
                <td>{purityPct(o.declared_purity)}</td>
                <td>{money(o.price_per_oz)}</td>
                <td className="gold">{money(o.total_usd)}</td>
                <td>
                  {o.is_deleted ? (
                    <span className="badge badge-red">Eliminada</span>
                  ) : (
                    <span className={`badge ${PO_STATUS_BADGE[o.status]}`}>
                      {PO_STATUS_LABEL[o.status]}
                    </span>
                  )}
                </td>
                <td>
                  <div className="row-actions">
                    {canApprove && o.status === 'pending_approval' && !o.is_deleted ? (
                      <>
                        <button
                          className="btn btn-sm btn-primary"
                          disabled={approveMutation.isPending}
                          onClick={() => approveMutation.mutate(o.id)}
                        >
                          Aprobar
                        </button>
                        <button
                          className="btn btn-sm btn-ghost"
                          disabled={rejectMutation.isPending}
                          onClick={() => rejectMutation.mutate(o.id)}
                        >
                          Rechazar
                        </button>
                      </>
                    ) : null}
                    {canManage && o.is_deleted ? (
                      <button
                        className="btn btn-sm btn-ghost"
                        disabled={restoreMutation.isPending}
                        onClick={() => restoreMutation.mutate(o.id)}
                      >
                        Restaurar
                      </button>
                    ) : null}
                    {canManage && !o.is_deleted && o.status === 'pending_approval' ? (
                      <button className="btn btn-sm btn-ghost" onClick={() => setEditing(o)}>
                        Editar
                      </button>
                    ) : null}
                    {canManage &&
                    !o.is_deleted &&
                    (o.status === 'pending_approval' || o.status === 'rejected') ? (
                      <button
                        className="btn btn-sm btn-ghost"
                        disabled={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(o.id)}
                      >
                        Eliminar
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
            {orders.data?.length === 0 ? (
              <tr>
                <td colSpan={9} className="empty-row">
                  Aún no hay órdenes de compra.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <PurchaseOrderFormModal
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
        <PurchaseOrderEditModal
          order={editing}
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
