/** Tipos del dominio de Terceros (Clientes/Proveedores), espejo del API. */

export type PartyKind = 'customer' | 'supplier';
export type PartyStatus = 'active' | 'evaluation' | 'inactive';

export interface Party {
  id: string;
  kind: PartyKind;
  legal_name: string;
  tax_id: string;
  status: PartyStatus;
  country: string | null;
  city: string | null;
  contact_name: string | null;
  phone: string | null;
  email: string | null;
  notes: string | null;
  // Proveedor
  main_material: string | null;
  certifications: string | null;
  rating: number | null;
  // Cliente
  segment: string | null;
  preferred_material: string | null;
  credit_limit: number | null;
  created_at: string | null;
}

export interface PartyKpis {
  total: number;
  active: number;
  evaluation: number;
  inactive: number;
}

export interface CreatePartyInput {
  legal_name: string;
  tax_id: string;
  status?: PartyStatus;
  country?: string | null;
  city?: string | null;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  notes?: string | null;
  main_material?: string | null;
  certifications?: string | null;
  rating?: number | null;
  segment?: string | null;
  preferred_material?: string | null;
  credit_limit?: number | null;
}

export const STATUS_LABEL: Record<PartyStatus, string> = {
  active: 'Activo',
  evaluation: 'En evaluación',
  inactive: 'Inactivo',
};

/** Mapea el estado del tercero a la variante de badge del design system. */
export const STATUS_BADGE: Record<PartyStatus, string> = {
  active: 'badge-green',
  evaluation: 'badge-blue',
  inactive: 'badge-gray',
};
