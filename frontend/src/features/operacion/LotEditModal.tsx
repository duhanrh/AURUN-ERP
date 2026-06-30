/** Modal compacto "Editar Lote": ubicación y estado de negocio del lote. */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import { LOT_STATUS_LABEL, type Lot, type LotStatus, type UpdateLotInput } from './types';

interface Props {
  lot: Lot;
  submitting: boolean;
  onSubmit: (input: UpdateLotInput) => Promise<void>;
  onClose: () => void;
}

export function LotEditModal({ lot, submitting, onSubmit, onClose }: Props) {
  const [location, setLocation] = useState(lot.location ?? '');
  const [status, setStatus] = useState<LotStatus>(lot.status);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({ location: location.trim() || null, status });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar el lote.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar Lote {lot.lot_code}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Ubicación</span>
            <input value={location} onChange={(e) => setLocation(e.target.value)} />
          </label>
          <label className="field">
            <span>Estado</span>
            <select value={status} onChange={(e) => setStatus(e.target.value as LotStatus)}>
              {(Object.keys(LOT_STATUS_LABEL) as LotStatus[]).map((s) => (
                <option key={s} value={s}>
                  {LOT_STATUS_LABEL[s]}
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
            {submitting ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </div>
  );
}
