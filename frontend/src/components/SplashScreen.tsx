/**
 * Pantalla de carga (splash) elegante y con marca. Reemplaza el texto plano
 * "Cargando sesión…". Usa la identidad del tenant (emblema/logo, nombre, eslogan)
 * del `brandingStore`, así respeta la personalización. Animación sutil: un anillo
 * dorado girando alrededor del emblema y una barra de progreso indeterminada.
 */

import { useBrandingStore } from '../theme/brandingStore';

interface SplashScreenProps {
  /** Texto bajo el eslogan (p. ej. "Preparando tu sesión…"). */
  message?: string;
}

export function SplashScreen({ message = 'Preparando tu sesión…' }: SplashScreenProps) {
  const identity = useBrandingStore((s) => s.identity);

  return (
    <div className="splash" role="status" aria-live="polite">
      <div className="splash-emblem">
        <span className="splash-ring" aria-hidden />
        {identity.logoUrl ? (
          <img className="splash-logo" src={identity.logoUrl} alt={identity.name} />
        ) : (
          <span className="splash-symbol" aria-hidden>
            {identity.symbol}
          </span>
        )}
      </div>

      <div className="splash-brand">{identity.name}</div>
      <div className="splash-tagline">{identity.tagline}</div>

      <div className="splash-progress" aria-hidden>
        <span className="splash-progress-bar" />
      </div>
      <div className="splash-message">{message}</div>
    </div>
  );
}
