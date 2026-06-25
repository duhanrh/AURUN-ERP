/** Barra superior — réplica de `.topbar` de la maqueta. */

import { PriceTicker } from './PriceTicker';

interface AppTopbarProps {
  title: string;
  subtitle: string;
}

export function AppTopbar({ title, subtitle }: AppTopbarProps) {
  return (
    <div className="topbar">
      <div>
        <span className="topbar-title">{title}</span>
        <span className="topbar-subtitle">{subtitle}</span>
      </div>
      <PriceTicker />
      <div className="topbar-actions">
        <div className="icon-btn" title="Nueva Transacción">
          +
        </div>
        <div className="icon-btn" title="Notificaciones">
          🔔
        </div>
        <div className="icon-btn" title="Configuración rápida">
          ⚙
        </div>
      </div>
    </div>
  );
}
