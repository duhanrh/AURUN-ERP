/**
 * Tab "Empresa / Comercio" (sección 7.17): datos legales y fiscales del negocio,
 * distintos de la marca visual. Encabezan las facturas y recibos impresos.
 * Escritura gated por `configuration:manage`.
 */

import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import { getCompany, updateCompany } from './config.api';
import type { Company } from './config.types';

const EMPTY: Company = {
  legal_name: '',
  trade_name: '',
  tax_id: '',
  tax_regime: '',
  address: '',
  city: '',
  phone: '',
  email: '',
  website: '',
};

export function CompanyTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const company = useQuery({ queryKey: ['configuration', 'company'], queryFn: getCompany });

  const [form, setForm] = useState<Company>(EMPTY);
  useEffect(() => {
    if (company.data) setForm(company.data);
  }, [company.data]);

  const save = useMutation({
    mutationFn: () => updateCompany(form),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['configuration', 'company'] }),
  });

  const set = (patch: Partial<Company>) => setForm((f) => ({ ...f, ...patch }));
  const field = (key: keyof Company) => ({
    value: form[key],
    disabled: !canManage,
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => set({ [key]: e.target.value }),
  });

  if (company.isLoading) return <div className="config-pane">Cargando datos de la empresa…</div>;

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Datos del comercio</h2>
          <p className="section-subtitle">
            Identidad legal/fiscal del negocio; aparece en la cabecera de facturas y recibos.
          </p>
        </div>
        {!canManage ? <ReadOnlyHint permission="configuration:manage" /> : null}
      </div>

      <div className="field-row">
        <label className="field">
          <span>Razón social</span>
          <input placeholder="Compra de Oro y Platino S.A.S." {...field('legal_name')} />
        </label>
        <label className="field">
          <span>Nombre comercial</span>
          <input placeholder="Joyería El Dorado" {...field('trade_name')} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>NIT / Identificación</span>
          <input placeholder="900123456-7" {...field('tax_id')} />
        </label>
        <label className="field">
          <span>Régimen tributario</span>
          <input placeholder="Responsable de IVA" {...field('tax_regime')} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Dirección</span>
          <input placeholder="Cra 50 # 50-50" {...field('address')} />
        </label>
        <label className="field">
          <span>Ciudad</span>
          <input placeholder="Medellín" {...field('city')} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Teléfono</span>
          <input placeholder="3001234567" {...field('phone')} />
        </label>
        <label className="field">
          <span>Correo</span>
          <input placeholder="contacto@empresa.com" {...field('email')} />
        </label>
      </div>
      <label className="field">
        <span>Sitio web</span>
        <input placeholder="https://empresa.com" {...field('website')} />
      </label>

      {canManage ? (
        <div className="row-actions" style={{ marginTop: '12px' }}>
          <button className="btn btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? 'Guardando…' : 'Guardar datos'}
          </button>
        </div>
      ) : null}
    </div>
  );
}
