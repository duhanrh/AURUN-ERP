/** Tab "Apariencia / Marca" (sección 5.6 / 7.17). Persiste en `tenant_branding`. */

import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { DEFAULT_BRAND } from '../../theme/tokens';
import { applyBranding } from './applyBranding';
import { getBranding, resetBranding, updateBranding } from './config.api';
import type { Branding, UpdateBrandingInput } from './config.types';

const PRESETS: { key: string; label: string; color: string }[] = [
  { key: 'gold', label: 'Aurum', color: '#C9A84C' },
  { key: 'emerald', label: 'Esmeralda', color: '#3DAA6E' },
  { key: 'platinum', label: 'Platino', color: '#A8B0C0' },
  { key: 'copper', label: 'Cobre', color: '#C77D4A' },
];

export function AppearanceTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const branding = useQuery({ queryKey: ['configuration', 'branding'], queryFn: getBranding });

  const [form, setForm] = useState<UpdateBrandingInput>({});

  useEffect(() => {
    if (branding.data) {
      const b = branding.data;
      setForm({
        brand_name: b.brand_name,
        tagline: b.tagline,
        logo_url: b.logo_url,
        color_primary: b.color_primary ?? DEFAULT_BRAND.gold,
        color_success: b.color_success ?? DEFAULT_BRAND.green,
        color_danger: b.color_danger ?? DEFAULT_BRAND.red,
      });
    }
  }, [branding.data]);

  const onSaved = async (b: Branding) => {
    applyBranding(b);
    await queryClient.invalidateQueries({ queryKey: ['configuration', 'branding'] });
  };

  const saveMutation = useMutation({ mutationFn: () => updateBranding(form), onSuccess: onSaved });
  const resetMutation = useMutation({ mutationFn: resetBranding, onSuccess: onSaved });

  if (branding.isLoading) return <div className="config-section">Cargando marca…</div>;

  const set = (patch: Partial<UpdateBrandingInput>) => setForm((f) => ({ ...f, ...patch }));

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Apariencia y marca</h2>
          <p className="section-subtitle">
            {branding.data?.is_customized ? 'Marca personalizada' : 'Tema Aurum por defecto'}
          </p>
        </div>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Nombre de marca</span>
          <input
            value={form.brand_name ?? ''}
            placeholder="AURUM ERP"
            disabled={!canManage}
            onChange={(e) => set({ brand_name: e.target.value || null })}
          />
        </label>
        <label className="field">
          <span>Eslogan</span>
          <input
            value={form.tagline ?? ''}
            placeholder="Mining Intelligence"
            disabled={!canManage}
            onChange={(e) => set({ tagline: e.target.value || null })}
          />
        </label>
      </div>

      <label className="field">
        <span>URL del logo (opcional)</span>
        <input
          value={form.logo_url ?? ''}
          placeholder="https://…"
          disabled={!canManage}
          onChange={(e) => set({ logo_url: e.target.value || null })}
        />
      </label>

      <div className="color-grid">
        <ColorField label="Primario" value={form.color_primary} disabled={!canManage} onChange={(v) => set({ color_primary: v })} />
        <ColorField label="Éxito" value={form.color_success} disabled={!canManage} onChange={(v) => set({ color_success: v })} />
        <ColorField label="Alerta" value={form.color_danger} disabled={!canManage} onChange={(v) => set({ color_danger: v })} />
      </div>
      <p className="field-hint">
        El fondo claro/oscuro se cambia con el conmutador de tema (☀/🌙) del encabezado.
      </p>

      {canManage ? (
        <div className="preset-row">
          <span className="field-hint">Presets:</span>
          {PRESETS.map((p) => (
            <button
              key={p.key}
              type="button"
              className="preset-swatch"
              style={{ background: p.color }}
              title={p.label}
              onClick={() => set({ color_primary: p.color })}
            />
          ))}
        </div>
      ) : null}

      {canManage ? (
        <div className="row-actions" style={{ marginTop: '16px' }}>
          <button
            className="btn btn-ghost"
            disabled={resetMutation.isPending}
            onClick={() => resetMutation.mutate()}
          >
            Restablecer tema por defecto
          </button>
          <button
            className="btn btn-primary"
            disabled={saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? 'Guardando…' : 'Guardar marca'}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function ColorField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: string | null | undefined;
  disabled: boolean;
  onChange: (v: string) => void;
}) {
  const color = value ?? '#000000';
  return (
    <label className="color-field">
      <span>{label}</span>
      <div className="color-input-row">
        <input type="color" value={color} disabled={disabled} onChange={(e) => onChange(e.target.value)} />
        <input
          className="color-hex"
          value={color}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </label>
  );
}
