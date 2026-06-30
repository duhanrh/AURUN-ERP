/**
 * Tab "Unidades de medida" (sección 7.17): gestiona las unidades configurables del
 * tenant (gramo base + tradicionales castellano/tomín/grano…) e incluye un
 * **conversor** que usa los factores del propio tenant (gramos como puente).
 *
 * Escrituras gated por `configuration:manage`; lectura por `configuration:access`.
 */

import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import {
  convertUnits,
  createUnit,
  deleteUnit,
  listUnits,
  restoreUnit,
  updateUnit,
} from './config.api';
import type { ConversionResult, UnitOfMeasure } from './config.types';

const UNITS_KEY = ['configuration', 'units'] as const;

export function UnitsTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const [showDeleted, setShowDeleted] = useState(false);

  const units = useQuery({
    queryKey: [...UNITS_KEY, showDeleted],
    queryFn: () => listUnits(showDeleted),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: UNITS_KEY });

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Unidades de medida</h2>
          <p className="section-subtitle">
            Unidades de peso configurables (factor a gramos editable). El gramo es la base.
          </p>
        </div>
        {!canManage ? <ReadOnlyHint permission="configuration:manage" /> : null}
      </div>

      <UnitConverter units={units.data ?? []} />

      <label className="toggle-deleted" style={{ marginTop: '8px' }}>
        <input
          type="checkbox"
          checked={showDeleted}
          onChange={(e) => setShowDeleted(e.target.checked)}
        />
        Mostrar eliminadas
      </label>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Unidad</th>
              <th>Símbolo</th>
              <th className="num">Factor (g)</th>
              <th>Estado</th>
              {canManage ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {units.data?.map((u) => (
              <UnitRow key={u.id} unit={u} canManage={canManage} onChanged={invalidate} />
            ))}
            {units.data && units.data.length === 0 ? (
              <tr>
                <td className="empty-row" colSpan={5}>
                  No hay unidades.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {canManage ? <AddUnitForm onCreated={invalidate} /> : null}
    </div>
  );
}

function UnitRow({
  unit,
  canManage,
  onChanged,
}: {
  unit: UnitOfMeasure;
  canManage: boolean;
  onChanged: () => void;
}) {
  const [factor, setFactor] = useState(unit.grams_factor);
  const dirty = factor.trim() !== unit.grams_factor && factor.trim() !== '';

  const save = useMutation({
    mutationFn: () => updateUnit(unit.id, { grams_factor: factor.trim() }),
    onSuccess: onChanged,
  });
  const remove = useMutation({ mutationFn: () => deleteUnit(unit.id), onSuccess: onChanged });
  const restore = useMutation({ mutationFn: () => restoreUnit(unit.id), onSuccess: onChanged });

  return (
    <tr className={unit.is_deleted ? 'row-deleted' : ''}>
      <td className="primary">
        {unit.name}
        {unit.is_base ? <span className="badge badge-gold" style={{ marginLeft: 8 }}>base</span> : null}
      </td>
      <td>{unit.symbol}</td>
      <td className="num">
        {canManage && !unit.is_base && !unit.is_deleted ? (
          <input
            className="inline-num"
            value={factor}
            inputMode="decimal"
            onChange={(e) => setFactor(e.target.value)}
          />
        ) : (
          unit.grams_factor
        )}
      </td>
      <td>
        <span className={`badge ${unit.is_active ? 'badge-green' : 'badge-gray'}`}>
          {unit.is_active ? 'Activa' : 'Inactiva'}
        </span>
      </td>
      {canManage ? (
        <td className="row-actions">
          {dirty && !unit.is_base && !unit.is_deleted ? (
            <button className="btn btn-sm btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
              Guardar
            </button>
          ) : null}
          {!unit.is_base && !unit.is_deleted ? (
            <button className="btn btn-sm btn-ghost" disabled={remove.isPending} onClick={() => remove.mutate()}>
              Eliminar
            </button>
          ) : null}
          {unit.is_deleted ? (
            <button className="btn btn-sm btn-ghost" disabled={restore.isPending} onClick={() => restore.mutate()}>
              Restaurar
            </button>
          ) : null}
        </td>
      ) : null}
    </tr>
  );
}

function AddUnitForm({ onCreated }: { onCreated: () => void }) {
  const [form, setForm] = useState({ code: '', name: '', symbol: '', grams_factor: '' });
  const create = useMutation({
    mutationFn: () => createUnit(form),
    onSuccess: () => {
      setForm({ code: '', name: '', symbol: '', grams_factor: '' });
      onCreated();
    },
  });
  const valid =
    form.code.trim() && form.name.trim() && form.symbol.trim() && Number(form.grams_factor) > 0;

  return (
    <div className="apikey-create" style={{ marginTop: '16px' }}>
      <div className="field-row">
        <label className="field">
          <span>Código</span>
          <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
        </label>
        <label className="field">
          <span>Nombre</span>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Símbolo</span>
          <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} />
        </label>
        <label className="field">
          <span>Factor a gramos</span>
          <input
            value={form.grams_factor}
            inputMode="decimal"
            placeholder="p. ej. 4.6"
            onChange={(e) => setForm({ ...form, grams_factor: e.target.value })}
          />
        </label>
      </div>
      {create.isError ? <p className="login-error">No se pudo crear la unidad.</p> : null}
      <div className="row-actions">
        <button className="btn btn-primary" disabled={!valid || create.isPending} onClick={() => create.mutate()}>
          {create.isPending ? 'Creando…' : 'Añadir unidad'}
        </button>
      </div>
    </div>
  );
}

function UnitConverter({ units }: { units: UnitOfMeasure[] }) {
  const active = useMemo(() => units.filter((u) => u.is_active && !u.is_deleted), [units]);
  const [quantity, setQuantity] = useState('1');
  const [from, setFrom] = useState('castellano');
  const [to, setTo] = useState('gramo');
  const [result, setResult] = useState<ConversionResult | null>(null);

  const convert = useMutation({
    mutationFn: () => convertUnits(quantity || '0', from, to),
    onSuccess: (r) => setResult(r),
  });

  const fromSymbol = active.find((u) => u.code === from)?.symbol ?? '';
  const toSymbol = active.find((u) => u.code === to)?.symbol ?? '';

  return (
    <div className="apikey-create">
      <div className="drawer-section-title">Conversor de unidades</div>
      <div className="converter-row">
        <label className="field">
          <span>Cantidad</span>
          <input value={quantity} inputMode="decimal" onChange={(e) => setQuantity(e.target.value)} />
        </label>
        <label className="field">
          <span>De</span>
          <select value={from} onChange={(e) => setFrom(e.target.value)}>
            {active.map((u) => (
              <option key={u.id} value={u.code}>
                {u.name} ({u.symbol})
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>A</span>
          <select value={to} onChange={(e) => setTo(e.target.value)}>
            {active.map((u) => (
              <option key={u.id} value={u.code}>
                {u.name} ({u.symbol})
              </option>
            ))}
          </select>
        </label>
        <button className="btn btn-primary" disabled={convert.isPending} onClick={() => convert.mutate()}>
          Convertir
        </button>
      </div>
      {result ? (
        <p className="converter-result">
          {result.quantity} {fromSymbol} = <strong>{result.result}</strong> {toSymbol}
          <span className="field-hint"> ({result.grams} g)</span>
        </p>
      ) : null}
    </div>
  );
}
