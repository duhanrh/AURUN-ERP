/**
 * ThemeProvider — aplica los tokens de marca del tenant activo como
 * CSS Custom Properties en el elemento raíz, replicando el patrón
 * `document.documentElement.style.setProperty(...)` de la maqueta (sección 3.3).
 */

import { useEffect, type ReactNode } from 'react';

import { useBrandingStore } from './brandingStore';
import { BRAND_CSS_VARS, type BrandTokens } from './tokens';

function applyTokens(tokens: BrandTokens): void {
  const root = document.documentElement.style;
  (Object.keys(BRAND_CSS_VARS) as (keyof BrandTokens)[]).forEach((key) => {
    root.setProperty(BRAND_CSS_VARS[key], tokens[key]);
  });
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const tokens = useBrandingStore((s) => s.tokens);

  useEffect(() => {
    applyTokens(tokens);
  }, [tokens]);

  return <>{children}</>;
}
