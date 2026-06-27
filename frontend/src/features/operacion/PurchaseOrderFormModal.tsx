/** Modal "Nueva Orden de Compra" (réplica de `modal-compra`, sección 7.2). */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { Party } from '../terceros/types';
import type { CreatePurchaseOrderInput, LotForm, Material } from './types';

interface Props {
  materials: Material[];
  suppliers: Party[];
  submitting: boolean;
  onSubmit: (input: CreatePurchaseOrderInput) => Promise<void>;
  onClose: () => void;
}

export function PurchaseOrderFormModal({ materials, suppliers, submitting, onSubmit, onClose }: Props) {
  const [supplierId, setSupplierId] = useState(suppliers[0]?.id ?? '');
  const [materialId, setMaterialId] = useState(materials[0]?.id ?? '');
  const [quantity, setQuantity] = useState('');
  const [purityPct, setPurityPct] = useState('75');
  const [form, setForm] = useState<LotForm>('raw');
  const [pricePerOz, setPricePerOz] = useState('');
  const [delivery, setDelivery] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        supplier_id: supplierId,
        material_id: materialId,
        quantity_g: quantity,
        declared_purity: String(Number(purityPct) / 100),
        price_per_oz: pricePerOz,
        form,
        expected_delivery: delivery || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo crear la orden.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Nueva Orden de Compra</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Proveedor</span>
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.legal_name}
                </option>
              ))}
            </select>
          </label>
          <div className="field-row">
            <label className="field">
              <span>Material</span>
              <select value={materialId} onChange={(e) => setMaterialId(e.target.value)} required>
                {materials.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
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
            {submitting ? 'Guardando…' : 'Crear orden'}
          </button>
        </div>
      </form>
    </div>
  );
}
