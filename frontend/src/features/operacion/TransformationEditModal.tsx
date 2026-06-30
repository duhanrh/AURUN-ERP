/** Modal compacto "Editar OT" (sólo en curso): responsable y fechas. */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { TransformationOrder, UpdateTransformationInput } from './procesos.types';

interface Props {
  order: TransformationOrder;
  submitting: boolean;
  onSubmit: (input: UpdateTransformationInput) => Promise<void>;
  onClose: () => void;
}

export function TransformationEditModal({ order, submitting, onSubmit, onClose }: Props) {
  const [responsible, setResponsible] = useState(order.responsible ?? '');
  const [startedAt, setStartedAt] = useState(order.started_at ?? '');
  const [expectedEnd, setExpectedEnd] = useState(order.expected_end ?? '');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit({
        responsible: responsible.trim() || null,
        started_at: startedAt || null,
        expected_end: expectedEnd || null,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo actualizar la orden.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Editar OT {order.order_code}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Responsable</span>
            <input value={responsible} onChange={(e) => setResponsible(e.target.value)} />
          </label>
          <div className="field-row">
            <label className="field">
              <span>Inicio</span>
              <input type="date" value={startedAt} onChange={(e) => setStartedAt(e.target.value)} />
            </label>
            <label className="field">
              <span>Fin estimado</span>
              <input
                type="date"
                value={expectedEnd}
                onChange={(e) => setExpectedEnd(e.target.value)}
              />
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
