/** Modal "Nueva Orden de Venta" (réplica de `modal-venta`, sección 7.3). */

import { useMemo, useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { Party } from '../terceros/types';
import { grams } from './format';
import type { CreateSalesOrderInput, Lot } from './types';

interface Props {
  customers: Party[];
  lots: Lot[];
  submitting: boolean;
  onSubmit: (input: CreateSalesOrderInput) => Promise<void>;
  onClose: () => void;
}

export function SalesOrderFormModal({ customers, lots, submitting, onSubmit, onClose }: Props) {
  // Sólo lotes con stock disponible pueden venderse.
  const sellable = useMemo(() => lots.filter((l) => Number(l.available_weight_g) > 0), [lots]);
  const [customerId, setCustomerId] = useState(customers[0]?.id ?? '');
  const [lotId, setLotId] = useState(sellable[0]?.id ?? '');
  const [quantity, setQuantity] = useState('');
  const [pricePerOz, setPricePerOz] = useState('');
  const [invoice, setInvoice] = useState('');
  const [error, setError] = useState<string | null>(null);

  const selectedLot = sellable.find((l) => l.id === lotId) ?? null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        customer_id: customerId,
        lot_id: lotId,
        quantity_g: quantity,
        price_per_oz: pricePerOz,
        invoice_number: invoice.trim() || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la venta.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Nueva Orden de Venta</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Cliente</span>
            <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.legal_name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Lote a vender</span>
            <select value={lotId} onChange={(e) => setLotId(e.target.value)} required>
              {sellable.length === 0 ? <option value="">— Sin lotes con stock —</option> : null}
              {sellable.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.lot_code} · {l.material_name} ({grams(l.available_weight_g)} disp.)
                </option>
              ))}
            </select>
          </label>
          <div className="field-row">
            <label className="field">
              <span>Cantidad (g)</span>
              <input
                type="number"
                min={0}
                step={0.0001}
                max={selectedLot ? Number(selectedLot.available_weight_g) : undefined}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Precio venta (USD/oz)</span>
              <input
                type="number"
                min={0}
                step={0.01}
                value={pricePerOz}
                onChange={(e) => setPricePerOz(e.target.value)}
                required
              />
            </label>
          </div>
          <label className="field">
            <span>Nº de factura (opcional)</span>
            <input value={invoice} onChange={(e) => setInvoice(e.target.value)} placeholder="FAC-0001" />
          </label>
          {selectedLot ? (
            <p className="field-hint">
              Stock disponible del lote: {grams(selectedLot.available_weight_g)}
            </p>
          ) : null}
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || sellable.length === 0}
          >
            {submitting ? 'Guardando…' : 'Registrar venta'}
          </button>
        </div>
      </form>
    </div>
  );
}
