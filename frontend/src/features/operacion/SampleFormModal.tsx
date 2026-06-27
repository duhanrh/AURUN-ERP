/** Modal "Registrar Muestra de Laboratorio" (sección 7.5). */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import { purityPct } from './format';
import type { AnalysisMethod, CreateSampleInput, SampleResult } from './procesos.types';
import { METHOD_LABEL, RESULT_LABEL } from './procesos.types';
import type { Lot } from './types';

interface Props {
  lots: Lot[];
  submitting: boolean;
  onSubmit: (input: CreateSampleInput) => Promise<void>;
  onClose: () => void;
}

export function SampleFormModal({ lots, submitting, onSubmit, onClose }: Props) {
  const [lotId, setLotId] = useState(lots[0]?.id ?? '');
  const [method, setMethod] = useState<AnalysisMethod>('fire_assay');
  const [measuredPct, setMeasuredPct] = useState('');
  const [result, setResult] = useState<SampleResult>('approved');
  const [analyst, setAnalyst] = useState('');
  const [error, setError] = useState<string | null>(null);

  const selectedLot = lots.find((l) => l.id === lotId) ?? null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        lot_id: lotId,
        method,
        measured_purity: String(Number(measuredPct) / 100),
        result,
        analyst: analyst.trim() || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar la muestra.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Registrar Muestra</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Lote de origen</span>
            <select value={lotId} onChange={(e) => setLotId(e.target.value)} required>
              {lots.length === 0 ? <option value="">— Sin lotes —</option> : null}
              {lots.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.lot_code} · {l.material_name}
                </option>
              ))}
            </select>
          </label>
          {selectedLot ? (
            <p className="field-hint">Pureza declarada del lote: {purityPct(selectedLot.declared_purity)}</p>
          ) : null}
          <div className="field-row">
            <label className="field">
              <span>Método</span>
              <select value={method} onChange={(e) => setMethod(e.target.value as AnalysisMethod)}>
                {(Object.keys(METHOD_LABEL) as AnalysisMethod[]).map((m) => (
                  <option key={m} value={m}>
                    {METHOD_LABEL[m]}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Pureza medida (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                value={measuredPct}
                onChange={(e) => setMeasuredPct(e.target.value)}
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label className="field">
              <span>Resultado</span>
              <select value={result} onChange={(e) => setResult(e.target.value as SampleResult)}>
                {(['approved', 'rejected', 'pending'] as SampleResult[]).map((r) => (
                  <option key={r} value={r}>
                    {RESULT_LABEL[r]}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Analista</span>
              <input value={analyst} onChange={(e) => setAnalyst(e.target.value)} />
            </label>
          </div>
          {result === 'rejected' ? (
            <p className="field-hint">Un resultado rechazado pondrá el lote en cuarentena.</p>
          ) : null}
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting || lots.length === 0}>
            {submitting ? 'Guardando…' : 'Registrar muestra'}
          </button>
        </div>
      </form>
    </div>
  );
}
