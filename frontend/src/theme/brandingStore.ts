/**
 * Store de branding del tenant activo (Zustand).
 *
 * En la maqueta esto vivía en `localStorage`; en producción la fuente de verdad
 * será el endpoint `GET /api/v1/tenants/me/branding` (sección 5.6). Por ahora
 * arranca con el tema "Aurum" por defecto. El ThemeProvider observa este store
 * y aplica los tokens como CSS Custom Properties.
 */

import { create } from 'zustand';

import {
  DEFAULT_BRAND,
  DEFAULT_IDENTITY,
  type BrandIdentity,
  type BrandTokens,
} from './tokens';

interface BrandingState {
  tokens: BrandTokens;
  identity: BrandIdentity;
  /** true cuando el tenant ha personalizado su marca (is_customized). */
  isCustomized: boolean;
  setBranding: (data: { tokens?: Partial<BrandTokens>; identity?: Partial<BrandIdentity> }) => void;
  resetToDefault: () => void;
}

export const useBrandingStore = create<BrandingState>((set) => ({
  tokens: { ...DEFAULT_BRAND },
  identity: { ...DEFAULT_IDENTITY },
  isCustomized: false,
  setBranding: ({ tokens, identity }) =>
    set((state) => ({
      tokens: tokens ? { ...state.tokens, ...tokens } : state.tokens,
      identity: identity ? { ...state.identity, ...identity } : state.identity,
      isCustomized: true,
    })),
  resetToDefault: () =>
    set({ tokens: { ...DEFAULT_BRAND }, identity: { ...DEFAULT_IDENTITY }, isCustomized: false }),
}));
