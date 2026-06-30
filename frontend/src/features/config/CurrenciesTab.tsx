/**
 * Tab "Monedas" (sección 7.17): monedas configurables del tenant con su moneda
 * base (sincronizada con el parámetro `base_currency`). CRUD con baja lógica.
 * Escritura gated por `configuration:manage`.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { ReadOnlyHint } from '../../components/ReadOnlyHint';
import {
  createCurrency,
  deleteCurrency,
  listCurrencies,
  restoreCurrency,
  setBaseCurrency,
} from './config.api';
import type { Currency } from './config.types';

const KEY = ['configuration', 'currencies'] as const;

export function CurrenciesTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const [showDeleted, setShowDeleted] = useState(false);
  const currencies = useQuery({
    queryKey: [...KEY, showDeleted],
    queryFn: () => listCurrencies(showDeleted),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: KEY });
    queryClient.invalidateQueries({ queryKey: ['configuration', 'parameters'] });
  };

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Monedas</h2>
          <p className="section-subtitle">
            Monedas del negocio. La marcada como base se usa en valorización y documentos.
          </p>
        </div>
        {!canManage ? <ReadOnlyHint permission="configuration:manage" /> : null}
      </div>

      <label className="toggle-deleted">
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
              <th>Código</th>
              <th>Nombre</th>
              <th>Símbolo</th>
              <th className="num">Decimales</th>
              <th>Base</th>
              {canManage ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {currencies.data?.map((c) => (
              <CurrencyRow key={c.id} currency={c} canManage={canManage} onChanged={invalidate} />
            ))}
            {currencies.data && currencies.data.length === 0 ? (
              <tr>
                <td className="empty-row" colSpan={6}>
                  No hay monedas.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {canManage ? <AddCurrencyForm onCreated={invalidate} /> : null}
    </div>
  );
}

function CurrencyRow({
  currency,
  canManage,
  onChanged,
}: {
  currency: Currency;
  canManage: boolean;
  onChanged: () => void;
}) {
  const setBase = useMutation({ mutationFn: () => setBaseCurrency(currency.id), onSuccess: onChanged });
  const remove = useMutation({ mutationFn: () => deleteCurrency(currency.id), onSuccess: onChanged });
  const restore = useMutation({ mutationFn: () => restoreCurrency(currency.id), onSuccess: onChanged });

  return (
    <tr className={currency.is_deleted ? 'row-deleted' : ''}>
      <td className="primary">{currency.code}</td>
      <td>{currency.name}</td>
      <td>{currency.symbol}</td>
      <td className="num">{currency.decimals}</td>
      <td>
        {currency.is_base ? (
          <span className="badge badge-gold">Base</span>
        ) : (
          <span className="badge badge-gray">—</span>
        )}
      </td>
      {canManage ? (
        <td className="row-actions">
          {!currency.is_base && !currency.is_deleted ? (
            <button className="btn btn-sm btn-ghost" disabled={setBase.isPending} onClick={() => setBase.mutate()}>
              Hacer base
            </button>
          ) : null}
          {!currency.is_base && !currency.is_deleted ? (
            <button className="btn btn-sm btn-ghost" disabled={remove.isPending} onClick={() => remove.mutate()}>
              Eliminar
            </button>
          ) : null}
          {currency.is_deleted ? (
            <button className="btn btn-sm btn-ghost" disabled={restore.isPending} onClick={() => restore.mutate()}>
              Restaurar
            </button>
          ) : null}
        </td>
      ) : null}
    </tr>
  );
}

function AddCurrencyForm({ onCreated }: { onCreated: () => void }) {
  const [form, setForm] = useState({ code: '', name: '', symbol: '', decimals: '2' });
  const create = useMutation({
    mutationFn: () =>
      createCurrency({
        code: form.code,
        name: form.name,
        symbol: form.symbol,
        decimals: Number(form.decimals),
      }),
    onSuccess: () => {
      setForm({ code: '', name: '', symbol: '', decimals: '2' });
      onCreated();
    },
  });
  const valid = form.code.trim() && form.name.trim() && form.symbol.trim();

  return (
    <div className="apikey-create" style={{ marginTop: '16px' }}>
      <div className="field-row">
        <label className="field">
          <span>Código (ISO)</span>
          <input placeholder="COP" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
        </label>
        <label className="field">
          <span>Nombre</span>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
      </div>
      <div className="field-row">
        <label className="field">
          <span>Símbolo</span>
          <input placeholder="$" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} />
        </label>
        <label className="field">
          <span>Decimales</span>
          <input
            inputMode="numeric"
            value={form.decimals}
            onChange={(e) => setForm({ ...form, decimals: e.target.value })}
          />
        </label>
      </div>
      {create.isError ? <p className="login-error">No se pudo crear la moneda.</p> : null}
      <div className="row-actions">
        <button className="btn btn-primary" disabled={!valid || create.isPending} onClick={() => create.mutate()}>
          {create.isPending ? 'Creando…' : 'Añadir moneda'}
        </button>
      </div>
    </div>
  );
}
