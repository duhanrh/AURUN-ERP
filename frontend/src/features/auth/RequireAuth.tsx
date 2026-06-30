/**
 * Guard de rutas autenticadas. Si no hay token redirige a `/login`. Si hay token
 * pero aún no se ha cargado el `Principal` (p. ej. tras recargar la página),
 * consulta `/auth/me` para rehidratar permisos antes de renderizar.
 */

import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { SplashScreen } from '../../components/SplashScreen';
import { fetchMe } from './api';
import { useAuthStore } from './authStore';

/** Tiempo mínimo que se muestra el splash al entrar (para que se alcance a ver). */
const MIN_SPLASH_MS = 3000;

export function RequireAuth() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const principal = useAuthStore((s) => s.principal);
  const setPrincipal = useAuthStore((s) => s.setPrincipal);
  const clear = useAuthStore((s) => s.clear);

  const [resolving, setResolving] = useState(accessToken !== null && principal === null);
  // Garantiza un mínimo de splash aunque la sesión resuelva al instante.
  const [minElapsed, setMinElapsed] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMinElapsed(true), MIN_SPLASH_MS);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    let active = true;
    if (accessToken && !principal) {
      fetchMe()
        .then((p) => active && setPrincipal(p))
        .catch(() => active && clear())
        .finally(() => active && setResolving(false));
    } else {
      setResolving(false);
    }
    return () => {
      active = false;
    };
  }, [accessToken, principal, setPrincipal, clear]);

  if (!accessToken) return <Navigate to="/login" replace />;
  if (resolving || !minElapsed) return <SplashScreen />;
  return <Outlet />;
}
