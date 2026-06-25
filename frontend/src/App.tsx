/**
 * Raíz de la aplicación: providers (Query + Theme) y enrutador.
 * El enrutador reemplaza la función `navigate()` de la maqueta por rutas reales,
 * preservando el mismo mapa de navegación (sección 3.3).
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import { PlaceholderPage } from './components/PlaceholderPage';
import { AppLayout } from './components/layout/AppLayout';
import { queryClient } from './lib/queryClient';
import { NAV_ITEMS } from './routes/navigation';
import { ThemeProvider } from './theme/ThemeProvider';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Router>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              {NAV_ITEMS.map((item) => (
                <Route key={item.id} path={item.path} element={<PlaceholderPage />} />
              ))}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
