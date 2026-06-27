/** Tab "API Keys" (sección 7.19): gestiona claves de la API pública por tenant. */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { availableScopes, createApiKey, listApiKeys, revokeApiKey } from './config.api';
import type { CreatedApiKey } from './config.types';

export function ApiKeysTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const keys = useQuery({ queryKey: ['configuration', 'api-keys'], queryFn: listApiKeys });
  const scopes = useQuery({ queryKey: ['configuration', 'scopes'], queryFn: availableScopes });

  const [name, setName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['configuration', 'api-keys'] });

  const createMutation = useMutation({
    mutationFn: () => createApiKey(name, selectedScopes),
    onSuccess: async (data) => {
      setCreated(data);
      setName('');
      setSelectedScopes([]);
      await invalidate();
    },
  });
  const revokeMutation = useMutation({ mutationFn: (id: string) => revokeApiKey(id), onSuccess: invalidate });

  const toggleScope = (scope: string) =>
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">API Keys</h2>
          <p className="section-subtitle">Claves de la API pública con scopes de solo lectura.</p>
        </div>
      </div>

      {created ? (
        <div className="apikey-reveal">
          <div className="apikey-reveal-label">
            Copia esta clave ahora: no se volverá a mostrar.
          </div>
          <code className="apikey-value">{created.full_key}</code>
          <button className="btn btn-sm btn-ghost" onClick={() => setCreated(null)}>
            Entendido
          </button>
        </div>
      ) : null}

      {canManage ? (
        <div className="apikey-create">
          <label className="field">
            <span>Nombre de la clave</span>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Integración BI" />
          </label>
          <div className="apikey-scopes">
            <span className="field-hint">Scopes:</span>
            {scopes.data?.scopes.map((scope) => (
              <label className="apikey-scope" key={scope}>
                <input
                  type="checkbox"
                  checked={selectedScopes.includes(scope)}
                  onChange={() => toggleScope(scope)}
                />
                <code>{scope}</code>
              </label>
            ))}
          </div>
          <button
            className="btn btn-primary"
            disabled={!name || selectedScopes.length === 0 || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            {createMutation.isPending ? 'Creando…' : 'Crear API Key'}
          </button>
        </div>
      ) : null}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Prefijo</th>
              <th>Scopes</th>
              <th>Estado</th>
              <th>Último uso</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {keys.data?.map((k) => (
              <tr key={k.id}>
                <td className="primary">{k.name}</td>
                <td className="audit-mono">{k.prefix}</td>
                <td>{k.scopes.join(', ')}</td>
                <td>
                  <span className={`badge ${k.is_active ? 'badge-green' : 'badge-gray'}`}>
                    {k.is_active ? 'Activa' : 'Revocada'}
                  </span>
                </td>
                <td className="audit-mono">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleString('es-CO') : '—'}
                </td>
                <td>
                  {canManage && k.is_active ? (
                    <button
                      className="btn btn-sm btn-ghost"
                      disabled={revokeMutation.isPending}
                      onClick={() => revokeMutation.mutate(k.id)}
                    >
                      Revocar
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
            {keys.data?.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-row">Aún no hay API Keys.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
