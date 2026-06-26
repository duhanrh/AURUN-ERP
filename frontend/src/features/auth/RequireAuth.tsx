/**
 * Guard de rutas autenticadas. Si no hay token redirige a `/login`. Si hay token
 * pero aún no se ha cargado el `Principal` (p. ej. tras recargar la página),
 * consulta `/auth/me` para rehidratar permisos antes de renderizar.
 */

import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { fetchMe } from './api';
import { useAuthStore } from './authStore';

export function RequireAuth() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const principal = useAuthStore((s) => s.principal);
  const setPrincipal = useAuthStore((s) => s.setPrincipal);
  const clear = useAuthStore((s) => s.clear);

  const [resolving, setResolving] = useState(accessToken !== null && principal === null);

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
  if (resolving) return <div className="route-loading">Cargando sesión…</div>;
  return <Outlet />;
}
