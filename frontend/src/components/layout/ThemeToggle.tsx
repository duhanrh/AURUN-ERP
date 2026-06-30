/** Conmutador de tema claro/oscuro para el topbar. */

import { useThemeMode } from '../../theme/themeMode';

export function ThemeToggle() {
  const mode = useThemeMode((s) => s.mode);
  const toggle = useThemeMode((s) => s.toggle);
  const isDark = mode === 'dark';

  return (
    <button
      type="button"
      className="icon-btn"
      onClick={toggle}
      aria-label={isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
      title={isDark ? 'Tema claro' : 'Tema oscuro'}
    >
      {isDark ? '☀' : '🌙'}
    </button>
  );
}
