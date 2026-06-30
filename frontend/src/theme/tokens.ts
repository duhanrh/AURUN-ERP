/**
 * Tokens de diseño del sistema AURUM ERP.
 *
 * Extraídos de la maqueta de referencia `erp_mineria_preciosos.html` (`:root`),
 * sección 2.4 del documento maestro. Constituyen el **tema "Aurum" por defecto**:
 * lo que se renderiza cuando un tenant no ha personalizado su branding (RF-08).
 *
 * En runtime estos valores se inyectan como CSS Custom Properties (ver ThemeProvider).
 * Más adelante, la parte personalizable por tenant se sobrescribirá desde
 * `tenant_branding` (sección 5.6); el resto permanece constante.
 */

/** Variables CSS personalizables por tenant (subconjunto de branding). */
export interface BrandTokens {
  /** Acento primario (--gold). */
  gold: string;
  /** Variante clara del acento (--gold-light). */
  goldLight: string;
  /** Variante oscura del acento (--gold-dim). */
  goldDim: string;
  /** Fondo base de la aplicación (--bg-deep). */
  bgDeep: string;
  /** Color de éxito / positivo (--green). */
  green: string;
  /** Color de alerta / negativo (--red). */
  red: string;
}

/** Identidad de marca (texto/logo) personalizable por tenant. */
export interface BrandIdentity {
  name: string;
  tagline: string;
  /** Símbolo (1-2 caracteres) usado si no hay logo en imagen. */
  symbol: string;
  /** URL del logo (Object Storage en producción); null = usar `symbol`. */
  logoUrl: string | null;
}

/** Colores estructurales del Design System (no personalizables por tenant en v1). */
export const STRUCTURAL_TOKENS = {
  bgPanel: '#13131A',
  bgCard: '#1A1A24',
  bgHover: '#22222E',
  border: '#2A2A38',
  borderGold: 'rgba(201,168,76,0.3)',
  textPrimary: '#F0EDE8',
  textSecondary: '#8A8A9A',
  textDim: '#4A4A5A',
  blue: '#4A7CC7',
  emerald: '#2D6B5A',
  silver: '#A8B0C0',
  platinum: '#D8DCE8',
} as const;

/** Tema "Aurum" por defecto del sistema (sección 2.4 / 5.6). */
export const DEFAULT_BRAND: BrandTokens = {
  gold: '#C9A84C',
  goldLight: '#E8C96A',
  goldDim: '#7A6228',
  bgDeep: '#0A0A0B',
  green: '#3DAA6E',
  red: '#D45454',
};

export const DEFAULT_IDENTITY: BrandIdentity = {
  name: 'AURUM ERP',
  tagline: 'Mining Intelligence',
  symbol: '⚜',
  logoUrl: null,
};

/** Presets de tema prototipados en la maqueta (Config → Apariencia). */
export const THEME_PRESETS: Record<string, BrandTokens> = {
  gold: { gold: '#C9A84C', goldLight: '#E8C96A', goldDim: '#7A6228', bgDeep: '#0A0A0B', green: '#3DAA6E', red: '#D45454' },
  emerald: { gold: '#3DAA6E', goldLight: '#5FCB90', goldDim: '#1F5C3E', bgDeep: '#0A0E0C', green: '#C9A84C', red: '#D45454' },
  platinum: { gold: '#A8B0C0', goldLight: '#D8DCE8', goldDim: '#5A6478', bgDeep: '#0E0E12', green: '#4A7CC7', red: '#D45454' },
  copper: { gold: '#C77D4A', goldLight: '#D4A574', goldDim: '#7A4A28', bgDeep: '#120D0A', green: '#3DAA6E', red: '#D45454' },
};

/**
 * Mapeo de tokens de marca → CSS Custom Properties que el ThemeProvider aplica
 * en runtime. `bgDeep` se omite a propósito: el fondo de página lo gobierna el
 * **modo claro/oscuro** (atributo `data-theme`), no el branding del tenant, para
 * que el conmutador de tema funcione de forma consistente. Ver `themeMode.ts`.
 */
export const BRAND_CSS_VARS: Partial<Record<keyof BrandTokens, string>> = {
  gold: '--gold',
  goldLight: '--gold-light',
  goldDim: '--gold-dim',
  green: '--green',
  red: '--red',
};
