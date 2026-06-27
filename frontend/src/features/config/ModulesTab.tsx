/** Tab "Módulos" (sección 7.17): activa/desactiva módulos de negocio del tenant. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '../auth/authStore';
import { listModules, setModule } from './config.api';

export function ModulesTab() {
  const queryClient = useQueryClient();
  const canManage = useAuthStore((s) => s.hasPermission('configuration:manage'));
  const modules = useQuery({ queryKey: ['configuration', 'modules'], queryFn: listModules });

  const toggle = useMutation({
    mutationFn: ({ key, isActive }: { key: string; isActive: boolean }) => setModule(key, isActive),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['configuration', 'modules'] }),
  });

  return (
    <div className="config-pane">
      <div className="section-head">
        <div>
          <h2 className="section-title">Módulos activos</h2>
          <p className="section-subtitle">Activa o desactiva módulos de negocio para el tenant.</p>
        </div>
      </div>

      <div className="module-list">
        {modules.data?.map((m) => (
          <div className="module-row" key={m.key}>
            <div>
              <div className="module-name">{m.label}</div>
              <div className="module-key">{m.key}</div>
            </div>
            <label className="switch">
              <input
                type="checkbox"
                checked={m.is_active}
                disabled={!canManage || toggle.isPending}
                onChange={(e) => toggle.mutate({ key: m.key, isActive: e.target.checked })}
              />
              <span className="switch-slider" />
            </label>
          </div>
        ))}
        {modules.isLoading ? <div className="field-hint">Cargando módulos…</div> : null}
      </div>
    </div>
  );
}
