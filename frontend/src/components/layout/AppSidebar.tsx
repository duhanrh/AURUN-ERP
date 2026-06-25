/** Barra lateral de navegación — réplica de `.sidebar` de la maqueta. */

import { NavLink } from 'react-router-dom';

import { useBrandingStore } from '../../theme/brandingStore';
import { NAV_SECTIONS } from '../../routes/navigation';
import { useUiStore } from './uiStore';

export function AppSidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const identity = useBrandingStore((s) => s.identity);

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
        {NAV_SECTIONS.map((section) => (
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
        <div className="user-avatar">AM</div>
        <div className="user-info">
          <div className="name">Admin Minero</div>
          <div className="role">Superusuario</div>
        </div>
        <button className="collapse-btn" onClick={toggleSidebar} aria-label="Colapsar menú">
          {collapsed ? '⟩' : '⟨'}
        </button>
      </div>
    </nav>
  );
}
