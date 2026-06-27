/**
 * Módulo de Ventas (sección 7.3): KPIs reales + tabla de OV. Crear una venta
 * consume stock del lote; cancelarla lo restituye (lo hace el backend).
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import {
  createSalesOrder,
  listCustomers,
  listLots,
  listSalesOrders,
  salesKpis,
  setSalesStatus,
} from './api';
import { grams, money } from './format';
import { SalesOrderFormModal } from './SalesOrderFormModal';
import { SO_STATUS_BADGE, SO_STATUS_LABEL, type CreateSalesOrderInput } from './types';

export function SalesPage() {
  const queryClient = useQueryClient();
  const canRead = useAuthStore((s) => s.hasPermission('sales:access'));
  const canManage = useAuthStore((s) => s.hasPermission('sales:manage'));
  const [modalOpen, setModalOpen] = useState(false);

  const kpis = useQuery({ queryKey: ['sales', 'kpis'], queryFn: salesKpis, enabled: canRead });
  const orders = useQuery({ queryKey: ['sales', 'orders'], queryFn: listSalesOrders, enabled: canRead });
  const customers = useQuery({ queryKey: ['customers'], queryFn: listCustomers, enabled: canManage });
  const lots = useQuery({ queryKey: ['inventory', 'lots'], queryFn: listLots, enabled: canManage });

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
        {canManage ? (
          <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
            + Nueva OV
          </button>
        ) : null}
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
              <tr key={o.id}>
                <td className="primary">{o.order_code}</td>
                <td>{o.customer_name}</td>
                <td>{o.lot_code}</td>
                <td>{o.material_name}</td>
                <td>{grams(o.quantity_g)}</td>
                <td>{money(o.price_per_oz)}</td>
                <td className="gold">{money(o.total_usd)}</td>
                <td>
                  <span className={`badge ${SO_STATUS_BADGE[o.status]}`}>
                    {SO_STATUS_LABEL[o.status]}
                  </span>
                </td>
                <td>
                  {canManage && !isTerminal(o.status) ? (
                    <div className="row-actions">
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
                    </div>
                  ) : null}
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
