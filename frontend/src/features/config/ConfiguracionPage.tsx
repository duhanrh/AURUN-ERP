/**
 * Configuración del tenant (sección 7.17): página `page-configuracion` con sus 4
 * tabs (Apariencia/Marca, Módulos, Parámetros, Usuarios y Roles). La marca, los
 * parámetros y los módulos se persisten en el backend (no en localStorage).
 */

import { useState } from 'react';

import { useAuthStore } from '../auth/authStore';
import { UsersRolesPage } from '../users/UsersRolesPage';
import { ApiKeysTab } from './ApiKeysTab';
import { AppearanceTab } from './AppearanceTab';
import { CompanyTab } from './CompanyTab';
import { CurrenciesTab } from './CurrenciesTab';
import { ModulesTab } from './ModulesTab';
import { ParametersTab } from './ParametersTab';
import { UnitsTab } from './UnitsTab';

type Tab =
  | 'empresa'
  | 'apariencia'
  | 'modulos'
  | 'parametros'
  | 'unidades'
  | 'monedas'
  | 'usuarios'
  | 'apikeys';

export function ConfiguracionPage() {
  const canAccess = useAuthStore((s) => s.hasPermission('configuration:access'));
  const [tab, setTab] = useState<Tab>('empresa');

  if (!canAccess) {
    return (
      <div className="page-placeholder">
        <div className="ph-icon">🔒</div>
        <h2>Sin acceso</h2>
        <p>No tienes el permiso <code>configuration:access</code>.</p>
      </div>
    );
  }

  return (
    <div className="config-section">
      <div className="tab-bar">
        <button className={`tab ${tab === 'empresa' ? 'active' : ''}`} onClick={() => setTab('empresa')}>
          Empresa
        </button>
        <button className={`tab ${tab === 'apariencia' ? 'active' : ''}`} onClick={() => setTab('apariencia')}>
          Apariencia / Marca
        </button>
        <button className={`tab ${tab === 'modulos' ? 'active' : ''}`} onClick={() => setTab('modulos')}>
          Módulos
        </button>
        <button className={`tab ${tab === 'parametros' ? 'active' : ''}`} onClick={() => setTab('parametros')}>
          Parámetros
        </button>
        <button className={`tab ${tab === 'unidades' ? 'active' : ''}`} onClick={() => setTab('unidades')}>
          Unidades
        </button>
        <button className={`tab ${tab === 'monedas' ? 'active' : ''}`} onClick={() => setTab('monedas')}>
          Monedas
        </button>
        <button className={`tab ${tab === 'usuarios' ? 'active' : ''}`} onClick={() => setTab('usuarios')}>
          Usuarios y Roles
        </button>
        <button className={`tab ${tab === 'apikeys' ? 'active' : ''}`} onClick={() => setTab('apikeys')}>
          API Keys
        </button>
      </div>

      {tab === 'empresa' ? <CompanyTab /> : null}
      {tab === 'apariencia' ? <AppearanceTab /> : null}
      {tab === 'modulos' ? <ModulesTab /> : null}
      {tab === 'parametros' ? <ParametersTab /> : null}
      {tab === 'unidades' ? <UnitsTab /> : null}
      {tab === 'monedas' ? <CurrenciesTab /> : null}
      {tab === 'usuarios' ? <UsersRolesPage /> : null}
      {tab === 'apikeys' ? <ApiKeysTab /> : null}
    </div>
  );
}
