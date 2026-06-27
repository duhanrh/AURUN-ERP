/** Modal "Registrar Nuevo Lote" (réplica de `modal-lote`, sección 7.1). */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { Party } from '../terceros/types';
import type { CreateLotInput, LotForm, Material } from './types';

interface LotFormModalProps {
  materials: Material[];
  suppliers: Party[];
  submitting: boolean;
  onSubmit: (input: CreateLotInput) => Promise<void>;
  onClose: () => void;
}

export function LotFormModal({
  materials,
  suppliers,
  submitting,
  onSubmit,
  onClose,
}: LotFormModalProps) {
  const [materialId, setMaterialId] = useState(materials[0]?.id ?? '');
  const [form, setForm] = useState<LotForm>('raw');
  const [purityPct, setPurityPct] = useState('99.9');
  const [grossWeight, setGrossWeight] = useState('');
  const [pricePerOz, setPricePerOz] = useState('');
  const [location, setLocation] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        material_id: materialId,
        form,
        declared_purity: String(Number(purityPct) / 100),
        gross_weight_g: grossWeight,
        price_per_oz: pricePerOz,
        location: location.trim() || null,
        supplier_id: supplierId || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar el lote.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Registrar Nuevo Lote</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
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
            <label className="field">
              <span>Peso bruto (g)</span>
              <input
                type="number"
                min={0}
                step={0.0001}
                value={grossWeight}
                onChange={(e) => setGrossWeight(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Precio (USD/oz)</span>
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
              <span>Ubicación</span>
              <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Planta Medellín" />
            </label>
          </div>
          <label className="field">
            <span>Origen / Proveedor (opcional)</span>
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="">— Sin proveedor —</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.legal_name}
                </option>
              ))}
            </select>
          </label>
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Guardando…' : 'Registrar lote'}
          </button>
        </div>
      </form>
    </div>
  );
}
