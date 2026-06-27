/**
 * Puente entre el branding persistido en el backend (`tenant_branding`) y el
 * `brandingStore` que el ThemeProvider observa. Si el tenant no ha personalizado
 * (`is_customized=false`) se aplica el tema "Aurum" por defecto (RF-08).
 */

import { useBrandingStore } from '../../theme/brandingStore';
import { DEFAULT_BRAND, type BrandIdentity, type BrandTokens } from '../../theme/tokens';
import type { Branding } from './config.types';

/** Mapea la marca del backend a los tokens del tema, derivando lo que no persiste. */
export function brandingToTokens(b: Branding): BrandTokens {
  return {
    gold: b.color_primary ?? DEFAULT_BRAND.gold,
    // goldLight/goldDim no se personalizan en v1: se conservan del tema base.
    goldLight: DEFAULT_BRAND.goldLight,
    goldDim: DEFAULT_BRAND.goldDim,
    bgDeep: b.color_background ?? DEFAULT_BRAND.bgDeep,
    green: b.color_success ?? DEFAULT_BRAND.green,
    red: b.color_danger ?? DEFAULT_BRAND.red,
  };
}

/** Aplica una marca del backend al store (o restablece el tema por defecto). */
export function applyBranding(b: Branding): void {
  const store = useBrandingStore.getState();
  if (!b.is_customized) {
    store.resetToDefault();
    return;
  }
  const identity: Partial<BrandIdentity> = { logoUrl: b.logo_url };
  if (b.brand_name) identity.name = b.brand_name;
  if (b.tagline) identity.tagline = b.tagline;
  store.setBranding({ tokens: brandingToTokens(b), identity });
}
