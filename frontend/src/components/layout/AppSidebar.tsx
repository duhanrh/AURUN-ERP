/** Barra lateral de navegación — réplica de `.sidebar` de la maqueta. */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { NavLink, useNavigate } from 'react-router-dom';

import { logout } from '../../features/auth/api';
import { useAuthStore } from '../../features/auth/authStore';
import { listModules } from '../../features/config/config.api';
import { useBrandingStore } from '../../theme/brandingStore';
import { NAV_SECTIONS } from '../../routes/navigation';
import { useUiStore } from './uiStore';

const ROLE_LABELS: Record<string, string> = {
  superusuario: 'Superusuario',
  gerente: 'Gerente',
  operativo: 'Operativo',
  finanzas: 'Finanzas',
  laboratorio: 'Laboratorio',
  solo_lectura: 'Solo lectura',
};

function initials(value: string): string {
  const parts = value.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? '').join('') || 'U';
}

export function AppSidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const identity = useBrandingStore((s) => s.identity);
  const navigate = useNavigate();

  const principal = useAuthStore((s) => s.principal);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const clear = useAuthStore((s) => s.clear);

  // Módulos activos del tenant: se ocultan del menú los desactivados (sección 7.17).
  // Los ítems no "toggleables" (Dashboard, Configuración, Auditoría) no aparecen en
  // la lista de módulos, así que siempre se muestran.
  const modulesQuery = useQuery({
    queryKey: ['configuration', 'modules'],
    queryFn: listModules,
    enabled: Boolean(principal),
  });
  const inactiveModules = useMemo(
    () => new Set((modulesQuery.data ?? []).filter((m) => !m.is_active).map((m) => m.key)),
    [modulesQuery.data],
  );
  const visibleSections = useMemo(
    () =>
      NAV_SECTIONS.map((section) => ({
        ...section,
        items: section.items.filter((item) => !inactiveModules.has(item.id)),
      })).filter((section) => section.items.length > 0),
    [inactiveModules],
  );

  async function handleLogout() {
    try {
      if (refreshToken) await logout(refreshToken);
    } finally {
      clear();
      navigate('/login', { replace: true });
    }
  }

  const displayName = principal?.user_id ? `Usuario ${principal.user_id.slice(0, 8)}` : 'Sin sesión';
  const roleLabel = principal?.role ? ROLE_LABELS[principal.role] ?? principal.role : '—';

  return (
    <nav className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      <div className="logo-area">
        <div className="logo-icon">
          {identity.logoUrl ? <img src={identity.logoUrl} alt={identity.name} /> : identity.symbol}
        </div>
        <div className="logo-text">
          <h1>{identity.name}</h1>
          <span>{identity.tagline}</span>
        </div>
      </div>

      <div className="nav-section">
        {visibleSections.map((section) => (
          <div key={section.label}>
            <div className="nav-label">{section.label}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-text">{item.label}</span>
                {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
              </NavLink>
            ))}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-avatar">{initials(displayName)}</div>
        <div className="user-info">
          <div className="name">{displayName}</div>
          <div className="role">{roleLabel}</div>
        </div>
        <button className="collapse-btn" onClick={handleLogout} aria-label="Cerrar sesión" title="Cerrar sesión">
          ⎋
        </button>
        <button className="collapse-btn" onClick={toggleSidebar} aria-label="Colapsar menú">
          {collapsed ? '⟩' : '⟨'}
        </button>
      </div>
    </nav>
  );
}
