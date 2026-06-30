/**
 * Módulo de Ventas (sección 7.3): KPIs reales + tabla de OV. Crear una venta
 * consume stock del lote; cancelarla lo restituye (lo hace el backend).
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import {
  createSalesOrder,
  deleteSalesOrder,
  listCustomers,
  listLots,
  listSalesOrders,
  restoreSalesOrder,
  salesKpis,
  setSalesStatus,
  updateSalesOrder,
} from './api';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import { grams, money } from './format';
import { SalesOrderEditModal } from './SalesOrderEditModal';
import { SalesOrderFormModal } from './SalesOrderFormModal';
import {
  SO_STATUS_BADGE,
  SO_STATUS_LABEL,
  type CreateSalesOrderInput,
  type SalesOrder,
  type UpdateSalesOrderInput,
} from './types';

export function SalesPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('sales:access'));
  const canManage = useAuthStore((s) => s.hasPermission('sales:manage'));
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<SalesOrder | null>(null);
  const [showDeleted, setShowDeleted] = useState(false);

  const kpis = useQuery({ queryKey: ['sales', 'kpis'], queryFn: salesKpis, enabled: canRead });
  const orders = useQuery({
    queryKey: ['sales', 'orders', { showDeleted }],
    queryFn: () => listSalesOrders(showDeleted),
    enabled: canRead,
  });
  const customers = useQuery({ queryKey: ['customers'], queryFn: listCustomers, enabled: canManage });
  const lots = useQuery({ queryKey: ['inventory', 'lots'], queryFn: () => listLots(), enabled: canManage });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['sales'] });
    await queryClient.invalidateQueries({ queryKey: ['inventory'] });
  };

  const createMutation = useMutation({
    mutationFn: (input: CreateSalesOrderInput) => createSalesOrder(input),
    onSuccess: async () => {
      await invalidate();
      setModalOpen(false);
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (id: string) => setSalesStatus(id, 'cancelled'),
    onSuccess: invalidate,
  });
  const completeMutation = useMutation({
    mutationFn: (id: string) => setSalesStatus(id, 'completed'),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({ mutationFn: deleteSalesOrder, onSuccess: invalidate });
  const restoreMutation = useMutation({ mutationFn: restoreSalesOrder, onSuccess: invalidate });
  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateSalesOrderInput }) =>
      updateSalesOrder(id, input),
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
        <p>No tienes el permiso <code>sales:access</code>.</p>
      </div>
    );
  }

  const k = kpis.data;
  const isTerminal = (s: string) => s === 'completed' || s === 'cancelled';

  return (
    <div className="module-page">
      <div className="kpi-grid">
        <KpiCard label="Monto vendido" value={money(k?.total_amount_usd)} variant="gold" />
        <KpiCard label="Total OV" value={k?.total_orders ?? '—'} variant="" />
        <KpiCard label="Pago pendiente" value={k?.pending_payment ?? '—'} variant="blue" />
        <KpiCard label="Completadas" value={k?.completed ?? '—'} variant="green" />
      </div>

      <div className="section-head">
        <div>
          <h2 className="section-title">Órdenes de venta</h2>
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
              + Nueva OV
            </button>
          ) : (
            <ReadOnlyHint permission="sales:manage" />
          )}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>OV #</th>
              <th>Cliente</th>
              <th>Lote</th>
              <th>Material</th>
              <th>Peso</th>
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
                <td>{o.customer_name}</td>
                <td>{o.lot_code}</td>
                <td>{o.material_name}</td>
                <td>{grams(o.quantity_g)}</td>
                <td>{money(o.price_per_oz)}</td>
                <td className="gold">{money(o.total_usd)}</td>
                <td>
                  {o.is_deleted ? (
                    <span className="badge badge-red">Eliminada</span>
                  ) : (
                    <span className={`badge ${SO_STATUS_BADGE[o.status]}`}>
                      {SO_STATUS_LABEL[o.status]}
                    </span>
                  )}
                </td>
                <td>
                  <div className="row-actions">
                    {canManage && !o.is_deleted && !isTerminal(o.status) ? (
                      <>
                        <button
                          className="btn btn-sm btn-primary"
                          disabled={completeMutation.isPending}
                          onClick={() => completeMutation.mutate(o.id)}
                        >
                          Completar
                        </button>
                        <button
                          className="btn btn-sm btn-ghost"
                          disabled={cancelMutation.isPending}
                          onClick={() => cancelMutation.mutate(o.id)}
                        >
                          Cancelar
                        </button>
                      </>
                    ) : null}
                    {canManage && !o.is_deleted && o.status === 'pending_payment' ? (
                      <button className="btn btn-sm btn-ghost" onClick={() => setEditing(o)}>
                        Editar
                      </button>
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
                    {canManage && !o.is_deleted && o.status === 'cancelled' ? (
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
                  Aún no hay órdenes de venta.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <SalesOrderFormModal
          customers={customers.data ?? []}
          lots={lots.data ?? []}
          submitting={createMutation.isPending}
          onSubmit={async (input) => {
            await createMutation.mutateAsync(input);
          }}
          onClose={() => setModalOpen(false)}
        />
      ) : null}

      {editing ? (
        <SalesOrderEditModal
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
