/** Modal "Registrar Pago" (Tesorería, sección 7.13).
 *
 * Un cobro (inbound) descarga una Cuenta por Cobrar; un pago (outbound) una Cuenta
 * por Pagar. El backend postea la contraparte de Caja/Bancos automáticamente.
 */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { PartyBalance, RegisterPaymentInput } from './finanzas.types';

interface Props {
  direction: 'inbound' | 'outbound';
  parties: PartyBalance[];
  submitting: boolean;
  onSubmit: (input: RegisterPaymentInput) => Promise<void>;
  onClose: () => void;
}

export function PaymentModal({ direction, parties, submitting, onSubmit, onClose }: Props) {
  const titled = direction === 'inbound' ? 'Registrar Cobro' : 'Registrar Pago';
  const selectable = parties.filter((p) => p.party_id);
  const [partyId, setPartyId] = useState(selectable[0]?.party_id ?? '');
  const [amount, setAmount] = useState('');
  const [account, setAccount] = useState('1110');
  const [error, setError] = useState<string | null>(null);

  const party = selectable.find((p) => p.party_id === partyId);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!party) {
      setError('Selecciona un tercero.');
      return;
    }
    try {
      await onSubmit({
        direction,
        party_id: party.party_id as string,
        party_name: party.party_name,
        amount,
        cash_account_code: account,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo registrar el pago.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>{titled}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>{direction === 'inbound' ? 'Cliente' : 'Proveedor'}</span>
            <select value={partyId} onChange={(e) => setPartyId(e.target.value)} required>
              {selectable.map((p) => (
                <option key={p.party_id} value={p.party_id as string}>
                  {p.party_name} — saldo {p.balance}
                </option>
              ))}
            </select>
          </label>
          <div className="field-row">
            <label className="field">
              <span>Monto (USD)</span>
              <input
                type="number"
                min={0}
                step={0.01}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </label>
            <label className="field">
              <span>Cuenta de caja</span>
              <select value={account} onChange={(e) => setAccount(e.target.value)}>
                <option value="1110">Bancos</option>
                <option value="1105">Caja</option>
              </select>
            </label>
          </div>
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting || !selectable.length}>
            {submitting ? 'Registrando…' : titled}
          </button>
        </div>
      </form>
    </div>
  );
}
