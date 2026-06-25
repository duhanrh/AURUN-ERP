/**
 * Página de marcador de posición para los módulos aún no implementados (Fase 1).
 * Cada módulo reemplazará esto por su pantalla real en la fase correspondiente
 * (sección 6), reutilizando los componentes del Design System (Anexo 13.2).
 */

import { useLocation } from 'react-router-dom';

import { NAV_ITEMS } from '../routes/navigation';

export function PlaceholderPage() {
  const location = useLocation();
  const item = NAV_ITEMS.find((i) => location.pathname.startsWith(i.path)) ?? NAV_ITEMS[0];

  return (
    <div className="page-placeholder">
      <div className="ph-icon">{item.icon}</div>
      <h2>{item.title}</h2>
      <p>
        Módulo en construcción. La pantalla de <strong>{item.label}</strong> se implementará
        en su fase correspondiente, fiel a la maqueta y reutilizando los componentes del
        Design System de Aurum.
      </p>
    </div>
  );
}
