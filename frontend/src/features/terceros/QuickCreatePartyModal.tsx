/**
 * Creación rápida de un tercero (cliente/proveedor) desde otro flujo (venta, compra,
 * lote). Pide lo mínimo (razón social + NIT, contacto opcional), lo crea vía API,
 * invalida la lista correspondiente y devuelve el tercero creado para seleccionarlo.
 */

import { useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '../auth/api';
import { createParty } from './api';
import type { CreatePartyInput, Party, PartyKind } from './types';

interface Props {
  kind: PartyKind;
  /** Prefill de la razón social con lo que el usuario escribió en el combobox. */
  initialName?: string;
  onCreated: (party: Party) => void;
  onClose: () => void;
}

export function QuickCreatePartyModal({ kind, initialName = '', onCreated, onClose }: Props) {
  const isSupplier = kind === 'supplier';
  const resource = isSupplier ? 'suppliers' : 'customers';
  const queryClient = useQueryClient();

  const [legalName, setLegalName] = useState(initialName);
  const [taxId, setTaxId] = useState('');
  const [contact, setContact] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (input: CreatePartyInput) => createParty(kind, input),
    onSuccess: async (party) => {
      await queryClient.invalidateQueries({ queryKey: [resource] });
      onCreated(party);
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'No se pudo crear el tercero.'),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    mutation.mutate({
      legal_name: legalName.trim(),
      tax_id: taxId.trim(),
      contact_name: contact.trim() || null,
      phone: phone.trim() || null,
      email: email.trim() || null,
    });
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>{isSupplier ? 'Nuevo Proveedor' : 'Nuevo Cliente'}</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="modal-body">
          <label className="field">
            <span>{isSupplier ? 'Razón social' : 'Nombre / Razón social'}</span>
            <input value={legalName} onChange={(e) => setLegalName(e.target.value)} required autoFocus />
          </label>
          <label className="field">
            <span>{isSupplier ? 'NIT / RUC' : 'NIT / Documento'}</span>
            <input value={taxId} onChange={(e) => setTaxId(e.target.value)} required />
          </label>
          <div className="field-row">
            <label className="field">
              <span>Contacto (opcional)</span>
              <input value={contact} onChange={(e) => setContact(e.target.value)} />
            </label>
            <label className="field">
              <span>Teléfono (opcional)</span>
              <input value={phone} onChange={(e) => setPhone(e.target.value)} />
            </label>
          </div>
          <label className="field">
            <span>Email (opcional)</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          {error ? <div className="login-error">{error}</div> : null}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creando…' : isSupplier ? 'Crear proveedor' : 'Crear cliente'}
          </button>
        </div>
      </form>
    </div>
  );
}
