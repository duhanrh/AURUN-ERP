/** Modal compacto "Editar Muestra": medición, resultado y analista.
 *
 * Cambiar el resultado a "Rechazado" pone el lote en cuarentena (lo hace el backend);
 * volver a "Aprobado" la levanta.
 */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import {
  RESULT_LABEL,
  type QualitySample,
  type SampleResult,
  type UpdateSampleInput,
} from './procesos.types';

interface Props {
  sample: QualitySample;
  submitting: boolean;
  onSubmit: (input: UpdateSampleInput) => Promise<void>;
  onClose: () => void;
}

export function SampleEditModal({ sample, submitting, onSubmit, onClose }: Props) {
  const [measuredPct, setMeasuredPct] = useState(String(Number(sample.measured_purity) * 100));
  const [result, setResult] = useState<SampleResult>(sample.result);
  const [analyst, setAnalyst] = useState(sample.analyst ?? '');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        measured_purity: String(Number(measuredPct) / 100),
        result,
        analyst: analyst.trim() || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar la muestra.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar Muestra {sample.sample_code}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="field-row">
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
            <label className="field">
              <span>Resultado</span>
              <select value={result} onChange={(e) => setResult(e.target.value as SampleResult)}>
                {(Object.keys(RESULT_LABEL) as SampleResult[]).map((r) => (
                  <option key={r} value={r}>
                    {RESULT_LABEL[r]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="field">
            <span>Analista</span>
            <input value={analyst} onChange={(e) => setAnalyst(e.target.value)} />
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
