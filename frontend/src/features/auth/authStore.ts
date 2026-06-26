/**
 * Store de sesión (Zustand) con persistencia en localStorage.
 *
 * Guarda los tokens, el tenant activo (necesario como cabecera `X-Tenant-ID` en
 * login/refresh hasta que exista resolución por subdominio) y el `Principal`
 * derivado del access token. Las pantallas leen `permissions` de aquí para ocultar
 * acciones (la autorización real la impone el backend, sección 10.2).
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { Principal, TokenPair } from './types';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  principal: Principal | null;
  setTenantId: (tenantId: string) => void;
  setTokens: (tokens: TokenPair) => void;
  setPrincipal: (principal: Principal | null) => void;
  clear: () => void;
  hasPermission: (code: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      tenantId: null,
      principal: null,
      setTenantId: (tenantId) => set({ tenantId }),
      setTokens: (tokens) =>
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),
      setPrincipal: (principal) => set({ principal }),
      clear: () => set({ accessToken: null, refreshToken: null, principal: null }),
      hasPermission: (code) => get().principal?.permissions.includes(code) ?? false,
    }),
    {
      name: 'aurum.auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        tenantId: state.tenantId,
      }),
    },
  ),
);
