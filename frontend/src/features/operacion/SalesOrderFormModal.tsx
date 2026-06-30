/** Modal "Nueva Orden de Venta" (réplica de `modal-venta`, sección 7.3). */

import { useMemo, useState, type FormEvent } from 'react';

import { SearchableSelect, type SelectOption } from '../../components/SearchableSelect';
import { ApiError } from '../auth/api';
import { QuickCreatePartyModal } from '../terceros/QuickCreatePartyModal';
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
  const [extraCustomers, setExtraCustomers] = useState<Party[]>([]);
  const [customerId, setCustomerId] = useState(customers[0]?.id ?? '');
  const [lotId, setLotId] = useState(sellable[0]?.id ?? '');
  const [quantity, setQuantity] = useState('');
  const [pricePerOz, setPricePerOz] = useState('');
  const [invoice, setInvoice] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [createName, setCreateName] = useState<string | null>(null);

  const allCustomers = useMemo(() => {
    const seen = new Set(customers.map((c) => c.id));
    return [...extraCustomers.filter((c) => !seen.has(c.id)), ...customers];
  }, [customers, extraCustomers]);

  const customerOptions: SelectOption[] = allCustomers.map((c) => ({
    value: c.id,
    label: c.legal_name,
    hint: c.tax_id,
  }));
  const lotOptions: SelectOption[] = sellable.map((l) => ({
    value: l.id,
    label: `${l.lot_code} · ${l.material_name}`,
    hint: grams(l.available_weight_g),
  }));

  const selectedLot = sellable.find((l) => l.id === lotId) ?? null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!customerId) return setError('Selecciona un cliente.');
    if (!lotId) return setError('Selecciona un lote.');
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
    <>
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
              <SearchableSelect
                options={customerOptions}
                value={customerId}
                onChange={setCustomerId}
                placeholder="Buscar cliente…"
                onCreateNew={(q) => setCreateName(q)}
                createLabel={(q) => `Crear cliente «${q}»`}
              />
            </label>
            <label className="field">
              <span>Lote a vender</span>
              <SearchableSelect
                options={lotOptions}
                value={lotId}
                onChange={setLotId}
                placeholder="Buscar lote con stock…"
                emptyText="Sin lotes con stock"
              />
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

      {createName !== null ? (
        <QuickCreatePartyModal
          kind="customer"
          initialName={createName}
          onCreated={(party) => {
            setExtraCustomers((prev) => [party, ...prev]);
            setCustomerId(party.id);
            setCreateName(null);
          }}
          onClose={() => setCreateName(null)}
        />
      ) : null}
    </>
  );
}
