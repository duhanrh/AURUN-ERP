/**
 * Modo de tema (claro / oscuro) — independiente del branding del tenant.
 *
 * El branding personaliza el ACENTO (dorado/éxito/alerta); este store controla
 * el MODO (superficies y texto), aplicándolo como atributo `data-theme` en el
 * elemento raíz. Un único set de variables CSS (ver `theme.css`) se conmuta con
 * ese atributo. Arranca en **claro** y recuerda la elección en `localStorage`.
 *
 * El valor inicial se lee del atributo que el script inline de `index.html` ya
 * fijó antes de pintar (evita el parpadeo), por lo que el estado de React y el
 * DOM siempre coinciden.
 */

import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';

const STORAGE_KEY = 'aurum-theme';

function readInitialMode(): ThemeMode {
  if (typeof document !== 'undefined') {
    const attr = document.documentElement.dataset.theme;
    if (attr === 'light' || attr === 'dark') return attr;
  }
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {
    /* localStorage no disponible (modo privado): se ignora */
  }
  return 'light';
}

function persist(mode: ThemeMode): void {
  document.documentElement.dataset.theme = mode;
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    /* sin persistencia: el tema sigue funcionando en memoria */
  }
}

interface ThemeModeState {
  mode: ThemeMode;
  toggle: () => void;
  setMode: (mode: ThemeMode) => void;
}

export const useThemeMode = create<ThemeModeState>((set, get) => ({
  mode: readInitialMode(),
  toggle: () => {
    const next: ThemeMode = get().mode === 'dark' ? 'light' : 'dark';
    persist(next);
    set({ mode: next });
  },
  setMode: (mode) => {
    persist(mode);
    set({ mode });
  },
}));
