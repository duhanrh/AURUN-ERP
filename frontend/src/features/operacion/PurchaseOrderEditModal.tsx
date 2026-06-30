/** Modal compacto "Editar OC" (sólo en estado pendiente de aprobación). */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { LotForm, PurchaseOrder, UpdatePurchaseOrderInput } from './types';

interface Props {
  order: PurchaseOrder;
  submitting: boolean;
  onSubmit: (input: UpdatePurchaseOrderInput) => Promise<void>;
  onClose: () => void;
}

export function PurchaseOrderEditModal({ order, submitting, onSubmit, onClose }: Props) {
  const [quantity, setQuantity] = useState(order.quantity_g);
  const [purityPct, setPurityPct] = useState(String(Number(order.declared_purity) * 100));
  const [pricePerOz, setPricePerOz] = useState(order.price_per_oz);
  const [form, setForm] = useState<LotForm>(order.form);
  const [location, setLocation] = useState(order.location ?? '');
  const [delivery, setDelivery] = useState(order.expected_delivery ?? '');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        quantity_g: quantity,
        declared_purity: String(Number(purityPct) / 100),
        price_per_oz: pricePerOz,
        form,
        location: location.trim() || null,
        expected_delivery: delivery || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar la orden.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar OC {order.order_code}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="field-row">
            <label className="field">
              <span>Cantidad (g)</span>
              <input
                type="number"
                min={0}
                step={0.0001}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Pureza declarada (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                value={purityPct}
                onChange={(e) => setPurityPct(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Precio pactado (USD/oz)</span>
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
              <span>Tipo</span>
              <select value={form} onChange={(e) => setForm(e.target.value as LotForm)}>
                <option value="raw">Crudo</option>
                <option value="refined">Refinado</option>
              </select>
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Ubicación destino</span>
              <input value={location} onChange={(e) => setLocation(e.target.value)} />
            </label>
            <label className="field">
              <span>Entrega estimada</span>
              <input type="date" value={delivery} onChange={(e) => setDelivery(e.target.value)} />
            </label>
          </div>
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
