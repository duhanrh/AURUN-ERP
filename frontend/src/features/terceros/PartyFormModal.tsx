/**
 * Modal "Nuevo Cliente / Nuevo Proveedor" (réplica de `modal-cliente` /
 * `modal-proveedor`, secciones 7.5/7.6). Un único componente parametrizado por
 * `kind` muestra los campos comunes y los específicos del tipo.
 */

import { useState, type FormEvent } from 'react';

import { ApiError } from '../auth/api';
import type { CreatePartyInput, Party, PartyKind, PartyStatus } from './types';

const CUSTOMER_SEGMENTS = [
  'Joyería / Retail',
  'Institución Financiera',
  'Exportador',
  'Industria',
  'Particular',
];

const STATUS_OPTIONS: { value: PartyStatus; label: string }[] = [
  { value: 'active', label: 'Activo' },
  { value: 'evaluation', label: 'En evaluación' },
  { value: 'inactive', label: 'Inactivo' },
];

interface PartyFormModalProps {
  kind: PartyKind;
  submitting: boolean;
  initial?: Party | null;
  onSubmit: (input: CreatePartyInput) => Promise<void>;
  onClose: () => void;
}

export function PartyFormModal({ kind, submitting, initial, onSubmit, onClose }: PartyFormModalProps) {
  const isSupplier = kind === 'supplier';
  const isEdit = Boolean(initial);
  const [form, setForm] = useState({
    legal_name: initial?.legal_name ?? '',
    tax_id: initial?.tax_id ?? '',
    status: (initial?.status ?? 'active') as PartyStatus,
    country: initial?.country ?? '',
    city: initial?.city ?? '',
    contact_name: initial?.contact_name ?? '',
    phone: initial?.phone ?? '',
    email: initial?.email ?? '',
    main_material: initial?.main_material ?? '',
    certifications: initial?.certifications ?? '',
    rating: initial?.rating != null ? String(initial.rating) : '',
    segment: initial?.segment ?? CUSTOMER_SEGMENTS[0],
    preferred_material: initial?.preferred_material ?? '',
    credit_limit: initial?.credit_limit != null ? String(initial.credit_limit) : '',
  });
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function clean(value: string): string | null {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const base: CreatePartyInput = {
      legal_name: form.legal_name.trim(),
      tax_id: form.tax_id.trim(),
      status: form.status,
      country: clean(form.country),
      city: clean(form.city),
      contact_name: clean(form.contact_name),
      phone: clean(form.phone),
      email: clean(form.email),
    };
    const input: CreatePartyInput = isSupplier
      ? {
          ...base,
          main_material: clean(form.main_material),
          certifications: clean(form.certifications),
          rating: form.rating ? Number(form.rating) : null,
        }
      : {
          ...base,
          segment: form.segment,
          preferred_material: clean(form.preferred_material),
          credit_limit: form.credit_limit ? Number(form.credit_limit) : null,
        };
    try {
      await onSubmit(input);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'No se pudo guardar el tercero.');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>
            {isEdit
              ? isSupplier
                ? 'Editar Proveedor'
                : 'Editar Cliente'
              : isSupplier
                ? 'Nuevo Proveedor'
                : 'Nuevo Cliente'}
          </h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>

        <div className="modal-body">
          <label className="field">
            <span>{isSupplier ? 'Razón social' : 'Nombre / Razón social'}</span>
            <input
              value={form.legal_name}
              onChange={(e) => set('legal_name', e.target.value)}
              required
            />
          </label>

          <div className="field-row">
            <label className="field">
              <span>{isSupplier ? 'NIT / RUC' : 'NIT / Documento'}</span>
              <input value={form.tax_id} onChange={(e) => set('tax_id', e.target.value)} required />
            </label>
            <label className="field">
              <span>Estado</span>
              <select
                value={form.status}
                onChange={(e) => set('status', e.target.value as PartyStatus)}
              >
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="field-row">
            <label className="field">
              <span>{isSupplier ? 'País / Región' : 'Ciudad'}</span>
              <input
                value={isSupplier ? form.country : form.city}
                onChange={(e) => set(isSupplier ? 'country' : 'city', e.target.value)}
              />
            </label>
            {isSupplier ? (
              <label className="field">
                <span>Material principal</span>
                <input
                  value={form.main_material}
                  onChange={(e) => set('main_material', e.target.value)}
                />
              </label>
            ) : (
              <label className="field">
                <span>Segmento</span>
                <select value={form.segment} onChange={(e) => set('segment', e.target.value)}>
                  {CUSTOMER_SEGMENTS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          <div className="field-row">
            <label className="field">
              <span>Contacto</span>
              <input
                value={form.contact_name}
                onChange={(e) => set('contact_name', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Teléfono</span>
              <input value={form.phone} onChange={(e) => set('phone', e.target.value)} />
            </label>
          </div>

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              placeholder="contacto@empresa.com"
            />
          </label>

          {isSupplier ? (
            <div className="field-row">
              <label className="field">
                <span>Certificaciones</span>
                <input
                  value={form.certifications}
                  onChange={(e) => set('certifications', e.target.value)}
                  placeholder="RUC, RUCOM, ISO 9001"
                />
              </label>
              <label className="field">
                <span>Rating (0–5)</span>
                <input
                  type="number"
                  min={0}
                  max={5}
                  step={0.1}
                  value={form.rating}
                  onChange={(e) => set('rating', e.target.value)}
                />
              </label>
            </div>
          ) : (
            <div className="field-row">
              <label className="field">
                <span>Material preferente</span>
                <input
                  value={form.preferred_material}
                  onChange={(e) => set('preferred_material', e.target.value)}
                />
              </label>
              <label className="field">
                <span>Línea de crédito (USD)</span>
                <input
                  type="number"
                  min={0}
                  step={100}
                  value={form.credit_limit}
                  onChange={(e) => set('credit_limit', e.target.value)}
                  placeholder="Sin línea"
                />
              </label>
            </div>
          )}

          {error ? <div className="login-error">{error}</div> : null}
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting
              ? 'Guardando…'
              : isEdit
                ? 'Guardar cambios'
                : isSupplier
                  ? 'Crear proveedor'
                  : 'Crear cliente'}
          </button>
        </div>
      </form>
    </div>
  );
}
