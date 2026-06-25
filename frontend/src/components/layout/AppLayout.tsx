/**
 * Layout principal de la aplicación: sidebar + topbar + área de contenido.
 * Replica la estructura `.sidebar` + `.main` > `.topbar` + `.content` de la maqueta.
 */

import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';

import { NAV_ITEMS } from '../../routes/navigation';
import { AppSidebar } from './AppSidebar';
import { AppTopbar } from './AppTopbar';
import { useUiStore } from './uiStore';

export function AppLayout() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const location = useLocation();

  const current =
    NAV_ITEMS.find((item) => location.pathname.startsWith(item.path)) ?? NAV_ITEMS[0];

  useEffect(() => {
    document.title = `${current.title} · Aurum ERP`;
  }, [current.title]);

  return (
    <>
      <AppSidebar />
      <div className={`main${collapsed ? ' shifted' : ''}`}>
        <AppTopbar title={current.title} subtitle={current.subtitle} />
        <div className="content">
          <Outlet />
        </div>
      </div>
    </>
  );
}
