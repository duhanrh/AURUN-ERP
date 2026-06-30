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

export interface UnitOfMeasure {
  id: string;
  code: string;
  name: string;
  symbol: string;
  grams_factor: string;
  is_base: boolean;
  is_active: boolean;
  is_deleted: boolean;
}

export interface CreateUnitInput {
  code: string;
  name: string;
  symbol: string;
  grams_factor: string;
  is_active?: boolean;
}

export interface UpdateUnitInput {
  name?: string;
  symbol?: string;
  grams_factor?: string;
  is_active?: boolean;
}

export interface ConversionResult {
  quantity: string;
  from_unit: string;
  to_unit: string;
  grams: string;
  result: string;
}

export interface Currency {
  id: string;
  code: string;
  name: string;
  symbol: string;
  decimals: number;
  is_base: boolean;
  is_active: boolean;
  is_deleted: boolean;
}

export interface CreateCurrencyInput {
  code: string;
  name: string;
  symbol: string;
  decimals: number;
  is_active?: boolean;
}

export interface UpdateCurrencyInput {
  name?: string;
  symbol?: string;
  decimals?: number;
  is_active?: boolean;
}

export interface Company {
  legal_name: string;
  trade_name: string;
  tax_id: string;
  tax_regime: string;
  address: string;
  city: string;
  phone: string;
  email: string;
  website: string;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  is_active: boolean;
  last_used_at: string | null;
  revoked_at: string | null;
  created_at: string | null;
}

export interface CreatedApiKey {
  key: ApiKey;
  full_key: string;
}
