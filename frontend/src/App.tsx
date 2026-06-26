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
import { UsersRolesPage } from './features/users/UsersRolesPage';
import { queryClient } from './lib/queryClient';
import { NAV_ITEMS } from './routes/navigation';
import { ThemeProvider } from './theme/ThemeProvider';

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
                  <Route
                    key={item.id}
                    path={item.path}
                    element={
                      item.id === 'configuracion' ? <UsersRolesPage /> : <PlaceholderPage />
                    }
                  />
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
