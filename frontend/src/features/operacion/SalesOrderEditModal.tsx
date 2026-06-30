/** Modal compacto "Editar OV" (sólo en estado pendiente de pago). */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { SalesOrder, UpdateSalesOrderInput } from './types';

interface Props {
  order: SalesOrder;
  submitting: boolean;
  onSubmit: (input: UpdateSalesOrderInput) => Promise<void>;
  onClose: () => void;
}

export function SalesOrderEditModal({ order, submitting, onSubmit, onClose }: Props) {
  const [pricePerOz, setPricePerOz] = useState(order.price_per_oz);
  const [invoice, setInvoice] = useState(order.invoice_number ?? '');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({ price_per_oz: pricePerOz, invoice_number: invoice.trim() || null });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar la orden.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar OV {order.order_code}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Precio de venta (USD/oz)</span>
            <input
              type="number"
              min={0}
              step={0.01}
              value={pricePerOz}
              onChange={(e) => setPricePerOz(e.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>N.º de factura</span>
            <input value={invoice} onChange={(e) => setInvoice(e.target.value)} />
          </label>
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </div>
  );
}
