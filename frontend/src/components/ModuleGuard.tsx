/**
 * Guard de ruta por módulo activo (sección 7.17). Si el tenant tiene el módulo
 * desactivado, redirige al dashboard aunque se entre por URL directa (coherente con
 * el sidebar, que lo oculta). Mientras no se conoce el estado, deja pasar (no
 * redirige en falso); los módulos no "toggleables" nunca están en la lista → pasan.
 */

import type { ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';

import { listModules } from '../features/config/config.api';

export function ModuleGuard({ moduleKey, children }: { moduleKey: string; children: ReactNode }) {
  const { data } = useQuery({ queryKey: ['configuration', 'modules'], queryFn: listModules });
  const inactive = (data ?? []).some((m) => m.key === moduleKey && !m.is_active);
  if (inactive) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
