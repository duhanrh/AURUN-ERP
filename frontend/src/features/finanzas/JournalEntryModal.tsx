/** Modal "Nuevo Asiento" (réplica de `modal-asiento`, sección 7.12).
 *
 * Permite capturar un asiento manual de doble partida con N líneas. La UI no deja
 * registrar hasta que débitos = créditos (la misma invariante la revalida el backend).
 */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import { money } from '../operacion/format';
import type { Account, CreateManualEntryInput, ManualLineInput } from './finanzas.types';

interface Props {
  accounts: Account[];
  submitting: boolean;
  onSubmit: (input: CreateManualEntryInput) => Promise<void>;
  onClose: () => void;
}

interface DraftLine {
  account_code: string;
  debit: string;
  credit: string;
}

const emptyLine = (code: string): DraftLine => ({ account_code: code, debit: '', credit: '' });

export function JournalEntryModal({ accounts, submitting, onSubmit, onClose }: Props) {
  const firstCode = accounts[0]?.code ?? '';
  const [memo, setMemo] = useState('');
  const [lines, setLines] = useState<DraftLine[]>([emptyLine(firstCode), emptyLine(firstCode)]);
  const [error, setError] = useState<string | null>(null);

  const totalDebit = lines.reduce((sum, l) => sum + (Number(l.debit) || 0), 0);
  const totalCredit = lines.reduce((sum, l) => sum + (Number(l.credit) || 0), 0);
  const balanced = totalDebit > 0 && Math.abs(totalDebit - totalCredit) < 0.005;

  function patchLine(index: number, patch: Partial<DraftLine>) {
    setLines((prev) => prev.map((l, i) => (i === index ? { ...l, ...patch } : l)));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const payload: ManualLineInput[] = lines
      .filter((l) => Number(l.debit) > 0 || Number(l.credit) > 0)
      .map((l) => ({
        account_code: l.account_code,
        debit: String(Number(l.debit) || 0),
        credit: String(Number(l.credit) || 0),
      }));
    try {
      await onSubmit({ memo, lines: payload });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar el asiento.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal modal-wide" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Nuevo Asiento Contable</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>Glosa / Detalle</span>
            <input value={memo} onChange={(e) => setMemo(e.target.value)} required maxLength={240} />
          </label>

          <div className="journal-lines">
            <div className="journal-line journal-line-head">
              <span>Cuenta</span>
              <span>Débito</span>
              <span>Crédito</span>
              <span />
            </div>
            {lines.map((line, index) => (
              <div className="journal-line" key={index}>
                <select
                  value={line.account_code}
                  onChange={(e) => patchLine(index, { account_code: e.target.value })}
                >
                  {accounts.map((a) => (
                    <option key={a.id} value={a.code}>
                      {a.code} · {a.name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  placeholder="0.00"
                  value={line.debit}
                  onChange={(e) => patchLine(index, { debit: e.target.value, credit: '' })}
                />
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  placeholder="0.00"
                  value={line.credit}
                  onChange={(e) => patchLine(index, { credit: e.target.value, debit: '' })}
                />
                <button
                  type="button"
                  className="btn btn-sm btn-ghost"
                  disabled={lines.length <= 2}
                  onClick={() => setLines((prev) => prev.filter((_, i) => i !== index))}
                  aria-label="Quitar línea"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={() => setLines((prev) => [...prev, emptyLine(firstCode)])}
          >
            + Agregar línea
          </button>

          <div className="journal-totals">
            <span>Totales</span>
            <span className={balanced ? 'val-ok' : 'val-bad'}>{money(totalDebit)}</span>
            <span className={balanced ? 'val-ok' : 'val-bad'}>{money(totalCredit)}</span>
            <span>
              {balanced ? (
                <span className="badge badge-green">Cuadrado</span>
              ) : (
                <span className="badge badge-red">Descuadrado</span>
              )}
            </span>
          </div>

          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting || !balanced}>
            {submitting ? 'Registrando…' : 'Registrar Asiento'}
          </button>
        </div>
      </form>
    </div>
  );
}
