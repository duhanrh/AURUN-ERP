/** Tipos del módulo de Configuración (Fase 7), espejo del API `/configuration`. */

export interface Branding {
  brand_name: string | null;
  tagline: string | null;
  logo_url: string | null;
  color_primary: string | null;
  color_background: string | null;
  color_success: string | null;
  color_danger: string | null;
  is_customized: boolean;
}

export interface UpdateBrandingInput {
  brand_name?: string | null;
  tagline?: string | null;
  logo_url?: string | null;
  color_primary?: string | null;
  color_background?: string | null;
  color_success?: string | null;
  color_danger?: string | null;
}

export interface BusinessParameters {
  base_currency: string;
  weight_unit: string;
  min_stock_g: string;
  min_margin_pct: string;
  language: string;
  timezone: string;
  date_format: string;
  regulatory_entity: string;
}

export interface ModuleConfig {
  key: string;
  label: string;
  is_active: boolean;
}
