/** Tab "Parámetros" (sección 7.17): parámetros de negocio del tenant. */

import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { getParameters, updateParameters } from './config.api';
import type { BusinessParameters } from './config.types';

const EMPTY: BusinessParameters = {
  base_currency: 'USD',
  weight_unit: 'g',
  min_stock_g: '1000',
  min_margin_pct: '5',
  language: 'es',
  timezone: 'America/Bogota',
  date_format: 'YYYY-MM-DD',
  regulatory_entity: '',
};

export function ParametersTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const params = useQuery({ queryKey: ['configuration', 'parameters'], queryFn: getParameters });
  const [form, setForm] = useState<BusinessParameters>(EMPTY);

  useEffect(() => {
    if (params.data) setForm(params.data);
  }, [params.data]);

  const save = useMutation({
    mutationFn: () => updateParameters(form),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['configuration', 'parameters'] }),
  });

  const set = (patch: Partial<BusinessParameters>) => setForm((f) => ({ ...f, ...patch }));

  if (params.isLoading) return <div className="config-section">Cargando parámetros…</div>;

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Parámetros de negocio</h2>
          <p className="section-subtitle">Alimentan las alertas del Dashboard y las validaciones de venta.</p>
        </div>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Moneda base</span>
          <select value={form.base_currency} disabled={!canManage} onChange={(e) => set({ base_currency: e.target.value })}>
            <option value="USD">USD</option>
            <option value="COP">COP</option>
            <option value="EUR">EUR</option>
          </select>
        </label>
        <label className="field">
          <span>Unidad de peso</span>
          <select value={form.weight_unit} disabled={!canManage} onChange={(e) => set({ weight_unit: e.target.value })}>
            <option value="g">Gramos</option>
            <option value="kg">Kilogramos</option>
            <option value="oz">Onzas</option>
          </select>
        </label>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Stock mínimo (g)</span>
          <input
            type="number"
            min={0}
            step={0.01}
            value={form.min_stock_g}
            disabled={!canManage}
            onChange={(e) => set({ min_stock_g: e.target.value })}
          />
        </label>
        <label className="field">
          <span>Margen mínimo de venta (%)</span>
          <input
            type="number"
            min={0}
            max={100}
            step={0.01}
            value={form.min_margin_pct}
            disabled={!canManage}
            onChange={(e) => set({ min_margin_pct: e.target.value })}
          />
        </label>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Zona horaria</span>
          <input value={form.timezone} disabled={!canManage} onChange={(e) => set({ timezone: e.target.value })} />
        </label>
        <label className="field">
          <span>Formato de fecha</span>
          <select value={form.date_format} disabled={!canManage} onChange={(e) => set({ date_format: e.target.value })}>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
          </select>
        </label>
      </div>

      <label className="field">
        <span>Entidad reguladora</span>
        <input
          value={form.regulatory_entity}
          placeholder="p. ej. ANM"
          disabled={!canManage}
          onChange={(e) => set({ regulatory_entity: e.target.value })}
        />
      </label>

      {canManage ? (
        <div className="row-actions" style={{ marginTop: '16px' }}>
          <button className="btn btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? 'Guardando…' : 'Guardar parámetros'}
          </button>
        </div>
      ) : null}
    </div>
  );
}
