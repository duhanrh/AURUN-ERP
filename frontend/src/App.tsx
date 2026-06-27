/**
 * Raíz de la aplicación: providers (Query + Theme) y enrutador.
 *
 * Rutas públicas: `/login`. El resto cuelga de `RequireAuth` (sección 10): sin
 * sesión válida se redirige al login. El mapa de navegación (sección 3.3) se
 * conserva; `configuracion` ya monta la pantalla real de Usuarios y Roles (Fase 2),
 * el resto sigue en placeholder hasta su fase.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import { PlaceholderPage } from './components/PlaceholderPage';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './features/auth/LoginPage';
import { RequireAuth } from './features/auth/RequireAuth';
import { ConfiguracionPage } from './features/config/ConfiguracionPage';
import { FinanzasPage } from './features/finanzas/FinanzasPage';
import { InventoryPage } from './features/operacion/InventoryPage';
import { PurchasingPage } from './features/operacion/PurchasingPage';
import { QualityPage } from './features/operacion/QualityPage';
import { SalesPage } from './features/operacion/SalesPage';
import { TransformationPage } from './features/operacion/TransformationPage';
import { PartiesPage } from './features/terceros/PartiesPage';
import { queryClient } from './lib/queryClient';
import { NAV_ITEMS } from './routes/navigation';
import { ThemeProvider } from './theme/ThemeProvider';

/** Resuelve el componente de página real según el id de navegación (sección 3.3). */
function pageFor(id: string) {
  switch (id) {
    case 'configuracion':
      return <ConfiguracionPage />;
    case 'proveedores':
      return <PartiesPage kind="supplier" />;
    case 'clientes':
      return <PartiesPage kind="customer" />;
    case 'inventario':
      return <InventoryPage />;
    case 'compras':
      return <PurchasingPage />;
    case 'ventas':
      return <SalesPage />;
    case 'transformacion':
      return <TransformationPage />;
    case 'calidad':
      return <QualityPage />;
    case 'finanzas':
      return <FinanzasPage />;
    default:
      return <PlaceholderPage />;
  }
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppLayout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                {NAV_ITEMS.map((item) => (
                  <Route key={item.id} path={item.path} element={pageFor(item.id)} />
                ))}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Route>
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
